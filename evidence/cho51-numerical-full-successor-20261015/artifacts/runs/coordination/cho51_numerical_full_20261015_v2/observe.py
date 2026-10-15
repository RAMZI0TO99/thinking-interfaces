"""Fresh standard-library native resource observation, without compute admission."""
import argparse
import ctypes
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]


class Memory(ctypes.Structure):
    _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
        (name, ctypes.c_ulonglong) for name in (
            'total_physical', 'available_physical', 'total_page', 'available_page',
            'total_virtual', 'available_virtual', 'available_extended')]


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--name', required=True)
args = parser.parse_args()
if not args.name.isidentifier():
    raise ValueError('unused observation name required')
memory = Memory()
memory.length = ctypes.sizeof(memory)
api = ctypes.WinDLL('kernel32', use_last_error=True)
api.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(Memory)]
api.GlobalMemoryStatusEx.restype = ctypes.c_int
if not api.GlobalMemoryStatusEx(ctypes.byref(memory)):
    raise OSError(ctypes.get_last_error(), 'GlobalMemoryStatusEx failed')
free = shutil.disk_usage(ROOT).free
pauses = {str(path): path.exists() for path in (
    Path('D:/Aenv/pro2/WORK') / f'resume-{day}-001' / 'coordination/PRO2_REQUEST_PRO3_PAUSE.json'
    for day in ('20261007', '20261012', '20261013', '20261015'))}
sample = {
    'schema': 'cho51_numerical_full_successor_resource_observation_v1',
    'observed_utc': datetime.now(timezone.utc).isoformat(),
    'available_ram_bytes': memory.available_physical, 'free_disk_bytes': free,
    'startup_ram_required_bytes': 10 * 1024**3, 'active_ram_required_bytes': 4 * 1024**3,
    'free_disk_required_bytes': 20 * 1024**3, 'observed_pause_paths': pauses,
    'observation_satisfies_startup_floors': memory.available_physical >= 10 * 1024**3 and free >= 20 * 1024**3,
    'compute_admitted': False, 'job_launched': False,
    'peer_release_or_host_quiet_inferred': False, 'scientific_admission': False,
}
with (RUN / (args.name + '.json')).open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(sample, stream, indent=2, sort_keys=True, allow_nan=False)
    stream.write('\n')
print(json.dumps(sample))
