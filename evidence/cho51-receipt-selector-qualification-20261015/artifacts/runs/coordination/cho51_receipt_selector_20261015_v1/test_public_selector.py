"""Real public selector metadata checks on explicitly fabricated complete folds.

No tensors are decoded, no model is built, and no native case proof is made.
The per-case selector bridge is exercised through real canonical/factored
publication files; the separate full-roster tests mock native proof I/O.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.config import canonical_config_json, config_digest
from core.provenance import SourceProvenance, source_files
from docs.phase2.cho51_publication_collection_v1.collection import Cho51PublicationBinding
from docs.phase2.cho51_selector_collection_v1.collection import _verify_selector_case
from docs.phase2.cho51_tensor_verification_v1.contract import make_tensor_request
from docs.phase2.cho51_worker_bridge_v1.worker_bridge import Cho51WorkerRoute
from evaluation.phase2_cho_method_template import derive_cho_method_template
from evaluation.phase2_factored_evidence import SCHEMA, pack_factored_selection
from evaluation.phase2_records import envelope
from evaluation.phase2_runner import environment_digest, method_configuration
from evaluation.phase2_selection_evidence_binding import verify_cho_selection_evidence

ROOT = Path(__file__).resolve().parents[3]


def _write_once(path, raw):
    if path.exists():
        assert path.read_bytes() == raw
    else:
        with path.open('xb') as stream:
            stream.write(raw)


@pytest.fixture(scope='module')
def worlds():
    # Reuse only fixture-building methods from the pinned historical test AST.
    # Its tests and subject01 plan are never executed. The local fixture copy
    # explicitly targets subject02 and raises only its fabricated contract cap.
    path = ROOT / 'tests/test_phase2_selection_evidence_binding.py'
    tree = ast.parse(path.read_bytes())
    original = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'ChoSelectionEvidenceBindingTests')
    copied = copy.deepcopy(original)
    copied.name = 'FabricatedCho51SelectorWorld'
    copied.bases = []
    copied.body = [node for node in copied.body if not isinstance(node, ast.FunctionDef) or not node.name.startswith('test_')]

    class AdaptFixture(ast.NodeTransformer):
        def visit_Constant(self, node):
            if node.value == 'subject_01':
                return ast.copy_location(ast.Constant('subject_02'), node)
            return node

        def visit_Dict(self, node):
            self.generic_visit(node)
            for index, key in enumerate(node.keys):
                if isinstance(key, ast.Constant) and key.value == 'maximum_gradient_steps':
                    node.values[index] = ast.copy_location(ast.Constant(5253), node.values[index])
            return node

    copied = AdaptFixture().visit(copied)
    imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    module = ast.fix_missing_locations(ast.Module(body=[*imports, copied], type_ignores=[]))
    namespace = {'__name__': '_fabricated_cho51_selector_fixture'}
    exec(compile(module, str(path), 'exec'), namespace)
    cls = namespace[copied.name]
    cls.setUpClass()
    world = cls()
    owned_temp = Path(os.environ['TEMP']).resolve()
    assert owned_temp.is_relative_to(Path(__file__).resolve().parent)
    assert world.root.resolve().is_relative_to(owned_temp)
    assert source_files(world.root) == (world.root / 'configs/phase2/selection_ceiling.toml',)
    assert len(world.source['git_commit']) in (40, 64)
    assert all(c in '0123456789abcdef' for c in world.source['git_commit'])
    assert type(world.source['git_dirty']) is bool
    # This is the source hash of a tiny fixture workspace within the checkout;
    # it is deliberately distinct from the canonical project's source hash.
    assert world.source['source_sha256'] != '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
    assert len(world.catalogs) == 52 and len(world.selection.source_subjects) == 51
    assert 'subject_01' in world.selection.source_subjects
    assert 'subject_02' not in world.selection.source_subjects
    values = {}
    for method in ('eegnet', 'labram_linear', 'labram_lora', 'labram_full'):
        record, args = world.world(method)
        assert args['plan'].target_subject == 'subject_02'
        assert len(record['payload']['folds']) == 102
        assert record['payload']['contract']['maximum_gradient_steps'] == 5253
        values[method] = (record, args)
    try:
        yield SimpleNamespace(world=world, values=values)
    finally:
        cls.tearDownClass()


def publication(worlds, method, factored):
    record, args = worlds.values[method]
    root = args['root'].resolve()
    store = root / 'runs/phase2/selected_sources'
    for name in ('manifests', 'evidence', 'weights'):
        (store / name).mkdir(parents=True, exist_ok=True)
    blob = ('fabricated non-tensor bytes: ' + method).encode()
    weight_sha = hashlib.sha256(blob).hexdigest()
    _write_once(store / 'weights' / (weight_sha + '.safetensors'), blob)
    payload = record['payload']
    evidence_sha = record['sha256']
    if factored:
        raw = pack_factored_selection(record)
        physical_sha = hashlib.sha256(raw).hexdigest()
        evidence_name = physical_sha + '.factored.json'
    else:
        raw = (canonical_config_json(record) + '\n').encode()
        evidence_name = evidence_sha + '.json'
    _write_once(store / 'evidence' / evidence_name, raw)
    recipe = {'architecture': 'fabricated_metadata_only', 'method': method}
    manifest_payload = {
        'purpose': 'selected_source_snapshot', 'scope': 'engineering_only', 'scientific_evaluation': False,
        'evidence_sha256': evidence_sha, 'selected_candidate': payload['selected_candidate'],
        'selection_contract_sha256': payload['contract_sha256'], 'protocol_config_sha256': config_digest(args['protocol_config']),
        'source': payload['contract']['source'], 'model_class': 'fabricated.MetadataOnly',
        'model_recipe': recipe, 'model_recipe_sha256': config_digest(recipe),
        'model_state_sha256': args['adapter_model_state_sha256'],
        'tensor_schema': {'fabricated': {'shape': [1], 'dtype': 'torch.float32'}},
        'weights_sha256': weight_sha, 'weights_file': 'weights/' + weight_sha + '.safetensors',
        'evidence_file': 'evidence/' + evidence_name,
    }
    if factored:
        manifest_payload.update(evidence_format='factored_json_v1', evidence_schema=SCHEMA,
            evidence_physical_sha256=physical_sha, evidence_physical_bytes=len(raw))
    manifest = envelope('engineering_smoke', manifest_payload)
    path = store / 'manifests' / (manifest['sha256'] + '.json')
    _write_once(path, (canonical_config_json(manifest) + '\n').encode())
    method_config = derive_cho_method_template(args['plan'], payload['contract'], args['assets'])
    method_sha = method_configuration(method_config)
    binding = Cho51PublicationBinding(args['plan'].case_id, manifest['sha256'], path,
        evidence_sha, payload['contract_sha256'], payload['selected_candidate'], config_digest(args['protocol_config']),
        method_sha, environment_digest(), config_digest(recipe), args['adapter_model_state_sha256'], weight_sha)
    source = SourceProvenance(**payload['contract']['source'])
    request = make_tensor_request(project_root=root, plan=args['plan'], publication=binding,
        expected_source=source, method_config=method_config, protocol_config=args['protocol_config'])
    full = SimpleNamespace(catalogs=worlds.world.catalogs, labram_assets=worlds.world.assets,
        protocol_config_json=canonical_config_json(args['protocol_config']),
        selection_records_json={'subject_02': canonical_config_json(args['selection_record'])})
    route = Cho51WorkerRoute(SimpleNamespace(plans=(args['plan'],), method_config_sha256={method: method_sha}), full)
    return root, route, request, source


@pytest.mark.parametrize('method', ['eegnet', 'labram_linear', 'labram_lora', 'labram_full'])
@pytest.mark.parametrize('factored', [False, True])
def test_actual_public_selector_bridge_on_fabricated_complete_records(worlds, method, factored):
    root, route, request, source = publication(worlds, method, factored)
    claim, witness = _verify_selector_case(root, route, request, expected_source=source)
    witness.verify_stable()
    assert claim.case_id == request.plan.case_id
    assert claim.selected_candidate == 'first'
    assert claim.evidence_sha256 == request.publication.evidence_sha256
    assert claim.model_state_sha256 == request.publication.model_state_sha256


@pytest.mark.parametrize('method', ['eegnet', 'labram_linear', 'labram_lora', 'labram_full'])
@pytest.mark.parametrize('mutation', ['missing_fold', 'shifted_batch', 'wrong_winner', 'under_budget'])
def test_public_verifier_refuses_resealed_complete_record_tampering(worlds, method, mutation):
    original, args = worlds.values[method]
    payload = copy.deepcopy(original['payload'])
    if mutation == 'missing_fold':
        payload['folds'].pop()
    elif mutation == 'shifted_batch':
        step = payload['folds'][0]['source_fit']['steps'][0]
        step['trial_ids'] = list(reversed(step['trial_ids']))
    elif mutation == 'wrong_winner':
        payload['selected_candidate'] = 'second'
    else:
        payload['contract']['maximum_gradient_steps'] = 5252
        payload['contract_sha256'] = config_digest(payload['contract'])
    resealed = envelope('engineering_smoke', payload)
    changed = dict(args, record=resealed, evidence_sha256=resealed['sha256'])
    with pytest.raises(ValueError):
        verify_cho_selection_evidence(**changed)
