"""Fixed v2 test/read modes; no arbitrary command, provider query or write root."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


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
    if len(sys.argv) != 3 or sys.argv[1] not in {"tests", "smoke"}:
        raise ValueError("fixed mode and admitted output required")
    mode, output = sys.argv[1], Path(sys.argv[2])
    if mode == "tests":
        suite = unittest.TestSuite()
        for name in ("test_retained_reader", "test_auxiliary"):
            module = load("_v2_" + name, HERE / (name + ".py"))
            suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
        stream = BoundedText()
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
        payload = {"schema": "cho51_p3_retained_chain_tests_v2", "tests_run": result.testsRun,
                   "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
                   "successful": result.wasSuccessful() and result.testsRun > 0 and not result.skipped,
                   "report": stream.getvalue(), "boundary_qualified": False,
                   "launch_authorized": False, "scientific_admission": False}
        code = 0 if payload["successful"] else 1
    else:
        reader_module = load("_v2_retained_read_smoke", HERE / "retained_reader.py")
        with reader_module.RetainedArtifactSet(str(ROOT)) as retained:
            # This plan and its exact6 inputs are pinned by the parent review.
            plan = json.loads((HERE / "smoke-plan.json").read_bytes())
            if plan["schema"] != "cho51_p3_retained_read_smoke_plan_v2" or len(plan["artifacts"]) != 6:
                raise ValueError("smoke plan shape")
            for reference in plan["artifacts"]:
                retained.read(reference)
            retained.verify()
            witnesses = retained.witnesses
        payload = {"schema": "cho51_p3_retained_read_smoke_v2", "status": "UNRESOLVED", "artifacts_read": len(witnesses),
                   "retained_reads_verified": True, "retained_artifacts": list(witnesses),
                   "boundary_qualified": False, "launch_authorized": False, "scientific_admission": False,
                   "limitation": "Current local NTFS bytes/ordinary sharing only; no author, host, restart, old cleanup or runtime-load attestation"}
        code = 0
    raw = (json.dumps(payload, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode()
    if len(raw) > 1048576:
        raise ValueError("output exceeds1MiB")
    with output.open("xb") as stream:
        stream.write(raw)
        stream.flush()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
