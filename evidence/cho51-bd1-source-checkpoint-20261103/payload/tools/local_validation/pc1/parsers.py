"""Closed, supplied B/I/C projection parsers."""
from .common import decode, fields, freeze, integer, literal, pin, require, uuid

B_SCHEMA = "cho51_pc_binding_projection_v1"
I_SCHEMA = "cho51_pc_ingress_projection_v1"
C_SCHEMA = "cho51_pc_capture_projection_v1"
STATES = ("BOUND", "OPEN", "REVOKED", "DRAINED", "FROZEN", "TERMINAL")
FAULTS = ("NONE", "DOMAIN", "CAPACITY", "REENTRY", "LATE", "STOP", "RESOURCE", "TIMEOUT", "TARGET", "REFUSAL_HELPER", "TRANSPORT", "CUSTODY", "PUBLICATION", "UNKNOWN")

def _binding(raw):
    v = decode(raw)
    fields(v, ("schema", "operation", "basis", "source", "runtime", "actors", "clock_domain", "acquired", "native_witness"))
    literal(v["schema"], (B_SCHEMA,))
    uuid(v["operation"]); uuid(v["clock_domain"])
    for name in ("basis", "source", "runtime", "actors"):
        pin(v[name], 1, 4194304)
    integer(v["acquired"], 65535)
    pin(v["native_witness"], 1, 131072)
    return v

def _ingress(raw):
    v = decode(raw)
    fields(v, ("schema", "operation", "binding", "state", "cutoff", "entered", "committed", "refused", "pending", "late", "first_fault", "event_records", "events", "invocation_map", "native_witness"))
    literal(v["schema"], (I_SCHEMA,)); uuid(v["operation"])
    pin(v["binding"], 1, 8192); literal(v["state"], STATES)
    for name in ("cutoff", "entered", "committed", "refused", "pending", "late"):
        integer(v[name], 65535)
    integer(v["event_records"], 4096)
    literal(v["first_fault"], FAULTS)
    pin(v["events"], 0, 2097152); pin(v["invocation_map"], 1, 131072); pin(v["native_witness"], 1, 131072)
    require(v["entered"] == v["committed"] + v["refused"] + v["pending"], "ALGEBRA")
    require((v["event_records"] == 0) == (v["events"]["bytes"] == 0), "EVENTS")
    state = v["state"]
    require(state not in ("FROZEN", "TERMINAL") or (v["event_records"] > 0 and v["events"]["bytes"] > 0), "EVENTS")
    require((v["cutoff"] == 0 and v["late"] == 0) if state in ("BOUND", "OPEN") else v["cutoff"] > 0, "CUTOFF")
    require(state not in ("DRAINED", "FROZEN", "TERMINAL") or v["pending"] == 0, "PENDING")
    require(not (v["late"] or v["refused"]) or v["first_fault"] != "NONE", "FAULT")
    require(state != "BOUND" or not any(v[n] for n in ("entered", "committed", "refused", "pending", "event_records")), "BOUND_ACTIVITY")
    return v

def _capture(raw):
    v = decode(raw)
    fields(v, ("schema", "operation", "binding", "stdout", "stderr", "stdout_eof", "stderr_eof", "stdout_chunks", "stderr_chunks", "merge_records", "ledger", "raw_tool_role", "external_return_role", "status", "native_witness"))
    literal(v["schema"], (C_SCHEMA,)); uuid(v["operation"]); pin(v["binding"], 1, 8192)
    for name in ("stdout", "stderr"): pin(v[name], 0, 1048576)
    for name in ("stdout_eof", "stderr_eof"): require(type(v[name]) is bool, "BOOLEAN")
    for name in ("stdout_chunks", "stderr_chunks", "merge_records"): integer(v[name], 65535)
    pin(v["ledger"], 1, 131072); pin(v["native_witness"], 1, 131072)
    literal(v["raw_tool_role"], ("closeout/raw_tool_return",))
    literal(v["external_return_role"], ("closeout/external_return",))
    literal(v["status"], ("COMPLETE", "INCOMPLETE", "ERROR", "CANCELLED", "UNKNOWN"))
    require(v["status"] != "COMPLETE" or (v["stdout_eof"] and v["stderr_eof"]), "EOF")
    return v

def parse_binding(raw): return freeze(_binding(raw))
def parse_ingress(raw): return freeze(_ingress(raw))
def parse_capture(raw): return freeze(_capture(raw))
