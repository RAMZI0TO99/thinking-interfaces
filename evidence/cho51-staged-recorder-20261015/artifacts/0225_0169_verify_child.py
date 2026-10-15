"""Standalone detached restoration of an accepted immutable source publication.

This stage reuses the original source artifacts. It cannot fit, publish, alter
that failed transaction, or write an engineering-success recorder terminal.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime import Runtime, ROOT, RUN, ORIGIN, ORIGIN_PINS_SHA256, digest, identity, read_json


def origin_context(args):
    if (args.pins != RUN / 'pins.json' or args.contract != RUN / 'stage-contract.json'
            or any(re.fullmatch('[a-f0-9]{64}', value) is None
                for value in (args.expect_pins, args.expect_contract))
            or digest(args.pins) != args.expect_pins or digest(args.contract) != args.expect_contract):
        raise ValueError('independently pinned exact staged bundle and contract required')
    pins, contract = read_json(args.pins), read_json(args.contract)
    expected = {'schema': 'cho51_staged_eegnet_restore_contract_v1',
        'origin_pins_sha256': ORIGIN_PINS_SHA256,
        'output_path': str(RUN / 'verification_001'),
        'scientific_admission': False, 'original_case_attempts_remaining': 0,
        'source_training_replayed': False, 'parent_transaction_qualified': False}
    if (any(type(contract.get(key)) is not type(value) or contract[key] != value
            for key, value in expected.items())
            or pins.get('stage_contract_sha256') != args.expect_contract):
        raise ValueError('exact immutable staged reuse scope required')
    bound = {'origin_request': 'request', 'origin_source_result': 'source result',
        'origin_claim': 'claim', 'origin_source_qualification': 'source qualification',
        'origin_pins': 'origin pins'}
    paths = {}
    for stem, label in bound.items():
        path = Path(contract[stem + '_path'])
        expected_sha = contract[stem + '_sha256']
        if (type(expected_sha) is not str or re.fullmatch('[a-f0-9]{64}', expected_sha) is None
                or not path.is_relative_to(ROOT)
                or pins.get('files', {}).get(path.relative_to(ROOT).as_posix()) != expected_sha
                or digest(path) != expected_sha):
            raise ValueError('exact current contract-pinned origin ' + label + ' required')
        paths[stem] = path
    native = Path(contract['origin_native_directory'])
    if native != ROOT / 'runs/migration/20261015T131859Z_0795c61e69':
        raise ValueError('the original accepted v4 source native receipt is required')
    receipt_path = native / 'receipt.json'
    if (digest(receipt_path) != contract['origin_native_receipt_sha256']
            or pins['files'].get(receipt_path.relative_to(ROOT).as_posix()) != contract['origin_native_receipt_sha256']):
        raise ValueError('exact current accepted source receipt pin required')
    before = {path: identity(path) for path in (
        args.contract, *paths.values(), receipt_path, native / 'admission.json')}
    request = read_json(paths['origin_request'])
    if (request.get('schema') != 'cho51_complete_eegnet_request_v1'
            or request.get('scientific_admission') is not False
            or request.get('engineering_only') is not True
            or request.get('original_case_attempts_remaining') != 0
            or paths['origin_request'] != Path(request['workspace']) / 'request.json'
            or paths['origin_claim'] != Path(request['claim_path'])
            or paths['origin_pins'] != ORIGIN / 'pins.json'
            or Path(request['pins_path']) != paths['origin_pins']
            or Path(request['fixture_root']) != ORIGIN / 'validation_001/fixture'
            or request['independent_pins_sha256'] != ORIGIN_PINS_SHA256
            or request['claim_file_sha256'] != contract['origin_claim_sha256']
            or paths['origin_source_result'] != Path(request['selection_output']) / 'source-result.json'
            or paths['origin_source_qualification'] != Path(request['selection_output']) / 'qualification.json'):
        raise ValueError('unchanged exact original claimed source request required')
    source_result = read_json(paths['origin_source_result'])
    source_q = read_json(paths['origin_source_qualification'])
    expected_q = {'schema': 'cho51_complete_eegnet_source_qualification_v1', 'passed': True,
        'pins_sha256': ORIGIN_PINS_SHA256,
        'request_sha256': contract['origin_request_sha256'],
        'case_id': request['case_id'], 'claim_file_sha256': contract['origin_claim_sha256'],
        'source_pins_rechecked': 635, 'runtime_pins_rechecked': 5,
        'source_updates': 5151, 'support_updates': 102,
        'scientific_admission': False, 'original_case_attempts_remaining': 0}
    if (any(type(source_q.get(key)) is not type(value) or source_q[key] != value
            for key, value in expected_q.items()) or source_q.get('result') != source_result
            or source_result.get('schema') != 'cho51_complete_eegnet_source_result_v1'
            or source_result.get('passed') is not True
            or source_result.get('publication_performed') is not True
            or source_result.get('actual_gradient_updates') != 5253):
        raise ValueError('the accepted full source selection/publication qualification is required')
    receipt = read_json(receipt_path)
    state = receipt.get('native_state', {})
    required = ('job_created', 'created_suspended', 'limits_set', 'limits_query_verified',
        'atomic_job_assignment_requested', 'atomic_job_assignment_verified', 'assigned',
        'membership_verified', 'resumed', 'job_empty_before_close', 'job_closed',
        'process_handle_closed', 'thread_handle_closed', 'root_exit_after_job_close', 'assignment_step_seen')
    if (receipt.get('schema') != 'migration_guard_receipt_v1' or receipt.get('accepted') is not True
            or receipt.get('error') is not None or receipt.get('job_absent') is not True
            or receipt.get('job_name') != 'pro3_migration_' + native.name
            or state.get('job_named') != receipt['job_name']
            or any(state.get(key) is not True for key in required)
            or state.get('cleanup_errors') != [] or state.get('peak_sampling_errors') != []
            or receipt.get('result', {}).get('reason') != 'normal'
            or type(receipt.get('result', {}).get('exit_code')) is not int
            or receipt['result']['exit_code'] != 0):
        raise ValueError('the accepted cleanly closed original source native Job is required')
    if any(identity(path) != pin for path, pin in before.items()):
        raise ValueError('origin artifacts changed during pre-verification binding')
    return contract, request, source_result, before


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pins', type=Path, required=True)
    parser.add_argument('--expect-pins', required=True)
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--expect-contract', required=True)
    args = parser.parse_args()
    contract, request, source_result, before = origin_context(args)
    runtime = Runtime('detached', args.pins, args.expect_pins, Path(contract['output_path']), request)
    runtime.install_torch_guards()
    from docs.phase2.cho51_complete_eegnet_v2.transaction import load_complete_request
    if load_complete_request(request).sha256 != contract['origin_request_sha256']:
        raise ValueError('exact typed unchanged original source request required')
    from docs.phase2.cho51_staged_restore_v1.restore import verify_publication
    runtime.active = True
    try:
        result = verify_publication(request, source_result,
            expected_source_result_file_sha256=contract['origin_source_result_sha256'],
            set_protected_inputs=runtime.set_protected_inputs, detached_output=runtime.output)
    finally:
        runtime.active = False
    if (result.get('schema') != 'cho51_complete_eegnet_detached_result_v1'
            or result.get('passed') is not True
            or any(runtime.numerical_calls.get(key, 0) != 0 for key in (
                'optimizer_init', 'sgd_step', 'tensor_backward', 'autograd_backward', 'autograd_grad'))
            or runtime.source_steps != 0 or runtime.support_steps != 0
            or [row['enabled'] for row in runtime.protection_transitions] != [True, False]):
        raise ValueError('actual staged canonical restoration with no source replay or fitting required')
    if any(identity(path) != pin for path, pin in before.items()):
        raise ValueError('immutable origin bindings changed across staged detached verification')
    runtime.finish(result, contract['origin_request_sha256'])
    if any(identity(path) != pin for path, pin in before.items()):
        raise ValueError('immutable origin bindings changed during staged qualification')
    print(json.dumps({'passed': True, 'detached_restoration': True,
        'source_training_replayed': False, 'parent_transaction_qualified': False,
        'engineering_successes': 0, 'measured_cells': 0, 'scientific_admission': False}), flush=True)


if __name__ == '__main__':
    main()
