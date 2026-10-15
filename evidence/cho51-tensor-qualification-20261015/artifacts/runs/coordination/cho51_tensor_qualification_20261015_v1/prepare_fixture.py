"""Create one untrained EEGNet publication inside the admitted qualification Job."""
import ast
import json
import platform
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path


def prepare(out: Path, workspace: Path):
    import numpy as np
    import torch
    from core.config import config_digest
    from core.provenance import capture_source
    from docs.phase2.cho51_publication_collection_v1.collection import Cho51PublicationBinding
    from docs.phase2.cho51_tensor_verification_v1.contract import make_tensor_request
    from docs.phase2.cho51_tensor_verification_v1.launcher import prepare_tensor_bundle, digest
    from evaluation.labram_parity import state_digest
    from evaluation.phase2_cho_source_restore import _new_model, prepare_cho_source_restore
    from evaluation.phase2_records import envelope
    from evaluation.phase2_runner import CasePlan, environment_digest
    from evaluation.phase2_selected_source_store import SelectedSourceStore

    root = Path(__file__).resolve().parents[3]
    fixture = out / 'f'
    (fixture / 'configs').mkdir(parents=True, exist_ok=False)
    (fixture / 'configs/base.toml').write_bytes((root / 'configs/base.toml').read_bytes())
    # Extract only the existing pure config builder; no unittest setup, original
    # subject01 fixture or RAM replacement is imported/executed.
    prior = root / 'tests/test_phase2_cho_tensor_case_child.py'
    tree = ast.parse(prior.read_bytes())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_eegnet_method_config')
    module = ast.Module(body=[function], type_ignores=[])
    namespace = {'Any': object}
    exec(compile(module, str(prior), 'exec'), namespace)
    method = namespace['_eegnet_method_config']()
    plan = CasePlan('cho2017', 'subject_02', 'eegnet', 5, 11, 1)
    candidate = method['candidates'][0]
    prepared = prepare_cho_source_restore(root=fixture, plan=plan, method_config=method,
        expected_method_config_sha256=config_digest(method), selected_candidate=candidate['name'])
    model = _new_model(prepared)
    state_sha = state_digest(model)
    source = capture_source(fixture)
    protocol = {'protocol': {'schema_version': 1}, 'datasets': {'cho2017': {}}}
    contract = {
        'method': 'eegnet', 'dataset': 'cho2017', 'protocol_sha256': config_digest(protocol),
        'source': asdict(source), 'candidates': method['candidates'],
        'runtime': {'python': platform.python_version(), 'torch': str(torch.__version__),
            'numpy': np.__version__, 'braindecode': version('braindecode'), 'device': 'cpu',
            'dtype': 'float32', 'torch_threads': torch.get_num_threads(),
            'deterministic_algorithms': torch.are_deterministic_algorithms_enabled()},
    }
    evidence = envelope('engineering_smoke', {
        'purpose': 'bounded_eegnet_source_selection', 'contract': contract,
        'contract_sha256': config_digest(contract), 'complete': True,
        'selected_candidate': candidate['name'], 'outer_target_predictions_performed': False,
        'final_source_fit': {'candidate': candidate['name'], 'candidate_sha256': config_digest(candidate),
            'initial_state_sha256': state_sha, 'fitted_state_sha256': state_sha},
    })
    publication = SelectedSourceStore(fixture).publish(model, evidence,
        evidence_sha256=evidence['sha256'], protocol_config=protocol, model_recipe=prepared.model_recipe)
    binding = Cho51PublicationBinding(plan.case_id, publication.manifest_sha256,
        publication.manifest_path, evidence['sha256'], config_digest(contract), candidate['name'],
        config_digest(protocol), config_digest(method), environment_digest(),
        config_digest(prepared.model_recipe), state_sha, publication.weights_sha256)
    request = make_tensor_request(project_root=fixture, plan=plan, publication=binding,
        expected_source=source, method_config=method, protocol_config=protocol)
    assets = {str(path): digest(path) for path in (
        fixture / 'configs/base.toml', publication.manifest_path, publication.evidence_path, publication.weights_path)}
    bundle_sha = prepare_tensor_bundle(request.payload(), expected_request_sha256=request.sha256,
        workspace=workspace, asset_pins=assets, seconds=180)
    scope = dict(schema='cho51_untrained_eegnet_fixture_v1', case_id=plan.case_id,
        fixture_root=str(fixture), bundle_path=str(workspace / 'bundle.json'), bundle_sha256=bundle_sha,
        request_sha256=request.sha256, initial_state_sha256=state_sha, fitted_state_claim_sha256=state_sha,
        weights_sha256=publication.weights_sha256, weights_bytes=publication.weights_path.stat().st_size,
        actual_untrained_model_constructed=True, actual_safetensors_encoded=True,
        source_fit_and_complete_fields_are_fabricated=True, gradient_steps_performed=0,
        recording_or_target_predictions_performed=False, constructor_shape_inference_allowed=True,
        original_case_attempt_used=False, scientific_admission=False,
        base_storage_floor_preserved=True, all_roster_cases_executed=False)
    for path in (fixture / 'FIXTURE_SCOPE.json', out / 'fixture-scope.json'):
        with path.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(scope, stream, indent=2, sort_keys=True)
            stream.write('\n')
    del model
    print(json.dumps(scope), flush=True)
    return scope
