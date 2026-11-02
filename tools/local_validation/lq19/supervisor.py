"""SC1 source-only Guard/library successor; Q/QD dispatch explicitly refuses."""
import ctypes
import dataclasses
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import threading
import time
import types
import unittest
import unittest.mock
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).absolute().parents[3]
HERE = Path(__file__).absolute().parent
BASE = ROOT / "runs/coordination/cho51_p3_sc1_qualification_20261102_held"
STOP = ROOT / "runs/coordination/PROJECT_STOP.json"
MAX_RECORD = 8 * 1024**2


def initial_json(raw):
    if type(raw) is not bytes or len(raw) > MAX_RECORD:
        raise ValueError("bootstrap record bound")
    def pairs(items):
        value = {}
        for key, entry in items:
            if key in value:
                raise ValueError("duplicate bootstrap JSON key")
            value[key] = entry
        return value
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def read_bound(path, cap=MAX_RECORD):
    with Path(path).open("rb") as stream:
        raw = stream.read(cap + 1)
    if len(raw) > cap:
        raise ValueError("bootstrap read cap")
    return raw


def module_bytes(name, path, raw, pin):
    if len(raw) != pin["bytes"] or hashlib.sha256(raw).hexdigest() != pin["sha256"]:
        raise ValueError("bootstrap source byte mismatch")
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = name.rpartition(".")[0]
    sys.modules[name] = module
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def namespaces():
    for name in ("tools", "tools.local_validation", "tools.local_validation.v1", "tools.local_validation.lq19",
                 "tools.local_validation.q4", "tools.local_validation.p1", "tools.local_validation.lp19", "tools.local_validation.lp1",
                 "tools.local_validation.l1", "tools.local_validation.lhost1", "tools.local_validation.lplan1", "tools.local_validation.lplan16"):
        if name not in sys.modules:
            mod = types.ModuleType(name)
            mod.__package__ = name
            mod.__path__ = []
            sys.modules[name] = mod


def load_source(request, name, relative, reader=None):
    path = ROOT / relative
    raw = read_bound(path) if reader is None else reader.read_small(path, request["sources"][relative])
    return module_bytes(name, path, raw, request["sources"][relative])


def absent(path):
    # Distinguish true missing leaf from permissions, missing ancestor or links.
    for ancestor in [*reversed(path.parent.parents), path.parent]:
        value = ancestor.lstat()
        if not ancestor.is_dir() or value.st_file_attributes & 1024:
            raise ValueError("absence ancestry unknown/reparse")
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise ValueError("required absent path exists")


class _Counters(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_uint32), ("faults", ctypes.c_uint32)] + [
        (name, ctypes.c_size_t) for name in ("peak_working", "working", "peak_paged",
        "paged", "peak_nonpaged", "nonpaged", "pagefile", "peak_pagefile", "private")]


class _MemoryStatus(ctypes.Structure):
    """SC-M layout only; every sensor call owns a fresh zeroed instance."""
    _fields_ = [("length", ctypes.c_uint32), ("load", ctypes.c_uint32)] + [
        (name, ctypes.c_uint64) for name in (
            "total_physical", "available_physical", "total_pagefile",
            "available_pagefile", "total_virtual", "available_virtual",
            "available_extended_virtual")]


def _validate_memory_status_abi():
    expected = {"length": (0, 4), "load": (4, 4),
                "total_physical": (8, 8), "available_physical": (16, 8),
                "total_pagefile": (24, 8), "available_pagefile": (32, 8),
                "total_virtual": (40, 8), "available_virtual": (48, 8),
                "available_extended_virtual": (56, 8)}
    if (ctypes.sizeof(ctypes.c_void_p) != 8 or ctypes.sizeof(_MemoryStatus) != 64
            or ctypes.alignment(_MemoryStatus) != 8
            or len(_MemoryStatus._fields_) != len(expected)
            or any(name not in expected
                   or (getattr(_MemoryStatus, name).offset, ctypes.sizeof(kind)) != expected[name]
                   for name, kind in _MemoryStatus._fields_)):
        raise ValueError("SC1 requires the exact 64-bit MEMORYSTATUSEX ABI")


def within_soft_watermark(origin_qpc, frequency, qpc, origin_utc, current_utc, seconds):
    """Use integer QPC arithmetic and the unchanged caller UTC origin."""
    return (type(origin_qpc) is int and type(frequency) is int and type(qpc) is int
            and type(seconds) is int and frequency > 0 and seconds in (45, 53, 55, 60)
            and origin_qpc <= qpc < origin_qpc + seconds * frequency
            and origin_utc <= current_utc < origin_utc + timedelta(seconds=seconds))


