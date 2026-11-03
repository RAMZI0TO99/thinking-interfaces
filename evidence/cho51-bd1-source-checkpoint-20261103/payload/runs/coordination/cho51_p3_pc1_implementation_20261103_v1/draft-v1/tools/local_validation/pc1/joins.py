"""Independent expected binding join; no retained streams or native inputs."""
from .common import raw_pin, require, uuid
from .parsers import _binding, _ingress, _capture

class SuppliedResult:
    """Fixed non-authoritative result; callers cannot supply flag values."""
    __slots__ = ()
    @property
    def consistent(self): return "CONSISTENT_SUPPLIED"
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

def join(raw_b, raw_i, raw_c, expected_o, expected_b):
    uuid(expected_o)
    expected = _binding(expected_b)
    b, i, c = _binding(raw_b), _ingress(raw_i), _capture(raw_c)
    require(expected["operation"] == expected_o and b["operation"] == expected_o and i["operation"] == expected_o and c["operation"] == expected_o, "OPERATION")
    require(b == expected, "EXPECTED_BINDING")
    bp = raw_pin(raw_b)
    require(i["binding"] == bp and c["binding"] == bp, "BINDING_PIN")
    return SuppliedResult()

def dispatch(*args, **kwargs):
    return "REFUSED"
