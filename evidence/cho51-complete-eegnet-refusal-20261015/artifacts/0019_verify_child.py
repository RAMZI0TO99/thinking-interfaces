"""Detached selected-source tensor/history restoration with all fitting blocked."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from select_child import Runtime, digest, identity, load_request, read_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--expect-request', required=True)
    parser.add_argument('--source-result', type=Path, required=True)
    parser.add_argument('--expect-source-result', required=True)
    args = parser.parse_args()
    request = load_request(args.request, args.expect_request)
    expected_path = Path(request['selection_output']) / 'source-result.json'
    if args.source_result != expected_path or digest(expected_path) != args.expect_source_result:
        raise ValueError('parent-pinned actual accepted source result required')
    before = {path: identity(path) for path in (args.request, Path(request['claim_path']), expected_path)}
    source_result = read_json(expected_path)
    runtime = Runtime('detached', Path(request['pins_path']), request['independent_pins_sha256'],
        Path(request['detached_output']), request)
    runtime.install_torch_guards()
    from docs.phase2.cho51_complete_eegnet_v1.transaction import load_complete_request
    if load_complete_request(request).sha256 != args.expect_request:
        raise ValueError('exact typed independently pinned complete request required')
    from docs.phase2.cho51_complete_eegnet_v1.selection import verify_publication
    runtime.active = True
    try:
        result = verify_publication(request, source_result,
            expected_source_result_file_sha256=args.expect_source_result,
            set_protected_inputs=runtime.set_protected_inputs)
    finally:
        runtime.active = False
    if (result.get('schema') != 'cho51_complete_eegnet_detached_result_v1'
            or result.get('passed') is not True
            or any(runtime.numerical_calls.get(key, 0) != 0 for key in (
                'optimizer_init', 'sgd_step', 'tensor_backward', 'autograd_backward', 'autograd_grad'))
            or [row['enabled'] for row in runtime.protection_transitions] != [True, False]):
        raise ValueError('actual detached canonical restoration with no fitting required')
    if any(identity(path) != pin for path, pin in before.items()):
        raise ValueError('parent-pinned request/claim/source result changed across detached verification')
    runtime.finish(result, args.expect_request)
    print(json.dumps({'passed': True, 'detached_restoration': True, 'scientific_admission': False}), flush=True)


if __name__ == '__main__':
    main()
