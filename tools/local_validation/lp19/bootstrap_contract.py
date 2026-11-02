"""Closed supplied-data joins for the separately admitted native bootstrap."""
from ..v1 import records as r

QUALIFICATION = "runs/coordination/cho51_p3_startup_diagnostic_20261031_q3/root-qualification.json"
CONTROLS = ("accepted", "bad_identity")


def controls(value):
    r.require(type(value) is list and value == list(CONTROLS)
              and all(type(item) is str for item in value),
              "exact ordered native bootstrap controls")


def validate_request(request):
    r.require(type(request) is dict and request.get("stage") == "QD",
              "native bootstrap stage")
    ref = request.get("bootstrap_qualification")
    r.closed(ref, ("path", "bytes", "sha256"))
    r.require(ref["path"] == QUALIFICATION, "exact accepted bootstrap reference")
    r.exact_int(ref["bytes"], 1, 1024**2)
    r.require(type(ref["sha256"]) is str and r.HEX64.fullmatch(ref["sha256"]),
              "bootstrap digest")
    sources = request.get("sources")
    r.require(type(sources) is dict and type(sources.get(QUALIFICATION)) is dict,
              "bootstrap source pin required")
    r.require(r.canonical_bytes(sources[QUALIFICATION]) ==
              r.canonical_bytes({key: ref[key] for key in ("bytes", "sha256")}),
              "bootstrap reference covered by exact source pins")
    if request["stage"] == "QD":
        controls(request.get("bootstrap_controls"))
    else:
        r.require("bootstrap_controls" not in request, "P cannot select a Q control")
    return True


def validate_adoption(request, adoption):
    r.require(type(adoption) is dict and
              adoption.get("bootstrap_qualification_sha256") ==
              request["bootstrap_qualification"]["sha256"],
              "adoption binds accepted bootstrap qualification")
    return True


def validate_qualification(qualification, actual):
    r.require(type(qualification) is dict and type(actual) is dict,
              "bootstrap qualification and actual records")
    controls(qualification.get("bootstrap_controls"))
    controls(actual.get("bootstrap_controls"))
    return True
