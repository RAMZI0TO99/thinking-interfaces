"""Pure supplied accounting; no live guard, clock, capture or dispatch authority."""
from dataclasses import dataclass
from ..hb1 import common as c

RESERVATIONS = (('caller',8,9764864), ('supervisor',6,4653056), ('closeout',16,3293184))

@dataclass(frozen=True, slots=True)
class Capture:
    stdout: bytes
    stderr: bytes
    chunks: tuple
    consumed: bool
    @property
    def authenticated(self): return False

class CaptureModel:
    def __init__(self):
        self._streams = [bytearray(), bytearray()]
        self._chunks = []
        self._busy = False
        self._failed = False
    def append(self, stream, chunk, *, check):
        if self._busy or self._failed:
            self._failed = True
            raise c.Refusal('consumed or reentrant')
        self._busy = True
        try:
            c.checkpoint(check)
            c.require(not self._failed and type(stream) is str and stream in ('stdout','stderr') and type(chunk) is bytes and len(self._chunks) < 4096, 'stream')
            target = self._streams[0 if stream == 'stdout' else 1]
            c.require(len(target) + len(chunk) <= 1048576, 'overflow')
            target.extend(chunk)
            self._chunks.append((stream, chunk))
        except BaseException:
            self._failed = True
            raise
        finally:
            self._busy = False
    def snapshot(self):
        return Capture(bytes(self._streams[0]), bytes(self._streams[1]), tuple(self._chunks), self._failed or self._busy)

@dataclass(frozen=True, slots=True)
class GuardFacts:
    owner: str
    clock: str
    patch_surface: tuple
    @property
    def authenticated(self): return False
    @property
    def execution_accepted(self): return False


def guard_binding(*, owner, clock, patch_surface, guard_surface, check):
    """Closed tokens describe only a hypothetical independent binding."""
    c.checkpoint(check)
    c.token(owner); c.token(clock)
    c.require(owner != clock and type(patch_surface) is tuple and type(guard_surface) is tuple and len(patch_surface) <= 64 and 0 < len(guard_surface) <= 64, 'guard binding')
    for token in patch_surface + guard_surface:
        c.token(token)
    c.require(len(set(patch_surface)) == len(patch_surface) and len(set(guard_surface)) == len(guard_surface) and not set(patch_surface).intersection(guard_surface), 'guard isolation')
    return GuardFacts(owner, clock, patch_surface)


def deadlines(t0, fault, final_budget, margin):
    """Supplied integer seconds, with overflow and negative results refused."""
    for n in (t0, fault, final_budget, margin): c.integer(n)
    limit = 2**63 - 1
    c.require(t0 <= limit - 65 and t0 <= fault <= limit - 5
              and final_budget + margin < 60, 'deadline range')
    return min(t0+55, t0+60-final_budget-margin), min(fault+5,t0+65)


def supplied_gates(*, guard, final_verified, now, original_deadline, cleanup_deadline, check):
    c.checkpoint(check)
    for value in (now, original_deadline, cleanup_deadline): c.integer(value)
    c.require(guard is True and final_verified is True and now < min(original_deadline, cleanup_deadline), 'supplied gate refused')
    return ('SUPPLIED_MODEL_FACTS', False)


def dispatch(*args, **kwargs):
    raise c.Refusal('operational host unavailable; P disabled')
