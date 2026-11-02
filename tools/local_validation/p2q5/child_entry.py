"""Fixed Q suite and declared transport/timeout controls; no generic command."""
import hashlib
import io
import json
import msvcrt
import os
from pathlib import Path
import sys
import time
import types
import unittest

ROOT = Path(__file__).absolute().parents[3]


def main():
    if len(sys.argv) != 9 or sys.argv[3] not in ("suite", "badframe", "stall"):
        raise ValueError("fixed Q child arguments")
    admission, digest, mode, fixture, writer, origin, qpc, freq = sys.argv[1:]
    with Path(admission).open("rb") as stream:
        raw = stream.read(8 * 1024**2 + 1)
    if len(raw) > 8 * 1024**2 or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("child admission byte mismatch")
    request = json.loads(raw)
    relative = "tools/local_validation/p2q5/supervisor.py"
    with (ROOT / relative).open("rb") as stream:
        source = stream.read(1024**2 + 1)
    pin = request["sources"][relative]
    if len(source) != pin["bytes"] or hashlib.sha256(source).hexdigest() != pin["sha256"]:
        raise ValueError("child bootstrap source mismatch")
    sup = types.ModuleType("tools.local_validation.p2q5.supervisor")
    sup.__file__ = str(ROOT / relative)
    sys.modules[sup.__name__] = sup
    exec(compile(source, sup.__file__, "exec"), sup.__dict__)
    sup.namespaces()
    r = sup.load_source(request, "tools.local_validation.v1.records", "tools/local_validation/v1/records.py")
    p = sup.load_source(request, "tools.local_validation.p2q5.protocol", "tools/local_validation/p2q5/protocol.py")
    request = p.validate_admission(r.strict_loads(raw), ROOT.as_posix(), origin)
    fixture = Path(fixture)
    expected_fixture = sup.BASE / "attempts" / request["operation_id"] / "fixtures"
    if fixture != expected_fixture or not fixture.is_dir():
        raise ValueError("exact owned fixture root")
    cache = sup.BASE / "disabled-bytecode" / request["operation_id"]
    guard = sup.Guard(origin, int(qpc), int(freq), cache)
    guard.checkpoint()
    if sys.pycache_prefix != str(cache) or sys.flags.isolated != 1 or not sys.flags.no_site:
        raise ValueError("child isolated runtime")
    sup.restrict(request, cache, fixture)
    handle = int(writer)
    if handle <= 0:
        raise ValueError("original result handle")
    descriptor = msvcrt.open_osfhandle(handle, os.O_WRONLY | os.O_BINARY)
    with os.fdopen(descriptor, "wb", buffering=0) as pipe:
        if mode == "stall":
            while True:
                time.sleep(.1)
        if mode == "badframe":
            pipe.write(b"\x02\x00\x00\x00{}!")
            return 0
        sup.load_source(request, "tools.local_validation.v1.preparation", "tools/local_validation/v1/preparation.py")
        sup.load_source(request, "tools.local_validation.p2q5.native_reader", "tools/local_validation/p2q5/native_reader.py")
        sup.load_source(request, "tools.local_validation.q4.native_reader", "tools/local_validation/q4/native_reader.py")
        long_native = sup.load_source(request, "tools.local_validation.p2r5.native_reader", "tools/local_validation/p2r5/native_reader.py")
        sup.load_source(request, "tools.local_validation.p1.preparation", "tools/local_validation/p1/preparation.py")
        for leaf in ('manifest','pe','protocol','supervisor'):
            sup.load_source(request, 'tools.local_validation.p2r5.'+leaf, 'tools/local_validation/p2r5/'+leaf+'.py')
        modules = []
        for name in ("tools.local_validation.v1.test_foundation", "tools.local_validation.p2q5.test_native_reader",
                     "tools.local_validation.p2q5.test_protocol", "tools.local_validation.p1.test_preparation",
                     "tools.local_validation.p2r5.test_manifest", "tools.local_validation.p2r5.test_pe",
                     "tools.local_validation.p2r5.test_long_paths",
                     "tools.local_validation.p2r5.test_performance",
                     "tools.local_validation.p2r5.test_protocol"):
            module = sup.load_source(request, name, name.replace(".", "/") + ".py")
            if name.endswith(("test_native_reader", "test_preparation", "test_manifest", "test_long_paths", "test_performance")):
                module.FIXTURE_ROOT = fixture
            modules.append(module)
        tests = []
        def flatten(suite):
            for test in suite:
                if isinstance(test, unittest.TestSuite):
                    flatten(test)
                else:
                    tests.append(test)
        for module in modules:
            flatten(unittest.defaultTestLoader.loadTestsFromModule(module))
        tests.sort(key=lambda test: test.id())
        if [test.id() for test in tests] != request["expected_tests"]:
            raise ValueError("Q collection differs from reviewed exact roster")
        class BoundedText(io.StringIO):
            def write(self, text):
                if self.tell() + len(text) > 32768:
                    raise ValueError("test report text cap")
                return super().write(text)
        started = []
        class Result(unittest.TextTestResult):
            def startTest(self, test):
                guard.checkpoint()
                started.append(test.id())
                super().startTest(test)
            def stopTest(self, test):
                super().stopTest(test)
                guard.checkpoint()
        report = BoundedText()
        result = unittest.TextTestRunner(stream=report, verbosity=2, resultclass=Result).run(unittest.TestSuite(tests))
        guard.checkpoint()
        count = size = 0
        pending = [fixture.as_posix()]
        entries_seen = 0
        while pending:
            current = pending.pop()
            if len(current[len(fixture.as_posix()):].strip("/").split("/")) > 32:
                raise ValueError("fixture depth")
            with os.scandir(long_native.transport(current)) as entries:
                for entry in entries:
                    guard.checkpoint()
                    entries_seen += 1
                    if entries_seen > 50000:
                        raise ValueError("fixture entry cap")
                    path = current + "/" + entry.name
                    info = os.stat(long_native.transport(path), follow_symlinks=False)
                    if info.st_file_attributes & 0x440:
                        raise ValueError("fixture reparse/device")
                    if info.st_file_attributes & 0x10:
                        pending.append(path)
                        continue
                    # Existing refusal controls deliberately leave hardlinked
                    # JSON fixtures. This accounting census is not acceptance
                    # by the strict production reader; its link guards stay on.
                    if not entry.name.endswith(".json"):
                        raise ValueError("unexpected fixture file type")
                    count += 1
                    size += info.st_size
                    if count > 240 or size > 48 * 1024**2:
                        raise ValueError("fixture aggregate cap")
        payload = {"schema": "cho51_q_test_report_v1", "operation_id": request["operation_id"],
                   "tests": started, "tests_run": result.testsRun, "failures": len(result.failures),
                   "errors": len(result.errors), "skipped": len(result.skipped),
                   "expected_failures": len(result.expectedFailures), "unexpected_successes": len(result.unexpectedSuccesses),
                   "successful": result.wasSuccessful() and not result.skipped and not result.expectedFailures,
                   "report": report.getvalue(), "fixture_files": count, "fixture_bytes": size, **p.FALSES}
        encoded = r.canonical_bytes(payload)
        if len(encoded) > 1048576:
            raise ValueError("child frame cap")
        packet = len(encoded).to_bytes(4, "little") + encoded
        if pipe.write(packet) != len(packet):
            raise ValueError("short result pipe write")
        pipe.flush()
        guard.stop_watchdog.set()
    return 0  # Parent validates all test outcomes, including retained failures.


if __name__ == "__main__":
    raise SystemExit(main())





