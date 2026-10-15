"""Create one immutable reviewed chain bundle and individually pinned requests."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
CANDIDATE = ROOT / 'docs/phase2/cho51_linear_chain_v1'
PRIOR = ROOT / 'runs/coordination/cho51_linear_continuation_20261015_v1/pins.json'
PRIOR_SHA = '1e16577546807821112e58f671f0941e0ba3ab0c5980c82efa67d92b14e4a42b'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
SNAPSHOT = ROOT / '.cache/huggingface/hub/models--braindecode--labram-pretrained/snapshots/0563b6c626e7b40d9a36653b763715db94d945d7'
BASELINE = SNAPSHOT / 'model.safetensors'
BASELINE_SHA = '53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8'
CONFIG = SNAPSHOT / 'config.json'
CONFIG_SHA = '813073071865e6799f00f2c7ade117cb86238dd931c1b5f81e97ca68db00188b'
DESIGN = ROOT / 'docs/phase2/cho_design_decisions_20261012.json'
DESIGN_SHA = '654f06db0cadd3c67cca102edfadc3b667942bf84013e442aae700a7a3be7fc8'
FIXTURE = ROOT / 'runs/coordination/cho51_linear_lineage_20261015_v2/validation_001/fixture'
sys.path.insert(0, str(ROOT))


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def write_once(path, value):
    raw = encoded(value)
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return hashlib.sha256(raw).hexdigest()


def load_source(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError('exact pure metadata loader required')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def check_map(pins):
    for relative, sha in pins['files'].items():
        if digest(ROOT / relative) != sha:
            raise ValueError('fixed source/context pin changed: ' + relative)
    for absolute, sha in pins['runtime'].items():
        if digest(absolute) != sha:
            raise ValueError('fixed runtime pin changed: ' + absolute)
    if pins['baseline'] != {str(BASELINE): BASELINE_SHA} or digest(BASELINE) != BASELINE_SHA:
        raise ValueError('exact safe baseline pin required')


def initialize():
    if any((RUN / name).exists() for name in ('pins.json', 'method-config.json', 'chains', 'requests', 'fragments', 'dispatch')):
        raise ValueError('one unused immutable chain bundle required')
    if digest(PRIOR) != PRIOR_SHA:
        raise ValueError('exact accepted 1224/5 predecessor pin required')
    prior = json.loads(PRIOR.read_bytes())
    if len(prior['files']) != 1224 or len(prior['runtime']) != 5:
        raise ValueError('exact frozen 1224/5 predecessor inventory required')
    check_map(prior)
    if (BASELINE.resolve(strict=True) != BASELINE or BASELINE.is_symlink()
            or BASELINE.stat().st_size != 23299672 or digest(BASELINE) != BASELINE_SHA
            or CONFIG.resolve(strict=True) != CONFIG or CONFIG.is_symlink()
            or CONFIG.stat().st_size != 4776 or digest(CONFIG) != CONFIG_SHA
            or digest(DESIGN) != DESIGN_SHA):
        raise ValueError('exact safe baseline, architecture and adopted design required')
    method = [row for row in json.loads(DESIGN.read_bytes())['adopted_design']['candidate_template']['methods']
        if row['method'] == 'labram_linear']
    if len(method) != 1:
        raise ValueError('one exact adopted linear row required')
    method = method[0]
    method_sha = hashlib.sha256(encoded(method)).hexdigest()
    if method_sha != '37b07825274a45d0703bba56387aa75c42e612d84066996d4a3a8bf44cdd42af':
        raise ValueError('unchanged adopted method configuration bytes required')
    candidates = {CANDIDATE / name for name in ('plan.py', 'test_plan.py', 'origin.py', 'executor.py', 'selector.py', 'README.md')}
    if set(CANDIDATE.iterdir()) != candidates:
        raise ValueError('exact six-file generic chain candidate required')
    operations = {RUN / name for name in ('runtime.py', 'child.py', 'prepare.py', 'launch.ps1', 'observe.py', 'closeout.py')}
    paths = candidates | operations
    for path in paths:
        if path.suffix == '.py':
            ast.parse(path.read_bytes(), filename=str(path))
    reviewed = {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(paths)}
    if len(reviewed) != 12:
        raise ValueError('exact six candidate and six operational sources required')
    root_path = RUN / 'root-origin.json'
    root_sha = digest(root_path)
    origin = json.loads(root_path.read_bytes())
    review_path = RUN / 'source-review.json'
    review = json.loads(review_path.read_bytes())
    assets = {str(BASELINE): {'bytes': 23299672, 'sha256': BASELINE_SHA},
        str(CONFIG): {'bytes': 4776, 'sha256': CONFIG_SHA},
        str(DESIGN): {'bytes': DESIGN.stat().st_size, 'sha256': DESIGN_SHA}}
    if (review.get('source_only') is not True or review.get('remaining_actionable_findings') != []
            or review.get('files') != reviewed or review.get('lineage_assets') != assets
            or review.get('method_config_file_sha256') != method_sha
            or review.get('root_origin_file_sha256') != root_sha):
        raise ValueError('independent exact generic source/root/asset review required')
    origin_module = load_source('_cho51_chain_prepare_origin_v1', CANDIDATE / 'origin.py')
    if origin_module.build_root(ROOT) != origin:
        raise ValueError('root origin differs from independently authenticated fixed history')
    test_path = CANDIDATE / 'test_plan.py'
    test_nodes = []
    for node in ast.parse(test_path.read_bytes()).body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            if node.decorator_list:
                raise ValueError('literal unparametrized plan inventory required')
            test_nodes.append(test_path.relative_to(ROOT).as_posix() + '::' + node.name)
        elif isinstance(node, ast.ClassDef):
            test_nodes.extend(test_path.relative_to(ROOT).as_posix() + '::' + node.name + '::' + member.name
                for member in node.body if isinstance(member, ast.FunctionDef) and member.name.startswith('test_'))
    if len(test_nodes) != 36:
        raise ValueError('exact 36 parent plan tests and zero subtests required')
    files = dict(prior['files'])
    files.update(reviewed)
    files[PRIOR.relative_to(ROOT).as_posix()] = PRIOR_SHA
    files[review_path.relative_to(ROOT).as_posix()] = digest(review_path)
    files[root_path.relative_to(ROOT).as_posix()] = root_sha
    files[(RUN / 'method-config.json').relative_to(ROOT).as_posix()] = method_sha
    for relative, sha in origin['proofs'].items():
        path = ROOT / relative
        if (type(relative) is not str or Path(relative).is_absolute() or '..' in Path(relative).parts
                or '\\' in relative or path.resolve(strict=True) != path
                or path.suffix.lower() in {'.npz', '.npy', '.mat', '.safetensors', '.pt', '.pth', '.ckpt'}
                or digest(path) != sha or relative in files and files[relative] != sha):
            raise ValueError('immutable metadata-only root proof map required')
        files[relative] = sha
    pins = {'schema': 'cho51_linear_chain_pins_v1', 'prepared_utc': datetime.now(timezone.utc).isoformat(),
        'files': files, 'runtime': prior['runtime'], 'baseline': {str(BASELINE): BASELINE_SHA},
        'baseline_bytes': 23299672, 'architecture_bytes': 4776,
        'canonical_files': 432, 'canonical_source_sha256': CANONICAL,
        'predecessor_files': 1224, 'predecessor_pins_sha256': PRIOR_SHA,
        'source_review_path': str(review_path), 'source_review_sha256': digest(review_path),
        'reviewed_files': reviewed, 'lineage_assets': assets,
        'method_config_file_sha256': method_sha, 'root_origin_file_sha256': root_sha,
        'fixture_root': str(FIXTURE), 'required_selection_updates': 5253,
        'mne_resource_path': prior['mne_resource_path'], 'mne_resource_sha256': prior['mne_resource_sha256'],
        'seconds': 600, 'process_mib': 4096, 'job_mib': 5120,
        'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20, 'threads': 1,
        'gpu_hidden': True, 'test_nodes': test_nodes, 'expected_tests': 36, 'expected_subtests': 0,
        'pretrained_baseline_loaded': True, 'cohort_lineage_verified': False,
        'full_selector_verified': False, 'full_worker_verified': False,
        'scientific_admission': False, 'original_case_attempts_remaining': 0}
    if origin_module.build_root(ROOT) != origin:
        raise ValueError('immutable root history changed while preparing the bundle')
    write_once(RUN / 'method-config.json', method)
    pins_sha = write_once(RUN / 'pins.json', pins)
    for name in ('chains', 'requests', 'fragments', 'dispatch'):
        (RUN / name).mkdir()
    base_pairs = [{'candidate': name, 'validation_subject': f'subject_{subject:02d}'}
        for name in ('lr_1e-3', 'lr_2e-3') for subject in (1, 3, 4, 5, 6)]
    chain = {'schema': 'cho51_linear_chain_metadata_v1', 'root_origin_sha256': root_sha,
        'pins_sha256': pins_sha, 'chain_index': 0, 'leaves': [], 'accepted_pairs': base_pairs,
        'head_sha256': root_sha, 'complete': False}
    plan = load_source('_cho51_chain_prepare_plan_v1', CANDIDATE / 'plan.py')
    plan.validate_chain_metadata(chain)
    origin_module.verify_chain(origin, chain, ROOT, pins_sha256=pins_sha)
    chain_sha = write_once(RUN / 'chains/chain_000.json', chain)
    print(json.dumps({'pins_sha256': pins_sha, 'source_context_files': len(files), 'runtime_files': 5,
        'chain_path': str(RUN / 'chains/chain_000.json'), 'chain_file_sha256': chain_sha,
        'root_origin_file_sha256': root_sha, 'launched': False}))


def next_fragment(args):
    pins_path = RUN / 'pins.json'
    if digest(pins_path) != args.expect_pins:
        raise ValueError('exact independent immutable bundle pin required')
    pins = json.loads(pins_path.read_bytes())
    check_map(pins)
    chain_path = args.chain
    if (chain_path.resolve(strict=True) != chain_path or chain_path.parent != RUN / 'chains'
            or digest(chain_path) != args.expect_chain):
        raise ValueError('exact independently pinned direct chain snapshot required')
    chain = json.loads(chain_path.read_bytes())
    if chain_path != RUN / f"chains/chain_{chain['chain_index']:03d}.json":
        raise ValueError('exact sequential chain snapshot filename required')
    if any(int(path.stem.split('_')[1]) > chain['chain_index'] for path in (RUN / 'chains').glob('chain_*.json')):
        raise ValueError('latest accepted chain snapshot required')
    root_origin = json.loads((RUN / 'root-origin.json').read_bytes())
    origin_module = load_source('_cho51_chain_next_origin_v1', CANDIDATE / 'origin.py')
    origin_module.verify_chain(root_origin, chain, ROOT, pins_sha256=args.expect_pins)
    plan = load_source('_cho51_chain_next_plan_v1', CANDIDATE / 'plan.py')
    request = plan.next_request(chain, pins_sha256=args.expect_pins,
        root_origin_sha256=pins['root_origin_file_sha256'])
    plan.validate_request(request, chain, pins_sha256=args.expect_pins,
        root_origin_sha256=pins['root_origin_file_sha256'])
    path = RUN / f"requests/fragment_{request['index']:03d}.json"
    if (RUN / request['output_relative']).exists() or digest(chain_path) != args.expect_chain:
        raise ValueError('unused fragment output and unchanged parent chain required')
    request_sha = write_once(path, request)
    print(json.dumps({'request_path': str(path), 'request_sha256': request_sha,
        'index': request['index'], 'mode': request['mode'], 'pairs': len(request['pairs']),
        'budget': plan.budget(request), 'launched': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--next', action='store_true', dest='next_fragment')
    parser.add_argument('--chain', type=Path)
    parser.add_argument('--expect-chain')
    parser.add_argument('--expect-pins')
    args = parser.parse_args()
    if args.next_fragment:
        if any(value is None for value in (args.chain, args.expect_chain, args.expect_pins)):
            parser.error('--next requires --chain, --expect-chain and --expect-pins')
        next_fragment(args)
    else:
        if any(value is not None for value in (args.chain, args.expect_chain, args.expect_pins)):
            parser.error('initialization takes no dynamic request pins')
        initialize()


if __name__ == '__main__':
    main()
