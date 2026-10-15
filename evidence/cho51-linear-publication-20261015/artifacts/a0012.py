"""Fixed linear-selection origins and staged artifact proofs; stdlib only.

This module never constructs a model, imports tests, decodes tensor files or
grants the audit guard permission to read a public store's weights.  The bridge
must prove actual source capture and model-state equality inside its native Job.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
OLD = ROOT / 'runs/coordination/cho51_linear_chain_20261015_v1'
FINAL = OLD / 'fragments/fragment_007'
PUBLICATION = RUN / 'publication_001'
RESTORATION = RUN / 'restoration_001'
EVIDENCE_ROOT = PUBLICATION / 'project'
STORE = EVIDENCE_ROOT / 'runs/phase2/selected_sources'
ORDINARY = 8 * 1024**2
COMPLETE = 32 * 1024**2
WEIGHTS = 64 * 1024**2
OLD_PINS = '1e3776fd84c22fdba9d36c97113ca1fb90ec5912018cfdcdd0c4cfcaa264be2e'
OLD_REVIEW = 'cc1917e786e81092443d6a90c2be9708ea5ef034deb3bcb43572b23e6a887b8a'
OLD_ROOT = 'c0fe9fd254fe9acb409f1034ec79a6f75adbefd9bcd0b089d41fb850a5c59897'
OLD_CHAIN = '20375fcf55818d9f2ec4f57a29f2ce6490dff35029896189e56ca251d306c1d7'
OLD_LEAF = '3349e3dbbaeba3ec4721e6a62694bd9810c624600922e8add2abb99067a801ea'
OLD_REPORT = '7889e0c1c83eb4d2f269f5b6d60706d640304363faf3372fb0567ca8d1409615'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
MODEL_STATE = '8de802bc0577864edcfc857fa93cf24db527b09ecf0eded0b3e980a82a7b4c01'
RECIPE = 'bdb40fd0f3becf87cc619e87a536ee4a921e72efa422fcaaf235c3573865a452'
CONTRACT = '8397d34ee0a2280b406071e045988f98b1b73ce21fcecc0b9834518cd21993b1'
EVIDENCE = '1c19664276cc05d5252631513001871b532dc5362f93dfabf38e48acc9ca904a'
EVIDENCE_FILE = 'e497186ff0eece324830731f8cada32ff5698fc8c25e143f0f8f1519061a12c3'
BASELINE = '53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8'
MUTABLE_HEADS = {'AGENT_COORDINATION.md', 'CONTINUE_HERE.md', 'HANDOFF.md',
                 'PHASE2_START_HERE.md', 'README.md', 'WINDOWS_SETUP.md'}
observed = {}
_FROZEN = None
_CONTRACT_MODULE = None


def need(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, allow_nan=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def logical(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def physical(value):
    return hashlib.sha256(canonical(value) + b'\n').hexdigest()


def detached(value):
    return json.loads(canonical(value))


def signature(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def direct(path):
    path = Path(path)
    need(path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink(),
         'direct absolute file required: ' + str(path))
    return path


def relative(root, name):
    need(type(name) is str, 'plain repository-relative path required')
    p = PurePosixPath(name)
    need(not p.is_absolute() and '..' not in p.parts and '\\' not in name,
         'relative proof path escapes the project')
    return Path(root).joinpath(*p.parts)


def _read(path, *, expected=None, compact=False, maximum=None, single_link=True):
    path = direct(path)
    before = path.stat()
    need(stat.S_ISREG(before.st_mode) and (not single_link or before.st_nlink == 1),
         'regular single-link evidence required')
    if maximum is not None:
        need(0 <= before.st_size <= maximum, 'bounded artifact required: ' + str(path))
    raw = None
    h = hashlib.sha256()
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        need(signature(opened)[:4] == signature(before)[:4], 'opened artifact identity changed')
        if compact:
            need(maximum is not None, 'compact reads require an explicit limit')
            raw = stream.read(maximum + 1)
            need(len(raw) == before.st_size <= maximum, 'compact artifact length differs')
            h.update(raw)
        else:
            while True:
                block = stream.read(1024**2)
                if not block:
                    break
                h.update(block)
        need(signature(opened) == signature(os.fstat(stream.fileno())), 'artifact changed on its handle')
    need(signature(before) == signature(path.stat()), 'artifact changed during verification')
    digest = h.hexdigest()
    need(expected is None or expected == digest, 'independent artifact SHA differs: ' + str(path))
    pin = (*signature(before), digest)
    need(observed.setdefault(str(path), pin) == pin, 'artifact changed across metadata reads')
    return raw, pin


def _large_evidence(path):
    path = Path(path)
    return path == FINAL / 'selection-evidence.json' or path == STORE / 'evidence' / (EVIDENCE + '.json')


def remember(path, *, expected=None, compact=False, single_link=True, **ignored):
    """Compatibility reader. Store tensor files require explicit blob_facts instead."""
    path = Path(path)
    suffix = path.suffix.lower()
    need(suffix not in {'.npz', '.npy', '.mat', '.pth', '.pt', '.ckpt'}, 'array/pickle reads forbidden')
    if suffix == '.safetensors':
        allowed = {FINAL / 'selected-source.safetensors', ROOT / (
            '.cache/huggingface/hub/models--braindecode--labram-pretrained/snapshots/'
            '0563b6c626e7b40d9a36653b763715db94d945d7/model.safetensors')}
        need(path in allowed and not compact, 'no general public-store weights read permission')
        maximum = WEIGHTS
    else:
        metadata_suffixes = {'.json', '.jsonl', '.xml', '.log', '.md', '.txt', '.toml', '.py', '.ps1', '.lock', '.csv'}
        maximum = COMPLETE if _large_evidence(path) else ORDINARY if compact or suffix in metadata_suffixes else None
    return _read(path, expected=expected, compact=compact, maximum=maximum, single_link=single_link)


def _unique(rows):
    result = {}
    for key, value in rows:
        need(key not in result, 'duplicate JSON object key')
        result[key] = value
    return result


def decode(raw):
    value = json.loads(raw, object_pairs_hook=_unique,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON: ' + value)))
    canonical(value)  # Also rejects finite-looking decimal overflow such as1e999.
    return value


def document(path, *, expected=None, canonical_raw=False, **ignored):
    raw, pin = remember(path, expected=expected, compact=True)
    value = decode(raw)
    if canonical_raw:
        need(raw == canonical(value) + b'\n', 'canonical finite JSON plus LF required')
    return value, pin[-1]


def envelope_digest(record):
    need(type(record) is dict and type(record.get('sha256')) is str, 'hashed envelope required')
    body = dict(record)
    digest = body.pop('sha256')
    need(logical(body) == digest, 'logical envelope SHA differs')
    return digest


def load(name, path, expected=None):
    path = Path(path)
    if expected is not None:
        _read(path, expected=expected, single_link=False)
    spec = importlib.util.spec_from_file_location(name, path)
    need(spec is not None and spec.loader is not None, 'metadata module unavailable')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _frozen():
    global _FROZEN
    if _FROZEN is None:
        _FROZEN = load('_publication_frozen_linear_origin', ROOT / 'docs/phase2/cho51_linear_chain_v1/origin.py',
            '22955d17aaa0d066b11fef494666034a9f68d469f62feea034a382871f984f1b')
        _FROZEN._modules()
    return _FROZEN


def _pure_contract():
    global _CONTRACT_MODULE
    if _CONTRACT_MODULE is None:
        _CONTRACT_MODULE = load('_publication_pure_contract', ROOT / 'docs/phase2/cho51_linear_publication_v1/contract.py',
            '51ff7607df69bf980391373fb44b7bc486e06000a3ef610b364546b6a9ffaf96')
    return _CONTRACT_MODULE


def __getattr__(name):
    if name in {'old', 'launcher'}:
        metadata = _frozen()._modules()[1].M
        return getattr(metadata, name)
    raise AttributeError(name)


def verify_pin_map(pins, root=ROOT):
    need(Path(root) == ROOT, 'fixed architecture root required')
    predecessor, _ = document(OLD / 'pins.json', expected=OLD_PINS, canonical_raw=True)
    need(all(pins['files'].get(name) == sha for name, sha in predecessor['files'].items())
         and pins['runtime'] == predecessor['runtime'] and pins['baseline'] == predecessor['baseline'],
         'exact1710/5/1 predecessor extension required')
    review, _ = document(Path(pins['source_review_path']), expected=pins['source_review_sha256'])
    reviewed = {'docs/phase2/cho51_linear_publication_v1/' + name for name in
                ('bridge.py', 'contract.py', 'test_contract.py', 'README.md')}
    reviewed.update('runs/coordination/cho51_linear_publication_20261015_v1/' + name for name in
                    ('runtime.py', 'child.py', 'prepare.py', 'launch.ps1', 'observe.py', 'closeout.py', 'metadata.py'))
    need(review['source_only'] is True and review['remaining_actionable_findings'] == []
         and review['files'] == pins['reviewed_files'] and set(review['files']) == reviewed
         and all(pins['files'].get(name) == sha for name, sha in review['files'].items()),
         'exact eleven independently reviewed staged sources required')
    for name, sha in pins['files'].items():
        need(name not in MUTABLE_HEADS, 'mutable resume heads cannot become origin authority')
        path = relative(root, name)
        need(path.suffix.lower() not in {'.npz', '.npy', '.mat', '.safetensors', '.pth', '.pt', '.ckpt'},
             'source pin maps cannot contain arrays or tensor blobs')
        remember(path, expected=sha, single_link=False)
    for path, sha in pins['runtime'].items():
        remember(Path(path), expected=sha, single_link=False)
    for path, sha in pins.get('baseline', {}).items():
        need(sha == BASELINE, 'fixed audited baseline required')
        _, pin = remember(Path(path), expected=sha)
        need(pin[2] == 23299672, 'baseline physical size differs')


def native_pins(pins):
    return _frozen()._modules()[1].M.native_pins(pins)


def verify_native(directory, command, pins, root=ROOT):
    need(Path(root) == ROOT, 'fixed architecture root required')
    metadata = _frozen()._modules()[1].M
    operations, runtimes = native_pins(pins)
    return metadata.old.verify_native(Path(directory), command, 600, 4096, 5120,
        operations=operations, runtimes=runtimes, document=document, remember=remember, launcher=metadata.launcher)


def _artifact(path, expected):
    _, pin = remember(path, expected=expected)
    return {'path': str(path), 'file_sha256': pin[-1], 'size_bytes': pin[2]}


def build_origin(root=ROOT):
    """Reauthenticate chain7 and its fixed audit; never rehash mutable resume heads."""
    need(Path(root) == ROOT and ROOT.resolve(strict=True) == ROOT, 'exact architecture root required')
    observed.clear()
    pins, _ = document(OLD / 'pins.json', expected=OLD_PINS, canonical_raw=True)
    root_origin, _ = document(OLD / 'root-origin.json', expected=OLD_ROOT, canonical_raw=True)
    chain, _ = document(OLD / 'chains/chain_007.json', expected=OLD_CHAIN, canonical_raw=True)
    review, _ = document(OLD / 'final-review.json', expected=OLD_REVIEW, canonical_raw=True)
    need(review['passed'] is True and review['remaining_actionable_findings'] == []
         and review['metadata_only'] is True and len(review['checked_compact_proofs']) == 882,
         'exact accepted independent final audit required')
    history = _frozen().verify_chain(root_origin, chain, ROOT, pins_sha256=OLD_PINS)
    need(len(history.records) == len(history.accepted_pairs) == 102 and history.head_sha256 == OLD_LEAF,
         'all102 accepted native-origin records required')
    need(len(pins['files']) == 1710 and len(pins['runtime']) == 5 and len(pins['baseline']) == 1,
         'fixed1710/5/1 predecessor pins required')
    proofs = dict(review['checked_compact_proofs'])
    need(not (set(proofs) & MUTABLE_HEADS), 'mutable root heads found in hard proof map')
    for name, sha in proofs.items():
        path = relative(ROOT, name)
        maximum = COMPLETE if _large_evidence(path) else ORDINARY
        _read(path, expected=sha, compact=False, maximum=maximum)
    report = ROOT / 'docs/phase2/cho51_linear_chain_qualification_20261015.md'
    remember(report, expected=OLD_REPORT, compact=True)
    proofs[report.relative_to(ROOT).as_posix()] = OLD_REPORT
    proofs[(OLD / 'final-review.json').relative_to(ROOT).as_posix()] = OLD_REVIEW
    for path, pin in history.proof_identities.items():
        name = Path(path).relative_to(ROOT).as_posix()
        need(name not in proofs or proofs[name] == pin[-1], 'historical proof hash disagreement')
        proofs[name] = pin[-1]
    result, result_sha = document(FINAL / 'probe-result.json', expected=review['qualifications'][-1]['probe_sha256'], canonical_raw=True)
    evidence, _ = document(FINAL / 'selection-evidence.json', expected=EVIDENCE_FILE, canonical_raw=True)
    need(envelope_digest(evidence) == EVIDENCE and evidence['payload']['complete'] is True
         and evidence['payload']['contract_sha256'] == CONTRACT and result['total_verified_gradient_updates'] == 5253
         and result['full_selector_verified'] is True and result['public_complete_evidence_verifier_passed'] is True,
         'accepted complete evidence and public verifier witness required')
    schema, _ = document(FINAL / 'selected-state-schema.json', expected='d9a276bb86322512fa87f90e06351c6f8552d63490b25f85968ebcbe1cbc68b4', canonical_raw=True)
    need(schema['tensor_count'] == 223 and schema['elements'] == 5818138 and schema['model_state_sha256'] == MODEL_STATE,
         'accepted full-state schema differs')
    contract = _pure_contract()
    artifacts = contract._source_artifacts()
    for pin in artifacts.values():
        actual = _artifact(Path(pin['path']), pin['file_sha256'])
        need(actual == pin, 'fixed historical source artifact size differs')
    method, _ = document(Path(artifacts['method_config']['path']), expected=artifacts['method_config']['file_sha256'], canonical_raw=True)
    need(logical(method) == result['method_config_sha256'], 'method logical SHA differs')
    recipe = result['selected_model_recipe']
    need(logical(recipe) == result['selected_model_recipe_sha256'] == RECIPE
         and recipe['selected_candidate'] == result['selected_candidate'] == 'lr_1e-3', 'actual winning recipe differs')
    fixture_origin = root_origin['fixture_origin']
    identity, _ = document(Path(fixture_origin['input_identity_path']), expected=fixture_origin['input_identity_file_sha256'], canonical_raw=True)
    five = contract._five_tomls()
    need({name: pin['sha256'] for name, pin in identity['files'].items() if name.startswith('configs/')} == five,
         'exact five original fixture TOMLs required')
    source = evidence['payload']['contract']['source']
    need(source == {'git_commit': '4491e2a68126d6b7293261f4954b88c11c29049d', 'git_dirty': True,
                    'source_sha256': contract.EVIDENCE_SOURCE_SHA256}, 'original source provenance differs')
    value = {'schema': 'cho51_linear_publication_origin_v1', 'architecture_root': str(ROOT),
        'fixture_origin': fixture_origin, 'fixture_root': fixture_origin['fixture_root'],
        'source_context_root': str(EVIDENCE_ROOT), 'store_root': str(EVIDENCE_ROOT), 'evidence_root': str(EVIDENCE_ROOT),
        'publication_output': str(PUBLICATION), 'detached_output': str(RESTORATION),
        'case': result['case'], 'plan': result['case'], 'source': source,
        'source_artifacts': artifacts, 'five_tomls': five, 'original_input_files': identity['files'],
        'input_identity_path': fixture_origin['input_identity_path'], 'input_identity_file_sha256': fixture_origin['input_identity_file_sha256'],
        'input_identity_sha256': fixture_origin['input_identity_sha256'], 'input_file_count': 213, 'input_bytes': 734579463,
        'method_config_path': artifacts['method_config']['path'], 'method_config_file_sha256': artifacts['method_config']['file_sha256'],
        'method_config_sha256': logical(method), 'selection_evidence_path': artifacts['evidence']['path'],
        'selection_evidence_file_sha256': EVIDENCE_FILE, 'selection_evidence_sha256': EVIDENCE, 'selection_evidence_bytes': 23087023,
        'checkpoint_path': artifacts['checkpoint']['path'], 'checkpoint_file_sha256': artifacts['checkpoint']['file_sha256'],
        'checkpoint_bytes': 23294624, 'selected_checkpoint_path': artifacts['checkpoint']['path'],
        'selected_checkpoint_sha256': artifacts['checkpoint']['file_sha256'], 'selected_checkpoint_size_bytes': 23294624,
        'model_state_sha256': MODEL_STATE, 'model_recipe_sha256': RECIPE, 'selected_model_recipe_sha256': RECIPE,
        'selected_model_recipe': recipe, 'selected_candidate': 'lr_1e-3', 'contract_sha256': CONTRACT,
        'evidence_source_sha256': source['source_sha256'], 'fixture_source_sha256': source['source_sha256'],
        'origin_pins_path': str(OLD / 'pins.json'), 'origin_pins_sha256': OLD_PINS,
        'origin_root_path': str(OLD / 'root-origin.json'), 'origin_root_sha256': OLD_ROOT,
        'origin_chain_path': str(OLD / 'chains/chain_007.json'), 'origin_chain_sha256': OLD_CHAIN,
        'origin_final_review_sha256': OLD_REVIEW, 'origin_final_leaf_sha256': OLD_LEAF,
        'origin_probe_result_sha256': result_sha, 'source_pins': pins['files'], 'runtime_pins': pins['runtime'],
        'baseline_pins': pins['baseline'], 'proofs': dict(sorted(proofs.items())),
        'canonical_source_sha256': CANONICAL, 'historical_gradient_updates': 5253, 'current_gradient_updates': 0,
        'complete_folds': 102, 'publication_stage_qualified': False, 'detached_stage_qualified': False,
        'public_single_root_factory_qualified': False, 'original_case_attempts': 0, 'scientific_admission': False,
        'mutable_resume_heads_are_historical_context_only': sorted(MUTABLE_HEADS)}
    return detached(value)


def verify_origin(origin=None, root=ROOT):
    actual = build_origin(root)
    if origin is not None:
        need(canonical(actual) == canonical(origin), 'explicit fixed origin contract differs')
    return detached(actual)


def make_contract(origin):
    c = _pure_contract()
    value = {'schema': c.SCHEMA, 'architecture_root': str(ROOT), 'evidence_root': str(EVIDENCE_ROOT),
        'origin_fixture_root': origin['fixture_root'], 'publication_output': str(PUBLICATION), 'detached_output': str(RESTORATION),
        'origin_path': str(RUN / 'origin-contract.json'), 'origin_file_sha256': physical(origin),
        'source_artifacts': origin['source_artifacts'], 'case': origin['case'], 'selected_candidate': 'lr_1e-3',
        'canonical_source_sha256': CANONICAL, 'evidence_source_sha256': origin['evidence_source_sha256'],
        'five_tomls': origin['five_tomls'], 'historical_gradient_updates': 5253, 'current_gradient_updates': 0,
        'complete_folds': 102, 'source_policy': 'two_root_staged_bridge', 'public_single_root_factory_qualified': False,
        'publication_stage_qualified': False, 'detached_stage_qualified': False, 'scientific_admission': False,
        'original_case_attempts': 0, 'limits': {'ordinary_json_bytes': ORDINARY,
        'complete_evidence_json_bytes': COMPLETE, 'checkpoint_bytes': WEIGHTS}}
    c.validate_stage_contract(value)
    return detached(value)


def verify_stage_contract(contract, origin, root=ROOT):
    need(Path(root) == ROOT, 'fixed architecture root required')
    _pure_contract().validate_stage_contract(contract)
    need(canonical(contract) == canonical(make_contract(origin)), 'stage contract origin binding differs')


def verify_source_context(origin):
    """Only exact read-only TOMLs are mirrored; Git equality is checked by bridge."""
    need(origin['evidence_root'] == str(EVIDENCE_ROOT), 'fixed staged source context required')
    actual = {p.relative_to(EVIDENCE_ROOT).as_posix() for p in (EVIDENCE_ROOT / 'configs').rglob('*') if p.is_file() or p.is_symlink()}
    need(actual == set(origin['five_tomls']), 'mirrored five-TOML inventory differs')
    source_paths = set()
    for folder in ('core', 'encoder', 'adaptation', 'data', 'realtime', 'evaluation', 'scripts', 'tests', 'configs'):
        for extension in ('*.py', '*.toml', '*.ps1'):
            source_paths.update(path.relative_to(EVIDENCE_ROOT).as_posix()
                for path in (EVIDENCE_ROOT / folder).rglob(extension) if path.name != 'local.toml')
    for name in ('pyproject.toml', 'requirements.lock', 'requirements-core.lock', 'requirements-data.lock',
                 'requirements-ml.lock', '.python-version', '.gitattributes'):
        if (EVIDENCE_ROOT / name).exists():
            source_paths.add(name)
    need(source_paths == set(origin['five_tomls']) and not (EVIDENCE_ROOT / '.githooks').exists()
         and not (EVIDENCE_ROOT / '.git').exists(), 'mirror source inventory or Git discovery context changed')
    for name, sha in origin['five_tomls'].items():
        path = relative(EVIDENCE_ROOT, name)
        remember(path, expected=sha, compact=True)
        need(not (path.stat().st_mode & stat.S_IWRITE), 'mirrored TOML must be read only')
    need(not any(p.suffix.lower() in {'.npz', '.npy', '.mat'} for p in EVIDENCE_ROOT.rglob('*')),
         'fixture arrays cannot be copied into the staged source context')
    return {'root': str(EVIDENCE_ROOT), 'files': detached(origin['five_tomls'])}


def blob_facts(path, *, expected, size_bytes):
    """Explicit metadata-only hash, never a decoder or a guard permission grant."""
    path = Path(path)
    need(type(expected) is str and re.fullmatch('[a-f0-9]{64}', expected) is not None,
         'external physical blob hash required')
    need(type(size_bytes) is int and 0 < size_bytes <= WEIGHTS, 'bounded full-state blob required')
    need(path == FINAL / 'selected-source.safetensors' or path == STORE / 'weights' / (expected + '.safetensors'),
         'only the accepted checkpoint or exact owned CAS weight path is hashable')
    _, pin = _read(path, expected=expected, maximum=WEIGHTS)
    need(pin[2] == size_bytes, 'physical blob byte count differs')
    return {'path': str(path), 'file_sha256': expected, 'size_bytes': size_bytes, 'identity': list(pin[:-1])}


def _publication_files(result, origin):
    weights = Path(result['weights_path'])
    blob = blob_facts(weights, expected=result['weights_file_sha256'], size_bytes=result['weights_bytes'])
    need(result['model_state_sha256'] == MODEL_STATE and result['model_recipe_sha256'] == RECIPE
         and result['selected_candidate'] == 'lr_1e-3', 'published model identity differs')
    publication = result['publication']
    need(publication['weights_sha256'] == result['weights_file_sha256']
         and publication['manifest_sha256'] == result['manifest_sha256']
         and publication['evidence_sha256'] == EVIDENCE and publication['model_state_sha256'] == MODEL_STATE
         and publication['weights_format'] == 'full_v1' and publication['evidence_format'] == 'canonical_json_v1'
         and publication['resumed'] is False, 'actual fresh canonical publication receipt differs')
    manifest_path = Path(result['manifest_path'])
    need(manifest_path == STORE / 'manifests' / (result['manifest_sha256'] + '.json'), 'canonical manifest path required')
    manifest, _ = document(manifest_path, expected=result['manifest_file_sha256'], canonical_raw=True)
    need(envelope_digest(manifest) == result['manifest_sha256'], 'manifest logical SHA differs')
    payload = manifest['payload']
    expected = {'scope': 'engineering_only', 'scientific_evaluation': False, 'evidence_sha256': EVIDENCE,
        'selected_candidate': 'lr_1e-3', 'selection_contract_sha256': CONTRACT, 'source': origin['source'],
        'model_state_sha256': MODEL_STATE, 'model_recipe': origin['selected_model_recipe'], 'model_recipe_sha256': RECIPE,
        'weights_sha256': result['weights_file_sha256'], 'weights_file': 'weights/' + result['weights_file_sha256'] + '.safetensors',
        'evidence_file': 'evidence/' + EVIDENCE + '.json'}
    need(all(payload.get(k) == v for k, v in expected.items()), 'published manifest context differs')
    evidence_path = Path(result['evidence_path'])
    need(evidence_path == STORE / 'evidence' / (EVIDENCE + '.json'), 'exact canonical persisted evidence path required')
    evidence, _ = document(evidence_path, expected=result['evidence_file_sha256'], canonical_raw=True)
    need(envelope_digest(evidence) == result['evidence_sha256'] == EVIDENCE
         and evidence_path.stat().st_size == result['evidence_bytes'] <= COMPLETE
         and evidence['payload']['complete'] is True, 'published complete evidence differs')
    source_evidence, _ = document(FINAL / 'selection-evidence.json', expected=EVIDENCE_FILE, canonical_raw=True)
    need(evidence == source_evidence, 'canonical persisted evidence envelope differs from the accepted source')
    need(len(payload['tensor_schema']) == 223 and payload.get('weights_format', 'full_v1') == 'full_v1',
         'published full223-tensor state schema required')
    state_schema, _ = document(FINAL / 'selected-state-schema.json', expected=origin['source_artifacts']['state_schema']['file_sha256'], canonical_raw=True)
    projected = {name: {'shape': row['shape'], 'dtype': row['dtype']}
                 for name, row in state_schema['tensors'].items()}
    need(payload['tensor_schema'] == projected and state_schema['elements'] == 5818138
         and sum(row['elements'] for row in state_schema['tensors'].values()) == 5818138,
         'published tensor schema differs from the accepted state')
    facts = {'weights': blob, 'manifest': _artifact(manifest_path, result['manifest_file_sha256']),
             'evidence': _artifact(evidence_path, result['evidence_file_sha256'])}
    for name, fact in facts.items():
        pin = result['files'][name]
        need(all(pin.get(key) == fact[key] for key in ('path', 'file_sha256', 'size_bytes')),
             'publication result nested physical file pin differs')
        current = observed[fact['path']]
        need(pin['identity'] == list(current[:-1]), 'published physical file identity changed')
    return facts


def _stage_proof(mode, pins, expected_publication_result_sha256, root):
    need(Path(root) == ROOT and mode in ('publication', 'restoration'), 'fixed stage/root required')
    origin, _ = document(RUN / 'origin-contract.json', expected=pins['origin_contract_file_sha256'], canonical_raw=True)
    verify_origin(origin, root)
    contract, _ = document(RUN / 'stage-contract.json', expected=pins['stage_contract_file_sha256'], canonical_raw=True)
    verify_stage_contract(contract, origin, root)
    verify_pin_map(pins, root)
    out = PUBLICATION if mode == 'publication' else RESTORATION
    bridge, bridge_sha = document(out / (mode + '-result.json'),
        expected=expected_publication_result_sha256 if mode == 'publication' else None, canonical_raw=True)
    q, qsha = document(out / 'qualification.json', canonical_raw=True)
    wrapper, wrapper_sha = document(out / 'result.json', canonical_raw=True)
    need(q['schema'] == 'cho51_linear_' + mode + '_qualification_v1'
         and wrapper['schema'] == 'cho51_linear_' + mode + '_child_result_v1'
         and bridge['schema'] == 'cho51_linear_staged_' + mode + '_v1'
         and q['result'] == wrapper and wrapper['bridge_result'] == bridge
         and q['passed'] is True and wrapper['passed'] is True and bridge['passed'] is True,
         'exact passing bridge/wrapper/qualification chain required')
    need(q['pins_sha256'] == physical(pins) and q['unexpected_denials'] == 0
         and q['protected_target_read_attempts'] == [] and q['actual_gradient_updates'] == 0
         and q['source_updates'] == q['support_updates'] == 0
         and q['historical_gradient_updates'] == 5253
         and q['source_pins_rechecked'] == len(pins['files']) and q['runtime_pins_rechecked'] == 5
         and q['source_review_sha256'] == pins['source_review_sha256']
         and q['origin_contract_file_sha256'] == pins['origin_contract_file_sha256']
         and q['stage_contract_file_sha256'] == pins['stage_contract_file_sha256'],
         'zero-gradient guarded stage required')
    calls = q['observed_numerical_calls']
    for key, count in {'tensor_backward': 0, 'autograd_backward': 0, 'autograd_grad': 0, 'sgd_step': 0, 'optimizer_init': 0,
                       'safetensors_load': 3 if mode == 'publication' else 4,
                       'module_load_state_dict': 2 if mode == 'publication' else 4,
                       'module_strict_load': 2 if mode == 'publication' else 4,
                       'safetensors_save': 1 if mode == 'publication' else 0}.items():
        need(type(calls.get(key, 0)) is int and calls.get(key, 0) == count,
             'stage numerical observation budget differs: ' + key)
    need(q['target_or_classifier_inference_calls'] == 0 and q['constructor_dummy_forward_calls'] > 0,
         'only constructor-owned zero-input feature probing is permitted')
    common = {'architecture_root': str(ROOT), 'evidence_root': str(EVIDENCE_ROOT), 'source': origin['source'],
        'case': origin['case'], 'origin_file_sha256': pins['origin_contract_file_sha256'],
        'stage_contract_file_sha256': pins['stage_contract_file_sha256'], 'historical_gradient_updates': 5253,
        'current_gradient_updates': 0, 'actual_gradient_updates': 0, 'source_gradient_updates': 0,
        'support_gradient_updates': 0, 'model_state_sha256': MODEL_STATE, 'model_recipe_sha256': RECIPE,
        'selected_candidate': 'lr_1e-3', 'tensor_count': 223, 'elements': 5818138,
        'all_physical_inputs_rehashed_unchanged': True, 'mirror_source_unchanged': True,
        'torch_numpy_python_rng_unchanged': True, 'scientific_admission': False, 'cohort_lineage_verified': False,
        'recorder_used': False, 'full_worker_verified': False, 'measured_cells': 0,
        'original_case_attempts_remaining': 0, 'fitting_performed': False, 'target_prediction_performed': False,
        'public_single_root_factory_qualified': False, 'unchanged_single_root_factory_verified': False,
        'canonical_manifest_byte_bridge_verified': True, 'canonical_byte_bridge_weight_limit_unchanged': True}
    need(all(type(bridge.get(key)) is type(value) and bridge[key] == value for key, value in common.items()),
         'actual bridge result scope or source-context witness differs')
    stage_flags = {'publication_performed': mode == 'publication', 'publication_qualified': True,
        'restoration_qualified': mode == 'restoration', 'detached_stage_verified': mode == 'restoration',
        'new_staged_store_restore_verified': mode == 'restoration'}
    need(all(type(bridge.get(key)) is bool and bridge[key] is value for key, value in stage_flags.items()),
         'publication/restoration qualification scope differs')
    need([row['enabled'] for row in q['protected_target_transitions']] == [True, False], 'target protection transition pair required')
    need(wrapper['tests_passed'] is True and wrapper['skipped_reports'] == wrapper['unexpected_reports'] == wrapper['subtest_reports'] == [],
         'strict stage test accounting required')
    need(wrapper['expected_tests'] == 20 and wrapper['expected_subtests'] == wrapper['collected_subtests'] == 0
         and all(q[name] is wrapper[name] for name in ('tests_executed', 'tests_reused', 'tests_passed')),
         'qualification test summary differs from its exact wrapper')
    if mode == 'publication':
        need(wrapper['tests_executed'] is True and wrapper['tests_reused'] is False
             and wrapper['collected_tests'] == 20 and len(wrapper['reports']) == 20
             and wrapper['tests_reused_from_publication_result_sha256'] is None
             and wrapper['pytest_exit'] == 0 and all(row['phase'] == 'call' and row['outcome'] == 'passed' for row in wrapper['reports']),
             'twenty passing first-stage tests required')
    else:
        prior = verify_publication_proof(pins, expected_publication_result_sha256, root=root)
        need(bridge['publication_result']['path'] == str(PUBLICATION / 'publication-result.json')
             and bridge['publication_result']['file_sha256'] == expected_publication_result_sha256,
             'detached bridge predecessor physical publication result differs')
        need(wrapper['tests_executed'] is False and wrapper['tests_reused'] is True and wrapper['collected_tests'] == 0
             and wrapper['reports'] == [] and wrapper['pytest_exit'] is None
             and wrapper['tests_reused_from_publication_result_sha256'] == prior['result_sha256'],
             'detached stage must reuse the qualified exact first-stage tests')
        need(bridge['actual_store_restores'] == 2 and bridge['restore_weight_limits'] == [WEIGHTS, WEIGHTS]
             and bridge['all223_tensors_equal'] is True and bridge['restored_models_have_disjoint_storage'] is True
             and bridge['actual_adapter_released'] is True
             and bridge['actual_adapter_class'] == 'evaluation.phase2_pilot.LaBraMTunedAdapter',
             'two independent full-tensor and adapter restorations required')
        for name, filename, schema_name, released in (
            ('digest_witness', 'tensor-witness.json', 'cho51_linear_staged_tensor_witness_v1', False),
            ('adapter_witness', 'adapter-witness.json', 'cho51_linear_staged_adapter_witness_v1', True)):
            pin = bridge[name + '_file']
            need(Path(pin['path']) == out / filename, 'exact owned restoration witness file required')
            value, _ = document(out / filename, expected=pin['file_sha256'], canonical_raw=True)
            witness = bridge[name]
            need(value == {'schema': schema_name, **witness} and witness['manifest_sha256'] == prior['publication_result']['manifest_sha256']
                 and witness['evidence_sha256'] == EVIDENCE and witness['model_state_sha256'] == MODEL_STATE
                 and witness['model_recipe_sha256'] == RECIPE and witness['selected_candidate'] == 'lr_1e-3'
                 and witness['weights_sha256'] == prior['publication_result']['weights_file_sha256']
                 and witness['maximum_weights_bytes'] == WEIGHTS and witness['tensor_count'] == 223
                 and witness['elements'] == 5818138 and witness['public_complete_evidence_verifier_passed'] is True
                 and witness['canonical_store_restore_passed'] is True and witness['adapter_released'] is released,
                 'actual detached tensor/adapter restoration witness differs')
    mapping = q['observed_loaded_module_hashes']
    need(type(mapping) is dict and bool(mapping) and q['loaded_module_files'] == len(mapping), 'actual loaded-module map required')
    critical = ('docs/phase2/cho51_linear_publication_v1/bridge.py',
        'runs/coordination/cho51_linear_publication_20261015_v1/metadata.py',
        'evaluation/phase2_selected_source_store.py', 'evaluation/phase2_cho_source_restore.py',
        'evaluation/phase2_cho_selected_manifest_bridge.py', 'evaluation/phase2_cho_publication_gate.py',
        'evaluation/phase2_pilot.py', 'core/provenance.py', 'core/config.py', 'encoder/labram.py')
    need(all(str(ROOT / name) in mapping for name in critical), 'mandatory actual stage modules missing')
    for path, sha in mapping.items():
        remember(Path(path), expected=sha, single_link=False)
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'child.py'),
        '--mode', mode, '--pins', str(RUN / 'pins.json'), '--expect-pins', physical(pins), '--output', str(out)]
    if mode == 'restoration':
        command += ['--publication-result', str(PUBLICATION / 'publication-result.json'),
                    '--expect-publication-result', expected_publication_result_sha256]
    dispatch, _ = document(RUN / ('dispatch_' + mode + '_001.json'))
    dispatched, _ = document(RUN / ('dispatch_result_' + mode + '_001.json'))
    need(dispatch['child_command'] == dispatched['child_command'] == command and dispatched['guard_exit_code'] == 0,
         'exact accepted stage native command required')
    dispatch_fields = {'mode': mode, 'pins_sha256': physical(pins), 'expected_output': str(out),
                       'actual_gradient_updates': 0, 'scientific_admission': False}
    for value in (dispatch, dispatched):
        need(all(type(value.get(key)) is type(expected) and value[key] == expected
                 for key, expected in dispatch_fields.items()), 'dispatch scope or output binding differs')
        need(value['publication_result_file_sha256'] == expected_publication_result_sha256 if mode == 'restoration'
             else value['publication_result_file_sha256'] in (None, ''), 'dispatch predecessor result pin differs')
    need(q['publication_result_file_sha256'] == (expected_publication_result_sha256 if mode == 'restoration' else None),
         'qualification predecessor result pin differs')
    native = verify_native(dispatched['native_directory'], command, pins, root)
    files = _publication_files(bridge if mode == 'publication' else prior['publication_result'], origin)
    verify_source_context(origin)
    own_proofs = {}
    # The nested publication audit resets its own origin observation set.
    # Reauthenticate these three current files explicitly before cataloguing.
    for path, sha in ((out / (mode + '-result.json'), bridge_sha),
                      (out / 'qualification.json', qsha), (out / 'result.json', wrapper_sha)):
        document(path, expected=sha, canonical_raw=True)
        own_proofs[str(path)] = sha
    native_directory = Path(dispatched['native_directory'])
    dispatch_paths = {RUN / ('dispatch_' + mode + '_001.json'), RUN / ('dispatch_result_' + mode + '_001.json')}
    for name, pin in observed.items():
        path = Path(name)
        if (path.is_relative_to(out) or path.parent == native_directory or path in dispatch_paths):
            if path.suffix.lower() != '.safetensors':
                own_proofs[str(path)] = pin[-1]
    return {'publication_result': bridge if mode == 'publication' else prior['publication_result'], 'result': bridge,
        'result_sha256': bridge_sha, 'qualification': q, 'qualification_sha256': qsha, 'wrapper': wrapper,
        'wrapper_sha256': wrapper_sha, 'native': native, 'origin': origin, 'publication_files': files,
        'proofs': dict(sorted(own_proofs.items()))}


def verify_publication_proof(pins, expected_result_sha256, root=ROOT):
    need(type(expected_result_sha256) is str and re.fullmatch('[a-f0-9]{64}', expected_result_sha256) is not None,
         'external physical publication result SHA required')
    return _stage_proof('publication', pins, expected_result_sha256, root)


def verify_restoration_proof(pins, expected_publication_result_sha256, root=ROOT):
    need(type(expected_publication_result_sha256) is str and re.fullmatch('[a-f0-9]{64}', expected_publication_result_sha256) is not None,
         'external physical accepted publication result SHA required')
    return _stage_proof('restoration', pins, expected_publication_result_sha256, root)
