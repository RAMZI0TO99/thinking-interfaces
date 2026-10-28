"""Strict bounded metadata control-plane helpers; no numerical imports."""
from __future__ import annotations

import ctypes
import hashlib
import json
import math
import os
import stat
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path, PureWindowsPath

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
OUTPUT = RUN / 't1'
SCOPE = 'cho51_canonical_boundary_20261025_v5_a_tests'
BATCH_ID = 'a'
sys.path.insert(0, str(ROOT / 'runs/coordination/cho51_canonical_boundary_20261025_v5_aggregate'))
import aggregate as family
ZERO = dict(source_updates=0, restore_count=0, support_updates=0, gradient_updates=0,
            target_inference_calls=0, query_count=0, model_constructions=0, measured_cells=0)
PAUSES = tuple(Path('D:/Aenv/pro2/WORK') / f'resume-{day}-001/coordination/PRO2_REQUEST_PRO3_PAUSE.json'
               for day in ('20261007', '20261012', '20261013', '20261015', '20261025'))
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
FROZEN = {
    'tools/migration/guard.py': '1150228137873b783ba5800b89ded0e7598448f05da3b87a7ac0a62e6079f157',
    'tools/migration/common.py': 'fe2790bc2703af17b930dffe109d8c750fb8d0abfa205fbd40245aec178936d5',
    'tools/migration/job_adapter.py': 'a6902fabf675b329440b39404cdc4306e562fda4b47efefb19982c6c2502ae8b',
    'tools/migration/task.py': '8ffb5d42cfe7107d57b8bb7d69d07909cd1dd14bc32a5e645b1d675e0c3e8a70',
    'evaluation/phase2_supervision_primitives.py': '3590b6c72e9ddfbfa0de4e012b55b0237c77375ede5b75ccfe7352e4c8cb063e',
}
CONTROL_NAMES = ('finite_json', 'duplicate_json', 'nan_json', 'overflow_json', 'nested_json',
    'zero_budget', 'boolean_budget', 'owned_path', 'escaped_path', 'first_create', 'duplicate_create',
    'bounded_tail', 'full_window', 'short_window', 'junit_baseline', 'junit_duplicate',
    'junit_failure', 'junit_class', 'reports_baseline', 'reports_missing', 'reports_duplicate',
    'git_actual_spelling_list', 'git_actual_spelling_cmdline', 'git_status_tail', 'git_explicit_case_spelling',
    'git_alternate_executable', 'git_alternate_argument_executable', 'git_invalid_tail',
    'git_explicit_environment', 'git_descendant_cwd', 'git_relative_cwd',
    'pytest_alias_owned_paths', 'pytest_alias_outside_paths', 'pytest_alias_outside_destination')
GIT_PATH = Path('C:/Users/aladdin-alyanai/AppData/Local/Programs/Git/cmd/git.exe')
PYTEST_PATHLIB_SHA256 = 'c9fe77dccbf52afa1196ff92870ed919e09f254c082710a86ed417fd3ca90329'


def windows_path_matches(value, expected):
    if type(value) is not str or type(expected) is not str:
        return False
    path = PureWindowsPath(value)
    expected_path = PureWindowsPath(expected)
    return (path.is_absolute() and expected_path.is_absolute() and str(path) == value
            and '..' not in path.parts and path == expected_path)


def git_command_allowed(executable, arguments, cwd, environment, *, pinned_git, git_spelling, root):
    if (environment is not None or not windows_path_matches(git_spelling, pinned_git)
            or not windows_path_matches(cwd, root)
            or (executable is not None and not windows_path_matches(executable, pinned_git))):
        return False
    if type(arguments) is list:
        if not all(type(value) is str for value in arguments):
            return False
    elif type(arguments) is not str:
        return False
    forms = [[git_spelling, '--no-optional-locks', *tail] for tail in
             (['rev-parse', '--verify', 'HEAD'], ['status', '--porcelain', '--untracked-files=all'])]
    return any(arguments == form or arguments == subprocess.list2cmdline(form) for form in forms)


def pytest_alias_paths_owned(source, destination, output):
    for value in (source, destination):
        if type(value) not in (str, bytes):
            return False
        path = Path(os.path.abspath(os.fsdecode(value)))
        if not path.is_relative_to(output):
            return False
        for ancestor in (path, *path.parents):
            try:
                info = ancestor.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
                return False
    return True

def need(condition, message):
    if not condition:
        raise ValueError(message)

def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()

