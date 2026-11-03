"""Classify dedicated supplied input failures only."""
from .common import Refusal, REFUSAL_CODES
from .joins import join

class RefusedResult:
    """Finite-code refusal with fixed, non-authoritative properties."""
    __slots__ = ("_code",)
    def __init__(self, code):
        if type(code) is not str or code not in REFUSAL_CODES:
            raise ValueError("invalid refusal code")
        object.__setattr__(self, "_code", code)
    @property
    def code(self): return self._code
    @property
    def consistent(self): return "REFUSED_SUPPLIED"
    @property
    def native_authority(self): return False
    @property
    def execution_authorized(self): return False
    @property
    def debt_discharged(self): return False
    @property
    def dispatch(self): return "REFUSED"
    def __setattr__(self, name, value): raise AttributeError("immutable result")
    def __delattr__(self, name): raise AttributeError("immutable result")

def classify(raw_b, raw_i, raw_c, expected_o, expected_b):
    try:
        return join(raw_b, raw_i, raw_c, expected_o, expected_b)
    except Refusal as exc:
        return RefusedResult(exc.code)
