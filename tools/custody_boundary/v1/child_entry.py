"""Fixed fixture/diagnostic entry; no arbitrary command or import target."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


class BoundedText(io.StringIO):
    def write(self, value):
        if self.tell() + len(value) > 65536:
            raise RuntimeError("test report exceeds bound")
        return super().write(value)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in {"tests", "collect"}:
        raise ValueError("fixed mode and output required")
    mode, output = sys.argv[1], Path(sys.argv[2])
    if mode == "tests":
        module = load("_boundary_tests", HERE / "test_verifier.py")
        stream = BoundedText()
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
        payload = {"schema": "cho51_p3_boundary_fixture_result_v1", "mode": mode,
                   "tests_run": result.testsRun, "failures": len(result.failures),
                   "errors": len(result.errors), "skipped": len(result.skipped),
                   "successful": result.wasSuccessful() and result.testsRun > 0 and not result.skipped,
                   "report": stream.getvalue(), "machine_boundary_observed": False,
                   "launch_authorized": False, "scientific_admission": False}
        code = 0 if payload["successful"] else 1
    else:
        payload = load("_boundary_collector", HERE / "collector.py").collect()
        # Exit zero means a diagnostic was saved, never boundary qualification.
        code = 0 if not payload["errors"] else 1
    raw = (json.dumps(payload, ensure_ascii=True, allow_nan=False, indent=2) + "\n").encode("utf-8")
    if len(raw) > 1048576:
        raise RuntimeError("child payload exceeds1MiB")
    with output.open("xb") as stream:
        stream.write(raw)
        stream.flush()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
