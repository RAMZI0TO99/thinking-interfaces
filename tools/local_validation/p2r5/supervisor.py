"""File-only P supervisor; separately admitted original caller owns its Job.

Only verified observer source is compiled. Package/candidate bytes remain inert.
Platform images are declared local Windows trust, not physical-reader exceptions.
"""
import ctypes
import functools
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import sys
import threading
import time
import types
import uuid
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).absolute().parents[3]
HERE = Path(__file__).absolute().parent
PHASE = "runs/coordination/cho51_p3_dependency_prepare_20261029_p5"
Q_PHASE = "runs/coordination/cho51_p3_dependency_prepare_20261029_q5"
BASE = ROOT / PHASE
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
    for name in ("tools", "tools.local_validation", "tools.local_validation.v1", "tools.local_validation.p2r5",
                 "tools.local_validation.q4", "tools.local_validation.p1"):
        if name not in sys.modules:
            mod = types.ModuleType(name)
            mod.__package__ = name
            mod.__path__ = []
            sys.modules[name] = mod


def load_source(request, name, relative, reader=None):
    path = ROOT / relative
    raw = read_bound(path) if reader is None else reader.read_small(path, request["sources"][relative])
    return module_bytes(name, path, raw, request["sources"][relative])


@functools.lru_cache(maxsize=256)
def lexical_ancestors(path_text):
    """Cache strings only; never cache metadata, existence or guard results."""
    path = Path(path_text)
    return tuple(str(p) for p in (*reversed(path.parent.parents), path.parent))


def absent(path, stat_path=os.stat):
    # Fresh one-call no-follow metadata for every ancestor on every invocation.
    text = str(path)
    for ancestor in lexical_ancestors(text):
        value = stat_path(ancestor, follow_symlinks=False)
        if not value.st_file_attributes & 0x10 or value.st_file_attributes & 0x440:
            raise ValueError("absence ancestry unknown/reparse")
    try:
        stat_path(text, follow_symlinks=False)
    except FileNotFoundError:
        return
    raise ValueError("required absent path exists")


class _Counters(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_uint32), ("faults", ctypes.c_uint32)] + [
        (name, ctypes.c_size_t) for name in ("peak_working", "working", "peak_paged",
        "paged", "peak_nonpaged", "nonpaged", "pagefile", "peak_pagefile", "private")]


class Guard:
    def __init__(self, origin_utc, origin_qpc, frequency, cache):
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
        self.work_seconds = 240
        self.samples = 0
        self.min_ram = self.min_disk = 2**63 - 1
        self.max_private = 0
        self.started = time.monotonic()
        self.lock = threading.RLock()
        self.fault = None
        self.cleaning = False
        self.cleanup_deadline = 245.0
        self.stop_watchdog = threading.Event()
        # Independent from test/native work. The outer caller also bounds this
        # supervisor and closes its original process handle after return.
        self.watchdog = threading.Thread(target=self.watch, daemon=True, name="P-work-watchdog")
        self.watchdog.start()

    def elapsed(self):
        now = ctypes.c_int64()
        if not self.kernel.QueryPerformanceCounter(ctypes.byref(now)):
            raise OSError(ctypes.get_last_error(), "QPC")
        elapsed = (now.value - self.origin_qpc) / self.frequency
        if elapsed < 0:
            raise ValueError("QPC moved before origin")
        return elapsed

    def sample(self):
        memory = ctypes.create_string_buffer(64)
        ctypes.c_uint32.from_buffer(memory).value = 64
        if not self.kernel.GlobalMemoryStatusEx(memory):
            raise OSError(ctypes.get_last_error(), "RAM sensor")
        available = ctypes.c_uint64.from_buffer(memory, 16).value
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
        if available < 4 * 1024**3 or free < 20 * 1024**3 or counters.private > 4096 * 1024**2:
            raise RuntimeError("resource floor or parent commit cap")
        return {"available_ram_bytes": available, "free_disk_bytes": free,
                "parent_private_bytes": counters.private, "elapsed_seconds": self.elapsed()}

    def checkpoint(self):
        if self.fault:
            raise RuntimeError(self.fault)
        if self.cleaning:
            raise RuntimeError("work after cleanup origin")
        if self.elapsed() >= self.work_seconds or datetime.now(timezone.utc) >= self.origin + timedelta(seconds=self.work_seconds):
            raise RuntimeError("original caller work deadline")
        absent(STOP)
        absent(self.cache)
        self.sample()
        return True

    def enter_cleanup(self):
        self.cleaning = True
        self.cleanup_deadline = min(245.0, self.elapsed() + 5)

    def watch(self):
        while not self.stop_watchdog.wait(.1):
            try:
                if self.fault and time.monotonic() - getattr(self, '_fault_at', self.started) >= 5:
                    os._exit(125)
                elapsed = self.elapsed()
                if elapsed >= self.cleanup_deadline:
                    os._exit(124)  # owned Job dies on supervisor handle closure
                absent(STOP)
                absent(self.cache)
                self.sample()
                if elapsed >= 240 and not self.cleaning:
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