class Guard:
    def __init__(self, origin_utc, origin_qpc, frequency, cache):
        _validate_memory_status_abi()
        self.kernel = ctypes.WinDLL("kernel32.dll", use_last_error=True, winmode=0x800)
        self.psapi = ctypes.WinDLL("psapi.dll", use_last_error=True, winmode=0x800)
        self.kernel.QueryPerformanceCounter.argtypes = [ctypes.POINTER(ctypes.c_int64)]
        self.kernel.QueryPerformanceCounter.restype = ctypes.c_int
        self.kernel.QueryPerformanceFrequency.argtypes = [ctypes.POINTER(ctypes.c_int64)]
        self.kernel.QueryPerformanceFrequency.restype = ctypes.c_int
        self.kernel.GlobalMemoryStatusEx.argtypes = [ctypes.c_void_p]
        self.kernel.GlobalMemoryStatusEx.restype = ctypes.c_int
        self.kernel.GetCurrentProcess.restype = ctypes.c_void_p
        self.psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32]
        self.psapi.GetProcessMemoryInfo.restype = ctypes.c_int
        actual = ctypes.c_int64()
        if not self.kernel.QueryPerformanceFrequency(ctypes.byref(actual)) or actual.value != frequency:
            raise ValueError("caller QPC domain differs")
        self.origin = datetime.fromisoformat(origin_utc.replace("Z", "+00:00"))
        if self.origin.utcoffset() != timedelta(0) or type(origin_qpc) is not int or origin_qpc <= 0:
            raise ValueError("caller origin refused")
        self.origin_qpc, self.frequency = origin_qpc, frequency
        self.cache = cache
        self.work_seconds = 60
        self.soft_seconds = 60
        self.samples = 0
        self.min_ram = self.min_disk = 2**63 - 1
        self.max_private = 0
        self.started = time.monotonic()
        self.lock = threading.RLock()
        self.fault = None
        self.stop_watchdog = threading.Event()
        # Independent from test/native work. The outer caller also bounds this
        # supervisor and closes its original process handle after return.
        self.watchdog = threading.Thread(target=self.watch, daemon=True, name="Q-parent-watchdog")
        try:
            self.watchdog.start()
        except BaseException:
            self.stop_watchdog.set()
            if self.watchdog.is_alive(): self.watchdog.join(timeout=1)
            raise

    def elapsed(self):
        now = ctypes.c_int64()
        if not self.kernel.QueryPerformanceCounter(ctypes.byref(now)):
            raise OSError(ctypes.get_last_error(), "QPC")
        elapsed = (now.value - self.origin_qpc) / self.frequency
        if elapsed < 0:
            raise ValueError("QPC moved before origin")
        return elapsed

    def sample(self):
        memory = _MemoryStatus()
        memory.length = 64
        if not self.kernel.GlobalMemoryStatusEx(ctypes.byref(memory)):
            raise OSError(ctypes.get_last_error(), "RAM sensor")
        available = memory.available_physical
        free = shutil.disk_usage(ROOT).free
        counters = _Counters()
        counters.cb = ctypes.sizeof(counters)
        if not self.psapi.GetProcessMemoryInfo(self.kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            raise OSError(ctypes.get_last_error(), "parent memory sensor")
        with self.lock:
            self.samples += 1
            self.min_ram = min(self.min_ram, available)
            self.min_disk = min(self.min_disk, free)
            self.max_private = max(self.max_private, counters.private)
        if available < 4 * 1024**3 or free < 20 * 1024**3 or counters.private > 512 * 1024**2:
            raise RuntimeError("resource floor or parent commit cap")
        return {"available_ram_bytes": available, "free_disk_bytes": free,
                "parent_private_bytes": counters.private, "elapsed_seconds": self.elapsed()}

    def checkpoint(self):
        if self.fault:
            raise RuntimeError(self.fault)
        if self.elapsed() >= self.work_seconds or datetime.now(timezone.utc) >= self.origin + timedelta(seconds=self.work_seconds):
            raise RuntimeError("original caller work deadline")
        qpc = ctypes.c_int64()
        if not self.kernel.QueryPerformanceCounter(ctypes.byref(qpc)):
            raise OSError(ctypes.get_last_error(), 'QPC')
        if not within_soft_watermark(self.origin_qpc, self.frequency, qpc.value, self.origin,
                                     datetime.now(timezone.utc), self.soft_seconds):
            raise RuntimeError("QD original-origin watermark")
        absent(STOP)
        absent(self.cache)
        self.sample()
        return True

    def watch(self):
        while not self.stop_watchdog.wait(.1):
            try:
                if self.fault and time.monotonic() - getattr(self, '_fault_at', self.started) >= 5:
                    os._exit(125)
                elapsed = self.elapsed()
                if elapsed >= 65:
                    os._exit(124)  # owned Job dies on supervisor handle closure
                absent(STOP)
                absent(self.cache)
                self.sample()
                if elapsed >= 60:
                    self.fault = "work deadline"
                    self._fault_at = getattr(self, '_fault_at', time.monotonic())
            except BaseException as error:
                if self.fault is None:
                    self.fault = str(error)[:256]
                    first = time.monotonic()
                else:
                    first = getattr(self, "_fault_at", time.monotonic())
                self._fault_at = first
                if time.monotonic() - first >= 5:
                    os._exit(125)

    def summary(self):
        return {"sample_count": self.samples, "minimum_available_ram_bytes": self.min_ram,
                "minimum_free_disk_bytes": self.min_disk, "peak_parent_private_bytes": self.max_private,
                "elapsed_seconds": self.elapsed(), "guard_fault": self.fault}


def restrict(request, cache, fixture=None, native_paths=()):
    allowed = {str((ROOT / p)).lower() for p in request["sources"]}
    allowed |= {str(Path(p)).lower() for p in request["runtime"]["files"]}
    # Only these metadata inputs are read outside the pinned source/runtime.
    allowed |= {str(BASE / n).lower() for n in ("source-review.json", "contract-adoption.json")}
    allowed.add(str(BASE / ('api-mapping_'+request['operation_id']+'.json')).lower())
    allowed.add(str(BASE / ('native-helper_'+request['operation_id']+'.dll')).lower())
    allowed.add(str(BASE / ('native-diagnostic_'+request['operation_id']+'.json')).lower())
    allowed.add(str(BASE / ('l-bundle_'+request['operation_id']+'.json')).lower())
    allowed.update(str(Path(p)).lower() for p in native_paths)
    native_loads={str(p) for p in native_paths if str(p).endswith('.dll')}
    runtime_root = Path(request["runtime"]["root"])
    sys.path[:] = [str(runtime_root / "Lib"), str(runtime_root / "DLLs"), str(runtime_root)]
    write_root = None if fixture is None else str(fixture).lower()
    def audit_path(target):
        text = str(target)
        if text.startswith("\\\\?\\"):
            # Only reverse transport of an already valid ordinary drive path.
            # No normalization, UNC, device or dot-segment exception is added.
            canonical = text[4:].replace("\\", "/")
            sys.modules["tools.local_validation.v1.records"].windows_path(canonical, absolute=True)
            if text != "\\\\?\\" + canonical.replace("/", "\\"):
                raise PermissionError("noncanonical extended fixture transport")
            return str(Path(canonical)).lower()
        return str(Path(target).absolute()).lower()
    def inside(path):
        return write_root is not None and (path == write_root or path.startswith(write_root + os.sep))
    def audit(event, args):
        if event == "open":
            target = args[0]
            if type(target) is int:
                return  # original pipe/stdio descriptors, not a pathname
            text = audit_path(target)
            mode = args[1] or ""
            flags = args[2] or 0
            writing = any(c in mode for c in "wax+") or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            if writing:
                if not inside(text):
                    raise PermissionError("Q write outside owned fixtures")
            elif text not in allowed and not inside(text):
                # Fresh pycache absence permits an importlib cache miss only.
                if text.startswith(str(cache).lower() + os.sep) and not Path(target).exists():
                    return
                raise PermissionError("Q read outside pinned inputs")
        elif event in {"subprocess.Popen", "os.system", "os.posix_spawn", "socket.__new__", "socket.connect", "os.symlink"}:
            raise PermissionError("Q forbidden effect: " + event)
        elif event in {"os.remove", "os.rmdir", "os.mkdir", "os.rename", "os.link"}:
            paths = args[:2] if event in {"os.rename", "os.link"} else args[:1]
            if not all(inside(audit_path(p)) for p in paths):
                raise PermissionError("Q filesystem effect outside fixture")
        elif event == "ctypes.dlopen":
            name = args[0]
            if name not in ("kernel32", "kernel32.dll", "psapi.dll", None) and name not in native_loads:
                raise PermissionError("Q DLL outside declared Windows trust")
        elif event == "import" and len(args) > 1 and args[1]:
            path = str(Path(args[1]).absolute()).lower()
            if path not in allowed:
                raise PermissionError("Q import origin outside runtime pins")
    sys.addaudithook(audit)


def runtime_paths(root):
    """Exact Q base-runtime recipe; no package closure or loaded-image claim."""
    paths = {root / "python.exe"}
    paths.update(root.glob("*.dll"))
    for directory in (root / "Lib", root / "DLLs"):
        for current, dirs, files in os.walk(directory, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in ("site-packages", "__pycache__"))
            if len(Path(current).relative_to(root).parts) > 32:
                raise ValueError("runtime directory depth")
            for name in files:
                p = Path(current) / name
                if p.suffix.lower() in (".py", ".pyd", ".dll"):
                    paths.add(p)
                    if len(paths) > 2000:
                        raise ValueError("runtime count")
    return {p.as_posix() for p in paths}


def new_state():
    flags = ("limits_set", "limits_query_verified", "job_created", "created_suspended",
             "atomic_job_assignment_requested", "atomic_job_assignment_verified", "assigned", "membership_verified",
             "resumed", "job_empty_before_close", "job_closed", "root_exit_after_job_close",
             "process_handle_closed", "thread_handle_closed", "assignment_step_seen", "owned_job_termination_called")
    value = {key: False for key in flags}
    value.update(peak_samples=0, peak_process_commit_bytes=0, peak_job_commit_bytes=0,
                 cleanup_errors=[], peak_sampling_errors=[])
    return value


def lifecycle_ok(state):
    required = ("atomic_job_assignment_verified", "limits_query_verified", "job_empty_before_close", "job_closed",
                "root_exit_after_job_close", "process_handle_closed", "thread_handle_closed",
                "result_reader_closed", "result_writer_closed")
    return all(state.get(k) is True for k in required) and not state["cleanup_errors"] and not state["peak_sampling_errors"]


class PrefixTiming:
    """Bounded in-memory prefix, then a single independently owned journal."""
    def __init__(self, origin_utc, origin_qpc, frequency, admission_hash):
        self.origin_utc, self.oq, self.fq, self.ah = origin_utc, str(origin_qpc), str(frequency), admission_hash
        self.kernel = ctypes.WinDLL('kernel32.dll', use_last_error=True, winmode=0x800)
        self.kernel.QueryPerformanceCounter.argtypes = [ctypes.POINTER(ctypes.c_int64)]
        self.kernel.QueryPerformanceCounter.restype = ctypes.c_int
        self.items, self.size, self.guard, self.protocol, self.validator, self.journal = [], 0, None, None, None, None
        self.authority = 'pending'

    def capture(self):
        q = ctypes.c_int64()
        if not self.kernel.QueryPerformanceCounter(ctypes.byref(q)):
            raise OSError(ctypes.get_last_error(), 'timing QPC')
        now = datetime.now(timezone.utc)
        delta = now - datetime(1, 1, 1, tzinfo=timezone.utc)
        ticks = (delta.days * 86400 + delta.seconds) * 10_000_000 + delta.microseconds * 10
        samples = None
        if self.guard is not None:
            with self.guard.lock:
                samples = str(self.guard.samples)
        return str(q.value), str(ticks), samples

    def stage(self, stage, edge, code='ok', snapshot=None, nf=None, nb=None):
        if self.guard is not None:
            self.guard.checkpoint()
        q, u, samples = snapshot if snapshot is not None else self.capture()
        if stage == 'S08' and edge == 'end': self.authority = 'verified'
        n = len(self.items) + 1 if self.validator is None else self.validator.count
        event = {'v':1,'k':'E','n':str(n),'s':stage,'e':edge,'q':q,'u':u,'a':self.authority,
                 'c':code,'nf':None if nf is None else str(nf),'nb':None if nb is None else str(nb),'gs':samples}
        raw = (json.dumps(event, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode('ascii')
        if len(raw) > 512:
            raise ValueError('timing record capacity before buffer')
        if self.validator is None:
            if len(self.items) + 2 > 16 or self.size + len(raw) + 512 > 8192:
                raise ValueError('initial timing buffer cap')
            self.items.append(raw); self.size += len(raw)
        else:
            if self.journal is None and (len(self.items) + 1 > 32 or self.size + len(raw) > 16384):
                raise ValueError('early timing buffer cap')
            self.validator.accept(raw)
            if self.journal is None:
                self.items.append(raw); self.size += len(raw)
            else:
                self.journal.append(raw, flush=edge in ('end','mark'))
        if self.guard is not None:
            self.guard.checkpoint()

    def bind(self, protocol, operation):
        self.protocol = protocol
        origin = datetime.fromisoformat(self.origin_utc.replace('Z', '+00:00'))
        ticks = protocol.datetime_utc_ticks(origin)
        fraction = self.origin_utc.partition('.')[2].split('+')[0].rstrip('Z')
        if len(fraction) > 6:
            if len(fraction) != 7 or not fraction.isdigit(): raise ValueError('UTC tick precision')
            ticks += int(fraction[6])
        self.validator = protocol.TimingEvents('S', operation, self.ah, self.oq, self.fq, str(ticks), str(os.getpid()))
        header = protocol.encode_timing_event({'v':1,'k':'H','op':operation,'r':'S','n':'0','oq':self.oq,
                     'fq':self.fq,'ou':str(ticks),'pp':str(os.getpid()),'ah':self.ah})
        self.validator.accept(header)
        for raw in self.items: self.validator.accept(raw)
        self.items.insert(0, header); self.size += len(header)
        if len(self.items) > 16 or self.size > 8192: raise ValueError('initial timing buffer cap')

    def publish(self, journal):
        self.journal = journal
        for raw in self.items:
            self.guard.checkpoint(); journal.append(raw); self.guard.checkpoint()
        journal.flush()
        self.items.clear(); self.size = 0

    def terminal(self, complete):
        self.guard.checkpoint()
        q, u, _ = self.capture()
        raw = self.protocol.encode_timing_event({'v':1,'k':'T','n':str(self.validator.count),'q':q,'u':u,
                  'c':'ready_for_original_close' if complete else 'incomplete',
                  'lv':'complete' if complete else 'incomplete'})
        self.validator.accept(raw); self.journal.append(raw, flush=True)
        self.guard.checkpoint()

    def validate_readback(self, raw):
        validator = self.protocol.TimingEvents('S', self.validator.operation, self.ah, self.oq, self.fq,
                                                str(self.validator.ou), str(os.getpid()))
        if not raw.endswith(b'\n'): raise ValueError('torn journal')
        for line in raw.splitlines(keepends=True): validator.accept(line)
        if not validator.terminal or validator.count != self.validator.count:
            raise ValueError('journal terminal/readback mismatch')


def main(admission_path, admission_hash, origin_utc, origin_qpc, frequency, mapping_sha, mapping_identity, mapping_bytes, bundle_sha, bundle_identity, bundle_bytes):
    """QD prefix only. No mode dispatch, suite collection, or child launch."""
    raise RuntimeError('SC1 source-only successor: Q/QD dispatch remains unavailable')
    timing = guard = reader = outputs = journal = protocol = records = None
    request = operation = error = None
    startup, operations, handoff_capabilities = [], [], []
    mapping_ref = diagnostic_ref = diagnostic_identity = None
    result_report = None
    complete = final_verified = journal_create_started = False
    handle_closure = {'outputs':False, 'inputs':False, 'output_state':'not_created'}
    ledger = {'files':2, 'bytes':4096 + 1048576, 'paths':set()}
    try:
        if sys.platform != 'win32': raise ValueError('Windows QD required')
        timing = PrefixTiming(origin_utc, origin_qpc, frequency, admission_hash)
        timing.stage('S01', 'begin')
        admission_path = Path(admission_path)
        if admission_path.parent != BASE or not admission_path.name.startswith('admission_'):
            raise ValueError('admission namespace')
        raw = read_bound(admission_path)
        if hashlib.sha256(raw).hexdigest() != admission_hash: raise ValueError('admission caller hash')
        timing.stage('S01', 'end')
        timing.stage('S02', 'begin')
        preliminary = initial_json(raw)
        operation = preliminary['operation_id']
        cache = BASE / 'disabled-bytecode' / operation
        guard = Guard(origin_utc, int(origin_qpc), int(frequency), cache)
        guard.soft_seconds = 45
        timing.guard = guard
        timing.stage('S02', 'end')
        timing.stage('S03', 'begin')
        namespaces()
        records = load_source(preliminary, 'tools.local_validation.v1.records', 'tools/local_validation/v1/records.py')
        load_source(preliminary, 'tools.local_validation.lp19.pe', 'tools/local_validation/lp19/pe.py')
        load_source(preliminary, 'tools.local_validation.lp19.api_mapping', 'tools/local_validation/lp19/api_mapping.py')
        load_source(preliminary, 'tools.local_validation.lp19.bootstrap_contract', 'tools/local_validation/lp19/bootstrap_contract.py')
        protocol = load_source(preliminary, 'tools.local_validation.lq19.protocol', 'tools/local_validation/lq19/protocol.py')
        request = protocol.validate_admission(records.strict_loads(raw), ROOT.as_posix(), origin_utc)
        native = load_source(request, 'tools.local_validation.lq19.native_reader', 'tools/local_validation/lq19/native_reader.py')
        l_native = load_source(request, 'tools.local_validation.lq19.l_native', 'tools/local_validation/lq19/l_native.py')
        reader = native.RetainedReader(guard.checkpoint, max_files=2000, max_total_bytes=64*1024**2, max_file_bytes=16*1024**2)
        timing.bind(protocol, operation)
        timing.stage('S03', 'end')

        timing.stage('S04', 'begin')
        for index in range(2):
            guard.checkpoint(); startup.append(guard.sample())
            if index == 0: time.sleep(.21)
        if sys.pycache_prefix != str(cache) or sys.flags.isolated != 1 or not sys.flags.no_site:
            raise ValueError('isolated fresh bytecode configuration required')
        reader.read_small(admission_path, {'bytes':len(raw), 'sha256':admission_hash})
        timing.stage('S04', 'end')
        timing.stage('S05', 'begin', nf=0, nb=0)
        source_count = source_bytes = 0
        for name, expected in request['sources'].items():
            retained = reader.retain(ROOT / name, expected)
            source_count += 1; source_bytes += retained['bytes']
        timing.stage('S05', 'end', nf=source_count, nb=source_bytes)
        timing.stage('S06', 'begin', nf=0, nb=0)
        runtime_count = runtime_bytes = 0
        for name, expected in request['runtime']['files'].items():
            retained = reader.retain(Path(name), expected)
            runtime_count += 1; runtime_bytes += retained['bytes']
        timing.stage('S06', 'end', nf=runtime_count, nb=runtime_bytes)
        timing.stage('S07', 'begin')
        if Path(sys.executable).as_posix() != request['python'] or runtime_paths(Path(request['runtime']['root'])) != set(request['runtime']['files']):
            raise ValueError('current exact runtime census')
        timing.stage('S07', 'end')
        timing.stage('S08', 'begin')
        review = records.strict_loads(reader.read_small(BASE / request['review']['path'], {k:request['review'][k] for k in ('bytes','sha256')}))
        adoption = records.strict_loads(reader.read_small(BASE / request['adoption']['path'], {k:request['adoption'][k] for k in ('bytes','sha256')}))
        protocol.validate_chain(request, review, adoption)
        timing.stage('S08', 'end')
        timing.stage('S09', 'begin')
        future_out = BASE / 'attempts' / operation
        ledger['paths'].update((native.checked_path(future_out/'claim.json'), native.checked_path(future_out/'receipt.json')))
        journal_create_started = True
        journal = native.NativeTimingJournal(guard.checkpoint, BASE, operation, ledger, timing.validate_readback)
        timing.publish(journal)
        timing.stage('S09', 'end')

        timing.stage('S10', 'begin')
        mapping_path = reader.authorize_handoff(BASE.as_posix(), operation, 'mapping', {'bytes':int(mapping_bytes),'sha256':mapping_sha}, mapping_identity)
        mapping_raw = reader.read_small(mapping_path, max_bytes=1048576)
        mapping_descriptor = reader.retain(mapping_path)
        if hashlib.sha256(mapping_raw).hexdigest() != mapping_sha or mapping_descriptor['native_identity']['volume_serial'] + ':' + mapping_descriptor['native_identity']['file_id'] != mapping_identity:
            raise ValueError('caller-authenticated API mapping original identity')
        mapping_ref = {'path':protocol.PHASE+'/api-mapping_'+operation+'.json','bytes':len(mapping_raw),'sha256':mapping_sha}
        plan_relative = 'tools/local_validation/lp19/api_query_plan.json'
        plan = records.strict_loads(reader.read_small(ROOT/plan_relative, request['sources'][plan_relative]))
        mapping_value = records.strict_loads(mapping_raw)
        sys.modules['tools.local_validation.lp19.api_mapping'].validate_receipt(mapping_value,plan,operation,mapping_value['native_helper'],mapping_identity,request['sources'][plan_relative]['sha256'])
        timing.stage('S10', 'end')
        timing.stage('S11', 'begin')
        diagnostic_ref = mapping_value['native_diagnostic']; diagnostic_identity = mapping_value['native_diagnostic_native_identity']
        diagnostic_path = reader.authorize_handoff(BASE.as_posix(),operation,'diagnostic',{k:diagnostic_ref[k] for k in ('bytes','sha256')},diagnostic_identity)
        diagnostic_raw = reader.read_small(diagnostic_path,{k:diagnostic_ref[k] for k in ('bytes','sha256')},max_bytes=1048576)
        diagnostic_native = reader.retain(diagnostic_path)['native_identity']
        records.require(diagnostic_native['volume_serial']+':'+diagnostic_native['file_id']==diagnostic_identity,'diagnostic original identity')
        diagnostic = records.strict_loads(diagnostic_raw)
        sys.modules['tools.local_validation.lp19.api_mapping'].validate_diagnostic(diagnostic,plan,operation,mapping_value['native_helper'],diagnostic_identity,request['sources'][plan_relative]['sha256'],True)
        records.require(diagnostic['observation']==mapping_value['observation'] and diagnostic['native_helper_native_identity']==mapping_value['native_helper_native_identity'],'diagnostic/mapping observed join')
        timing.stage('S11', 'end')
        timing.stage('S12', 'begin')
        helper_path = reader.authorize_handoff(BASE.as_posix(),operation,'helper',{k:mapping_value['native_helper'][k] for k in ('bytes','sha256')},mapping_value['native_helper_native_identity'])
        reader.retain(helper_path); handoff_capabilities = reader.handoff_capabilities()
        policy_relative = 'tools/local_validation/lp19/native_policy.json'
        policy = records.strict_loads(reader.read_small(ROOT/policy_relative,request['sources'][policy_relative]))
        records.require(all(row['host'] in {p['name'] for p in policy['platform_images']} for row in mapping_value['observation']['rows']), 'resident hosts explicitly trusted')
        predecessor = request['predecessor']
        reader.retain(ROOT/predecessor['path'],{k:predecessor[k] for k in ('bytes','sha256')})
        timing.stage('S12', 'end')
        timing.stage('S13', 'begin')
        out = BASE / 'attempts' / operation
        reader.retain_directory(out.parent); absent(out); out.mkdir(); reader.retain_directory(out)
        timing.stage('S13', 'end')
        timing.stage('S14', 'begin')
        l_refs = l_native.load_bundle(reader,BASE.as_posix(),operation,bundle_sha,bundle_identity,bundle_bytes)
        timing.stage('S14', 'end')
        timing.stage('S15', 'begin')
        restrict(request, cache, out, [v['path'] for v in l_refs.values()])
        outputs = native.RetainedOutputs(reader, out, max_files=40, max_total_bytes=8*1024**2, max_file_bytes=1024**2)
        outputs._reserved.add(journal.path); outputs._reserved_bytes = 65536
        handle_closure['output_state'] = 'open'
        outputs.write('claim.json', records.canonical_bytes({'schema':'cho51_startup_timing_claim_v1','operation_id':operation,
                      'admission_sha256':admission_hash,'origin_utc':origin_utc,'origin_qpc':int(origin_qpc),'frequency':int(frequency),
                      'diagnostic_outcome':'incomplete','diagnostic_prefix_complete':False,
                      'timing':{'caller':None,'supervisor':None},'required_q_obligations_complete':False,
                      'qualification_accepted':False}), reserve_bytes=4096)
        fixture = out / 'fixtures'; fixture.mkdir()
        for key in ('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONUSERBASE'): os.environ.pop(key,None)
        os.environ.update(OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1',
                          CUDA_VISIBLE_DEVICES='-1', PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
        timing.stage('S15', 'end')
        timing.stage('S16', 'mark', 'prefix_stop')

        guard.soft_seconds = 53
        timing.stage('S17', 'begin'); reader.verify(); timing.stage('S17', 'end')
        timing.stage('S18', 'begin')
        if runtime_paths(Path(request['runtime']['root'])) != set(request['runtime']['files']): raise ValueError('runtime census drift')
        if any(fixture.iterdir()): raise ValueError('QD creates no suite fixtures')
        guard.checkpoint(); timing.stage('S18', 'end')
        timing.stage('S19', 'begin')
        outputs.verify()
        guard.checkpoint()  # Existing inputs/census/outputs must all finish before53.
        final_verified = True
        guard.soft_seconds = 55
        receipt = {'schema':'cho51_startup_timing_receipt_v1','operation_id':operation,'accepted_by_supervisor':False,
                   'error':None,'operations':operations,'resources':guard.summary(),'external_caller_return_pending':True,
                   'independent_actual_review_pending':True,'original_handle_closure_pending':True,
                   'diagnostic_outcome':'prefix_pending_review','diagnostic_prefix_complete':False,
                   'timing':{'caller':None,'supervisor':None},'required_q_obligations_complete':False,'qualification_accepted':False,
                   **protocol.FALSES}
        outputs.write('receipt.json', records.canonical_bytes(receipt), reserve_bytes=1048576)
        outputs.verify(); outputs.close(); handle_closure['outputs'] = True; handle_closure['output_state'] = 'closed'
        timing.stage('S19', 'end')
        timing.stage('S20', 'begin'); reader.close(); handle_closure['inputs'] = True; timing.stage('S20', 'end')
        timing.stage('S21', 'mark'); timing.terminal(True)
        journal.seal(); journal.close()
        guard.checkpoint()
        complete = True
    except BaseException as exc:
        error = type(exc).__name__ + ': ' + str(exc)[:768]
        # The first failure is preserved; journal faults cannot replace it.
        if timing is not None and timing.journal is not None and not timing.journal.failed:
            try:
                stage = timing.validator.stack[-1] if timing.validator.stack else 'S21'
                timing.stage(stage, 'fail', 'unknown')
            except BaseException:
                pass
        if reader is not None:
            reader.checkpoint = lambda: True  # cleanup only, never final verification
    finally:
        if outputs is not None and not handle_closure['outputs']:
            try:
                receipt_path = native.checked_path(out / 'receipt.json')
                if not outputs._closed and receipt_path not in outputs._reserved:
                    failure_receipt = {'schema':'cho51_startup_timing_receipt_v1','operation_id':operation,
                        'accepted_by_supervisor':False,'error':error,'operations':operations,'resources':guard.summary(),
                        'external_caller_return_pending':True,'independent_actual_review_pending':True,
                        'original_handle_closure_pending':True,'diagnostic_outcome':'incomplete',
                        'diagnostic_prefix_complete':False,'timing':{'caller':None,'supervisor':None},
                        'required_q_obligations_complete':False,'qualification_accepted':False,**protocol.FALSES}
                    outputs.write('receipt.json', records.canonical_bytes(failure_receipt), reserve_bytes=1048576)
                if not outputs._closed: outputs.verify()
            except BaseException as exc:
                if error is None: error = type(exc).__name__ + ': ' + str(exc)[:768]
            finally:
                try:
                    outputs.close(); handle_closure['outputs'] = True; handle_closure['output_state'] = 'closed'
                except BaseException as exc:
                    if error is None: error = type(exc).__name__ + ': ' + str(exc)[:768]
        if reader is not None and not handle_closure['inputs']:
            try:
                reader.close(); handle_closure['inputs'] = True
            except BaseException as exc:
                if error is None: error = type(exc).__name__ + ': ' + str(exc)[:768]
        if journal is not None:
            try:
                if not journal.sealed and not journal.failed and timing is not None and timing.validator is not None:
                    timing.stage('S21', 'mark'); timing.terminal(False); journal.seal()
            except BaseException:
                pass
            try: journal.close()
            except BaseException as exc:
                if error is None: error = type(exc).__name__ + ': ' + str(exc)[:768]
                complete = False
        if guard is not None:
            guard.stop_watchdog.set()
            guard.watchdog.join(timeout=1)
            if guard.watchdog.is_alive():
                if error is None: error = 'watchdog shutdown not observed'
                complete = False
    if protocol is None:
        raise RuntimeError(error or 'QD early initialization refused')
    # Shutdown may consume the publication reserve. Use the original clock
    # without restarting a stopped watchdog or granting another work interval.
    def publication_clock():
        if guard is None or guard.fault or guard.watchdog.is_alive(): return False
        qpc = ctypes.c_int64()
        if not guard.kernel.QueryPerformanceCounter(ctypes.byref(qpc)): return False
        return within_soft_watermark(guard.origin_qpc, guard.frequency, qpc.value, guard.origin,
                                     datetime.now(timezone.utc), 55)
    if not publication_clock():
        complete = False
        if error is None: error = 'QD publication deadline/guard refused after shutdown'
    if error is not None or not final_verified: complete = False
    descriptor = None if journal is None else journal.descriptor()
    custody_unknown = ((journal_create_started and journal is None)
                       or (journal is not None and not (journal.file_closed and journal.ancestry_closed))
                       or (reader is not None and not handle_closure['inputs'])
                       or (outputs is not None and not handle_closure['outputs']))
    allocation = {'supervisor_files':ledger['files'] if outputs is None else max(ledger['files'],len(outputs._reserved)),
                  'supervisor_bytes':ledger['bytes'] if outputs is None else max(ledger['bytes'],outputs._reserved_bytes),
                  'supervisor_file_cap':40,'supervisor_byte_cap':8*1024**2,
                  'fixture_files':0 if complete else None,'fixture_bytes':0 if complete else None,
                  'fixture_largest':0 if complete else None}
    returned = {'schema':'cho51_startup_timing_supervisor_return_v1','operation_id':operation,
          'accepted_by_supervisor':False,'error':error,'handle_closure':handle_closure,
          'api_mapping':mapping_ref,'api_mapping_native_identity':mapping_identity,
          'native_diagnostic':diagnostic_ref,'native_diagnostic_native_identity':diagnostic_identity,
          'caller_artifact_capabilities':handoff_capabilities,'resources':None if guard is None else guard.summary(),
          'output_allocation':allocation,'diagnostic_outcome':'prefix_pending_review' if complete else ('custody_unknown' if custody_unknown else 'incomplete'),
          'diagnostic_prefix_complete':complete,'timing':{'caller':None,'supervisor':descriptor},
          'required_q_obligations_complete':False,'qualification_accepted':False,**protocol.FALSES}
    encoded = json.dumps(returned, allow_nan=False)
    if not publication_clock():
        complete = False
        returned.update(diagnostic_prefix_complete=False,
                        diagnostic_outcome='custody_unknown' if custody_unknown else 'incomplete',
                        error=error or 'QD publication deadline refused immediately before output')
        encoded = json.dumps(returned, allow_nan=False)
    print(encoded, flush=True)
    if not publication_clock(): return 1  # Caller refuses even if an earlier positive frame was emitted.
    return 0 if complete else 1