def zero_budget(value):
    return type(value) is dict and set(value) == set(ZERO) and all(type(member) is int and member == 0 for member in value.values())

def lease_fits(start, end):
    return start + timedelta(seconds=605) <= end

def unique(rows):
    result = {}
    for name, value in rows:
        need(name not in result, 'duplicate JSON key')
        result[name] = value
    return result

def parse(raw):
    value = json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    def finite(member, depth=0):
        need(depth <= 80, 'control JSON nesting limit exceeded')
        if type(member) is float:
            need(math.isfinite(member), 'nonfinite control JSON number')
        elif type(member) is dict:
            for child in member.values():
                finite(child, depth + 1)
        elif type(member) is list:
            for child in member:
                finite(child, depth + 1)
    finite(value)
    return value

def file_key(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns

def direct(path, *, git=False):
    need(type(path) is Path or isinstance(path, Path), 'actual path required')
    need(path.is_absolute() and path.resolve(strict=True) == path, 'direct absolute path required')
    for ancestor in (path, *path.parents):
        info = ancestor.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 1024,
             'reparse or alias path refused')
    info = path.stat()
    exception = git and path == GIT_PATH and info.st_nlink == 2 and info.st_size == 46480
    need(stat.S_ISREG(info.st_mode) and (info.st_nlink == 1 or exception), 'single-link regular file required')
    return file_key(info)

def read(path, expected=None, maximum=8 * 1024**2, *, retain=True, git=False):
    before = direct(path, git=git)
    need(0 <= before[2] <= maximum, 'bounded file required')
    digest = hashlib.sha256()
    pieces, count = [], 0
    with path.open('rb') as stream:
        opened = file_key(os.fstat(stream.fileno()))
        while True:
            chunk = stream.read(min(1024**2, maximum + 1 - count))
            if not chunk:
                break
            count += len(chunk)
            need(count <= maximum, 'file grew beyond bound')
            digest.update(chunk)
            if retain:
                pieces.append(chunk)
        finished = file_key(os.fstat(stream.fileno()))
    need(opened == finished and opened[:4] == before[:4] and direct(path, git=git) == before and count == before[2],
         'file physical identity changed')
    observed = digest.hexdigest()
    need(expected is None or observed == expected, 'physical byte pin differs: ' + str(path))
    return (b''.join(pieces) if retain else observed), before

def document(path, expected=None):
    return parse(read(path, expected)[0])

def tail(path, maximum=4000):
    before = direct(path)
    with path.open('rb') as stream:
        opened = file_key(os.fstat(stream.fileno()))
        stream.seek(max(0, before[2] - maximum))
        raw = stream.read(maximum + 1)
        finished = file_key(os.fstat(stream.fileno()))
    need(len(raw) <= maximum and opened == finished and opened[:4] == before[:4]
         and direct(path) == before, 'bounded log tail identity changed')
    return raw.decode('utf-8', errors='replace')

def write(path, value):
    raw = canonical(value)
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return hashlib.sha256(raw).hexdigest()

def pause_check():
    need(not any(path.exists() for path in PAUSES), 'genuine peer pause requested')

def pins(expected):
    value = document(RUN / 'pins.json', expected)
    need(value['schema'] == 'cho51_canonical_boundary_pins_v1' and value['scope'] == SCOPE
         and value['startup_ram_gib'] == 4 and value['active_ram_gib'] == 4 and value['disk_gib'] == 20
         and value['seconds'] == 600 and value['process_mib'] == 4096 and value['job_mib'] == 5120
         and value['scientific_admission'] is False and zero_budget(value['expected_numerical_budget']),
         'exact metadata phase pins required')
    need(type(value['expected_tests']) is int and value['expected_tests'] == family.BATCH_COUNTS[BATCH_ID]
         and family.header_matches(value, BATCH_ID), 'exact full/selected planned batch counts required')
    need(set(value['reviewed_files']) == set(family.source_relatives()), 'complete frozen family source inventory required')
    need(type(value['expected_stdlib_controls']) is int and value['expected_stdlib_controls'] == len(CONTROL_NAMES),
         'exact current stdlib control count required')
    review = document(RUN / 'source-review.json', value['source_review_sha256'])
    need(review['source_only'] is True and review['remaining_actionable_findings'] == []
         and review['files'] == value['reviewed_files']
         and type(review['expected_tests']) is int and review['expected_tests'] == value['expected_tests']
         and type(review['expected_stdlib_controls']) is int
         and review['expected_stdlib_controls'] == len(CONTROL_NAMES)
         and family.header_matches(review, BATCH_ID), 'settled source review required')
    return value

