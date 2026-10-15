"""Create exact reviewed synthetic linear continuation pins; no numerical imports."""
from __future__ import annotations

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
CANDIDATE = ROOT / 'docs/phase2/cho51_linear_continuation_v1'
PRIOR = ROOT / 'runs/coordination/cho51_linear_lineage_20261015_v2/pins.json'
PRIOR_SHA = '9d5c2da133dc1119304fe1e2219fef3d292d277fd4287bcceb019451f8cc30ca'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
SNAPSHOT = ROOT / '.cache/huggingface/hub/models--braindecode--labram-pretrained/snapshots/0563b6c626e7b40d9a36653b763715db94d945d7'
BASELINE = SNAPSHOT / 'model.safetensors'
BASELINE_SHA = '53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8'
CONFIG = SNAPSHOT / 'config.json'
CONFIG_SHA = '813073071865e6799f00f2c7ade117cb86238dd931c1b5f81e97ca68db00188b'
DESIGN = ROOT / 'docs/phase2/cho_design_decisions_20261012.json'
DESIGN_SHA = '654f06db0cadd3c67cca102edfadc3b667942bf84013e442aae700a7a3be7fc8'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def write_once(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def main():
    if any((RUN / name).exists() for name in ('pins.json', 'method-config.json', 'validation_001')):
        raise ValueError('fresh unused lineage pins, configuration and output required')
    if digest(PRIOR) != PRIOR_SHA:
        raise ValueError('exact frozen 1047/5 predecessor required')
    prior = json.loads(PRIOR.read_bytes())
    if len(prior['files']) != 1047 or len(prior['runtime']) != 5:
        raise ValueError('exact frozen 1047/5 predecessor inventory required')
    for relative, sha in prior['files'].items():
        if digest(ROOT / relative) != sha:
            raise ValueError('frozen predecessor source/context drift: ' + relative)
    for path, sha in prior['runtime'].items():
        if digest(path) != sha:
            raise ValueError('frozen predecessor runtime drift: ' + path)
    if (BASELINE.resolve(strict=True) != BASELINE or BASELINE.is_symlink()
            or BASELINE.stat().st_size != 23299672 or digest(BASELINE) != BASELINE_SHA
            or CONFIG.resolve(strict=True) != CONFIG or CONFIG.is_symlink()
            or CONFIG.stat().st_size != 4776 or digest(CONFIG) != CONFIG_SHA
            or digest(DESIGN) != DESIGN_SHA):
        raise ValueError('exact preexisting safe baseline, architecture and adopted design required')
    rows = [row for row in json.loads(DESIGN.read_bytes())['adopted_design']['candidate_template']['methods']
        if row['method'] == 'labram_linear']
    if len(rows) != 1:
        raise ValueError('exact one adopted linear method row required')
    method = rows[0]
    expected = [{'name': name, 'source': {'batch_size': 2, 'learning_rate': rate,
        'method': 'linear', 'partial_depth': None, 'steps_per_subject': 1},
        'support': {'learning_rate': rate, 'method': 'linear', 'partial_depth': None,
            'query_batch_size': 8, 'steps': 1}}
        for name, rate in (('lr_1e-3', .001), ('lr_2e-3', .002))]
    if method['candidates'] != expected or method['early_stopping'] is not False:
        raise ValueError('exact adopted two-rate linear method required')
    method_raw = encoded(method)
    method_sha = hashlib.sha256(method_raw).hexdigest()
    candidate_paths = {CANDIDATE / name for name in ('probe.py', 'selector.py', 'contract.py', 'test_contract.py', 'README.md', 'origin.py')}
    if set(CANDIDATE.iterdir()) != candidate_paths:
        raise ValueError('exact six-file linear continuation candidate required')
    operations = {RUN / name for name in ('runtime.py', 'child.py', 'prepare.py', 'launch.ps1', 'observe.py', 'closeout.py')}
    paths = candidate_paths | operations
    for path in paths:
        if path.suffix == '.py':
            ast.parse(path.read_bytes(), filename=str(path))
    reviewed = {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(paths)}
    if len(reviewed) != 12:
        raise ValueError('exact six candidate and six operational sources required')
    review_path = RUN / 'source-review.json'
    review = json.loads(review_path.read_bytes())
    origin_path = RUN / 'origin-contract.json'
    origin_sha = digest(origin_path)
    origin_contract = json.loads(origin_path.read_bytes())
    origin_spec = importlib.util.spec_from_file_location('_cho51_linear_continuation_prepare_origin_v1', CANDIDATE / 'origin.py')
    if origin_spec is None or origin_spec.loader is None:
        raise ValueError('exact stdlib origin verifier source required')
    origin_module = importlib.util.module_from_spec(origin_spec)
    sys.modules[origin_spec.name] = origin_module
    origin_spec.loader.exec_module(origin_module)
    origin_module.verify_origin(origin_contract, ROOT)
    if (origin_contract.get('fixture_root') != str(PRIOR.parent / 'validation_001/fixture')
            or origin_contract.get('adopted_folds') != 2
            or origin_contract.get('historical_gradient_updates') != 102):
        raise ValueError('exact previously accepted two-fold readonly origin required')
    assets = {str(BASELINE): {'bytes': 23299672, 'sha256': BASELINE_SHA},
        str(CONFIG): {'bytes': 4776, 'sha256': CONFIG_SHA},
        str(DESIGN): {'bytes': DESIGN.stat().st_size, 'sha256': DESIGN_SHA}}
    if (review.get('source_only') is not True or review.get('remaining_actionable_findings') != []
            or review.get('files') != reviewed or review.get('lineage_assets') != assets
            or review.get('method_config_file_sha256') != method_sha
            or review.get('origin_contract_file_sha256') != origin_sha):
        raise ValueError('exact independent source, baseline, architecture and method-byte review required')
    test_path = CANDIDATE / 'test_contract.py'
    test_nodes, expected_tests = [], 0
    for node in ast.parse(test_path.read_bytes()).body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            count = 1
            for mark in node.decorator_list:
                if isinstance(mark, ast.Call) and isinstance(mark.func, ast.Attribute) and mark.func.attr == 'parametrize':
                    if len(mark.args) < 2 or not isinstance(mark.args[1], (ast.List, ast.Tuple)):
                        raise ValueError('literal test parameter inventory required')
                    count *= len(mark.args[1].elts)
            test_nodes.append(test_path.relative_to(ROOT).as_posix() + '::' + node.name)
            expected_tests += count
        elif isinstance(node, ast.ClassDef):
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name.startswith('test_'):
                    test_nodes.append(test_path.relative_to(ROOT).as_posix() + '::' + node.name + '::' + member.name)
                    expected_tests += 1
    if len(test_nodes) != 37 or expected_tests != 37:
        raise ValueError('exact 37 continuation-contract parent tests required')
    method_path = RUN / 'method-config.json'
    files = dict(prior['files'])
    files.update(reviewed)
    files[PRIOR.relative_to(ROOT).as_posix()] = PRIOR_SHA
    files[review_path.relative_to(ROOT).as_posix()] = digest(review_path)
    files[method_path.relative_to(ROOT).as_posix()] = method_sha
    files[origin_path.relative_to(ROOT).as_posix()] = origin_sha
    for relative, sha in origin_contract['proofs'].items():
        path = ROOT / relative
        if (type(relative) is not str or Path(relative).is_absolute() or '..' in Path(relative).parts
                or '\\' in relative or path.resolve(strict=True) != path
                or path.suffix.lower() in {'.npz', '.npy', '.mat', '.safetensors', '.pt', '.pth', '.ckpt'}
                or digest(path) != sha or relative in files and files[relative] != sha):
            raise ValueError('exact immutable metadata-only origin proof map required')
        files[relative] = sha
    for path in (CONFIG, DESIGN, ROOT / 'configs/phase2/forward_parity.toml',
            ROOT / 'configs/labram_checkpoint_audit.toml', ROOT / '.venv/Lib/site-packages/_pytest/subtests.py'):
        relative = path.relative_to(ROOT).as_posix()
        value = digest(path)
        if relative in files and files[relative] != value:
            raise ValueError('inherited architecture/configuration pin drift')
        files[relative] = value
    pins = {'schema': 'cho51_linear_continuation_pins_v1', 'prepared_utc': datetime.now(timezone.utc).isoformat(),
        'files': files, 'runtime': prior['runtime'], 'baseline': {str(BASELINE): BASELINE_SHA},
        'baseline_bytes': 23299672, 'architecture_bytes': 4776,
        'canonical_files': 432, 'canonical_source_sha256': CANONICAL,
        'predecessor_files': 1047, 'predecessor_pins_sha256': PRIOR_SHA,
        'source_review_path': str(review_path), 'source_review_sha256': digest(review_path),
        'reviewed_files': reviewed, 'lineage_assets': assets,
        'method_config_file_sha256': method_sha, 'origin_contract_file_sha256': origin_sha,
        'fixture_root': origin_contract['fixture_root'],
        'historical_gradient_updates': 102, 'adopted_historical_folds': 2,
        'combined_folds': 10, 'pending_folds': 92, 'combined_described_gradient_updates': 510,
        'mne_resource_path': prior['mne_resource_path'], 'mne_resource_sha256': prior['mne_resource_sha256'],
        'seconds': 600, 'process_mib': 4096, 'job_mib': 5120,
        'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20, 'threads': 1,
        'gpu_hidden': True, 'actual_gradient_updates': 408, 'source_updates': 400, 'support_updates': 8,
        'diagnostic_folds': 8, 'required_selection_updates': 5253,
        'test_nodes': test_nodes, 'expected_tests': expected_tests, 'expected_subtests': 23,
        'pretrained_baseline_loaded': True, 'cohort_lineage_verified': False,
        'full_selector_verified': False, 'full_worker_verified': False,
        'scientific_admission': False, 'original_case_attempts_remaining': 0}
    origin_module.verify_origin(origin_contract, ROOT)
    if digest(origin_path) != origin_sha:
        raise ValueError('origin contract changed during preparation')
    write_once(method_path, method_raw)
    write_once(RUN / 'pins.json', encoded(pins))
    print(json.dumps({'source_context_files': len(files), 'runtime_files': len(pins['runtime']),
        'baseline_files': 1, 'expected_tests': expected_tests, 'pins_sha256': digest(RUN / 'pins.json'),
        'method_config_file_sha256': method_sha, 'launched': False}))


if __name__ == '__main__':
    main()
