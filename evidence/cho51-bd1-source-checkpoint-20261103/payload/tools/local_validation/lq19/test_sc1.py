"""SC-H/SC-M supplied-call tests. Source only; not native qualification.

No test is run by import. Fake readers never open a file or load a native DLL.
Real NTFS/ABI/resource/fault/ownership scenarios still require fresh admission.
"""
import ctypes
import hashlib
import threading
import unittest
from types import SimpleNamespace
from unittest import mock

from ..lp19 import native_reader as lp
from . import native_reader as lq
from . import supervisor as sup


class _ReadCalls:
    def __init__(self, raw, events, step=65536, failure=None):
        self.raw, self.events, self.step, self.failure = raw, events, step, failure
        self.offset = self.rewinds = 0
        self.buffers, self.counter_addresses, self.counter_inputs = [], [], []
        self.on_read = None

    def SetFilePointerEx(self, handle, offset, result, method):
        self.events.append('seek')
        self.rewinds += 1
        self.offset = 0
        return self.failure != 'seek'

    def ReadFile(self, handle, buffer, amount, count_pointer, overlapped):
        self.events.append(('read', amount))
        counter = ctypes.cast(count_pointer, ctypes.POINTER(ctypes.c_uint32)).contents
        self.counter_inputs.append(counter.value)
        self.counter_addresses.append(ctypes.addressof(counter))
        self.buffers.append(buffer)  # Retain references so address reuse is observable.
        if self.on_read:
            callback, self.on_read = self.on_read, None
            callback()
        if self.failure == 'read':
            return False
        if self.failure == 'count':
            counter.value = amount + 1
            return True
        part = self.raw[self.offset:self.offset + min(amount, self.step)]
        ctypes.memset(buffer, 0xA5, ctypes.sizeof(buffer))
        if part:
            ctypes.memmove(buffer, part, len(part))
        self.offset += len(part)
        counter.value = len(part)
        return True


def _reader(module, raw, *, step=65536, failure=None, fail_check=None):
    reader = module.RetainedReader.__new__(module.RetainedReader)
    reader._closed = False
    events = []
    calls = [0]

    def checkpoint():
        events.append('check')
        calls[0] += 1
        if calls[0] == fail_check:
            raise RuntimeError('injected live checkpoint refusal')
        return True

    reader.checkpoint = checkpoint
    reader._error = lambda message: OSError(message)
    reader.api = _ReadCalls(raw, events, step, failure)
    return reader, events


