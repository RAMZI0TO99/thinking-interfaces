"""Fixed admitted tests or local passive provider capture; no arbitrary command."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location("_v4_" + name, HERE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class BoundedText(io.StringIO):
    def write(self, text):
        if self.tell() + len(text) > 65536:
            raise ValueError("test report exceeds64KiB")
        return super().write(text)


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in {"tests", "collect"}:
        raise ValueError("fixed mode and admitted output required")
    mode, output = sys.argv[1], Path(sys.argv[2])
    if mode == "tests":
        suite = unittest.TestSuite()
        for name in ("test_decoder", "test_collector"):
            suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(load(name)))
        report = BoundedText()
        result = unittest.TextTestRunner(stream=report, verbosity=2).run(suite)
        payload = {"schema": "cho51_p3_provider_tests_v4", "tests_run": result.testsRun,
                   "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
                   "successful": result.wasSuccessful() and result.testsRun > 0 and not result.skipped,
                   "report": report.getvalue(), "boundary_qualified": False,
                   "host_association_authenticated": False, "launch_authorized": False, "scientific_admission": False}
        code = 0 if payload["successful"] else 1
    else:
        collector, decoder = load("collector"), load("decoder")
        plan = json.loads((HERE / "provider-plan.json").read_bytes())
        payload = collector.collect(plan, decoder)
        code = 0 if payload["native_handles_closed_cleanly"] else 1
    raw = (json.dumps(payload, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode()
    if len(raw) > 1048576:
        raise ValueError("payload exceeds1MiB")
    with output.open("xb") as stream:
        stream.write(raw)
        stream.flush()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
