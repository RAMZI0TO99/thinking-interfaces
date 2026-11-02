"""Adversarial tests, executable only in an independently admitted owned Job."""
import importlib.util
import os
from pathlib import Path
import sys
import unittest
from unittest import mock
import io
import json

HERE = Path(__file__).absolute().parent
spec = importlib.util.spec_from_file_location('_inventory_test_subject', HERE / 'inventory.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
FIXTURE_ROOT = None


class InventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if FIXTURE_ROOT is None:
            raise RuntimeError('admitted fixture root required')
        FIXTURE_ROOT.mkdir()

    def setUp(self):
        self.path = FIXTURE_ROOT / (self._testMethodName + '.bin')
        self.path.write_bytes(b'fixture')
        self.inv = m.RetainedInventory()

    def tearDown(self):
        self.inv.close()

    def test_pin_and_reverify(self):
        self.inv.read(self.path, {'bytes': 7, 'sha256': m.digest(b'fixture')})
        self.assertEqual(self.inv.verify()[0]['bytes'], 7)

    def test_bad_hash(self):
        with self.assertRaises(ValueError):
            self.inv.read(self.path, {'bytes': 7, 'sha256': '0' * 64})

    def test_bad_size(self):
        with self.assertRaises(ValueError):
            self.inv.read(self.path, {'bytes': 8, 'sha256': m.digest(b'fixture')})

    def test_alias_duplicate(self):
        self.inv.read(self.path)
        with self.assertRaises(ValueError):
            self.inv.read(self.path)

    def test_hardlink_refused(self):
        other = self.path.with_suffix('.link')
        os.link(self.path, other)
        with self.assertRaises(ValueError):
            self.inv.read(self.path)

    def test_existing_writer_refused(self):
        with self.path.open('r+b'):
            with self.assertRaises(OSError):
                self.inv.read(self.path)

    def test_new_writer_refused(self):
        self.inv.read(self.path)
        with self.assertRaises(OSError):
            self.path.open('r+b')

    def test_output_collision_and_readback(self):
        out = m.Outputs(self.inv, FIXTURE_ROOT)
        try:
            out.write('claim.json', b'one')
            out.verify()
            with self.assertRaises(OSError):
                out.write('claim.json', b'two')
        finally:
            out.close()

    def test_bounds(self):
        old = m.MAX_FILE
        try:
            m.MAX_FILE = 6
            with self.assertRaises(ValueError):
                self.inv.read(self.path)
        finally:
            m.MAX_FILE = old

    def test_roster_is_explicit(self):
        self.inv.read(self.path)
        (FIXTURE_ROOT / 'unlisted.bin').write_bytes(b'unlisted')
        self.assertEqual(len(self.inv.verify()), 1)

    def test_parent_identity_failure_keeps_handle_owned(self):
        target = FIXTURE_ROOT
        original = m.native_identity
        calls = 0
        def fail_second(api, handle):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('injected identity failure')
            return original(api, handle)
        with mock.patch.object(m, 'native_identity', side_effect=fail_second):
            with self.assertRaises(OSError):
                self.inv.retain_directory(target)
        self.assertIn(target, self.inv.directories)
        self.assertIsNone(self.inv.directories[target][1])

    def test_fdopen_failure_closes_transferred_descriptor(self):
        close = m.os.close
        with mock.patch.object(m.os, 'fdopen', side_effect=OSError('injected fdopen')), mock.patch.object(m.os, 'close', wraps=close) as observed:
            with self.assertRaises(OSError):
                self.inv.read(self.path)
            self.assertEqual(observed.call_count, 1)

    def test_output_fdopen_failure_closes_descriptor(self):
        directory = FIXTURE_ROOT / self._testMethodName
        directory.mkdir()
        out = m.Outputs(self.inv, directory)
        close = m.os.close
        with mock.patch.object(m.os, 'fdopen', side_effect=OSError('injected fdopen')), mock.patch.object(m.os, 'close', wraps=close) as observed:
            with self.assertRaises(OSError):
                out.write('claim.json', b'fixture')
            self.assertEqual(observed.call_count, 1)

    def test_output_blocks_writer_and_delete(self):
        directory = FIXTURE_ROOT / self._testMethodName
        directory.mkdir()
        out = m.Outputs(self.inv, directory)
        try:
            out.write('payload.json', b'fixture')
            with self.assertRaises(OSError):
                (directory / 'payload.json').open('r+b')
            with self.assertRaises(OSError):
                (directory / 'payload.json').unlink()
            out.verify()
        finally:
            out.close()

    def test_read_checkpoint_interrupts_and_chunk_bound(self):
        calls = []
        self.inv.checkpoint = lambda: calls.append(True)
        self.assertEqual(self.inv.read_stream(io.BytesIO(b'x' * 1048577), 1048577), b'x' * 1048577)
        self.assertGreaterEqual(len(calls), 2)
        with self.assertRaises(ValueError):
            self.inv.read_stream(io.BytesIO(b'xx'), 1)
        self.inv.checkpoint = mock.Mock(side_effect=RuntimeError('stop'))
        with self.assertRaises(RuntimeError):
            self.inv.read(self.path)

    def test_file_count_and_total_bounds(self):
        for field, value in (('MAX_FILES', 0), ('MAX_TOTAL', 6)):
            with mock.patch.object(m, field, value):
                with self.assertRaises(ValueError):
                    self.inv.read(self.path)

    def test_alias_and_depth_syntax(self):
        for bad in (Path('relative'), Path('D:/x:stream'), Path('D:/NUL'), Path('D:/' + '/'.join(['x'] * 33))):
            with self.assertRaises((ValueError, OSError)):
                m.checked_path(bad)

    def test_verified_bootstrap_executes_exact_bytes(self):
        spec = importlib.util.spec_from_file_location('_inventory_runner_tests', HERE / 'validation_runner.py')
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        code = b'VALUE = 42\n'
        raw = json.dumps({'sources': {'tools/custody_boundary/v8/inventory.py': {'bytes': len(code), 'sha256': m.digest(code)}}}).encode()
        self.assertEqual(runner.load_pinned_inventory(raw, m.digest(raw), code).VALUE, 42)
        for request, digest, source in ((raw, '0'*64, code), (raw, m.digest(raw), code+b'# changed'), (raw, m.digest(raw), b'x'*1048577)):
            with self.assertRaises(ValueError):
                runner.load_pinned_inventory(request, digest, source)

    def test_deadline_serialization_matches_frozen_consumer(self):
        from datetime import UTC, datetime, timedelta
        spec = importlib.util.spec_from_file_location('_inventory_deadline_test', HERE.parents[2] / 'evaluation/phase2_supervision_primitives.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        stamp = (datetime.now(UTC) + timedelta(seconds=10)).isoformat()
        body = {'schema': 'phase2_supervision_deadlines_v1', 'attempt_deadline_utc': stamp, 'session_deadline_utc': stamp}
        directory = FIXTURE_ROOT / self._testMethodName
        directory.mkdir()
        out = m.Outputs(self.inv, directory)
        try:
            out.write('deadline.json', (json.dumps(body, sort_keys=True, separators=(',', ':'))+'\n').encode())
            self.assertEqual(module.DeadlineLease.load(directory / 'deadline.json').attempt_deadline_utc.isoformat(), stamp)
        finally:
            out.close()