def verify_files(value):
    for name, expected in value['files'].items():
        path = Path(name)
        read(path, expected, 2 * 1024**3, retain=False, git=path.name == 'git.exe')
    for name, expected in FROZEN.items():
        read(ROOT / name, expected, 1024**2, retain=False)
    pause_check()

def admission(value, pins_sha):
    accepted = document(RUN / 'admission.json')
    need(accepted['schema'] == 'cho51_canonical_boundary_admission_v1' and accepted['accepted'] is True
         and accepted['pins_sha256'] == pins_sha and accepted['source_review_sha256'] == value['source_review_sha256']
         and zero_budget(accepted['expected_numerical_budget']) and type(accepted['maximum_jobs']) is int and accepted['maximum_jobs'] == 1
         and type(accepted['expected_metadata_tests']) is int and accepted['expected_metadata_tests'] == value['expected_tests']
         and type(accepted['expected_stdlib_controls']) is int and accepted['expected_stdlib_controls'] == len(CONTROL_NAMES)
         and type(accepted['external_stdlib_closeout_maximum_seconds']) is int
         and accepted['external_stdlib_closeout_maximum_seconds'] == 300
         and accepted['automatic_retry_permitted'] is False and accepted['scientific_admission'] is False,
         'fresh exact Root admission required')
    need(family.header_matches(accepted, BATCH_ID), 'exact Root batch/full-collection binding required')
    peer = document(Path(accepted['peer_release_path']), accepted['peer_release_sha256'])
    expected = dict(schema='pro2_pro3_compute_release_v1', scope=SCOPE, released=True, pins_sha256=pins_sha,
        maximum_jobs=1, max_job_seconds=600, process_mib=4096, job_mib=5120, startup_ram_gib=4,
        active_ram_gib=4, disk_gib=20, expected_numerical_budget=ZERO,
        expected_metadata_tests=value['expected_tests'], expected_stdlib_controls=len(CONTROL_NAMES),
        external_stdlib_closeout_maximum_seconds=300,
        owner_resource_amendment_sha256=value['owner_resource_amendment_sha256'], scientific_admission=False)
    need(all(type(peer.get(name)) is type(member) and peer[name] == member for name, member in expected.items()),
         'exact fresh metadata peer grant required')
    need(zero_budget(peer['expected_numerical_budget']) and family.header_matches(peer, BATCH_ID),
         'strict integer-zero and exact complementary peer batch required')
    for field in ('window_start_utc', 'window_end_utc'):
        need(type(peer[field]) is str and accepted[field] == peer[field], 'UTC string window required')
    now = datetime.now(timezone.utc)
    need(datetime.fromisoformat(peer['window_start_utc']).astimezone(timezone.utc) <= now
         <= datetime.fromisoformat(peer['window_end_utc']).astimezone(timezone.utc),
         'live peer window required')
    amendment = document(RUN / 'owner-resource-amendment.json', value['owner_resource_amendment_sha256'])
    need(amendment['owner_instruction_exact'] == 'use what you have . i have freed the ram you have more now!' and amendment['scope'] == SCOPE
         and amendment['startup_ram_gib'] == 4 and amendment['active_ram_gib'] == 4
         and amendment['canonical_guard_modified'] is False and amendment['scientific_admission'] is False,
         'new directly scoped owner resource amendment required')
    pause_check()
    return accepted, peer

def job_api():
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.OpenJobObjectW.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_wchar_p]
    api.OpenJobObjectW.restype = ctypes.c_void_p
    api.CloseHandle.argtypes = [ctypes.c_void_p]
    api.GetCurrentProcess.restype = ctypes.c_void_p
    api.IsProcessInJob.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
    return api

def job_absent(name):
    api = job_api()
    ctypes.set_last_error(0)
    handle = api.OpenJobObjectW(4, False, name)
    error = ctypes.get_last_error()
    if handle:
        api.CloseHandle(handle)
    need(not handle and error == 2, 'scoped native Job not freshly absent')

def membership(name):
    api = job_api()
    handle = api.OpenJobObjectW(4, False, name)
    need(handle, 'named private Job required')
    try:
        member = ctypes.c_int()
        need(api.IsProcessInJob(api.GetCurrentProcess(), handle, ctypes.byref(member)) and member.value,
             'actual named Job membership required')
    finally:
        api.CloseHandle(handle)
