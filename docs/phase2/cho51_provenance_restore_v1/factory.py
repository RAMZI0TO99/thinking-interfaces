"""Explicit historical producer/current executor restoration, engineering only.

The admitted pins authenticate the two roles independently. Every store read has
an explicit byte bound and stable regular-file identity. Numerical imports and
strict restoration occur only inside ``restore`` under the caller's live lock.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import stat
import sys
from dataclasses import asdict, dataclass, fields
from importlib.metadata import version
from pathlib import Path

from core.config import config_digest
from core.provenance import capture_source
from evaluation.phase2_records import verify_envelope

MAXIMUM_JSON = 8 * 1024**2
MAXIMUM_EVIDENCE = 32 * 1024**2
MAXIMUM_WEIGHTS = 64 * 1024**2
MAXIMUM_RUNTIME = 2 * 1024**3
SCHEMA = 'cho51_provenance_restore_request_v1'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(value, label):
    _need(type(value) is str and len(value) == 64
        and all(character in '0123456789abcdef' for character in value), label + ' digest required')
    return value


def _object(value):
    def unique(rows):
        result = {}
        for name, member in rows:
            _need(name not in result, 'duplicate JSON key')
            result[name] = member
        return result
    result = json.loads(value, object_pairs_hook=unique,
        parse_constant=lambda member: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    _need(type(result) is dict, 'plain JSON object required')
    return result


def _json_field(value):
    _need(type(value) is str, 'immutable canonical JSON text required')
    result = _object(value)
    _need(canonical(result) == value, 'canonical finite JSON text required')
    return result


def _source(value):
    result = _json_field(value)
    _need(set(result) == {'git_commit', 'source_sha256', 'git_dirty'}
        and type(result['git_commit']) is str and len(result['git_commit']) in (40, 64)
        and all(character in '0123456789abcdef' for character in result['git_commit'])
        and type(result['git_dirty']) is bool, 'explicit real Git producer/executor identity required')
    _sha(result['source_sha256'], 'source')
    return result


def _absolute(value):
    _need(type(value) is str and value and Path(value).is_absolute()
        and str(Path(value).absolute()) == value, 'normalized absolute path required')
    return Path(value)


def _identity(path, *, runtime_binary=False, expected_sha256=None):
    _need(path.resolve(strict=True) == path.absolute() and not path.is_symlink(),
        'direct non-alias path required')
    for ancestor in (path, *path.parents):
        observed = ancestor.lstat()
        _need(not stat.S_ISLNK(observed.st_mode)
            and not getattr(observed, 'st_file_attributes', 0) & 1024,
            'reparse or symlink file ancestor refused')
    observed = path.stat()
    git_exception = (runtime_binary is True
        and path == Path('C:/Users/aladdin-alyanai/AppData/Local/Programs/Git/cmd/git.exe')
        and expected_sha256 == 'da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f'
        and observed.st_nlink == 2 and observed.st_size == 46480)
    _need(stat.S_ISREG(observed.st_mode) and (observed.st_nlink == 1 or git_exception),
        'single-link regular file required')
    return (observed.st_dev, observed.st_ino, observed.st_size,
        observed.st_mtime_ns, observed.st_ctime_ns)


def read_pinned(path, sha256, maximum_bytes, *, retain=True, runtime_binary=False):
    """Bound every read on the same descriptor; hash bytes before returning them."""
    _sha(sha256, 'physical file')
    _need(isinstance(path, Path) and path.is_absolute() and type(maximum_bytes) is int
        and 0 < maximum_bytes <= MAXIMUM_RUNTIME and type(retain) is bool
        and type(runtime_binary) is bool,
        'explicit finite physical file bound required')
    before = _identity(path, runtime_binary=runtime_binary, expected_sha256=sha256)
    expected_links = path.stat().st_nlink
    _need(0 < before[2] <= maximum_bytes, 'physical file exceeds its byte bound')
    digest = hashlib.sha256()
    pieces = []
    total = 0
    with path.open('rb') as stream:
        observed = os.fstat(stream.fileno())
        opened = (observed.st_dev, observed.st_ino, observed.st_size,
            observed.st_mtime_ns, observed.st_ctime_ns)
        _need(opened[:4] == before[:4] and observed.st_nlink == expected_links
            and stat.S_ISREG(observed.st_mode), 'descriptor differs from pinned regular file')
        while True:
            chunk = stream.read(min(1024**2, maximum_bytes + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            _need(total <= maximum_bytes, 'physical file grew beyond its byte bound')
            digest.update(chunk)
            if retain:
                pieces.append(chunk)
        observed = os.fstat(stream.fileno())
        finished = (observed.st_dev, observed.st_ino, observed.st_size,
            observed.st_mtime_ns, observed.st_ctime_ns)
        _need(observed.st_nlink == expected_links and stat.S_ISREG(observed.st_mode),
            'descriptor ceased to be a single-link regular file')
    _need(opened == finished and before == _identity(path, runtime_binary=runtime_binary,
            expected_sha256=sha256) and total == before[2]
        and digest.hexdigest() == sha256, 'physical file changed or digest differs')
    return (b''.join(pieces) if retain else None), before


def _document(path, sha256, maximum_bytes=MAXIMUM_JSON):
    raw, identity = read_pinned(path, sha256, maximum_bytes)
    value = _object(raw)
    _need(raw in (canonical(value).encode(), (canonical(value) + '\n').encode()),
        'physical metadata must be finite canonical JSON')
    return value, identity


@dataclass(frozen=True, slots=True)
class HistoricalProducer:
    source_json: str
    manifest_sha256: str
    manifest_file_sha256: str
    evidence_sha256: str
    evidence_file_sha256: str
    weights_sha256: str
    model_state_sha256: str
    model_recipe_sha256: str
    selection_contract_sha256: str
    selected_candidate: str
    publication_path: str
    publication_file_sha256: str

    def __post_init__(self):
        _source(self.source_json)
        for field in fields(self):
            if field.name.endswith('sha256'):
                _sha(getattr(self, field.name), field.name)
        _need(type(self.selected_candidate) is str and bool(self.selected_candidate.strip()),
            'explicit selected candidate required')
        _absolute(self.publication_path)


@dataclass(frozen=True, slots=True)
class ExecutorContext:
    root: str
    source_json: str
    runtime_json: str
    source_files_json: str
    runtime_files_json: str

    def __post_init__(self):
        root = _absolute(self.root)
        _source(self.source_json)
        runtime = _json_field(self.runtime_json)
        _need(set(runtime) == {'python_full', 'python', 'executable', 'torch', 'numpy', 'braindecode'}
            and all(type(member) is str and member for member in runtime.values()),
            'exact independent current runtime declaration required')
        _absolute(runtime['executable'])
        for name in ('source_files_json', 'runtime_files_json'):
            pinned = _json_field(getattr(self, name))
            _need(bool(pinned), 'nonempty independently pinned file inventory required')
            for path, digest in pinned.items():
                member = _absolute(path)
                _sha(digest, 'executor file')
                if name == 'source_files_json':
                    _need(member.is_relative_to(root), 'executor source file outside root')


@dataclass(frozen=True, slots=True)
class RestoreRequest:
    producer: HistoricalProducer
    executor: ExecutorContext
    plan_json: str
    store_root: str
    workspace: str
    claim_path: str
    claim_sha256: str
    pins_path: str
    pins_sha256: str
    method_config_sha256: str
    protocol_config_sha256: str

    def __post_init__(self):
        _need(type(self.producer) is HistoricalProducer and type(self.executor) is ExecutorContext,
            'exact independent producer and executor types required')
        self.producer.__post_init__()
        self.executor.__post_init__()
        plan = _json_field(self.plan_json)
        _need(set(plan) == {'dataset', 'target_subject', 'method', 'shots_per_class', 'model_seed', 'repetition'}
            and plan['dataset'] == 'cho2017' and plan['method'] == 'labram_linear'
            and plan['target_subject'] in {f'subject_{number:02d}' for number in range(2, 53)}
            and type(plan['shots_per_class']) is int and plan['shots_per_class'] == 5
            and type(plan['model_seed']) is int and plan['model_seed'] in (11, 23, 37, 53, 71)
            and type(plan['repetition']) is int and plan['repetition'] == 1,
            'adopted linear Cho five-shot case required')
        root = Path(self.executor.root)
        for name in ('store_root', 'workspace', 'claim_path', 'pins_path'):
            _need(_absolute(getattr(self, name)).is_relative_to(root), 'request path outside executor project')
        _need(Path(self.store_root) != root and Path(self.workspace) != root
            and Path(self.workspace) != Path(self.store_root)
            and not Path(self.workspace).is_relative_to(Path(self.store_root))
            and not Path(self.store_root).is_relative_to(Path(self.workspace)),
            'distinct owned workspace and historical store required')
        for name in ('claim_sha256', 'pins_sha256', 'method_config_sha256', 'protocol_config_sha256'):
            _sha(getattr(self, name), name)

    def payload(self):
        return dict(schema=SCHEMA, **asdict(self), engineering_only=True,
            scientific_admission=False, maximum_weights_bytes=MAXIMUM_WEIGHTS,
            expected_counts=dict(source_updates=0, support_updates=0, query_calls=0,
                selected_restores=1, measured_cells=0))

    @property
    def sha256(self):
        return hashlib.sha256(canonical(self.payload()).encode()).hexdigest()


def load_request(value):
    _need(type(value) is dict and value.get('schema') == SCHEMA, 'exact factory request schema required')
    members = {field.name: value[field.name] for field in fields(RestoreRequest)}
    members['producer'] = HistoricalProducer(**members['producer'])
    members['executor'] = ExecutorContext(**members['executor'])
    result = RestoreRequest(**members)
    _need(canonical(result.payload()) == canonical(value), 'exact immutable factory request fields required')
    return result


@dataclass(frozen=True, slots=True)
class AuthenticatedSelection:
    manifest_json: str
    evidence_json: str
    manifest_identity: tuple
    evidence_identity: tuple
    weights_identity: tuple
    publication_identity: tuple


@dataclass(frozen=True, slots=True)
class RestoredSource:
    adapter: object
    model: object
    witness: dict


class ProvenanceRestoreFactory:
    def __init__(self, request, request_path, request_file_sha256, assert_live_lock):
        _need(type(request) is RestoreRequest and isinstance(request_path, Path)
            and callable(assert_live_lock), 'typed restoration request and live identity lock required')
        request.__post_init__()
        _sha(request_file_sha256, 'durable request')
        _need(request_file_sha256 == request.sha256 and request_path.parent == Path(request.workspace),
            'current request digest and owned workspace required')
        from evaluation.phase2_runner import LockedCase
        _need(type(getattr(assert_live_lock, '__self__', None)) is LockedCase
            and getattr(assert_live_lock, '__func__', None) is LockedCase._require_active,
            'actual canonical LockedCase._require_active bound method required')
        self.request = request
        self.request_path = request_path
        self.request_file_sha256 = request_file_sha256
        self.assert_live_lock = assert_live_lock
        self._used = False
        self._attempt_pin = None

    def _current(self):
        request = self.request
        request.__post_init__()
        _need(self.assert_live_lock() is not False, 'current CaseRecorder identity lock lost')
        raw, _ = read_pinned(self.request_path, self.request_file_sha256, MAXIMUM_JSON)
        _need(raw == canonical(request.payload()).encode(), 'durable current request differs')
        if self._attempt_pin is not None:
            attempt_sha256, attempt_identity = self._attempt_pin
            _, observed_identity = read_pinned(Path(request.workspace) / 'restore-attempt.json',
                attempt_sha256, MAXIMUM_JSON, retain=False)
            _need(observed_identity == attempt_identity, 'durable restoration attempt changed')
        pins, _ = _document(Path(request.pins_path), request.pins_sha256)
        _need(pins.get('factory_producer') == asdict(request.producer)
            and pins.get('factory_executor') == asdict(request.executor),
            'request producer/executor differs from independently admitted pins')
        from evaluation.phase2_runner import CaseRecorder, LockedCase, environment_digest
        session = self.assert_live_lock.__self__
        _need(type(session) is LockedCase and type(session._recorder) is CaseRecorder
            and asdict(session.plan) == _json_field(request.plan_json),
            'actual lock belongs to another case or recorder type')
        recorder = session._recorder
        expected_claim = recorder._claims / (session.plan.case_id + '.attempt1.claim.json')
        _need(Path(request.claim_path) == expected_claim,
            'claim is outside the actual locked recorder case')
        case_id = session.plan.case_id
        terminals = (
            recorder._attempts / (case_id + '.attempt1.failure.json'),
            recorder._intents / (case_id + '.intent.json'),
            recorder._successes / (case_id + '.success.json'),
            recorder._engineering_intents / (case_id + '.intent.json'),
            recorder._engineering_successes / (case_id + '.success.json'),
        )
        _need(not any(path.exists() or path.is_symlink() for path in terminals),
            'a failed or terminal case cannot reuse its restoration request')
        claim, _ = _document(expected_claim, request.claim_sha256)
        claim_payload = claim.get('payload')
        claim_context = pins.get('factory_claim')
        _need(type(claim_context) is dict and set(claim_context) == {
                'recorder_root', 'output_root', 'source', 'worker', 'attempt'}
            and claim_context.get('recorder_root') == str(recorder._root)
            and claim_context.get('output_root') == str(recorder.output_root)
            and type(claim_context.get('attempt')) is int and claim_context['attempt'] == 1
            and type(claim_context.get('worker')) is str and bool(claim_context['worker'].strip())
            and claim_context.get('source') == asdict(capture_source(recorder._root)),
            'independently admitted current recorder context differs')
        expected_claim_payload = dict(purpose='pilot_case_claim', case=asdict(session.plan),
            worker=claim_context['worker'], attempt=1, environment_sha256=environment_digest(),
            source=claim_context['source'], engineering_only=True)
        _need(type(claim_payload) is dict and claim_payload == expected_claim_payload
            and verify_envelope(claim, kind='engineering_smoke', expected_payload=expected_claim_payload),
            'current locked claim schema, case, worker, attempt, environment or source differs')
        executor = request.executor
        _need(asdict(capture_source(Path(executor.root))) == _source(executor.source_json),
            'actual current Git/source context differs')
        sources = _json_field(executor.source_files_json)
        for required in (Path(__file__).absolute(), Path(__file__).with_name('selection.py').absolute()):
            _need(str(required) in sources, 'restoration factory sources must be independently pinned')
        for path, digest in sources.items():
            read_pinned(Path(path), digest, MAXIMUM_JSON, retain=False)
        runtime = _json_field(executor.runtime_json)
        _need(runtime == dict(python_full=sys.version, python=platform.python_version(),
            executable=str(Path(sys.executable).resolve()),
            **{name: version(name) for name in ('torch', 'numpy', 'braindecode')}),
            'current interpreter/dependency versions differ')
        binaries = _json_field(executor.runtime_files_json)
        for executable in (sys.executable, sys._base_executable):
            _need(str(Path(executable).resolve()) in binaries,
                'effective Python launcher and base binary must be independently pinned')
        for path, digest in binaries.items():
            read_pinned(Path(path), digest, MAXIMUM_RUNTIME, retain=False, runtime_binary=True)
        _need(self.assert_live_lock() is not False, 'current CaseRecorder identity lock lost')

    def authenticate(self):
        """Authenticate exact historical bytes and current admission without decoding tensors."""
        self._current()
        request, producer = self.request, self.request.producer
        store = Path(request.store_root)
        _need(store.is_dir() and store.resolve(strict=True) == store, 'direct historical store required')
        publication, publication_identity = _document(Path(producer.publication_path), producer.publication_file_sha256)
        _need(publication.get('schema') == 'cho51_linear_staged_publication_v1'
            and publication.get('passed') is True and publication.get('engineering_only') is True
            and publication.get('scientific_admission') is False
            and publication.get('historical_full_selector_verified') is True
            and type(publication.get('measured_cells')) is int and publication['measured_cells'] == 0
            and publication.get('source') == _source(producer.source_json)
            and publication.get('case') == _json_field(request.plan_json),
            'independently admitted historical publication ancestry differs')
        for name, expected in dict(manifest_sha256=producer.manifest_sha256,
                manifest_file_sha256=producer.manifest_file_sha256,
                evidence_sha256=producer.evidence_sha256, evidence_file_sha256=producer.evidence_file_sha256,
                weights_file_sha256=producer.weights_sha256, model_state_sha256=producer.model_state_sha256,
                model_recipe_sha256=producer.model_recipe_sha256, selected_candidate=producer.selected_candidate).items():
            _need(publication.get(name) == expected, 'historical publication ' + name + ' differs')
        manifest_path = store / 'manifests' / (producer.manifest_sha256 + '.json')
        evidence_path = store / 'evidence' / (producer.evidence_sha256 + '.json')
        weights_path = store / 'weights' / (producer.weights_sha256 + '.safetensors')
        _need(publication.get('manifest_path') == str(manifest_path)
            and publication.get('evidence_path') == str(evidence_path)
            and publication.get('weights_path') == str(weights_path), 'foreign historical store paths')
        manifest, manifest_identity = _document(manifest_path, producer.manifest_file_sha256)
        payload = manifest.get('payload')
        expected_fields = {'purpose', 'scope', 'scientific_evaluation', 'evidence_sha256',
            'selected_candidate', 'selection_contract_sha256', 'protocol_config_sha256',
            'source', 'model_class', 'model_recipe', 'model_recipe_sha256',
            'model_state_sha256', 'tensor_schema', 'weights_sha256', 'weights_file', 'evidence_file'}
        _need(type(payload) is dict and verify_envelope(manifest, kind='engineering_smoke', expected_payload=payload)
            and expected_fields <= set(payload) <= expected_fields | {'weights_format', 'evidence_format'}
            and manifest.get('sha256') == producer.manifest_sha256
            and payload.get('purpose') == 'selected_source_snapshot'
            and payload.get('scope') == 'engineering_only' and payload.get('scientific_evaluation') is False
            and payload.get('source') == _source(producer.source_json)
            and payload.get('protocol_config_sha256') == request.protocol_config_sha256
            and payload.get('model_class') == 'encoder.labram.LaBraMClassifier'
            and payload.get('weights_format', 'full_v1') == 'full_v1'
            and payload.get('evidence_format', 'canonical_json_v1') == 'canonical_json_v1',
            'selected source manifest context or full-state format differs')
        for name in ('evidence_sha256', 'weights_sha256', 'model_state_sha256',
                'model_recipe_sha256', 'selected_candidate', 'selection_contract_sha256'):
            _need(payload.get(name) == getattr(producer, name), 'selected manifest ' + name + ' differs')
        _need(payload.get('weights_file') == 'weights/' + weights_path.name
            and payload.get('evidence_file') == 'evidence/' + evidence_path.name
            and config_digest(payload.get('model_recipe', {})) == producer.model_recipe_sha256,
            'selected manifest paths or recipe digest differ')
        evidence, evidence_identity = _document(evidence_path, producer.evidence_file_sha256, MAXIMUM_EVIDENCE)
        claim = evidence.get('payload')
        _need(type(claim) is dict and verify_envelope(evidence, kind='engineering_smoke', expected_payload=claim)
            and evidence.get('sha256') == producer.evidence_sha256
            and claim.get('purpose') == 'bounded_labram_source_selection'
            and claim.get('complete') is True and claim.get('outer_target_predictions_performed') is False,
            'complete historical selected evidence required')
        contract, final_fit = claim.get('contract'), claim.get('final_source_fit')
        _need(type(contract) is dict and type(final_fit) is dict
            and config_digest(contract) == producer.selection_contract_sha256 == claim.get('contract_sha256')
            and contract.get('source') == _source(producer.source_json)
            and contract.get('protocol_sha256') == request.protocol_config_sha256
            and claim.get('selected_candidate') == producer.selected_candidate
            and final_fit.get('candidate') == producer.selected_candidate
            and final_fit.get('fitted_state_sha256') == producer.model_state_sha256,
            'mixed producer, recipe, selection contract or final tensor state')
        _, weights_identity = read_pinned(weights_path, producer.weights_sha256, MAXIMUM_WEIGHTS, retain=False)
        _need(publication.get('weights_bytes') == weights_identity[2], 'historical weight byte count differs')
        self._current()
        return AuthenticatedSelection(canonical(manifest), canonical(evidence), manifest_identity,
            evidence_identity, weights_identity, publication_identity)

    def begin_restoration(self):
        """Durably consume this locked request before any numerical work starts."""
        _need(not self._used, 'restoration request is once-only; a failure must not replay it')
        self._used = True
        self._current()
        marker = Path(self.request.workspace) / 'restore-attempt.json'
        raw = (canonical(dict(schema='cho51_provenance_restore_attempt_v1',
            request_sha256=self.request.sha256, claim_sha256=self.request.claim_sha256,
            pins_sha256=self.request.pins_sha256, scientific_admission=False)) + '\n').encode()
        with marker.open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        attempt_sha256 = hashlib.sha256(raw).hexdigest()
        _, attempt_identity = read_pinned(marker, attempt_sha256, MAXIMUM_JSON, retain=False)
        self._attempt_pin = attempt_sha256, attempt_identity

    def restore(self, *, method_config, protocol_config, catalogs, selection_record, assets):
        """Release the genuine adapter after full metadata and strict tensor restoration."""
        self.begin_restoration()
        authenticated = self.authenticate()
        request, producer = self.request, self.request.producer
        from dataclasses import asdict as typed_dict
        import torch
        from safetensors.torch import load
        from encoder.labram import LaBraMClassifier
        from evaluation.labram_parity import state_digest
        from evaluation.phase2_cho_execution_gate import _method_config
        from evaluation.phase2_cho_source_restore import (
            prepare_cho_source_restore, _new_model, _check_labram_baseline, _require_host_ram,
        )
        from evaluation.phase2_pilot import LaBraMTunedAdapter
        from evaluation.phase2_runner import CasePlan, method_configuration
        from docs.phase2.cho51_provenance_restore_v1.selection import verify_historical_selection

        plan = CasePlan(**_json_field(request.plan_json))
        _need(method_configuration(method_config) == request.method_config_sha256
            and config_digest(protocol_config) == request.protocol_config_sha256,
            'caller method or protocol configuration differs')
        prepared = prepare_cho_source_restore(root=Path(request.executor.root), plan=plan,
            method_config=method_config, expected_method_config_sha256=request.method_config_sha256,
            selected_candidate=producer.selected_candidate)
        manifest = _object(authenticated.manifest_json)['payload']
        evidence = _object(authenticated.evidence_json)
        contract, final_fit = evidence['payload']['contract'], evidence['payload']['final_source_fit']
        _need(prepared.model_recipe == manifest['model_recipe']
            and config_digest(prepared.model_recipe) == producer.model_recipe_sha256,
            'independently derived canonical architecture recipe differs')
        _need(manifest.get('model_class') == 'encoder.labram.LaBraMClassifier',
            'canonical selected model class differs')
        _method_config(plan, method_config, contract, assets)
        current_runtime = _json_field(request.executor.runtime_json)
        recorded_runtime = contract.get('runtime')
        _need(type(recorded_runtime) is dict
            and set(recorded_runtime) == {'python', 'torch', 'numpy', 'braindecode',
                'device', 'dtype', 'torch_threads', 'deterministic_algorithms'}
            and recorded_runtime.get('device') == 'cpu' and recorded_runtime.get('dtype') == 'float32'
            and type(recorded_runtime.get('python')) is str
            and all(recorded_runtime.get(name) == current_runtime[name] for name in ('torch', 'numpy', 'braindecode')),
            'historical runtime schema or numerical dependency compatibility differs')
        verified = verify_historical_selection(record=evidence, evidence_sha256=producer.evidence_sha256,
            plan=plan, protocol_config=protocol_config, catalogs=catalogs, selection_record=selection_record,
            assets=assets, root=Path(request.executor.root), producer_source=_source(producer.source_json),
            adapter_model_state_sha256=producer.model_state_sha256,
            adapter_source_settings=typed_dict(prepared.source_settings),
            adapter_support_settings=typed_dict(prepared.support_settings))
        _need(verified.selected_candidate == producer.selected_candidate, 'complete historical winner differs')
        _require_host_ram(4.0)
        self._current()
        model = _new_model(prepared, contract=contract, final_fit=final_fit)
        _check_labram_baseline(prepared)
        backbone_before = state_digest(model.backbone)
        _require_host_ram(4.0)
        weights_path = Path(request.store_root) / 'weights' / (producer.weights_sha256 + '.safetensors')
        blob, identity = read_pinned(weights_path, producer.weights_sha256, MAXIMUM_WEIGHTS)
        _need(identity == authenticated.weights_identity, 'selected weight identity changed before safe decoder')
        tensors = load(blob)
        expected = model.state_dict()
        schema = manifest.get('tensor_schema')
        _need(type(model) is LaBraMClassifier and type(schema) is dict
            and set(tensors) == set(expected) == set(schema), 'exact canonical tensor inventory required')
        for name, tensor in tensors.items():
            declared = schema[name]
            _need(type(declared) is dict and tensor.device.type == 'cpu'
                and tensor.dtype == expected[name].dtype and tensor.shape == expected[name].shape
                and declared == {'dtype': str(tensor.dtype), 'shape': list(tensor.shape)}
                and bool(torch.isfinite(tensor).all()), 'finite canonical tensor schema differs')
        from evaluation.phase2_selected_source_store import _tensor_state_digest
        _need(_tensor_state_digest(tensors) == producer.model_state_sha256,
            'decoded selected tensor state differs from independently pinned final fit')
        self._current()
        model.load_state_dict(tensors, strict=True)
        _need(state_digest(model) == producer.model_state_sha256
            and state_digest(model.backbone) == backbone_before
            and tuple(name for name, parameter in model.named_parameters() if parameter.requires_grad)
                == ('head.weight', 'head.bias')
            and sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad) == 402
            and not any(module.training for module in model.modules())
            and all(parameter.grad is None for parameter in model.parameters()),
            'strictly restored selected model or head-only source mask differs')
        adapter = LaBraMTunedAdapter(plan.method, model, prepared.support_settings)
        _need(type(adapter) is LaBraMTunedAdapter and adapter._model is model,
            'genuine canonical adapter delivery required')
        _check_labram_baseline(prepared)
        final = self.authenticate()
        _need(final == authenticated and state_digest(model) == producer.model_state_sha256,
            'authenticated ancestry or restored state changed before adapter delivery')
        witness = dict(schema='cho51_provenance_restored_source_v1', passed=True,
            request_sha256=request.sha256, claim_sha256=request.claim_sha256, pins_sha256=request.pins_sha256,
            restore_attempt_sha256=self._attempt_pin[0],
            workspace=request.workspace, store_root=request.store_root,
            historical_source=_source(producer.source_json), current_executor_source=_source(request.executor.source_json),
            historical_runtime=recorded_runtime, current_executor_runtime=current_runtime,
            historical_publication_file_sha256=producer.publication_file_sha256,
            manifest_sha256=producer.manifest_sha256, manifest_file_sha256=producer.manifest_file_sha256,
            complete_evidence_sha256=producer.evidence_sha256, complete_evidence_file_sha256=producer.evidence_file_sha256,
            selection_contract_sha256=producer.selection_contract_sha256, complete_metadata_verified=True,
            model_recipe_sha256=producer.model_recipe_sha256, model_state_sha256=producer.model_state_sha256,
            weights_sha256=producer.weights_sha256, weights_bytes=identity[2], maximum_weights_bytes=MAXIMUM_WEIGHTS,
            tensor_count=len(tensors), elements=sum(tensor.numel() for tensor in tensors.values()),
            adapter_class=type(adapter).__module__ + '.' + type(adapter).__qualname__,
            selected_restores=1, model_constructions=1, safe_decodes=2, strict_state_loads=2,
            source_updates=0, support_updates=0, query_calls=0, measured_cells=0,
            engineering_only=True, scientific_admission=False, unchanged_single_root_factory_verified=False,
            native_closeout_status='pending_external_post_job')
        return RestoredSource(adapter, model, witness)
