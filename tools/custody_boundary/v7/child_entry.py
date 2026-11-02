"""Fixed injected tests or bounded local Sysmon read under fresh admission."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class BoundedText(io.StringIO):
    def write(self, text):
        if self.tell() + len(text) > 65536:
            raise ValueError("report exceeds64KiB")
        return super().write(text)


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in {"tests", "capture"}:
        raise ValueError("fixed mode and admitted output required")
    mode, output = sys.argv[1], Path(sys.argv[2])
    if mode == "tests":
        tests = load("_v7_tests", HERE / "test_collector.py")
        suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
        report = BoundedText()
        result = unittest.TextTestRunner(stream=report, verbosity=2).run(suite)
        payload = {"schema": "cho51_p3_sysmon_tests_v7", "tests_run": result.testsRun,
                   "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
                   "successful": result.wasSuccessful() and result.testsRun > 0 and not result.skipped,
                   "report": report.getvalue(), "boundary_qualified": False,
                   "launch_authorized": False, "scientific_admission": False}
        code = 0 if payload["successful"] else 1
    else:
        collector = load("_v7_collector", HERE / "collector.py")
        native = load("_v7_native", HERE.parent / "v4/collector.py")
        decoder = load("_v7_decoder", HERE.parent / "v5/decoder.py")
        payload = collector.run(native, decoder)
        payload["schema"] = "cho51_p3_sysmon_capture_v7"
        payload["fresh_provider_observation"] = True
        payload["native_handles_closed"] = payload["native_health"]["closed_cleanly"]
        payload["raw_event_count"] = sum(len(q["events"]) for q in payload["queries"])
        code = 0 if payload["native_handles_closed"] else 1
    raw = (json.dumps(payload, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode()
    if len(raw) > 1048576:
        raise ValueError("output exceeds1MiB")
    with output.open("xb") as stream:
        stream.write(raw)
        stream.flush()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
