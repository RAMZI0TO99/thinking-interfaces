"""Fixed admitted tests or offline decoding of one pinned saved capture."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAPTURE = "runs/coordination/cho51_p3_provider_qualification_20261028_v4/attempts/076a41b3-fcc1-4553-aa56-a75a7bfcfef1/payload.json"
CAPTURE_BYTES = 53785
CAPTURE_SHA256 = "7df7f2a813f32588a08cfaa3c1100e905d935f283c28292e9bad62e9371ab906"


def load(name):
    spec = importlib.util.spec_from_file_location("_v5_" + name, HERE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class BoundedText(io.StringIO):
    def write(self, text):
        if self.tell() + len(text) > 65536:
            raise ValueError("test report exceeds64KiB")
        return super().write(text)


def redecode():
    # Parent retains this exact input under deny-write/delete handles. Check it
    # again before interpreting; no caller-supplied path or provenance flag.
    with (ROOT / CAPTURE).open("rb") as stream:
        raw = stream.read(CAPTURE_BYTES + 1)
    if len(raw) != CAPTURE_BYTES or hashlib.sha256(raw).hexdigest() != CAPTURE_SHA256:
        raise ValueError("saved native capture pin differs")
    captured = json.loads(raw)
    decoder = load("decoder")
    rows, queries, seen = [], [], set()
    for query in captured["queries"]:
        queries.append({"key": query["spec"]["key"], "spec": query["spec"],
                        "selected_query_exhausted": query["selected_query_exhausted"],
                        "truncated": query["truncated"], "errors": query["errors"],
                        "metadata_exhausted": query["metadata"]["exhausted"],
                        "metadata_truncated": query["metadata"]["truncated"],
                        "metadata_errors": query["metadata"]["errors"]})
        for raw_event in query["events"]:
            row = {"query_key": query["spec"]["key"], "raw_sha256": raw_event["sha256"]}
            try:
                event = decoder.decode_event(raw_event, query["spec"])
            except decoder.DecodeError as exc:
                row.update(status="REFUSED_DECODING", reason=str(exc)[:256])
            else:
                identity = (event["channel"], event["record_id"])
                if identity in seen:
                    raise ValueError("duplicate selected record identity")
                seen.add(identity)
                row.update(status="DECODED", event=event,
                           generic_qualification=decoder.qualify_event(event, query["metadata"]),
                           native_qualification=decoder.qualify_native_event(event, query["metadata"]))
            rows.append(row)
    return {"schema": "cho51_p3_provider_redecode_v5", "status": "UNRESOLVED",
            "input": {"path": CAPTURE, "bytes": CAPTURE_BYTES, "sha256": CAPTURE_SHA256},
            "interpretation": "Offline decoding of retained EvtRender XML and EventMetadataEventTemplate fragments",
            "fresh_provider_observation": False, "rows": rows, "queries": queries,
            "decoded_count": sum(row["status"] == "DECODED" for row in rows),
            "matched_native_count": sum(row.get("native_qualification", {}).get("status") == "MATCHED_NATIVE_TEMPLATE_FRAGMENT" for row in rows),
            "historical_custody_closed": False, "historical_operation_released": False,
            "historical_retry_allowed": False, "host_association_authenticated": False,
            "restart_qualified": False, "clock_order_qualified": False,
            "persisted_domain_excluded": False, "boundary_qualified": False,
            "launch_authorized": False, "scientific_admission": False}


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in {"tests", "redecode"}:
        raise ValueError("fixed mode and admitted output required")
    mode, output = sys.argv[1], Path(sys.argv[2])
    if mode == "tests":
        suite = unittest.TestSuite()
        for name in ("test_decoder", "test_collector"):
            suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(load(name)))
        report = BoundedText()
        result = unittest.TextTestRunner(stream=report, verbosity=2).run(suite)
        payload = {"schema": "cho51_p3_provider_tests_v5", "tests_run": result.testsRun,
                   "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
                   "successful": result.wasSuccessful() and result.testsRun > 0 and not result.skipped,
                   "report": report.getvalue(), "boundary_qualified": False,
                   "host_association_authenticated": False, "launch_authorized": False, "scientific_admission": False}
        code = 0 if payload["successful"] else 1
    else:
        payload = redecode()
        code = 0
    raw = (json.dumps(payload, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode()
    if len(raw) > 1048576:
        raise ValueError("payload exceeds1MiB")
    with output.open("xb") as stream:
        stream.write(raw)
        stream.flush()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
