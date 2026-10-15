"""Explicit two-root publication/restoration using unchanged canonical storage.

Numerical imports and execution require a freshly admitted native child. The
architecture comes from the real project; evidence provenance and the store
belong to an exact five-TOML mirror of the accepted synthetic fixture.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import stat
import sys

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / 'runs/coordination/cho51_linear_publication_20261015_v1'
MAXIMUM_JSON = 8 * 1024**2
MAXIMUM_EVIDENCE = 32 * 1024**2
MAXIMUM_WEIGHTS = 64 * 1024**2


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _canonical(value):
    return json.dumps(value, allow_nan=False, sort_keys=True, separators=(',', ':'))


def _plain(value):
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {name: _plain(member) for name, member in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(member) for member in value]
    return value


def _read(path, expected_sha256, maximum=MAXIMUM_JSON):
    from docs.phase2.cho51_linear_lineage_v1.probe import _read_baseline
    path = Path(path)
    raw, pin = _read_baseline(path, maximum_bytes=maximum,
        expected_bytes=path.stat().st_size, expected_sha256=expected_sha256)
    return raw, pin


def _object(path, expected_sha256, maximum=MAXIMUM_JSON):
    raw, pin = _read(path, expected_sha256, maximum)
    def unique(rows):
        result = {}
        for key, value in rows:
            _need(key not in result, 'duplicate metadata JSON key')
            result[key] = value
        return result
    value = json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite metadata JSON')))
    _need(type(value) is dict and raw == (_canonical(value) + '\n').encode('utf-8'),
          'exact finite canonical JSON object and newline required')
    return value, pin


def _observed(path, maximum=MAXIMUM_JSON):
    """Hash an actual newly published file without an unbounded preliminary read."""
    from docs.phase2.cho51_linear_lineage_v1.probe import _identity
    before = _identity(path)
    _need(0 < before[2] <= maximum, 'new publication file exceeds its independent byte bound')
    with path.open('rb') as stream:
        info = os.fstat(stream.fileno())
        opened = info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns
        _need(opened[:4] == before[:4], 'new publication descriptor differs')
        raw = stream.read(maximum + 1)
        info = os.fstat(stream.fileno())
        finished = info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns
    _need(opened == finished and _identity(path) == before and len(raw) == before[2],
          'new publication file changed during bounded hashing')
    return raw, hashlib.sha256(raw).hexdigest()


def _write(path, value):
    raw = (_canonical(value) + '\n').encode('utf-8')
    _need(0 < len(raw) <= MAXIMUM_JSON, 'ordinary result must remain within8MiB')
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {'path': str(path), 'file_sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw)}


def _metadata():
    name = '_cho51_linear_publication_metadata_v1'
    if name not in sys.modules:
        path = RUN / 'metadata.py'
        spec = importlib.util.spec_from_file_location(name, path)
        _need(spec is not None and spec.loader is not None, 'pinned stage metadata helper required')
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def _context(stage_contract):
    from core.config import config_digest
    from core.provenance import capture_source
    from docs.phase2.cho51_linear_continuation_v1.probe import _existing_fixture
    from docs.phase2.cho51_linear_publication_v1.contract import validate_stage_contract
    from evaluation.phase2_runner import CasePlan, method_configuration
    from evaluation.phase2_records import verify_envelope

    stage_contract = json.loads(_canonical(stage_contract))
    validate_stage_contract(stage_contract)
    origin, origin_pin = _object(Path(stage_contract['origin_path']), stage_contract['origin_file_sha256'])
    metadata = _metadata()
    verified_origin = metadata.verify_origin(origin, ROOT)
    _need(verified_origin == origin, 'independently authenticated origin snapshot differs')
    metadata.verify_stage_contract(stage_contract, origin, ROOT)
    fixture = _existing_fixture(origin['fixture_origin'])
    inputs = fixture.verify_inputs()
    record, evidence_pin = _object(Path(origin['selection_evidence_path']),
        origin['selection_evidence_file_sha256'], MAXIMUM_EVIDENCE)
    method, method_pin = _object(Path(origin['method_config_path']), origin['method_config_file_sha256'])
    plan = CasePlan(**origin['case'])
    payload, contract = record['payload'], record['payload']['contract']
    source = asdict(capture_source(fixture.root))
    _need(verify_envelope(record, kind='engineering_smoke', expected_payload=payload)
          and record['sha256'] == origin['selection_evidence_sha256']
          and evidence_pin['size_bytes'] == origin['selection_evidence_bytes']
          and payload['complete'] is True and payload['outer_target_predictions_performed'] is False
          and payload['selected_candidate'] == origin['selected_candidate']
          and payload['contract_sha256'] == config_digest(contract) == origin['contract_sha256']
          and len(payload['folds']) == 102 and len(payload['final_source_fit']['steps']) == 51
          and source == contract['source'] == origin['source']
          and method_configuration(method) == origin['method_config_sha256']
          and plan.method == 'labram_linear' and plan.target_subject == 'subject_02',
          'exact complete engineering source, method and original fixture context required')
    _need(ROOT == Path(stage_contract['architecture_root'])
          and Path(stage_contract['evidence_root']) == Path(origin['store_root'])
          and Path(stage_contract['origin_fixture_root']) == fixture.root,
          'explicit architecture and evidence roots differ from the pinned two-root contract')
    return {'stage': stage_contract, 'origin': origin, 'metadata': metadata, 'fixture': fixture,
            'inputs': inputs, 'record': record, 'contract': contract, 'source': source,
            'plan': plan, 'method': method, 'origin_pin': origin_pin,
            'evidence_pin': evidence_pin, 'method_pin': method_pin,
            'mirror': Path(stage_contract['evidence_root'])}


def _mirror_source(context):
    from core.provenance import capture_source, source_files
    from docs.phase2.cho51_source_fold_probe_v1.fixture import CONFIGURATIONS
    mirror = context['mirror']
    _need(mirror.is_dir() and mirror.resolve(strict=True) == mirror
          and {path.relative_to(mirror).as_posix() for path in source_files(mirror)} == set(CONFIGURATIONS)
          and all(not ((mirror / relative).stat().st_mode & stat.S_IWRITE) for relative in CONFIGURATIONS)
          and not (mirror / 'data').exists(), 'mirror must contain exactly the five source TOMLs and no data')
    source = capture_source(mirror)
    _need(asdict(source) == context['source'], 'mirror full source fingerprint or Git context differs')
    context['metadata'].verify_source_context(context['origin'])
    return source


def _create_mirror(context, output):
    from docs.phase2.cho51_source_fold_probe_v1.fixture import CONFIGURATIONS
    mirror, fixture = context['mirror'], context['fixture']
    _need(mirror == output / 'project' and not mirror.exists(), 'fresh exact metadata mirror required')
    mirror.mkdir(exist_ok=False)
    for relative in CONFIGURATIONS:
        expected = context['inputs']['files'][relative]
        raw, pin = _read(fixture.root / relative, expected['sha256'], 1024**2)
        _need(len(raw) == expected['size_bytes'], 'original fixture configuration length changed')
        target = mirror / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        target.chmod(0o444)
    _mirror_source(context)


def _prepared(context):
    from core.config import config_digest
    from evaluation.phase2_cho_source_restore import prepare_cho_source_restore
    prepared = prepare_cho_source_restore(root=ROOT, plan=context['plan'], method_config=context['method'],
        expected_method_config_sha256=context['origin']['method_config_sha256'],
        selected_candidate=context['origin']['selected_candidate'])
    _need(config_digest(prepared.model_recipe) == context['origin']['model_recipe_sha256'],
          'independently derived winning architecture recipe differs')
    return prepared


def _check_model(context, prepared, model):
    import torch
    from evaluation.labram_parity import state_digest
    from evaluation.phase2_cho_publication_gate import _require_selected_model_class
    _require_selected_model_class(model, context['plan'].method, prepared.model_recipe)
    state = model.state_dict()
    _need(len(state) == 223 and sum(value.numel() for value in state.values()) == 5818138
          and len(model.backbone.blocks) == 12 and int(model.backbone.embed_dim) == 200
          and tuple(name for name, p in model.named_parameters() if p.requires_grad) == ('head.weight', 'head.bias')
          and sum(p.numel() for p in model.parameters() if p.requires_grad) == 402
          and not any(module.training for module in model.modules())
          and all(parameter.grad is None for parameter in model.parameters())
          and all(value.device.type == 'cpu' and value.dtype == torch.float32
                  and torch.isfinite(value).all().item() for value in state.values())
          and state_digest(model) == context['origin']['model_state_sha256'],
          'actual complete finite fitted classifier state or exact linear mask differs')


def _load_selected_checkpoint(context, prepared):
    import torch
    from safetensors.torch import load
    from evaluation.labram_parity import state_digest
    from evaluation.phase2_cho_source_restore import _new_model, _check_labram_baseline, _require_host_ram
    _require_host_ram(6.0)
    model = _new_model(prepared, contract=context['contract'], final_fit=context['record']['payload']['final_source_fit'])
    backbone_before = state_digest(model.backbone)
    _check_labram_baseline(prepared)
    _require_host_ram(4.0)
    raw, pin = _read(Path(context['origin']['checkpoint_path']), context['origin']['checkpoint_file_sha256'], MAXIMUM_WEIGHTS)
    _need(pin['size_bytes'] == context['origin']['checkpoint_bytes'], 'selected source checkpoint length differs')
    tensors = load(raw)
    expected = model.state_dict()
    _need(set(tensors) == set(expected) and len(tensors) == 223
          and all(tensor.device.type == 'cpu' and tensor.dtype == expected[name].dtype
                  and tensor.shape == expected[name].shape and torch.isfinite(tensor).all().item()
                  for name, tensor in tensors.items()), 'bounded selected safe tensor schema differs')
    model.load_state_dict(tensors, strict=True)
    _check_model(context, prepared, model)
    _need(state_digest(model.backbone) == backbone_before, 'fitted linear checkpoint changed frozen backbone or buffers')
    _require_host_ram(4.0)
    return model, pin


def _verify_complete(context, prepared, model, record=None):
    from evaluation.labram_parity import state_digest
    from evaluation.phase2_cho_execution_gate import _method_config
    from evaluation.phase2_cho_source_restore import _runtime_dependencies, _check_labram_baseline
    from evaluation.phase2_selection_evidence_binding import verify_cho_selection_evidence
    record = context['record'] if record is None else record
    _need(record == context['record'], 'published/restored complete evidence must remain exactly unchanged')
    _runtime_dependencies(record['payload']['contract'])
    _method_config(context['plan'], context['method'], record['payload']['contract'], context['fixture'].assets)
    verified = verify_cho_selection_evidence(record=record, evidence_sha256=record['sha256'],
        plan=context['plan'], protocol_config=context['fixture'].protocol,
        catalogs=context['fixture'].catalogs, selection_record=context['fixture'].selection_record,
        assets=context['fixture'].assets, root=context['mirror'],
        adapter_model_state_sha256=state_digest(model), adapter_source_settings=asdict(prepared.source_settings),
        adapter_support_settings=asdict(prepared.support_settings))
    _need(verified.selected_candidate == context['origin']['selected_candidate']
          and verified.evidence_sha256 == context['origin']['selection_evidence_sha256'],
          'canonical complete-evidence verifier returned a different winner or record')
    _check_labram_baseline(prepared)
    _mirror_source(context)
    return verified


def _files(context, publication):
    from core.config import config_digest
    from evaluation.phase2_cho_selected_manifest_bridge import verify_cho_selected_manifest_files
    publication = _plain(asdict(publication)) if not isinstance(publication, dict) else publication
    mirror, origin = context['mirror'], context['origin']
    expected = mirror / 'runs/phase2/selected_sources'
    weights = Path(publication['weights_path'])
    evidence = Path(publication['evidence_path'])
    manifest = Path(publication['manifest_path'])
    _need(weights == expected / 'weights' / f"{publication['weights_sha256']}.safetensors"
          and evidence == expected / 'evidence' / f"{origin['selection_evidence_sha256']}.json"
          and manifest == expected / 'manifests' / f"{publication['manifest_sha256']}.json",
          'canonical publication paths differ from the independently pinned default store')
    _, weight_before = _read(weights, publication['weights_sha256'], MAXIMUM_WEIGHTS)
    _, evidence_pin = _object(evidence, origin['selection_evidence_file_sha256'], MAXIMUM_EVIDENCE)
    _, manifest_raw_sha = _observed(manifest)
    _, manifest_pin = _object(manifest, manifest_raw_sha)
    source = _mirror_source(context)
    witness = verify_cho_selected_manifest_files(mirror, manifest,
        manifest_sha256=publication['manifest_sha256'], evidence_sha256=origin['selection_evidence_sha256'],
        selection_contract_sha256=origin['contract_sha256'], selected_candidate=origin['selected_candidate'],
        protocol_config_sha256=config_digest(context['fixture'].protocol), expected_source=source,
        model_recipe_sha256=origin['model_recipe_sha256'], model_state_sha256=origin['model_state_sha256'])
    witness.verify_stable()
    _, weight_after = _read(weights, publication['weights_sha256'], MAXIMUM_WEIGHTS)
    _need(weight_before == weight_after and witness.weights_sha256 == publication['weights_sha256']
          and witness.evidence_file_sha256 == evidence_pin['file_sha256']
          and witness.manifest_file_sha256 == manifest_pin['file_sha256'],
          'canonical byte witness or stage-owned64MiB weight binding changed')
    return {'weights': weight_after, 'evidence': evidence_pin, 'manifest': manifest_pin}, witness


def _finish_context(context, rng):
    import numpy as np
    import torch
    from core.provenance import capture_source
    _need(context['fixture'].verify_inputs() == context['inputs']
          and asdict(capture_source(context['fixture'].root)) == context['source'],
          'all original inputs and full fixture provenance must remain unchanged')
    _mirror_source(context)
    _need(context['metadata'].verify_origin(context['origin'], ROOT) == context['origin'],
          'historical source origin changed during publication/restoration')
    after = np.random.get_state()
    _need(torch.equal(torch.random.get_rng_state(), rng[0]) and after[0] == rng[1][0]
          and np.array_equal(after[1], rng[1][1]) and after[2:] == rng[1][2:]
          and random.getstate() == rng[2], 'stage must preserve global Torch/NumPy/Python RNG')


def _common(context):
    from core.config import config_digest
    return {'passed': True, 'method': 'labram_linear', 'architecture_root': str(ROOT),
        'evidence_root': str(context['mirror']), 'store_root': str(context['mirror']),
        'source': context['source'], 'case': asdict(context['plan']), 'case_id': context['plan'].case_id,
        'stage_contract_sha256': config_digest(context['stage']),
        'stage_contract_file_sha256': hashlib.sha256((_canonical(context['stage']) + '\n').encode()).hexdigest(),
        'origin_file_sha256': context['origin_pin']['file_sha256'],
        'selected_candidate': context['origin']['selected_candidate'],
        'model_state_sha256': context['origin']['model_state_sha256'],
        'model_recipe_sha256': context['origin']['model_recipe_sha256'],
        'historical_gradient_updates': 5253, 'complete_folds': 102, 'historical_final_source_updates': 51,
        'actual_gradient_updates': 0, 'current_gradient_updates': 0,
        'source_gradient_updates': 0, 'support_gradient_updates': 0,
        'tensor_count': 223, 'elements': 5818138, 'head_parameters': 402,
        'all_physical_inputs_rehashed_unchanged': True, 'mirror_source_unchanged': True,
        'torch_numpy_python_rng_unchanged': True, 'pretrained_baseline_loaded': True,
        'pretrained_weights_loaded': True, 'historical_full_selector_verified': True,
        'source_policy': 'two_root_staged_bridge', 'two_root_bridge': True,
        'cohort_lineage_verified': False, 'engineering_only': True, 'scientific_admission': False,
        'original_case_attempts_remaining': 0, 'measured_cells': 0, 'recorder_used': False,
        'full_worker_verified': False, 'public_selected_source_restore_exercised': False,
        'unchanged_single_root_factory_verified': False, 'public_single_root_factory_qualified': False,
        'target_prediction_performed': False, 'fitting_performed': False}


def publish_source(output: Path, stage_contract: dict, *, set_protected_inputs) -> dict:
    import numpy as np
    import torch
    from evaluation.labram_parity import state_digest
    from evaluation.phase2_cho_publication_gate import _selected_model as canonical_selected_model
    from evaluation.phase2_cho_source_restore import _require_host_ram
    from evaluation.phase2_pilot import LaBraMTunedAdapter
    from evaluation.phase2_selected_source_store import SelectedSourceStore

    _need(isinstance(output, Path) and output.is_dir() and output.resolve(strict=True) == output
          and callable(set_protected_inputs), 'direct owned publication output and target protection required')
    rng = torch.random.get_rng_state().clone(), np.random.get_state(), random.getstate()
    context = _context(stage_contract)
    _need(output == Path(stage_contract['publication_output'])
          and not (output / 'publication-result.json').exists(), 'fresh exact publication output required')
    _create_mirror(context, output)
    protected = False
    try:
        set_protected_inputs(context['fixture'].protected_outer_paths, True)
        protected = True
        prepared = _prepared(context)
        model, source_checkpoint = _load_selected_checkpoint(context, prepared)
        verified = _verify_complete(context, prepared, model)
        adapter = LaBraMTunedAdapter(context['plan'].method, model, prepared.support_settings)
        _need(canonical_selected_model(adapter, context['plan'].method) is model,
              'canonical selected-adapter model extraction differs')
        _require_host_ram(4.0)
        publication = SelectedSourceStore(context['mirror']).publish(model, context['record'],
            evidence_sha256=verified.evidence_sha256, protocol_config=context['fixture'].protocol,
            model_recipe=prepared.model_recipe, weights_format='full_v1', evidence_format='canonical_json_v1')
        _need(not publication.resumed and publication.model_state_sha256 == context['origin']['model_state_sha256']
              and publication.selected_candidate == verified.selected_candidate
              and publication.weights_format == 'full_v1' and publication.evidence_format == 'canonical_json_v1'
              and state_digest(model) == publication.model_state_sha256, 'actual canonical publication differs')
        files, witness = _files(context, publication)
        witness.verify_stable()
        _check_model(context, prepared, model)
        _require_host_ram(4.0)
    finally:
        if protected:
            set_protected_inputs(context['fixture'].protected_outer_paths, False)
    _finish_context(context, rng)
    result = {**_common(context), 'schema': 'cho51_linear_staged_publication_v1',
        'publication_performed': True, 'publication_qualified': True, 'restoration_qualified': False,
        'new_staged_store_restore_verified': False, 'detached_stage_verified': False,
        'publication': _plain(asdict(publication)), 'files': files, 'source_checkpoint': source_checkpoint,
        'weights_path': str(publication.weights_path), 'weights_file_sha256': publication.weights_sha256,
        'weights_bytes': files['weights']['size_bytes'], 'manifest_path': str(publication.manifest_path),
        'manifest_sha256': publication.manifest_sha256, 'manifest_file_sha256': files['manifest']['file_sha256'],
        'evidence_path': str(publication.evidence_path), 'evidence_sha256': publication.evidence_sha256,
        'evidence_file_sha256': files['evidence']['file_sha256'], 'evidence_bytes': files['evidence']['size_bytes'],
        'canonical_manifest_byte_bridge_verified': True, 'stage_weight_limit_bytes': MAXIMUM_WEIGHTS,
        'canonical_byte_bridge_weight_limit_unchanged': True,
        'source_evidence_file_sha256': context['evidence_pin']['file_sha256']}
    _write(output / 'publication-result.json', result)
    return result


def _restore_once(context, publication_result, *, release_adapter):
    from core.config import config_digest
    from evaluation.labram_parity import state_digest
    from evaluation.phase2_cho_publication_gate import _selected_model
    from evaluation.phase2_cho_source_restore import _new_model, _pre_restore_evidence, _runtime_dependencies, _check_labram_baseline, _require_host_ram
    from evaluation.phase2_pilot import LaBraMTunedAdapter
    from evaluation.phase2_selected_source_store import SelectedSourceStore

    prepared = _prepared(context)
    store = SelectedSourceStore(context['mirror'])
    manifest_sha, evidence_sha = publication_result['manifest_sha256'], publication_result['evidence_sha256']
    _require_host_ram(6.0)
    files_before, witness = _files(context, publication_result['publication'])
    before = store.preflight_full_weights(manifest_sha, maximum_bytes=MAXIMUM_WEIGHTS)
    record, contract, final_fit = _pre_restore_evidence(store, manifest_sha, evidence_sha)
    _need(record == context['record'], 'persisted complete evidence changed before lineage reconstruction')
    _runtime_dependencies(contract)
    _require_host_ram(4.0)
    model = _new_model(prepared, contract=contract, final_fit=final_fit)
    _check_labram_baseline(prepared)
    _require_host_ram(4.0)
    _need(store.preflight_full_weights(manifest_sha, maximum_bytes=MAXIMUM_WEIGHTS) == before,
          'published full weights changed before bounded restore')
    restored = store.restore(manifest_sha, model, expected_evidence_sha256=evidence_sha,
        protocol_config=context['fixture'].protocol, model_recipe=prepared.model_recipe,
        maximum_weights_bytes=MAXIMUM_WEIGHTS)
    _require_host_ram(4.0)
    _need(restored.model is model and restored.evidence_record == record
          and restored.publication.weights_format == 'full_v1'
          and restored.publication.manifest_sha256 == manifest_sha
          and restored.publication.evidence_sha256 == evidence_sha
          and restored.publication.weights_sha256 == before.sha256
          and restored.publication.model_state_sha256 == context['origin']['model_state_sha256'],
          'actual canonical bounded restore differs from independently pinned publication')
    _check_model(context, prepared, model)
    verified = _verify_complete(context, prepared, model, restored.evidence_record)
    files_after, final_witness = _files(context, restored.publication)
    _need(files_before == files_after
          and store.preflight_full_weights(manifest_sha, maximum_bytes=MAXIMUM_WEIGHTS) == before,
          'publication physical identities changed during bounded tensor restoration')
    witness.verify_stable()
    final_witness.verify_stable()
    _runtime_dependencies(contract)
    _check_labram_baseline(prepared)
    _require_host_ram(4.0)
    adapter = None
    if release_adapter:
        adapter = LaBraMTunedAdapter(context['plan'].method, model, prepared.support_settings)
        _need(type(adapter) is LaBraMTunedAdapter and _selected_model(adapter, context['plan'].method) is model,
              'staged adapter factory must release the genuine canonical tuned adapter')
    witness_result = {'manifest_sha256': manifest_sha, 'evidence_sha256': evidence_sha,
        'selected_candidate': verified.selected_candidate, 'model_recipe_sha256': config_digest(prepared.model_recipe),
        'model_state_sha256': state_digest(model), 'weights_sha256': restored.publication.weights_sha256,
        'maximum_weights_bytes': MAXIMUM_WEIGHTS, 'tensor_count': 223, 'elements': 5818138,
        'public_complete_evidence_verifier_passed': True, 'canonical_store_restore_passed': True,
        'adapter_released': release_adapter,
        'adapter_class': f'{type(adapter).__module__}.{type(adapter).__qualname__}' if adapter is not None else None}
    return model, adapter, witness_result


def _staged_digest_check(context, publication_result):
    """New two-root digest checker: return a private model/witness, no adapter."""
    model, adapter, witness = _restore_once(context, publication_result, release_adapter=False)
    _need(adapter is None and witness['adapter_released'] is False,
          'staged digest checker must not release a target adapter')
    return model, witness


def _staged_adapter_factory(context, publication_result):
    """New two-root factory: return the real model, tuned adapter and witness.

    The context comes from this bridge's authenticated ``_context`` boundary;
    the caller supplies fresh native admission and protected-input scope.
    This is a separate staged API, not ``restore_cho_selected_source``.
    """
    from evaluation.phase2_pilot import LaBraMTunedAdapter
    model, adapter, witness = _restore_once(context, publication_result, release_adapter=True)
    _need(type(adapter) is LaBraMTunedAdapter and adapter._model is model
          and witness['adapter_released'] is True, 'genuine staged adapter release differs')
    return model, adapter, witness


def verify_publication(output: Path, stage_contract: dict, publication_result: dict, *,
                       expected_publication_result_sha256: str, set_protected_inputs) -> dict:
    import numpy as np
    import torch
    from core.config import config_digest

    _need(isinstance(output, Path) and output.is_dir() and output.resolve(strict=True) == output
          and callable(set_protected_inputs), 'direct detached output and target protection required')
    rng = torch.random.get_rng_state().clone(), np.random.get_state(), random.getstate()
    context = _context(stage_contract)
    _need(output == Path(stage_contract['detached_output']) and not (output / 'restoration-result.json').exists(),
          'fresh exact detached restoration output required')
    actual, publication_pin = _object(Path(stage_contract['publication_output']) / 'publication-result.json',
                                      expected_publication_result_sha256)
    _need(actual == publication_result and actual['passed'] is True and actual['publication_qualified'] is True
          and actual['schema'] == 'cho51_linear_staged_publication_v1'
          and actual['model_state_sha256'] == context['origin']['model_state_sha256']
          and actual['model_recipe_sha256'] == context['origin']['model_recipe_sha256'],
          'externally pinned actual publication result differs')
    publication = actual['publication']
    _need(actual['stage_contract_sha256'] == config_digest(context['stage'])
          and actual['architecture_root'] == str(ROOT) and actual['evidence_root'] == str(context['mirror'])
          and actual['store_root'] == str(context['mirror']) and actual['source'] == context['source']
          and actual['case'] == asdict(context['plan'])
          and publication['resumed'] is False and publication['weights_format'] == 'full_v1'
          and publication['evidence_format'] == 'canonical_json_v1'
          and all(actual[key] == publication[key] for key in (
              'manifest_path', 'manifest_sha256', 'evidence_path', 'evidence_sha256',
              'weights_path', 'selected_candidate', 'model_state_sha256'))
          and actual['weights_file_sha256'] == publication['weights_sha256']
          and actual['evidence_sha256'] == context['origin']['selection_evidence_sha256']
          and actual['selected_candidate'] == context['origin']['selected_candidate'],
          'publication context, canonical paths or duplicated independent pins differ')
    _mirror_source(context)
    expected_files, _ = _files(context, publication)
    _need(expected_files == actual['files']
          and actual['weights_bytes'] == expected_files['weights']['size_bytes']
          and actual['evidence_bytes'] == expected_files['evidence']['size_bytes']
          and actual['manifest_file_sha256'] == expected_files['manifest']['file_sha256']
          and actual['evidence_file_sha256'] == expected_files['evidence']['file_sha256'],
          'immutable publication file pins changed before detached model construction')
    protected = False
    try:
        set_protected_inputs(context['fixture'].protected_outer_paths, True)
        protected = True
        digest_model, digest_witness = _staged_digest_check(context, actual)
        adapter_model, adapter, adapter_witness = _staged_adapter_factory(context, actual)
        states = digest_model.state_dict(), adapter_model.state_dict()
        storage = [{value.untyped_storage().data_ptr() for value in state.values() if value.numel()} for state in states]
        _need(digest_model is not adapter_model and not storage[0] & storage[1]
              and set(states[0]) == set(states[1]) and len(states[0]) == 223
              and all(torch.equal(states[0][name], states[1][name]) for name in states[0])
              and adapter._model is adapter_model,
              'two genuine fresh staged restorations must match all223 tensors without shared storage')
        _, final_pin = _object(Path(stage_contract['publication_output']) / 'publication-result.json',
                               expected_publication_result_sha256)
        _need(final_pin == publication_pin, 'pinned publication result changed across detached restoration')
    finally:
        if protected:
            set_protected_inputs(context['fixture'].protected_outer_paths, False)
    _finish_context(context, rng)
    digest_pin = _write(output / 'tensor-witness.json', {
        'schema': 'cho51_linear_staged_tensor_witness_v1', **digest_witness})
    adapter_pin = _write(output / 'adapter-witness.json', {
        'schema': 'cho51_linear_staged_adapter_witness_v1', **adapter_witness})
    result = {**_common(context), 'schema': 'cho51_linear_staged_restoration_v1',
        'publication_performed': False, 'publication_qualified': True, 'restoration_qualified': True,
        'detached_stage_verified': True, 'new_staged_store_restore_verified': True,
        'publication_result': publication_pin, 'digest_witness': digest_witness, 'adapter_witness': adapter_witness,
        'digest_witness_file': digest_pin, 'adapter_witness_file': adapter_pin,
        'actual_store_restores': 2, 'restore_weight_limits': [MAXIMUM_WEIGHTS, MAXIMUM_WEIGHTS],
        'all223_tensors_equal': True, 'restored_models_have_disjoint_storage': True,
        'actual_adapter_class': adapter_witness['adapter_class'], 'actual_adapter_released': True,
        'staged_digest_checker': 'docs.phase2.cho51_linear_publication_v1.bridge._staged_digest_check',
        'staged_adapter_factory': 'docs.phase2.cho51_linear_publication_v1.bridge._staged_adapter_factory',
        'adapter_factory_returns_actual_model_and_adapter': True,
        'canonical_manifest_byte_bridge_verified': True, 'canonical_byte_bridge_weight_limit_unchanged': True}
    _write(output / 'restoration-result.json', result)
    return result
