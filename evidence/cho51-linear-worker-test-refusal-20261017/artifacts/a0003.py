"""Locked engineering recorder for explicitly reused source and restore evidence.

The supplied verifier must independently qualify the historical source and the
separately accepted staged restoration. This transaction performs no numerical
work and never upgrades an original case to scientific acceptance.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import math
import ast
import sys
from types import ModuleType
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from core.config import config_digest, config_snapshot
from fractions import Fraction
from collections.abc import Mapping
from docs.phase2.cho51_linear_recorder_v1 import transaction as R
from docs.phase2.cho51_worker_bridge_v1.worker_bridge import Cho51WorkerRoute
from docs.phase2.cho51_route_candidate_v1 import route_contract as PLANNER
import evaluation.phase2_protocol as PROTOCOL
from evaluation.phase2_cho_case_inputs import ChoFirstTrancheRoute, ChoCaseInputs
from docs.phase2.cho51_worker_lifecycle_v1 import lifecycle as L
from evaluation.phase2_profile_binding import (
    CHO_CHANNELS, CHO_CLASSES, ChoProfileAssets60Hz, ChoProfileBinding60Hz,
)
from evaluation.phase2_records import verify_envelope
from scripts.audit_phase2_protocol import validate_protocol

_METADATA_SOURCES = {
    'settings': ('adaptation/labram_manifest.py',
        'cd83efea8d7c2a67d49b9505625787f939b2bb47f206bc109ab0d362f41fd36a'),
    'target': ('docs/phase2/cho51_linear_target_route_v1/target_route.py',
        '80468b32ef18c9efa58502077797f2e02925ba13cfbe5d83ce0b33b62c042500'),
}
_METADATA_NODES = {
    'settings': (('LaBraMTuningSettings', ast.ClassDef),),
    'target': (('PLAN', ast.Assign), ('SELECTED_STATE_SHA256', ast.Assign),
        ('SETTINGS', ast.Assign), ('SUBJECTS', ast.Assign), ('TRIAL_IDS', ast.Assign),
        ('_need', ast.FunctionDef), ('prepare_target_contract', ast.FunctionDef),
        ('validate_binding', ast.FunctionDef)),
}


def _metadata_nodes(source_name, raw):
    """Select a positive metadata allowlist from whole-file authenticated bytes."""
    if (type(source_name) is not str or source_name not in _METADATA_SOURCES
            or type(raw) is not bytes
            or hashlib.sha256(raw).hexdigest() != _METADATA_SOURCES[source_name][1]):
        raise ValueError('exact complete metadata source pin required before AST selection')
    tree = ast.parse(raw, filename=str(L.ROOT / _METADATA_SOURCES[source_name][0]))
    expected = dict(_METADATA_NODES[source_name])
    found = {}
    for node in tree.body:
        name = node.name if isinstance(node, (ast.ClassDef, ast.FunctionDef)) else (
            node.targets[0].id if isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name) else None)
        if name not in expected:
            continue
        if name in found or type(node) is not expected[name]:
            raise ValueError('duplicate or unexpected selected metadata AST shape')
        if any(isinstance(child, (ast.Import, ast.ImportFrom)) for child in ast.walk(node)):
            raise ValueError('selected metadata nodes cannot import source modules')
        found[name] = node
    if set(found) != set(expected):
        raise ValueError('complete exact metadata AST allowlist required')
    # Preserve authenticated source order, including constants before functions.
    return [node for node in tree.body if any(node is value for value in found.values())]


def _load_target_metadata():
    """Execute only pinned metadata AST; never import the target/model modules."""
    module = ModuleType('_cho51_linear_worker_target_metadata_v2')
    module.__dict__.update(dict(dataclass=dataclass, asdict=asdict, math=math, json=json,
        config_digest=config_digest, config_snapshot=config_snapshot, Mapping=Mapping,
        CasePlan=L.CasePlan, TrialCatalog=PROTOCOL.TrialCatalog,
        ChoProfileAssets60Hz=ChoProfileAssets60Hz, ChoProfileBinding60Hz=ChoProfileBinding60Hz,
        CHO_CHANNELS=CHO_CHANNELS, CHO_CLASSES=CHO_CLASSES, verify_envelope=verify_envelope,
        validate_protocol=validate_protocol, source_selection=PROTOCOL.source_selection,
        nested_episode=PROTOCOL.nested_episode, require_digest=PROTOCOL.require_digest))
    if module.__name__ in sys.modules:
        raise ValueError('private metadata module name must be unused before loading')
    sys.modules[module.__name__] = module
    receipts = {}
    try:
        for source_name, (relative, digest) in _METADATA_SOURCES.items():
            path = L.ROOT / relative
            raw, identity = L._read(path, digest)
            nodes = _metadata_nodes(source_name, raw)
            body = [ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), *nodes]
            tree = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))
            exec(compile(tree, str(path), 'exec', dont_inherit=True), module.__dict__)
            if L._read(path, digest)[1] != identity:
                raise ValueError('metadata source physical identity changed during isolated loading')
            receipts[source_name] = dict(path=str(path), sha256=digest, bytes=len(raw),
                selected_nodes=[name for name, _ in _METADATA_NODES[source_name]])
        module.metadata_isolation = dict(schema='cho51_linear_worker_metadata_ast_v2',
            full_source_modules_imported=False, numerical_imports_executed=False,
            source_derived_settings_class=True, sources=receipts)
    except BaseException:
        sys.modules.pop(module.__name__, None)
        raise
    return module


TARGET = _load_target_metadata()

WorkerContext = L.WorkerContext
CasePlan = L.CasePlan
CaseRecorder = L.CaseRecorder
RecoveryRequired = L.RecoveryRequired
WORKER = 'cho51_linear_worker_route_engineering'
_PATHS = ('fixture_root', 'recorder_root', 'workspace', 'pins_path', 'claim_path',
          'origin_contract_path')
_TARGET_FILE_DIGESTS = ('target_witness_file_sha256', 'target_result_file_sha256',
    'target_qualification_file_sha256', 'target_native_receipt_file_sha256', 'target_final_review_file_sha256')
_TARGET_DIGESTS = ('target_contract_sha256', *_TARGET_FILE_DIGESTS,
    'target_profile_binding_sha256', 'target_source_state_sha256',
    'target_adapted_state_sha256', 'target_metrics_sha256')
_BINDINGS = ('claim_file_sha256', 'execution_source_sha256', 'independent_pins_sha256',
             'owner_decision_sha256', 'environment_sha256', 'origin_contract_file_sha256',
             'fixture_source_sha256', 'fixture_git_commit', 'fixture_git_dirty',
             'historical_case_id', 'historical_git_commit', 'historical_source_sha256',
             'historical_git_dirty', 'worker_route_sha256') + _TARGET_DIGESTS
_INTS = dict(attempt=1, historical_gradient_updates=5253, current_gradient_updates=0,
    historical_source_updates=5151, historical_support_updates=102, fold_count=102, final_source_subjects=51,
    restored_tensors=223, restored_elements=5818138, head_parameters=402,
    historical_restore_count=2, current_restore_count=0, current_target_inference_calls=0, measured_cells=0, original_case_attempts_remaining=0,
    prior_target_support_updates=1, prior_target_restore_count=1,
    prior_target_inference_calls=1, prior_target_query_count=2,
    current_source_updates=0, current_support_updates=0)
_FLAGS = dict(source_work_reused=True, restore_work_reused=True, engineering_only=True,
    scientific_admission=False, original_scientific_case_qualified=False,
    staged_two_root_provenance=True, unchanged_single_root_factory_verified=False,
    historical_publication_qualified=True, historical_detached_restoration_qualified=True,
    prior_target_work_reused=True, prior_target_route_qualified=True,
    unchanged_canonical_worker_verified=False, full_worker_verified=False)
HISTORICAL_CASE_ID = '9d3596b5e7653e1708eb208d6b150b86cae02227e6cd73a25e4358e675afc141'
HISTORICAL_SOURCE = dict(
    git_commit='4491e2a68126d6b7293261f4954b88c11c29049d',
    source_sha256='9c2e6ad444c44309f9d4becda2909fba0d2fe315f047560f9adbce56397c9299',
    git_dirty=True)
_PROOF_DIGESTS = ('selected_state_sha256', 'weights_file_sha256', 'manifest_sha256',
                  'complete_evidence_sha256', 'recipe_sha256')
# Exact byte roles grant exceptions only to these already accepted artifacts.
# Weights are streamed solely through hashlib; no header or tensor is decoded.
_ROLE_SPECS = {
    'complete_evidence': (32 * 1024**2, 23087023,
        'e497186ff0eece324830731f8cada32ff5698fc8c25e143f0f8f1519061a12c3', '.json'),
    'selected_weights': (64 * 1024**2, 23294624,
        '3033608533114fc1d484aa37b2c8ccf492ada90b28bef9e0ef617aa467ec8048', '.safetensors'),
    'baseline_weights': (64 * 1024**2, 23299672,
        '53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8', '.safetensors'),
}
_METADATA_SUFFIXES = {'.json', '.toml', '.py', '.ps1', '.md', '.txt', '.log', '.xml',
    '.lock', '.cmd', '.bat', '.ini', '.cfg', '.yaml', '.yml', '.sha256'}
_METADATA_NAMES = {'.gitattributes', '.gitignore', '.python-version',
                   'pre-commit', 'pre-merge-commit'}


def _source_identities(value):
    if (type(value.fixture_git_commit) is not str
            or len(value.fixture_git_commit) not in (40, 64)
            or any(c not in '0123456789abcdef' for c in value.fixture_git_commit)
            or type(value.fixture_git_dirty) is not bool
            or value.historical_case_id != HISTORICAL_CASE_ID
            or value.historical_git_commit != HISTORICAL_SOURCE['git_commit']
            or value.historical_source_sha256 != HISTORICAL_SOURCE['source_sha256']
            or value.historical_git_dirty is not True):
        raise ValueError('distinct exact historical and current source identities required')


_read_origin_file = R._read_origin_file


def _route_contract(route, plan, context):
    """Dispatch the actual typed route, then bind all ordered route metadata."""
    _only_plan(plan)
    if type(route) is not Cho51WorkerRoute or type(route._full_route) is not ChoFirstTrancheRoute:
        raise ValueError('actual adopted worker route and canonical full route required')
    full = route._full_route
    subjects = tuple(f'subject_{i:02d}' for i in range(1, 53))
    methods = ('labram_linear', 'labram_lora', 'labram_full', 'eegnet')
    expected = tuple(CasePlan('cho2017', subject, method, 5, seed, 1)
        for subject in subjects for method in methods for seed in L.SEEDS)
    retained = tuple(p for p in expected if p.target_subject != 'subject_01')
    if (type(full.plans) is not tuple or full.plans != expected
            or any(type(p) is not CasePlan for p in full.plans)
            or route.plans != retained or len(route.plans) != 1020
            or set(route.plans) != set(context.adopted_plans)
            or route.contract.owner_decision_sha256 != context.owner_decision_sha256
            or set(full.selection_records_json) != set(subjects)
            or set(full.episode_records_json) != set(subjects)):
        raise ValueError('ordered full1040/adopted1020 worker route differs')
    decisions = tuple(PLANNER._json(PLANNER._bytes(L.ROOT, name)) for name in (
        'evidence/cho51-adoption-route-20261013/owner/adoption.json',
        'evidence/cho51-adoption-route-20261013/owner/accepted-proposal.json',
        'evidence/phase2-readiness-20261012/worker/roster.json'))
    rebuilt = PLANNER.prepare_route_contract((*decisions, PROTOCOL, CasePlan), full.catalogs)
    if (route.contract.plans != rebuilt.plans or route.contract.catalogs != rebuilt.catalogs
            or not isinstance(route.contract.selections, Mapping)
            or dict(route.contract.selections) != dict(rebuilt.selections)
            or not isinstance(route.contract.method_config_sha256, Mapping)
            or dict(route.contract.method_config_sha256) != dict(rebuilt.method_config_sha256)
            or route.contract.owner_decision_sha256 != rebuilt.owner_decision_sha256):
        raise ValueError('all five declared adopted route contract fields must match independent rederivation')
    inputs = route.inputs_for(plan)
    if type(inputs) is not ChoCaseInputs or inputs.plan != plan or inputs.profile != 'cho_profile_b_60hz_v1':
        raise ValueError('actual worker dispatch must return canonical typed linear inputs')
    contract = TARGET.prepare_target_contract(plan=plan, protocol_config=inputs.protocol_config,
        catalogs=inputs.catalogs, selection_record=inputs.selection_record,
        episode_record=inputs.episode_record, assets=inputs.assets)
    route_digest = config_digest(dict(plans=[asdict(p) for p in full.plans],
        adopted_case_ids=[p.case_id for p in route.plans],
        owner_decision_sha256=route.contract.owner_decision_sha256,
        method_config_sha256=dict(rebuilt.method_config_sha256),
        catalogs=[asdict(c) for c in full.catalogs],
        assets={subject: asdict(asset) for subject, asset in full.labram_assets.items()},
        protocol_config=inputs.protocol_config, target_contract=contract))
    return contract, route_digest


def validate_target_metrics(value, target_contract):
    """Recompute the accepted two wrong predictions without tensor operations."""
    keys = {'query_logits', 'query_targets', 'query_predictions', 'confusion_matrix',
            'balanced_accuracy', 'query_count', 'correct_query_predictions',
            'scientific_predictive_performance_qualified'}
    if type(value) is not dict or set(value) != keys:
        raise ValueError('exact accepted target metrics required')
    logits, targets = value['query_logits'], value['query_targets']
    if (type(logits) is not list or len(logits) != 2
            or any(type(row) is not list or len(row) != 2 for row in logits)
            or any(type(x) not in (int, float) or not math.isfinite(x) for row in logits for x in row)
            or type(targets) is not list or targets != target_contract['query_labels']
            or any(type(x) is not int or x not in (0, 1) for x in targets)):
        raise ValueError('finite two-class logits and exact independent query labels required')
    predictions = [0 if row[0] >= row[1] else 1 for row in logits]
    confusion = [[0, 0], [0, 0]]
    for target, prediction in zip(targets, predictions, strict=True):
        confusion[target][prediction] += 1
    if any(sum(row) == 0 for row in confusion):
        raise ValueError('both query classes must be present')
    rational = sum((Fraction(row[i], sum(row)) for i, row in enumerate(confusion)), Fraction()) / 2
    expected = dict(query_logits=logits, query_targets=targets, query_predictions=predictions,
        confusion_matrix=confusion, balanced_accuracy=[rational.numerator, rational.denominator], query_count=2,
        correct_query_predictions=0, scientific_predictive_performance_qualified=False)
    if (L._encoded(value) != L._encoded(expected) or predictions != [1, 0]
            or targets != [0, 1] or confusion != [[0, 1], [1, 0]] or rational != 0):
        raise ValueError('accepted historical target metrics must preserve exact zero-of-two result')
    return config_digest(expected)


def _check_route(route, request, context, origin_contract):
    contract, digest = _route_contract(route, request.plan, context)
    summary = origin_contract['summary']
    if (digest != request.worker_route_sha256 or digest != summary.get('worker_route_sha256')
            or L._encoded(contract) != L._encoded(summary.get('target_contract'))
            or config_digest(contract) != request.target_contract_sha256
            or L._encoded({s: asdict(a) for s, a in route.labram_assets.items()})
                != L._encoded(summary.get('target_assets'))):
        raise ValueError('worker dispatch, assets or reconstructed target contract differs from accepted origin')
    payload = summary.get('target_profile_binding')
    if type(payload) is not dict or set(payload) != {f.name for f in fields(TARGET.ChoProfileBinding60Hz)}:
        raise ValueError('exact accepted target Profile B binding required')
    values = dict(payload)
    for name in ('classes', 'channel_names', 'support_trial_ids', 'query_trial_ids',
                 'support_profile_b_rows', 'query_profile_b_rows'):
        if type(values[name]) is not list:
            raise ValueError('canonical serialized binding arrays required')
        values[name] = tuple(values[name])
    binding = TARGET.ChoProfileBinding60Hz(**values)
    TARGET.validate_binding(binding, contract, route.catalogs[1], route.labram_assets['subject_02'])
    if binding.sha256 != request.target_profile_binding_sha256:
        raise ValueError('accepted Profile B binding digest differs')
    return digest


def _request_values(plan, context, workspace, origin_contract_path, origin_contract_file_sha256,
                    summary, claim_file_sha256='0' * 64):
    return dict(plan=plan, fixture_root=context.fixture_root, recorder_root=context.recorder_root,
        workspace=workspace, pins_path=context.pins_path, independent_pins_sha256=context.independent_pins_sha256,
        execution_source_sha256=context.execution_source_sha256, owner_decision_sha256=context.owner_decision_sha256,
        claim_path=context.recorder_root / 'claims' / (plan.case_id + '.attempt1.claim.json'),
        claim_file_sha256=claim_file_sha256, fixture_source_sha256=context.fixture_source.source_sha256,
        environment_sha256=context.environment_sha256, origin_contract_path=origin_contract_path,
        origin_contract_file_sha256=origin_contract_file_sha256, fixture_git_commit=context.fixture_source.git_commit,
        fixture_git_dirty=context.fixture_source.git_dirty, worker_route_sha256=summary['worker_route_sha256'],
        **{name: summary[name] for name in _TARGET_DIGESTS})

def _only_plan(plan):
    L._plan(plan)
    if plan != CasePlan('cho2017', 'subject_02', 'labram_linear', 5, 11, 1):
        raise ValueError('only adopted subject02 LaBraM linear seed11 five-shot engineering case admitted')


def _scope(value, *, attempt=False):
    integers = _INTS if attempt else {key: item for key, item in _INTS.items() if key != 'attempt'}
    if (any(type(getattr(value, key)) is not int or getattr(value, key) != item
            for key, item in integers.items())
            or any(getattr(value, key) is not item for key, item in _FLAGS.items())):
        raise ValueError('exact reused-source/restoration engineering scope required')


@dataclass(frozen=True, slots=True)
class WorkerRequest:
    plan: CasePlan
    fixture_root: Path
    recorder_root: Path
    workspace: Path
    pins_path: Path
    independent_pins_sha256: str
    execution_source_sha256: str
    owner_decision_sha256: str
    claim_path: Path
    claim_file_sha256: str
    fixture_source_sha256: str
    environment_sha256: str
    origin_contract_path: Path
    origin_contract_file_sha256: str
    fixture_git_commit: str
    fixture_git_dirty: bool
    worker_route_sha256: str
    target_contract_sha256: str
    target_witness_file_sha256: str
    target_result_file_sha256: str
    target_qualification_file_sha256: str
    target_native_receipt_file_sha256: str
    target_final_review_file_sha256: str
    target_profile_binding_sha256: str
    target_source_state_sha256: str
    target_adapted_state_sha256: str
    target_metrics_sha256: str
    historical_case_id: str = HISTORICAL_CASE_ID
    historical_git_commit: str = HISTORICAL_SOURCE['git_commit']
    historical_source_sha256: str = HISTORICAL_SOURCE['source_sha256']
    historical_git_dirty: bool = True
    attempt: int = 1
    historical_gradient_updates: int = 5253
    current_gradient_updates: int = 0
    historical_source_updates: int = 5151
    historical_support_updates: int = 102
    fold_count: int = 102
    final_source_subjects: int = 51
    restored_tensors: int = 223
    restored_elements: int = 5818138
    head_parameters: int = 402
    historical_restore_count: int = 2
    current_restore_count: int = 0
    current_target_inference_calls: int = 0
    measured_cells: int = 0
    original_case_attempts_remaining: int = 0
    prior_target_support_updates: int = 1
    prior_target_restore_count: int = 1
    prior_target_inference_calls: int = 1
    prior_target_query_count: int = 2
    current_source_updates: int = 0
    current_support_updates: int = 0
    source_work_reused: bool = True
    restore_work_reused: bool = True
    engineering_only: bool = True
    scientific_admission: bool = False
    original_scientific_case_qualified: bool = False
    historical_publication_qualified: bool = True
    historical_detached_restoration_qualified: bool = True
    staged_two_root_provenance: bool = True
    unchanged_single_root_factory_verified: bool = False
    prior_target_work_reused: bool = True
    prior_target_route_qualified: bool = True
    unchanged_canonical_worker_verified: bool = False
    full_worker_verified: bool = False

    def __post_init__(self):
        _only_plan(self.plan)
        _scope(self, attempt=True)
        _source_identities(self)
        for name in _PATHS:
            L._path(getattr(self, name), name)
        for item in fields(self):
            if item.name.endswith('sha256'):
                L._sha(getattr(self, item.name), item.name)
        if (self.execution_source_sha256 != L.CANONICAL_SOURCE_SHA256
                or self.fixture_source_sha256 == self.execution_source_sha256
                or self.recorder_root != self.fixture_root / 'runs/phase2/lifecycle'
                or self.claim_path != self.recorder_root / 'claims' / (self.plan.case_id + '.attempt1.claim.json')
                or self.workspace.name != self.plan.case_id
                or self.workspace.is_relative_to(self.fixture_root)
                or self.pins_path.is_relative_to(self.fixture_root)
                or self.origin_contract_path.is_relative_to(self.fixture_root)
                or self.origin_contract_path.is_relative_to(self.workspace.parent.parent)):
            raise ValueError('fresh staged request paths and independently pinned origin differ')

    def payload(self):
        value = asdict(self)
        for name in _PATHS:
            value[name] = str(getattr(self, name))
        return dict(schema='cho51_linear_worker_request_v1', case_id=self.plan.case_id, **value)

    @property
    def sha256(self):
        return hashlib.sha256(L._encoded(self.payload())).hexdigest()


def load_worker_request(payload):
    expected = {item.name for item in fields(WorkerRequest)} | {'schema', 'case_id'}
    if (type(payload) is not dict or set(payload) != expected
            or payload.get('schema') != 'cho51_linear_worker_request_v1'):
        raise ValueError('exact staged request schema required')
    values = {key: payload[key] for key in expected - {'schema', 'case_id'}}
    if type(values['plan']) is not dict or set(values['plan']) != {item.name for item in fields(CasePlan)}:
        raise ValueError('exact serialized adopted plan required')
    values['plan'] = CasePlan(**values['plan'])
    for name in _PATHS:
        if type(values[name]) is not str:
            raise ValueError('serialized absolute path string required')
        values[name] = Path(values[name])
    result = WorkerRequest(**values)
    if result.payload() != payload:
        raise ValueError('staged request differs from exact typed reconstruction')
    return result


@dataclass(frozen=True, slots=True)
class VerifiedWorkerProof:
    request_sha256: str
    case_id: str
    claim_file_sha256: str
    execution_source_sha256: str
    independent_pins_sha256: str
    owner_decision_sha256: str
    environment_sha256: str
    origin_contract_file_sha256: str
    fixture_source_sha256: str
    fixture_git_commit: str
    fixture_git_dirty: bool
    historical_case_id: str
    historical_git_commit: str
    historical_source_sha256: str
    historical_git_dirty: bool
    worker_route_sha256: str
    verified_origin_files: int
    selected_state_sha256: str
    weights_file_sha256: str
    manifest_sha256: str
    complete_evidence_sha256: str
    recipe_sha256: str
    target_contract_sha256: str
    target_witness_file_sha256: str
    target_result_file_sha256: str
    target_qualification_file_sha256: str
    target_native_receipt_file_sha256: str
    target_final_review_file_sha256: str
    target_profile_binding_sha256: str
    target_source_state_sha256: str
    target_adapted_state_sha256: str
    target_metrics_sha256: str
    historical_gradient_updates: int = 5253
    current_gradient_updates: int = 0
    historical_source_updates: int = 5151
    historical_support_updates: int = 102
    fold_count: int = 102
    final_source_subjects: int = 51
    restored_tensors: int = 223
    restored_elements: int = 5818138
    head_parameters: int = 402
    historical_restore_count: int = 2
    current_restore_count: int = 0
    current_target_inference_calls: int = 0
    measured_cells: int = 0
    original_case_attempts_remaining: int = 0
    prior_target_support_updates: int = 1
    prior_target_restore_count: int = 1
    prior_target_inference_calls: int = 1
    prior_target_query_count: int = 2
    current_source_updates: int = 0
    current_support_updates: int = 0
    source_work_reused: bool = True
    restore_work_reused: bool = True
    engineering_only: bool = True
    scientific_admission: bool = False
    original_scientific_case_qualified: bool = False
    historical_publication_qualified: bool = True
    historical_detached_restoration_qualified: bool = True
    staged_two_root_provenance: bool = True
    unchanged_single_root_factory_verified: bool = False
    prior_target_work_reused: bool = True
    prior_target_route_qualified: bool = True
    unchanged_canonical_worker_verified: bool = False
    full_worker_verified: bool = False

    def __post_init__(self):
        _scope(self)
        _source_identities(self)
        for item in fields(self):
            if item.name.endswith('sha256') or item.name == 'case_id':
                L._sha(getattr(self, item.name), item.name)
        if type(self.verified_origin_files) is not int or self.verified_origin_files <= 0:
            raise ValueError('positive physically verified origin file count required')


@dataclass(frozen=True, slots=True)
class WorkerCompletion:
    request: WorkerRequest
    proof: VerifiedWorkerProof
    request_path: Path
    attestation_path: Path
    attestation_file_sha256: str
    engineering_receipt: Path


def _origin_assets(request):
    raw, identity = L._read(request.origin_contract_path, request.origin_contract_file_sha256)
    contract = json.loads(raw)
    if (type(contract) is not dict or set(contract) != {'schema', 'files', 'roles', 'summary'}
            or contract.get('schema') != 'cho51_linear_worker_origin_contract_v1'
            or raw != L._encoded(contract) or type(contract.get('files')) is not dict
            or not contract['files'] or type(contract.get('roles')) is not dict
            or set(contract['roles']) != set(contract['files'])
            or type(contract.get('summary')) is not dict):
        raise ValueError('exact canonical pinned origin contract required')
    summary = contract['summary']
    for key, value in {**{k: v for k, v in _INTS.items() if k != 'attempt'}, **_FLAGS}.items():
        if type(summary.get(key)) is not type(value) or summary[key] != value:
            raise ValueError('origin summary differs from exact engineering reuse scope')
    if (type(summary.get('restore_limits')) is not list
            or len(summary['restore_limits']) != 2
            or any(type(value) is not int or value != 64 * 1024**2 for value in summary['restore_limits'])):
        raise ValueError('both accepted historical restores must use explicit 64-MiB bounds')
    if (summary.get('historical_case_id') != request.historical_case_id
            or summary.get('historical_source') != HISTORICAL_SOURCE
            or type(summary.get('historical_source')) is not dict
            or type(summary['historical_source'].get('git_dirty')) is not bool
            or type(summary.get('historical_plan')) is not dict
            or summary['historical_plan'] != asdict(request.plan)
            or any(type(summary['historical_plan'][key]) is not type(value)
                for key, value in asdict(request.plan).items())):
        raise ValueError('historical source identity and adopted plan must remain recorded history')
    for name in _PROOF_DIGESTS:
        L._sha(summary.get(name), name)
    for name in (*_TARGET_DIGESTS, 'worker_route_sha256'):
        L._sha(summary.get(name), name)
        if summary[name] != getattr(request, name):
            raise ValueError('accepted target or route pin differs from current request')
    if (type(summary.get('target_contract')) is not dict
            or config_digest(summary['target_contract']) != request.target_contract_sha256
            or validate_target_metrics(summary.get('target_metrics'), summary['target_contract'])
                != request.target_metrics_sha256
            or type(summary.get('target_profile_binding')) is not dict
            or config_digest(summary['target_profile_binding']) != request.target_profile_binding_sha256
            or request.target_source_state_sha256 != TARGET.SELECTED_STATE_SHA256
            or summary['selected_state_sha256'] != request.target_source_state_sha256
            or request.target_adapted_state_sha256
                != '5bd88f2afb0a2e667e3576bb82c037e3314cce0e8cfb4383ee7439fee57787dd'):
        raise ValueError('accepted target contract, state, binding or metrics differs')
    proof_paths = summary.get('target_proof_paths')
    if type(proof_paths) is not dict or set(proof_paths) != set(_TARGET_FILE_DIGESTS):
        raise ValueError('all five exact accepted target physical proof paths required')
    for name, value in proof_paths.items():
        if (type(value) is not str or contract['files'].get(value) != getattr(request, name)
                or contract['roles'].get(value) != 'metadata'):
            raise ValueError('accepted target proof file must be independently metadata-pinned')
    result = {request.origin_contract_path: identity}
    for name, digest in contract['files'].items():
        if type(name) is not str:
            raise ValueError('absolute origin file strings required')
        path = Path(name)
        L._path(path, 'origin file')
        L._sha(digest, 'origin file pin')
        if (str(path) != name or path == request.origin_contract_path
                or path.is_relative_to(request.workspace.parent.parent)
                or path.is_relative_to(request.fixture_root)):
            raise ValueError('origin files must remain outside the fresh recorder output')
        result[path] = _read_origin_file(path, digest, contract['roles'][name])
    if (not set(_ROLE_SPECS).issubset(set(contract['roles'].values()))
            or not any(contract['roles'][name] == 'selected_weights'
                and digest == summary['weights_file_sha256']
                for name, digest in contract['files'].items())):
        raise ValueError('selected weights, baseline and complete evidence need their exact physical roles')
    witness = json.loads(L._read(Path(proof_paths['target_witness_file_sha256']),
        request.target_witness_file_sha256)[0])
    if (type(witness) is not dict or witness.get('schema') != 'cho51-linear-target-route-engineering-v1'
            or witness.get('accepted') is not True or witness.get('engineering_only') is not True
            or witness.get('scientific_admission') is not False
            or type(witness.get('measured_cells')) is not int or witness['measured_cells'] != 0
            or L._encoded(witness.get('contract')) != L._encoded(summary['target_contract'])
            or L._encoded(witness.get('profile_binding')) != L._encoded(summary['target_profile_binding'])
            or witness.get('profile_binding_sha256') != request.target_profile_binding_sha256
            or witness.get('source_state_sha256') != request.target_source_state_sha256
            or witness.get('witnesses', {}).get('adapted_state_sha256') != request.target_adapted_state_sha256
            or any(L._encoded(witness.get(k)) != L._encoded(summary['target_metrics'][k])
                for k in ('query_logits', 'query_targets', 'confusion_matrix', 'balanced_accuracy', 'query_count'))
            or any(type(witness.get(k)) is not int or witness[k] != v for k, v in
                dict(source_updates=0, support_updates=1, gradient_updates=1,
                     current_restore_callback_calls=1, target_inference_calls=1, record_cell_calls=0).items())):
        raise ValueError('accepted target witness no longer matches bound worker reuse scope')
    return contract, result


def _verify_proof(request, proof):
    if type(proof) is not VerifiedWorkerProof:
        raise ValueError('exact immutable staged reuse proof required')
    proof.__post_init__()
    if (proof.request_sha256 != request.sha256 or proof.case_id != request.plan.case_id
            or any(getattr(proof, key) != getattr(request, key) for key in _BINDINGS)):
        raise ValueError('staged proof differs from fresh request, claim, pins or origin')
    contract, identities = _origin_assets(request)
    if (proof.verified_origin_files != len(contract['files'])
            or any(getattr(proof, name) != contract['summary'][name] for name in _PROOF_DIGESTS)):
        raise ValueError('staged proof differs from physical origin assets or selected state')
    return identities


def _claim(path, plan, context):
    raw, identity = L._read(path)
    claim = json.loads(raw)
    payload = claim.get('payload') if type(claim) is dict else None
    if (type(payload) is not dict or set(payload) != {
            'purpose', 'case', 'worker', 'attempt', 'environment_sha256', 'source', 'engineering_only'}
            or payload.get('purpose') != 'pilot_case_claim'
            or payload.get('case') != asdict(plan) or type(payload.get('attempt')) is not int or payload['attempt'] != 1
            or payload.get('worker') != WORKER or payload.get('source') != asdict(context.fixture_source)
            or payload.get('environment_sha256') != context.environment_sha256
            or payload.get('engineering_only') is not True
            or not L.verify_envelope(claim, kind='engineering_smoke', expected_payload=payload)
            or raw != L._encoded(claim)):
        raise ValueError('fresh staged engineering claim no longer verifies')
    source_sha = payload['source'].get('source_sha256')
    L._sha(source_sha, 'fixture claim source')
    return identity, source_sha


def _request_context(request, context):
    if (request.fixture_root != context.fixture_root or request.recorder_root != context.recorder_root
            or request.fixture_source_sha256 != context.fixture_source.source_sha256
            or request.fixture_git_commit != context.fixture_source.git_commit
            or request.fixture_git_dirty is not context.fixture_source.git_dirty
            or request.workspace != context.parent_output / 'cases' / request.plan.case_id
            or any(getattr(request, key) != getattr(context, key) for key in (
                'pins_path', 'independent_pins_sha256', 'execution_source_sha256',
                'owner_decision_sha256', 'environment_sha256'))):
        raise ValueError('staged request differs from independently current context')


def _attestation(request, proof):
    return dict(schema='cho51_linear_worker_attestation_v1', request_sha256=request.sha256,
        case_id=request.plan.case_id, claim_file_sha256=request.claim_file_sha256,
        proof=asdict(proof), source_work_reused=True, restore_work_reused=True,
        historical_gradient_updates=5253, current_gradient_updates=0,
        engineering_only=True, scientific_admission=False, measured_cells=0,
        original_scientific_case_qualified=False, original_case_attempts_remaining=0,
        staged_two_root_provenance=True, unchanged_single_root_factory_verified=False,
        historical_publication_qualified=True, historical_detached_restoration_qualified=True,
    prior_target_work_reused=True, prior_target_route_qualified=True,
    unchanged_canonical_worker_verified=False, full_worker_verified=False)


def run_worker_case(recorder, plan, *, context, route, workspace, origin_contract_path,
        origin_contract_file_sha256, backend, verifier):
    """Claim once and qualify metadata under the real identity lock; no fitting."""
    _only_plan(plan)
    pins_identity = L._context_check(context, recorder, plan)
    L._path(workspace, 'unused staged case workspace')
    L._future_direct(workspace)
    L._path(origin_contract_path, 'independent origin contract')
    L._sha(origin_contract_file_sha256, 'independent origin contract pin')
    if (workspace != context.parent_output / 'cases' / plan.case_id or workspace.exists()
            or workspace.is_symlink() or origin_contract_path.is_relative_to(context.parent_output)
            or not callable(backend) or not callable(verifier)):
        raise ValueError('unused staged workspace and independent metadata callbacks required')
    # Reject malformed/drifting origins before consuming a fresh claim.
    initial = json.loads(L._read(origin_contract_path, origin_contract_file_sha256)[0])
    if type(initial) is not dict or type(initial.get('summary')) is not dict:
        raise ValueError('independently pinned worker origin summary required')
    preview = WorkerRequest(**_request_values(plan, context, workspace, origin_contract_path,
        origin_contract_file_sha256, initial['summary']))
    origin_contract, origin_identity = _origin_assets(preview)
    _check_route(route, preview, context, origin_contract)
    request_path, attestation = workspace / 'request.json', workspace / 'parent-attestation.json'
    with recorder.case_session(plan) as locked:
        claim_path = locked.claim_new(worker=WORKER, attempt=1)
        request = None
        try:
            claim_identity, fixture_source_sha = _claim(claim_path, plan, context)
            request = WorkerRequest(**_request_values(plan, context, workspace, origin_contract_path,
                origin_contract_file_sha256, initial['summary'], claim_identity[-1]))
            if _origin_assets(request)[1] != origin_identity:
                raise ValueError('origin changed while obtaining fresh recorder claim')
            workspace.mkdir(parents=True, exist_ok=False)
            if L._write_json_once(request_path, request.payload()) != request.sha256:
                raise ValueError('durable staged request differs')
            request_identity = L._read(request_path, request.sha256)[1]
            opaque = backend(request, request_path, request.sha256)
            proof = verifier(request, opaque)
            proof_identities = _verify_proof(request, proof)

            def stable():
                if (L._context_check(context, recorder, plan) != pins_identity
                        or _claim(claim_path, plan, context)[0] != claim_identity
                        or L._read(request_path, request.sha256)[1] != request_identity
                        or _origin_assets(request)[1] != origin_identity):
                    raise ValueError('staged claim, request, context or origin changed')
                _check_route(route, request, context, origin_contract)

            stable()
            if verifier(request, opaque) != proof or _verify_proof(request, proof) != proof_identities:
                raise ValueError('staged proof changed before durable attestation')
            stable()
            attested_sha = L._write_json_once(attestation, _attestation(request, proof))
            stable()
            if (L._read(attestation, attested_sha)[1][-1] != attested_sha
                    or _verify_proof(request, proof) != proof_identities):
                raise ValueError('durable staged proof changed before terminal publication')
            receipt = locked.record_engineering_success(attempt=1, attested_evidence_sha256=attested_sha)
            completion = recorder.completion((plan,))
            if completion['engineering_success'] != 1 or completion['measured'] != 0:
                raise ValueError('staged recorder terminal must remain engineering-only')
            return WorkerCompletion(request, proof, request_path, attestation, attested_sha, receipt)
        except BaseException as error:
            if L._accepted_artifact_exists(recorder, plan, attestation):
                raise RecoveryRequired('durable staged artifact exists; explicit external-digest recovery required') from error
            locked.record_failure(attempt=1, reason=dict(purpose='cho51_linear_worker_failure',
                error=type(error).__name__ + ': ' + str(error),
                request_sha256=None if request is None else request.sha256,
                current_gradient_updates=0, source_work_reused=True, restore_work_reused=True,
                engineering_only=True, scientific_admission=False,
                original_scientific_case_qualified=False, original_case_attempts_remaining=0,
    prior_target_support_updates=1, prior_target_restore_count=1,
    prior_target_inference_calls=1, prior_target_query_count=2,
    current_source_updates=0, current_support_updates=0))
            raise


def recover_worker_case(recorder, *, context, route, request_path, expected_request_sha256,
        expected_attestation_sha256, verifier):
    """Reverify origin and replay an existing engineering intent, without backend."""
    L._sha(expected_request_sha256, 'external staged request pin')
    L._sha(expected_attestation_sha256, 'external staged attestation pin')
    if not callable(verifier):
        raise ValueError('independent read-only origin verifier required')
    raw, request_identity = L._read(request_path, expected_request_sha256)
    request = load_worker_request(json.loads(raw))
    if raw != L._encoded(request.payload()) or request_path != request.workspace / 'request.json':
        raise ValueError('externally pinned staged request differs')
    _request_context(request, context)
    pins_identity = L._context_check(context, recorder, request.plan)
    origin_identity = _origin_assets(request)[1]
    origin_contract = _origin_assets(request)[0]
    _check_route(route, request, context, origin_contract)
    attestation = request.workspace / 'parent-attestation.json'
    raw_attestation, attestation_identity = L._read(attestation, expected_attestation_sha256)
    payload = json.loads(raw_attestation)
    if type(payload) is not dict or type(payload.get('proof')) is not dict:
        raise ValueError('exact externally pinned staged attestation required')
    proof = VerifiedWorkerProof(**payload['proof'])
    if (raw_attestation != L._encoded(payload)
            or config_digest(payload) != config_digest(_attestation(request, proof))):
        raise ValueError('externally pinned staged parent attestation differs')
    proof_identities = _verify_proof(request, proof)
    with recorder.case_session(request.plan) as locked:
        claim_identity = _claim(request.claim_path, request.plan, context)[0]
        if claim_identity[-1] != request.claim_file_sha256:
            raise ValueError('staged recovery claim differs from request')
        if verifier(request, proof) != proof:
            raise ValueError('independent origin reverification differs from durable staged proof')
        _check_route(route, request, context, origin_contract)
        if (L._context_check(context, recorder, request.plan) != pins_identity
                or _claim(request.claim_path, request.plan, context)[0] != claim_identity
                or L._read(request_path, expected_request_sha256)[1] != request_identity
                or L._read(attestation, expected_attestation_sha256)[1] != attestation_identity
                or _origin_assets(request)[1] != origin_identity
                or _verify_proof(request, proof) != proof_identities):
            raise ValueError('staged recovery inputs changed before locked terminal replay')
        return locked.recover_engineering_success(expected_attested_evidence_sha256=expected_attestation_sha256)