class HashScratchTests(unittest.TestCase):
    def _both(self):
        return (lp, lq)

    def test_h01_empty_requires_eof_and_original_guard_order(self):
        for module in self._both():
            with self.subTest(module=module.__name__):
                reader, events = _reader(module, b'')
                pin, raw = reader._hash(1, 0, collect=True)
                self.assertEqual(raw, b'')
                self.assertEqual(pin, {'bytes': 0, 'sha256': hashlib.sha256(b'').hexdigest()})
                self.assertEqual(events, ['check', 'seek', 'check', ('read', 1), 'check'])

    def test_h02_chunk_and_actual_supervisor_file_boundaries(self):
        for module in self._both():
            for size in (1, 65535, 65536, 65537, 16 * 1024**2):
                with self.subTest(module=module.__name__, size=size):
                    raw = b'k' * size
                    reader, events = _reader(module, raw)
                    pin, collected = reader._hash(1, size)
                    self.assertIsNone(collected)
                    self.assertEqual(pin['sha256'], hashlib.sha256(raw).hexdigest())
                    self.assertEqual(pin['bytes'], size)
                    self.assertEqual(len({id(b) for b in reader.api.buffers}), 1)
                    self.assertEqual(ctypes.sizeof(reader.api.buffers[0]), min(65536, size + 1))
                    self.assertTrue(all(1 <= e[1] <= 65536 for e in events if isinstance(e, tuple)))
                    self.assertEqual([e for e in events if isinstance(e, tuple)][-1], ('read', 1))

    def test_h03_short_positive_reads_keep_every_guard(self):
        for module in self._both():
            reader, events = _reader(module, b'abcde', step=1)
            _, raw = reader._hash(1, 5, collect=True)
            self.assertEqual(raw, b'abcde')
            expected = ['check', 'seek']
            for amount in (6, 5, 4, 3, 2, 1):
                expected.extend(['check', ('read', amount), 'check'])
            self.assertEqual(events, expected)

    def test_h04_short_and_growing_streams_refuse(self):
        for module in self._both():
            for raw, length in ((b'abc', 4), (b'abcde', 4)):
                reader, _ = _reader(module, raw)
                with self.assertRaises(module.Refusal):
                    reader._hash(1, length)

    def test_h05_native_failure_and_oversized_count_refuse(self):
        for module in self._both():
            for failure in ('seek', 'read', 'count'):
                reader, events = _reader(module, b'abc', failure=failure)
                expected = module.Refusal if failure == 'count' else OSError
                with self.assertRaises(expected):
                    reader._hash(1, 3)
                self.assertLessEqual(sum(isinstance(e, tuple) for e in events), 1)

    def test_h06_pre_and_post_read_checkpoint_fail_closed(self):
        for module in self._both():
            for number, reads in ((2, 0), (3, 1)):
                reader, events = _reader(module, b'ab', fail_check=number)
                with self.assertRaisesRegex(RuntimeError, 'checkpoint refusal'):
                    reader._hash(1, 2)
                self.assertEqual(sum(isinstance(e, tuple) for e in events), reads)

    def test_h07_counter_reset_and_poisoned_tail(self):
        for module in self._both():
            reader, _ = _reader(module, b'abcdefg', step=2)
            pin, raw = reader._hash(1, 7, collect=True)
            self.assertEqual(raw, b'abcdefg')
            self.assertEqual(pin['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(reader.api.counter_inputs, [0] * 5)
            self.assertEqual(len(set(reader.api.counter_addresses)), 1)

    def test_h08_returned_chunks_never_alias_reused_scratch(self):
        for module in self._both():
            reader, _ = _reader(module, b'abcdef', step=2)
            pin, raw = reader._hash(1, 6, collect=True)
            ctypes.memset(reader.api.buffers[0], 0xCC, ctypes.sizeof(reader.api.buffers[0]))
            self.assertIs(type(raw), bytes)
            self.assertEqual(raw, b'abcdef')
            self.assertEqual(pin['sha256'], hashlib.sha256(b'abcdef').hexdigest())

    def test_h09_nested_readers_and_calls_have_distinct_scratch(self):
        for module in self._both():
            outer, _ = _reader(module, b'outer')
            inner, _ = _reader(module, b'inner')
            results = []
            outer.api.on_read = lambda: results.append(inner._hash(2, 5, collect=True))
            _, result = outer._hash(1, 5, collect=True)
            self.assertEqual(result, b'outer')
            self.assertEqual(results[0][1], b'inner')
            self.assertIsNot(outer.api.buffers[0], inner.api.buffers[0])

    def test_h11_repeated_hash_passes_rewind_and_read_fresh(self):
        for module in self._both():
            reader, _ = _reader(module, b'first')
            first, _ = reader._hash(1, 5)
            prior_buffer = reader.api.buffers[0]
            reader.api.raw = b'other'
            second, raw = reader._hash(1, 5, collect=True)
            self.assertNotEqual(first['sha256'], second['sha256'])
            self.assertEqual(raw, b'other')
            self.assertEqual(reader.api.rewinds, 2)
            self.assertIsNot(prior_buffer, reader.api.buffers[-1])

    def test_h12_scratch_allocation_failure_follows_guard_and_no_read(self):
        for module in self._both():
            reader, events = _reader(module, b'ab')
            with mock.patch.object(module.ctypes, 'create_string_buffer', side_effect=MemoryError):
                with self.assertRaises(MemoryError):
                    reader._hash(1, 2)
            self.assertEqual(events, ['check', 'seek', 'check'])


class _Sensors:
    def __init__(self, ram=5 * 1024**3, private=64 * 1024**2):
        self.ram, self.private = ram, private
        self.events, self.memories = [], []
        self.fail = None
        self.reenter = None

    def GlobalMemoryStatusEx(self, pointer):
        memory = ctypes.cast(pointer, ctypes.POINTER(sup._MemoryStatus)).contents
        self.events.append(('ram', memory.length, memory.available_physical))
        self.memories.append((pointer, memory))  # Keep storage alive during nested observations.
        if self.reenter:
            call, self.reenter = self.reenter, None
            call()
        memory.available_physical = self.ram
        return self.fail != 'ram'

    def GetCurrentProcess(self):
        self.events.append('process')
        return 1

    def GetProcessMemoryInfo(self, handle, pointer, size):
        value = ctypes.cast(pointer, ctypes.POINTER(sup._Counters)).contents
        self.events.append(('private', value.cb, size))
        value.private = self.private
        return self.fail != 'private'


def _guard(sensors):
    guard = sup.Guard.__new__(sup.Guard)
    guard.kernel = guard.psapi = sensors
    guard.lock = threading.RLock()
    guard.samples = 0
    guard.min_ram = guard.min_disk = 2**63 - 1
    guard.max_private = 0
    guard.elapsed = lambda: 1.0
    return guard


class FreshMemoryTests(unittest.TestCase):
    def _disk(self, sensors, free=21 * 1024**3):
        def query(path):
            sensors.events.append('disk')
            return SimpleNamespace(free=free)
        return mock.patch.object(sup.shutil, 'disk_usage', side_effect=query)

    def test_m01_exact_layout_and_field_widths(self):
        sup._validate_memory_status_abi()
        self.assertEqual(ctypes.sizeof(sup._MemoryStatus), 64)
        self.assertEqual(ctypes.alignment(sup._MemoryStatus), 8)
        self.assertEqual(sup._MemoryStatus.available_physical.offset, 16)
        self.assertEqual([ctypes.sizeof(t) for _, t in sup._MemoryStatus._fields_], [4, 4] + [8] * 7)

    def test_m02_samples_get_new_zeroed_storage_and_fresh_values(self):
        sensors = _Sensors()
        guard = _guard(sensors)
        with self._disk(sensors):
            first = guard.sample()
            sensors.ram += 4096
            second = guard.sample()
        self.assertEqual(second['available_ram_bytes'] - first['available_ram_bytes'], 4096)
        self.assertNotEqual(ctypes.addressof(sensors.memories[0][1]), ctypes.addressof(sensors.memories[1][1]))
        self.assertEqual([e for e in sensors.events if isinstance(e, tuple) and e[0] == 'ram'], [('ram', 64, 0)] * 2)

    def test_m03_resource_boundaries_are_unchanged(self):
        for ram, disk, private, refused in ((4 * 1024**3, 20 * 1024**3, 512 * 1024**2, False),
                                          (4 * 1024**3 - 1, 20 * 1024**3, 1, True),
                                          (4 * 1024**3, 20 * 1024**3 - 1, 1, True),
                                          (4 * 1024**3, 20 * 1024**3, 512 * 1024**2 + 1, True)):
            sensors = _Sensors(ram, private)
            guard = _guard(sensors)
            with self._disk(sensors, disk):
                if refused:
                    with self.assertRaises(RuntimeError): guard.sample()
                else:
                    guard.sample()

    def test_m04_each_sensor_failure_remains_a_failure(self):
        for failure in ('ram', 'disk', 'private', 'qpc'):
            sensors, guard = _Sensors(), None
            guard = _guard(sensors)
            sensors.fail = failure
            if failure == 'qpc':
                guard.elapsed = mock.Mock(side_effect=OSError('QPC'))
            query = mock.Mock(side_effect=OSError('disk')) if failure == 'disk' else mock.Mock(return_value=SimpleNamespace(free=21 * 1024**3))
            with mock.patch.object(sup.shutil, 'disk_usage', query), mock.patch.object(sup.ctypes, 'get_last_error', return_value=5, create=True):
                with self.assertRaises(OSError): guard.sample()

    def test_m05_nested_samples_never_share_mutable_storage(self):
        sensors = _Sensors()
        guard = _guard(sensors)
        nested = []
        sensors.reenter = lambda: nested.append(guard.sample())
        with self._disk(sensors):
            outer = guard.sample()
        self.assertEqual(guard.samples, 2)
        self.assertEqual(nested[0]['available_ram_bytes'], outer['available_ram_bytes'])
        self.assertNotEqual(ctypes.addressof(sensors.memories[0][1]), ctypes.addressof(sensors.memories[1][1]))

    def test_m06_sample_keeps_sensor_order_and_every_invocation(self):
        sensors = _Sensors()
        guard = _guard(sensors)
        with self._disk(sensors):
            guard.sample(); guard.sample()
        names = [event[0] if isinstance(event, tuple) else event for event in sensors.events]
        self.assertEqual(names, ['ram', 'disk', 'process', 'private'] * 2)

    def test_m07_guard_checkpoints_still_call_live_sample(self):
        sensors = _Sensors()
        guard = _guard(sensors)
        guard.fault = None
        guard.origin = sup.datetime.now(sup.timezone.utc)
        guard.work_seconds = guard.soft_seconds = 60
        guard.origin_qpc, guard.frequency = 1, 10000000
        guard.cache = sup.ROOT / 'injected-absent-cache'
        # Checkpoint's direct QPC check has an independent injected observation.
        def qpc(pointer):
            ctypes.cast(pointer, ctypes.POINTER(ctypes.c_int64)).contents.value = 10000001
            return True
        sensors.QueryPerformanceCounter = qpc
        with mock.patch.object(sup, 'absent') as absent, self._disk(sensors):
            guard.checkpoint(); guard.checkpoint()
        self.assertEqual(guard.samples, 2)
        self.assertEqual(absent.call_count, 4)

    def test_m08_layout_mismatch_refuses_before_native_use(self):
        class Bad(ctypes.Structure):
            _fields_ = [('length', ctypes.c_uint32)]
        with mock.patch.object(sup, '_MemoryStatus', Bad), mock.patch.object(sup.ctypes, 'WinDLL', create=True) as dll:
            with self.assertRaises(ValueError):
                sup.Guard('2026-11-02T00:00:00Z', 1, 10000000, None)
            dll.assert_not_called()
