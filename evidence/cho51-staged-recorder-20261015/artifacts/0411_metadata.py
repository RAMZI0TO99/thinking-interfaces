"""Read-only byte/native evidence checks for an explicitly staged restore.

Imports only the standard library and frozen metadata/Windows Job helpers.
Never imports models, arrays, a recorder, or the scientific runtime.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path, PurePosixPath

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
ORIGIN = ROOT / 'runs/coordination/cho51_complete_eegnet_20261015_v4'
ORIGIN_PINS_SHA = 'a7a0dc3a554b9351d16070ee3ad12162fc69404c4dc08cccab4c7bf25e19dac8'
ORIGIN_REVIEW_SHA = 'e8e13870099a84e6de167f496a728227374ebd322cf5c6ff56ae5008648b4d45'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
CASE = '9d0b17621302211d3396cfa2a8cf6113a5887b3ca9ffbf439fddd5ffcf8c2b78'
WORKSPACE = ORIGIN / 'validation_001/cases' / CASE
NATIVE = ROOT / 'runs/migration/20261015T131859Z_0795c61e69'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


old = load('_staged_frozen_metadata', ORIGIN / 'closeout.py')
launcher = load('_staged_frozen_native', ROOT / 'docs/phase2/cho51_tensor_verification_v1/launcher.py')
observed = {}


def remember(path, *, expected=None, compact=False, archive=False, **ignored):
    path = Path(path)
    raw, pin = old.inspect(path, compact=compact)
    if expected is not None and pin[-1] != expected:
        raise ValueError('external file SHA differs: ' + str(path))
    previous = observed.setdefault(str(path), pin)
    if previous != pin:
        raise ValueError('evidence identity changed during metadata verification: ' + str(path))
    return raw, pin


def document(path, *, expected=None, canonical_raw=False, **ignored):
    raw, pin = remember(path, expected=expected, compact=True)
    value = old.decode(raw)
    if canonical_raw and raw != old.canonical(value) + b'\n':
        raise ValueError('canonical finite JSON bytes required')
    return value, pin[-1]


def verify_pin_map(pins):
    for relative, expected in pins['files'].items():
        path = PurePosixPath(relative)
        if path.is_absolute() or '..' in path.parts or '\\' in relative:
            raise ValueError('direct repository relative pin required')
        # Installed/frozen source can have multiple hard links; evidence cannot.
        _, actual = old.inspect(ROOT.joinpath(*path.parts), single_link=False)
        if actual[-1] != expected:
            raise ValueError('source/context pin drift: ' + relative)
    for absolute, expected in pins['runtime'].items():
        _, actual = old.inspect(Path(absolute), single_link=False)
        if actual[-1] != expected:
            raise ValueError('runtime pin drift: ' + absolute)


def native_pins(pins):
    view = {'files': {str(ROOT / name): sha for name, sha in pins['files'].items()}, 'runtime': pins['runtime']}
    return launcher._guard_operation_pins(view), launcher._guard_runtime_pins(view)


def verify_origin():
    observed.clear()
    if old.source_check(ROOT) != CANONICAL:
        raise ValueError('canonical source drift')
    pins, _ = document(ORIGIN / 'pins.json', expected=ORIGIN_PINS_SHA)
    final, _ = document(ORIGIN / 'packet/final-review.json', expected=ORIGIN_REVIEW_SHA)
    if len(pins['files']) != 635 or len(pins['runtime']) != 5:
        raise ValueError('exact accepted origin source/runtime inventory required')
    verify_pin_map(pins)
    request_path = WORKSPACE / 'request.json'
    request, request_sha = document(request_path, expected=final['request_file_sha256'], canonical_raw=True)
    claim_path = Path(request['claim_path'])
    document(claim_path, expected=final['claim_file_sha256'], canonical_raw=True)
    result_path = WORKSPACE / 'source_output/source-result.json'
    result, result_sha = document(result_path, expected=final['source_result_file_sha256'], canonical_raw=True)
    q_path = result_path.with_name('qualification.json')
    q, q_sha = document(q_path, expected=final['source_qualification_file_sha256'], canonical_raw=True)
    old.fields(q, {'schema': 'cho51_complete_eegnet_source_qualification_v1', 'passed': True,
        'pins_sha256': ORIGIN_PINS_SHA, 'request_sha256': request_sha,
        'claim_file_sha256': request['claim_file_sha256'], 'result': result,
        'source_pins_rechecked': 635, 'runtime_pins_rechecked': 5, 'unexpected_denials': 0,
        'source_updates': 5151, 'support_updates': 102, 'scientific_admission': False})
    old.fields(result, {'schema': 'cho51_complete_eegnet_source_result_v1', 'passed': True,
        'request_sha256': request_sha, 'pins_sha256': ORIGIN_PINS_SHA,
        'claim_file_sha256': request['claim_file_sha256'], 'actual_gradient_updates': 5253,
        'source_updates': 5151, 'support_updates': 102, 'fold_count': 102,
        'final_source_subjects': 51, 'complete': True, 'publication_performed': True,
        'full_selector_verified': True, 'public_selection_verifier_passed': True,
        'scientific_admission': False, 'measured_cells': 0})
    if len(q['observed_loaded_module_hashes']) != 4719:
        raise ValueError('exact 4719 observed origin source modules required')
    for path, sha in q['observed_loaded_module_hashes'].items():
        if old.inspect(Path(path), single_link=False)[1][-1] != sha:
            raise ValueError('origin loaded source module changed: ' + path)
    operations, runtimes = native_pins(pins)
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(ORIGIN / 'select_child.py'),
               '--request', str(request_path), '--expect-request', request_sha]
    native = old.verify_native(NATIVE, command, 420, 3072, 4096,
        operations=operations, runtimes=runtimes, document=document, remember=remember, launcher=launcher)
    dispatch, _ = document(WORKSPACE / 'source-native-dispatch.json', canonical_raw=True)
    old.fields(dispatch, {'child_command': command, 'native_directory': str(NATIVE), 'guard_exit_code': 0,
        'request_sha256': request_sha, 'pins_sha256': ORIGIN_PINS_SHA, 'kind': 'source'})
    fixture = Path(request['fixture_root'])
    identity, _ = document(Path(request['fixture_identity_path']), expected=request['fixture_identity_file_sha256'], canonical_raw=True)
    logical_identity = dict(identity)
    identity_sha = logical_identity.pop('sha256')
    if hashlib.sha256(old.canonical(logical_identity)).hexdigest() != identity_sha or identity_sha != request['fixture_identity_sha256']:
        raise ValueError('origin synthetic identity logical SHA differs')
    if len(identity['files']) != 213:
        raise ValueError('exact 213 synthetic input files required')
    input_bytes = 0
    for relative, pin in identity['files'].items():
        relative_path = PurePosixPath(relative)
        if relative_path.is_absolute() or '..' in relative_path.parts or '\\' in relative:
            raise ValueError('fixture relative input path required')
        _, actual = remember(fixture.joinpath(*relative_path.parts), expected=pin['sha256'])
        if actual[2] != pin['size_bytes']:
            raise ValueError('origin physical input size differs')
        input_bytes += actual[2]
    if input_bytes != 734579463:
        raise ValueError('exact physical input bytes required')
    method, _ = document(Path(request['method_config_path']), expected=request['method_config_file_sha256'], canonical_raw=True)
    if hashlib.sha256(old.canonical(method)).hexdigest() != request['method_config_sha256']:
        raise ValueError('origin logical method SHA differs')
    for pin in result['publication_files'].values():
        _, actual = remember(Path(pin['path']), expected=pin['file_sha256'])
        if list(actual[:-1]) != pin['identity'] or actual[2] != pin['size_bytes']:
            raise ValueError('origin publication physical identity changed')
    trace, _ = document(Path(result['optimizer_trace_path']), expected=result['optimizer_trace_file_sha256'], canonical_raw=True)
    if len(trace['events']) != 5253:
        raise ValueError('actual origin optimizer transcript count differs')
    evidence, _ = document(Path(result['selection_evidence_path']), canonical_raw=True)
    history = old.verify_complete_history(evidence, method,
        protocol_sha256=identity['protocol_sha256'], source_selection_sha256=identity['source_selection_sha256'],
        fixture_source_sha256=request['fixture_source_sha256'])
    # Preserve the failed transaction and its external immutable refusal packet.
    packet = ROOT / 'evidence/cho51-complete-eegnet-resource-refusal-20261015'
    manifest, _ = document(packet / 'manifest.json', expected='a9a469b47604e18f64df4b7c118ef624d05d86b2448c1f671cfb2e7545cdf81f')
    document(packet / 'summary.json', expected='6881ff8496b3bee836ab69438537cfa7c6312205707027acd2004887b03b4cdc')
    for row in manifest['artifacts']:
        for path in (ROOT / row['source'], packet / row['path']):
            _, actual = remember(path, expected=row['sha256'], compact=True)
            if actual[2] != row['bytes']:
                raise ValueError('frozen refusal archive/source byte count differs')
    failure_path = Path(request['recorder_root']) / 'attempts' / (CASE + '.attempt1.failure.json')
    document(failure_path, canonical_raw=True)
    document(ORIGIN / 'source-review.json', expected=pins['source_review_sha256'])
    for name in ('20261015T131826Z_7d29560b93', '20261015T132158Z_6da3b33f16'):
        document(ROOT / 'runs/migration' / name / 'receipt.json')
        launcher._job_absent('pro3_migration_' + name)
    recorder = Path(request['recorder_root'])
    claims = list((recorder / 'claims').glob('*.claim.json'))
    failures = list((recorder / 'attempts').glob('*.failure.json'))
    if (len(claims) != 1 or len(failures) != 1
            or set(recorder.rglob('*.json')) != {claim_path, failure_path}
            or (WORKSPACE / 'parent-attestation.json').exists()):
        raise ValueError('failed origin ledger inventory changed')
    return {'pins': pins, 'request': request, 'request_path': request_path, 'request_sha': request_sha,
        'result': result, 'result_path': result_path, 'result_sha': result_sha,
        'q_path': q_path, 'q_sha': q_sha, 'native': native, 'history': history,
        'input_files': 213, 'input_bytes': input_bytes, 'module_files': 4719,
        'files': {path: pin[-1] for path, pin in observed.items()}}


def check_contract(contract, origin):
    expected = {'schema': 'cho51_staged_eegnet_restore_contract_v1',
        'origin_request_path': str(origin['request_path']), 'origin_request_sha256': origin['request_sha'],
        'origin_source_result_path': str(origin['result_path']), 'origin_source_result_sha256': origin['result_sha'],
        'origin_claim_path': origin['request']['claim_path'], 'origin_claim_sha256': origin['request']['claim_file_sha256'],
        'origin_source_qualification_path': str(origin['q_path']), 'origin_source_qualification_sha256': origin['q_sha'],
        'origin_native_directory': str(NATIVE), 'origin_native_receipt_sha256': origin['native']['receipt_file_sha256'],
        'origin_pins_path': str(ORIGIN / 'pins.json'), 'origin_pins_sha256': ORIGIN_PINS_SHA,
        'output_path': str(RUN / 'verification_001'), 'origin_files': origin['files'],
        'source_work_reused': True, 'source_training_replayed': False, 'historical_gradient_updates': 5253,
        'current_gradient_updates': 0, 'parent_transaction_qualified': False,
        'engineering_successes': 0, 'measured_cells': 0, 'scientific_admission': False,
        'original_case_attempts_remaining': 0}
    old.fields(contract, expected, exact=True)


def make_contract(origin):
    value = {'schema': 'cho51_staged_eegnet_restore_contract_v1',
        'origin_request_path': str(origin['request_path']), 'origin_request_sha256': origin['request_sha'],
        'origin_source_result_path': str(origin['result_path']), 'origin_source_result_sha256': origin['result_sha'],
        'origin_claim_path': origin['request']['claim_path'], 'origin_claim_sha256': origin['request']['claim_file_sha256'],
        'origin_source_qualification_path': str(origin['q_path']), 'origin_source_qualification_sha256': origin['q_sha'],
        'origin_native_directory': str(NATIVE), 'origin_native_receipt_sha256': origin['native']['receipt_file_sha256'],
        'origin_pins_path': str(ORIGIN / 'pins.json'), 'origin_pins_sha256': ORIGIN_PINS_SHA,
        'output_path': str(RUN / 'verification_001'), 'origin_files': origin['files'],
        'source_work_reused': True, 'source_training_replayed': False, 'historical_gradient_updates': 5253,
        'current_gradient_updates': 0, 'parent_transaction_qualified': False,
        'engineering_successes': 0, 'measured_cells': 0, 'scientific_admission': False,
        'original_case_attempts_remaining': 0}
    check_contract(value, origin)
    return value