def install_audit(request, admission_path, cache, out):
    """Mutable finite allowlist; additions are reviewed retained-input pins only."""
    allowed = {str((ROOT / p).absolute()).lower() for p in request["sources"]}
    allowed.update(str(Path(p).absolute()).lower() for p in request["runtime"]["files"])
    allowed.add(str(admission_path.absolute()).lower())
    observer = {str((ROOT / p).absolute()).lower() for p in request["sources"]
                if p.startswith("tools/local_validation/") and p.endswith(".py")}
    runtime = {str(Path(p).absolute()).lower() for p in request["runtime"]["files"]}
    writes = str(out.absolute()).lower()

    def add(path):
        allowed.add(str(Path(path).absolute()).lower())

    def inside(path):
        return path == writes or path.startswith(writes + os.sep)

    def audit(event, args):
        if event == "open":
            if type(args[0]) is int:
                return
            path = str(Path(args[0]).absolute()).lower()
            mode, flags = args[1] or "", args[2] or 0
            writing = any(c in mode for c in "wax+") or bool(flags &
                (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            if writing:
                if not inside(path):
                    raise PermissionError("P ordinary write outside owned output")
            elif path not in allowed and not inside(path):
                if path.startswith(str(cache).lower() + os.sep):
                    # No cache byte read is permitted; only an actual miss.
                    try:
                        Path(path).lstat()
                    except FileNotFoundError:
                        return
                raise PermissionError("P ordinary read outside finite pinned inputs")
        elif event in {"subprocess.Popen", "os.system", "os.posix_spawn", "os.exec",
                       "socket.__new__", "socket.connect", "os.symlink", "os.link"}:
            raise PermissionError("P forbidden effect: " + event)
        elif event in {"os.remove", "os.rmdir", "os.mkdir", "os.rename"}:
            paths = args[:2] if event == "os.rename" else args[:1]
            if not all(inside(str(Path(p).absolute()).lower()) for p in paths):
                raise PermissionError("P ordinary filesystem effect outside output")
        elif event == "ctypes.dlopen":
            if args[0] not in ("kernel32.dll", "psapi.dll", None):
                raise PermissionError("P undeclared native load")
        elif event == "import" and len(args) > 1 and args[1]:
            if str(Path(args[1]).absolute()).lower() not in runtime | observer:
                raise PermissionError("P import outside observer/bootstrap")
        elif event == "compile":
            if str(Path(args[1]).absolute()).lower() not in observer | runtime:
                raise PermissionError("P compile outside verified observer/bootstrap")
        elif event == "exec":
            if str(Path(args[0].co_filename).absolute()).lower() not in observer | runtime:
                raise PermissionError("P exec outside verified observer/bootstrap")
    sys.addaudithook(audit)
    return add


def runtime_paths(root):
    paths = {root / "python.exe"}
    paths.update(root.glob("*.dll"))
    for directory in (root / "Lib", root / "DLLs"):
        for current, dirs, files in os.walk(directory, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in ("site-packages", "__pycache__"))
            if len(Path(current).relative_to(root).parts) > 32:
                raise ValueError("runtime directory depth")
            for name in files:
                if Path(name).suffix.lower() in (".py", ".pyd", ".dll"):
                    paths.add(Path(current) / name)
                    if len(paths) > 2000:
                        raise ValueError("runtime count")
    return {p.as_posix() for p in paths}


def load_ref(ref, reader, records, add_allowed):
    records.closed(ref, ("path", "bytes", "sha256"))
    records.windows_path(ref["path"])
    path = ROOT / ref["path"]
    add_allowed(path)
    return records.strict_loads(reader.read_small(path, {k: ref[k] for k in ("bytes", "sha256")}))


def read_pin_map(request, recipe, reader, records, protocol, add_allowed):
    index = load_ref(request["map_index"], reader, records, add_allowed)
    records.closed(index, ("schema", "recipe_sha256", "files", "total_bytes", "pages", "extra_paths"))
    records.require(index["schema"] == "cho51_p2_pin_index_v1" and
        index["recipe_sha256"] == request["sources"]["tools/local_validation/p2r5/dependency_recipe.json"]["sha256"],
        "pin index recipe join")
    records.exact_int(index["files"], 1, 25000)
    records.exact_int(index["total_bytes"], upper=4 * 1024**3)
    records.require(type(index["extra_paths"]) is list and index["extra_paths"] == request["extra_paths"],
                    "pin index exact extras")
    pages = index["pages"]
    records.require(type(pages) is list and 1 <= len(pages) <= 256, "pin page count")
    pins, aliases, page_paths, total = {}, set(), set(), 0
    for number, ref in enumerate(pages):
        reader._check()
        records.closed(ref, ("path", "bytes", "sha256", "rows"))
        records.require(ref["path"] == PHASE + "/pin-page-" + str(number).zfill(3) + ".json",
                        "exact ordered pin page namespace")
        records.exact_int(ref["rows"], 1, 2048)
        protocol.pin({k: ref[k] for k in ("bytes", "sha256")})
        records.require(ref["path"] not in page_paths, "duplicate pin page")
        page_paths.add(ref["path"])
        page = load_ref({k: ref[k] for k in ("path", "bytes", "sha256")}, reader, records, add_allowed)
        records.closed(page, ("schema", "rows"))
        rows = page["rows"]
        records.require(page["schema"] == "cho51_p2_pin_page_v1" and type(rows) is list
                        and len(rows) == ref["rows"], "pin page schema/rows")
        for row in rows:
            records.closed(row, ("path", "bytes", "sha256"))
            path = records.windows_path(row["path"], absolute=True)
            records.require(path.lower() not in aliases, "physical pin alias")
            protocol.pin({k: row[k] for k in ("bytes", "sha256")}, 2 * 1024**3)
            aliases.add(path.lower())
            pins[path] = {k: row[k] for k in ("bytes", "sha256")}
            total += row["bytes"]
            records.require(len(pins) <= 25000 and total <= 4 * 1024**3, "physical pin aggregate caps")
    records.require(len(pins) == index["files"] and total == index["total_bytes"], "pin index aggregate join")
    # Explicitly prevent control self-hash cycles, even if a caller supplied one.
    controls = {str((ROOT / p).as_posix()).lower() for p in page_paths}
    controls.add((ROOT / request["map_index"]["path"]).as_posix().lower())
    records.require(not (set(path.lower() for path in pins) & controls), "control/map self hash refused")
    return index, pins


def retained_range(reader, path, offset, count):
    """Exact bounded seek/read under the original retained physical identity."""
    reader._check()
    handle, descriptor, facts = reader._files[path]
    if type(offset) is not int or type(count) is not int or not 0 <= count <= 65536 or not 0 <= offset <= descriptor["bytes"] - count:
        raise ValueError("retained PE range cap")
    if reader._facts(handle, path, False) != facts:
        raise ValueError("PE original handle facts drift")
    if not reader.api.SetFilePointerEx(handle, offset, None, 0):
        raise reader._error("PE retained range seek")
    buffer, read = ctypes.create_string_buffer(count), ctypes.c_uint32()
    if count and not reader.api.ReadFile(handle, buffer, count, ctypes.byref(read), None):
        raise reader._error("PE retained range read")
    reader._check()
    if read.value != count or reader._facts(handle, path, False) != facts:
        raise ValueError("PE range short read/facts drift")
    return buffer.raw[:count]


def platform_file(path, guard):
    """Declared OS trust metadata, intentionally outside physical-reader claims."""
    guard.checkpoint()
    if type(path) is not str or not path.startswith("C:/Windows/System32/") or "/" in path[len("C:/Windows/System32/"):]:
        raise ValueError("exact declared System32 image path")
    for ancestor in [*reversed(Path(path).parent.parents), Path(path).parent]:
        info = ancestor.lstat()
        if not info.st_file_attributes & 0x10 or info.st_file_attributes & 0x440:
            raise ValueError("platform image ancestry")
    info = os.stat(path, follow_symlinks=False)
    if info.st_file_attributes & 0x450 or not info.st_size > 0:
        raise ValueError("platform ordinary image required")
    guard.checkpoint()
    return {"path": path, "bytes": info.st_size, "file_id_observation_hex": format(info.st_ino, "x"),
            "links": info.st_nlink, "basis": "declared_local_Windows_platform_trust_not_physical_reader_pin"}


def native_observation(pins, policy, reader, guard, pe, records, outputs, add_allowed):
    records.closed(policy, ("schema", "created_utc", "platform_images", "scope", "native_search_qualified",
        "abi_qualified", "launch_authorized", "scientific_admission", "api_sets", "api_set_source"))
    records.require(policy["schema"] == "cho51_p2_native_policy_v1" and all(policy[k] is False
        for k in ("native_search_qualified", "abi_qualified", "launch_authorized", "scientific_admission")), "native policy flags")
    images = policy["platform_images"]
    records.require(type(images) is list and 1 <= len(images) <= 512, "platform image count")
    names = {}
    for row in images:
        records.closed(row, ("name", "path", "basis", "present_at_static_inventory"))
        records.require(type(row["name"]) is str and row["name"] == row["name"].lower()
            and row["path"] == "C:/Windows/System32/" + row["name"] and row["name"] not in names,
            "platform image name/path")
        names[row["name"]] = row
    source = policy["api_set_source"]
    records.closed(source, ("path", "bytes", "sha256", "schema_version", "method"))
    records.require(source["path"] == "C:/Windows/System32/apisetschema.dll" and
        type(source["schema_version"]) is int and source["schema_version"] == 6, "API set source")
    records.exact_int(source["bytes"], 1, 2*1024**2)
    before = platform_file(source["path"], guard)
    add_allowed(source["path"])
    digest, count, chunks = hashlib.sha256(), 0, []
    with open(source["path"], "rb") as stream:
        while True:
            guard.checkpoint()
            raw = stream.read(65536)
            if not raw:
                break
            count += len(raw)
            records.require(count <= source["bytes"], "API set source read cap")
            digest.update(raw)
            chunks.append(raw)
    records.require(count == source["bytes"] and digest.hexdigest() == source["sha256"]
        and platform_file(source["path"], guard) == before, "fresh reviewed API set source bytes")
    api_sets = policy["api_sets"]
    records.require(pe.api_set_namespace(b''.join(chunks)) == api_sets,
                    'policy API namespace must equal retained image derivation')
    records.require(type(api_sets) is dict and len(api_sets) <= 10000, "API namespace bound")
    for name, hosts in api_sets.items():
        records.require(type(name) is str and name == name.lower() and name.endswith(".dll")
            and type(hosts) is list and len(hosts) <= 32 and all(pe.host_basename(h) == h
                for h in hosts), "API namespace entry")
    observations = {}
    total_names = 0
    observation_pages = []
    batch = []
    def publish(kind, rows):
        descriptor = outputs.write("native-" + kind + "-" + str(len(observation_pages)).zfill(3) + ".json",
            records.canonical_bytes({"schema": "cho51_p2_native_" + kind + "_page_v1", "rows": rows}))
        observation_pages.append(descriptor)
    for path in sorted(pins):
        if path.lower().endswith((".exe", ".dll", ".pyd")):
            reader._check()
            reader.retain(path, pins[path])
            observation = pe.imports(lambda offset, count: retained_range(reader, path, offset, count), pins[path]["bytes"])
            total_names += len(observation["imports"]) + len(observation["delay_imports"])
            records.require(total_names <= 100000, "native edge aggregate output bound")
            observations[path] = observation
            batch.append({"path": path, "observation": observation})
            if len(batch) == 128:
                publish("pe", batch)
                batch = []
    if batch:
        publish("pe", batch)
    resolution = pe.resolve(observations, pins, set(names), api_sets)
    records.require(not resolution["missing"], "unresolved native physical dependency: " +
        '; '.join(row['name'][:96]+' from '+row['importer'].rsplit('/',1)[-1][:64]
                  for row in resolution['missing'][:4]))
    used = set()
    for edge in resolution["edges"]:
        if edge["kind"] == "declared_platform_trust":
            used.add(edge["name"])
        elif edge["kind"] == "reviewed_api_set_namespace":
            used.update(edge["platform_hosts"])
    platform = [platform_file(names[name]["path"], guard) for name in sorted(used)]
    for offset in range(0, len(resolution["edges"]), 512):
        publish("edges", resolution["edges"][offset:offset+512])
    publish("platform", platform)
    return {"pe_images": len(observations), "edge_count": len(resolution["edges"]),
        "platform_image_count": len(platform), "api_set_source_sha256": source["sha256"],
        "pages": [{k: d[k] for k in ("path", "bytes", "sha256")} for d in observation_pages],
        "complete_physical_candidates": True, "native_search_qualified": False, "abi_qualified": False,
        "launch_authorized": False, "scientific_admission": False}


def main(admission_path, admission_hash, origin_utc, origin_qpc, frequency):
    if sys.platform != "win32":
        raise ValueError("Windows P required")
    admission_path = Path(admission_path)
    if admission_path.parent != BASE or not re.fullmatch(r"admission_[0-9a-f-]{36}\.json", admission_path.name):
        raise ValueError("P admission namespace")
    raw = read_bound(admission_path)
    if hashlib.sha256(raw).hexdigest() != admission_hash:
        raise ValueError("P admission caller pin")
    preliminary = initial_json(raw)
    operation = preliminary["operation_id"]
    if type(operation) is not str or str(uuid.UUID(operation)) != operation:
        raise ValueError("canonical operation UUID")
    if admission_path.name != "admission_" + operation + ".json":
        raise ValueError("admission UUID filename join")
    cache = BASE / "disabled-bytecode" / operation
    out = BASE / "attempts" / operation
    guard = Guard(origin_utc, int(origin_qpc), int(frequency), cache)
    reader = outputs = prepared = records = protocol = None
    accepted, error = False, None
    output_descriptors, control_descriptors, startup = [], [], []
    closure = {"inputs": False, "outputs": False, "guard_thread_joined": False,
               "cleanup_errors": []}
    summary = None
    try:
        for index_sample in range(2):
            guard.checkpoint()
            startup.append(guard.sample())
            if index_sample == 0:
                time.sleep(.21)
        if sys.pycache_prefix != str(cache) or sys.flags.isolated != 1 or not sys.flags.no_site or not sys.flags.dont_write_bytecode:
            raise ValueError("P isolated fresh bytecode configuration")
        if any(os.environ.get(key) != "1" for key in
               ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS")) or os.environ.get("CUDA_VISIBLE_DEVICES") != "-1":
            raise ValueError("P one-thread/hidden-GPU environment")
        # The outer original caller binds this bootstrap file before dispatch;
        # repeat its supplied source-byte check before any observer module exec.
        own = read_bound(__file__)
        own_pin = preliminary["sources"]["tools/local_validation/p2r5/supervisor.py"]
        if len(own) != own_pin["bytes"] or hashlib.sha256(own).hexdigest() != own_pin["sha256"]:
            raise ValueError("supervisor bootstrap bytes")
        namespaces()
        add_allowed = install_audit(preliminary, admission_path, cache, out)
        records = load_source(preliminary, "tools.local_validation.v1.records", "tools/local_validation/v1/records.py")
        protocol = load_source(preliminary, "tools.local_validation.p2r5.protocol", "tools/local_validation/p2r5/protocol.py")
        if protocol.PHASE != PHASE or protocol.Q_PHASE != Q_PHASE:
            raise ValueError("observer fixed phase join")
        request = protocol.validate(records.strict_loads(raw), ROOT.as_posix(), origin_utc)
        native = load_source(request, "tools.local_validation.p2r5.native_reader", "tools/local_validation/p2r5/native_reader.py")
        reader = native.RetainedReader(guard.checkpoint)
        reader.read_small(admission_path, {"bytes": len(raw), "sha256": admission_hash})
        for path, pin in request["sources"].items():
            guard.checkpoint()
            reader.retain(ROOT / path, pin)
        for path, pin in request["runtime"]["files"].items():
            guard.checkpoint()
            reader.retain(path, pin)
        if Path(sys.executable).as_posix() != request["python"] or runtime_paths(Path(request["runtime"]["root"])) != set(request["runtime"]["files"]):
            raise ValueError("fresh executable/runtime census")
        reader.retain(request["caller_runtime"]["path"], {k: request["caller_runtime"][k] for k in ("bytes", "sha256")})
        controls = {}
        for key in ("review", "adoption", "qualification", "coverage_review"):
            controls[key] = load_ref(request[key], reader, records, add_allowed)
        qualification = controls["qualification"]
        for key, basename in (("source_review", "source-review.json"), ("actual_review", "actual-review.json")):
            records.require(type(qualification.get(key)) is dict and
                qualification[key].get("path") == Q_PHASE + "/" + basename,
                "fixed Q control path before read")
        q_source = load_ref(qualification["source_review"], reader, records, add_allowed)
        q_actual = load_ref(qualification["actual_review"], reader, records, add_allowed)
        protocol.validate_chain(request, controls["review"], controls["adoption"], qualification,
                                controls["coverage_review"], q_source, q_actual)
        helper = request["native_helper"]
        helper_descriptor = reader.retain(ROOT / helper["path"], {k: helper[k] for k in ("bytes", "sha256")})
        helper_native = helper_descriptor["native_identity"]
        records.require(helper_native["volume_serial"] + ":" + helper_native["file_id"] ==
            qualification["native_builder_controls"]["helper_identity"], "qualified original native PE identity")
        recipe_path = "tools/local_validation/p2r5/dependency_recipe.json"
        recipe = records.strict_loads(reader.read_small(ROOT / recipe_path, request["sources"][recipe_path]))
        index, pins = read_pin_map(request, recipe, reader, records, protocol, add_allowed)
        for path in pins:
            add_allowed(path)
        # Current admission/control/page files are retained separately, not added
        # to the proposed physical map or hashed cyclically into themselves.
        control_descriptors = [descriptor for _, descriptor, _ in reader._files.values()]
        reader.retain_directory(out.parent)
        absent(out)
        guard.checkpoint()
        out.mkdir()
        reader.retain_directory(out)
        outputs = native.RetainedOutputs(reader, out)
        outputs.write("claim.json", records.canonical_bytes({"schema": "cho51_p_claim_v1",
            "operation_id": operation, "admission_sha256": admission_hash,
            "origin_utc": origin_utc, "origin_qpc": int(origin_qpc), "frequency": int(frequency),
            "stage": "P", "actual_result_accepted": False, **protocol.FALSES}))
        manifest = load_source(request, "tools.local_validation.p2r5.manifest", "tools/local_validation/p2r5/manifest.py", reader)
        pe = load_source(request, "tools.local_validation.p2r5.pe", "tools/local_validation/p2r5/pe.py", reader)
        prepared = manifest.prepare(reader, recipe, pins, outputs, request["extra_paths"])
        policy_path = "tools/local_validation/p2r5/native_policy.json"
        policy = records.strict_loads(reader.read_small(ROOT / policy_path, request["sources"][policy_path]))
        summary = native_observation(pins, policy, reader, guard, pe, records, outputs, add_allowed)
        if runtime_paths(Path(request["runtime"]["root"])) != set(request["runtime"]["files"]):
            raise ValueError("final runtime census drift")
        guard.checkpoint()
        outputs.write("result.json", records.canonical_bytes({"schema": "cho51_p_result_v1",
            "status": "PHYSICAL_MAP_OBSERVED_REVIEW_PENDING", "operation_id": operation,
            "admission_sha256": admission_hash, "input_pin_index": request["map_index"],
            "physical_index": prepared.index, "native_summary": summary,
            "startup_samples": startup, "resources": guard.summary(),
            "control_inputs": control_descriptors, "external_caller_return_pending": True,
            "independent_actual_review_pending": True, "handle_closure_pending": True,
            "coverage_review_established": False, "abi_loader_qualified": False, **protocol.FALSES}))
        # Sole complete acceptance pass: after PE and result publication, with
        # every original handle live. verify() never memoizes a prior result.
        prepared.verify()
        output_descriptors = outputs.verify()
        guard.checkpoint()
        accepted = True
    except BaseException as exc:
        error = type(exc).__name__ + ": " + str(exc)[:768]
        if outputs is not None:
            # Preserve successfully published partial descriptors without a new
            # read/effect or a claim that failed inputs/outputs were reverified.
            output_descriptors = [descriptor for _, descriptor, _ in outputs._files.values()]
    finally:
        guard.enter_cleanup()
        if outputs is not None:
            try:
                outputs.close()
                closure["outputs"] = True
            except BaseException as exc:
                closure["cleanup_errors"].append("outputs: " + type(exc).__name__ + ": " + str(exc)[:256])
        else:
            closure["outputs"] = True
        if reader is not None:
            try:
                reader.close()
                closure["inputs"] = True
            except BaseException as exc:
                closure["cleanup_errors"].append("inputs: " + type(exc).__name__ + ": " + str(exc)[:256])
        else:
            closure["inputs"] = True
        guard.stop_watchdog.set()
        guard.watchdog.join(timeout=.5)
        closure["guard_thread_joined"] = not guard.watchdog.is_alive()
    accepted = accepted and not closure["cleanup_errors"] and all(closure[k] is True
        for k in ("inputs", "outputs", "guard_thread_joined")) and guard.fault is None
    if guard.elapsed() > guard.cleanup_deadline or guard.elapsed() >= 300 or datetime.now(timezone.utc) >= guard.origin + timedelta(seconds=300):
        accepted = False
        error = error or "original cleanup/whole return deadline"
    # stdout is the bounded caller-owned pipe; it carries exact output native
    # identities and hashes while control/map inputs are bound by saved pages.
    receipt = {"schema": "cho51_p_supervisor_return_v1", "operation_id": operation,
        "status": "PHYSICAL_MAP_OBSERVED_REVIEW_PENDING" if accepted else "P_FAILED_CONSUMED",
        "observed_by_supervisor": accepted, "accepted_by_supervisor": accepted, "error": error, "handle_closure": closure,
        "outputs": output_descriptors, "resources": guard.summary(),
        "input_identity_verified_before_release": accepted,
        "final_full_input_verification_completed_before_release": accepted,
        "output_identity_verified_before_release": accepted,
        "external_caller_return_pending": True, "independent_actual_review_pending": True,
        "coverage_review_established": False, "abi_loader_qualified": False,
        **({k: False for k in ("historical_custody_closed", "historical_operation_released",
            "historical_retry_allowed", "restart_qualified", "boundary_qualified",
            "complete_dependency_closure", "launch_authorized", "scientific_admission")})}
    encoded = records.canonical_bytes(receipt) if records is not None else (
        json.dumps(receipt, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())
    if len(encoded) > 1048576:
        raise ValueError("P stdout receipt cap")
    sys.stdout.buffer.write(encoded + b"\n")
    sys.stdout.buffer.flush()
    return 0 if accepted else 1


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise SystemExit("P requires admission path/hash, caller UTC/QPC/frequency")
    raise SystemExit(main(*sys.argv[1:]))








