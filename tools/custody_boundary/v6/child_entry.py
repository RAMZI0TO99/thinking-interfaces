"""Fixed tests or retained offline custody assessment; no live provider query."""
import importlib.util
import io
import json
from datetime import UTC, datetime
from pathlib import Path
import sys
import unittest
import uuid

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
    if len(sys.argv) != 3 or sys.argv[1] not in {"tests", "assess"}:
        raise ValueError("fixed mode and admitted output required")
    mode, output = sys.argv[1], Path(sys.argv[2])
    if mode == "tests":
        tests = load("_v6_tests", HERE / "test_assessor.py")
        suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
        report = BoundedText()
        result = unittest.TextTestRunner(stream=report, verbosity=2).run(suite)
        payload = {"schema": "cho51_p3_custody_intake_tests_v6", "tests_run": result.testsRun,
                   "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
                   "successful": result.wasSuccessful() and result.testsRun > 0 and not result.skipped,
                   "report": report.getvalue(), "boundary_qualified": False,
                   "launch_authorized": False, "scientific_admission": False}
        code = 0 if payload["successful"] else 1
    else:
        assessor = load("_v6_assessor", HERE / "assessor.py")
        reader = load("_v6_retained_reader", HERE.parent / "v3/retained_reader.py")
        # The plan is a parent-held reviewed source; each input gets an additional
        # retained native file identity in this child, kept through assessment.
        plan = json.loads((HERE / "intake-plan.json").read_bytes())
        with reader.RetainedArtifactSet(str(ROOT)) as retained:
            artifacts = {ref["path"]: retained.read(ref) for ref in plan["artifacts"].values()}
            assessment = assessor.assess(plan, artifacts)
            if assessment["status"] != "UNRESOLVED":
                raise ValueError("fixed retained input no longer yields expected unresolved disposition")
            candidate = assessor.build_disposition(
                assessment, plan, str(uuid.uuid4()), datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                artifacts[plan["artifacts"]["disposition_schema"]["path"]])
            retained.verify()
            witnesses = list(retained.witnesses)
        payload = {"schema": "cho51_p3_custody_intake_actual_v6", "status": "UNRESOLVED",
                   "assessment": assessment, "candidate_disposition": candidate,
                   "root_adoption_pending": True, "retained_reads_verified": True,
                   "artifacts_read": len(witnesses), "retained_artifacts": witnesses,
                   "fresh_provider_observation": False, "historical_custody_closed": False,
                   "historical_operation_released": False, "historical_retry_allowed": False,
                   "boundary_qualified": False, "launch_authorized": False, "scientific_admission": False}
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
