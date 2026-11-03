"""Synthetic supplied-only test inputs; no original witness."""
import json
from .common import raw_pin
from .parsers import B_SCHEMA, I_SCHEMA, C_SCHEMA
O = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"
P = {"bytes": 1, "sha256": "a" * 64}
EMPTY = {"bytes": 0, "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}
def encode(v): return (json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")
def binding():
    return {"schema": B_SCHEMA, "operation": O, "basis": dict(P), "source": dict(P), "runtime": dict(P), "actors": dict(P), "clock_domain": OTHER, "acquired": 1, "native_witness": dict(P)}
def ingress(b):
    return {"schema": I_SCHEMA, "operation": O, "binding": raw_pin(b), "state": "BOUND", "cutoff": 0, "entered": 0, "committed": 0, "refused": 0, "pending": 0, "late": 0, "first_fault": "NONE", "event_records": 0, "events": dict(EMPTY), "invocation_map": dict(P), "native_witness": dict(P)}
def capture(b):
    return {"schema": C_SCHEMA, "operation": O, "binding": raw_pin(b), "stdout": dict(EMPTY), "stderr": dict(EMPTY), "stdout_eof": True, "stderr_eof": True, "stdout_chunks": 0, "stderr_chunks": 0, "merge_records": 0, "ledger": dict(P), "raw_tool_role": "closeout/raw_tool_return", "external_return_role": "closeout/external_return", "status": "COMPLETE", "native_witness": dict(P)}
