"""Flat, authenticated linear-fold origins; standard-library metadata only.

The fixed root adopts ten already accepted folds. Each subsequent leaf refers
only to its own finite native attempt and the preceding head digest. No ancestor
archive is copied into a new leaf, and no model, test or fitting module is loaded.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import stat
import sys

ROOT = Path(__file__).resolve().parents[3]
RUN_RELATIVE = 'runs/coordination/cho51_linear_chain_20261015_v1'
OLD_RELATIVE = 'runs/coordination/cho51_linear_continuation_20261015_v1'
OLD_PINS = '1e16577546807821112e58f671f0941e0ba3ab0c5980c82efa67d92b14e4a42b'
OLD_FINAL = 'c7c90b590c0272551baef6bd691b903d01a9373727b37157718592ecbc1014b1'
OLD_REVIEW = '68f82525c2b7adf6118c53dd7abe38019488faf83153377a9480d67362a41dc4'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
INITIAL = '90a9d34ecba2aa96a942f7bd70724f63c2071042141935dbbcd78e0b373b89a7'
CONTRACT = '8397d34ee0a2280b406071e045988f98b1b73ce21fcecc0b9834518cd21993b1'
INPUT = '4abdfea1f6f9ee8a29782b30723e288bf490ffcb7a8c02bf962704bb68d5b1c0'
RECIPE = 'bdb40fd0f3becf87cc619e87a536ee4a921e72efa422fcaaf235c3573865a452'
BASELINE = '53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8'
SOURCES = tuple(f'subject_{n:02d}' for n in range(1, 53) if n != 2)
FULL_PAIRS = tuple((candidate, subject) for candidate in ('lr_1e-3', 'lr_2e-3') for subject in SOURCES)
_TOKEN = object()
_ROOT_CACHE = {}
_MODULES = None


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _canonical(value):
    return json.dumps(value, allow_nan=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def _snapshot(value):
    return json.loads(_canonical(value))


def _logical(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _physical(value):
    return hashlib.sha256(_canonical(value) + b'\n').hexdigest()


def _load(name, path, expected=None):
    if expected is not None:
        with path.open('rb') as stream:
            _need(hashlib.file_digest(stream, 'sha256').hexdigest() == expected,
                  'pinned metadata source changed: ' + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    _need(spec is not None and spec.loader is not None, 'metadata reader unavailable')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _modules():
    global _MODULES
    if _MODULES is None:
        # These modules load only pinned standard-library metadata helpers.
        old = _load('_linear_chain_old_origin', ROOT / 'docs/phase2/cho51_linear_continuation_v1/origin.py',
            '271afa462599007b3825349e80b57fd258e8f0e1444abb7c58274abf11ffff1a')
        old._metadata(ROOT)  # Authenticates all four transitive readers before import.
        closeout = _load('_linear_chain_old_closeout', ROOT / OLD_RELATIVE / 'closeout.py',
            'cb95f6a5b267561a4ded702d0a9217046f561b4ccaa9a90a8835912175a8e0a6')
        contract = _load('_linear_chain_fold_contract', ROOT / 'docs/phase2/cho51_linear_continuation_v1/contract.py',
            '4f4be8e9a82c0878d71bd8d7b9d53fe94b01f433cd5defee2b9b7dff3c1d9200')
        _MODULES = old, closeout, contract
    return _MODULES


class _Audit:
    """One hash per shared physical path per audit, with identity checks on reuse."""
    def __init__(self, root):
        _need(isinstance(root, Path) and root == ROOT and root.resolve(strict=True) == root,
              'exact direct project root required')
        self.root = root
        self.old, self.previous, self.contract = _modules()
        self.M = self.previous.M
        self.seen, self.options, self.raw, self.proofs, self.inputs = {}, {}, {}, {}, {}

    def path(self, relative):
        _need(type(relative) is str, 'plain relative proof path required')
        parts = PurePosixPath(relative)
        _need(not parts.is_absolute() and '..' not in parts.parts and '\\' not in relative,
              'proof path escapes the project')
        path = self.root.joinpath(*parts.parts)
        _need(path.is_relative_to(self.root), 'proof path escapes the project')
        return path

    def check(self, path, *, expected=None, compact=False, single_link=True, proof=False):
        path = Path(path)
        key = str(path)
        prior = self.seen.get(key)
        if prior is not None and (not compact or key in self.raw):
            info = path.stat()
            signature = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
            _need(signature == prior[:-1] and (not single_link or info.st_nlink == 1),
                  'previously authenticated file changed: ' + key)
            raw, pin = self.raw.get(key), prior
        else:
            raw, pin = self.M.old.inspect(path, compact=compact, single_link=single_link)
            _need(prior is None or prior == pin, 'physical proof changed across reads')
            self.seen[key] = pin
            if compact:
                self.raw[key] = raw
        if expected is not None:
            _need(pin[-1] == expected, 'independent file hash differs: ' + key)
        previous_options = self.options.get(key, (False, False))
        self.options[key] = (compact or previous_options[0], single_link or previous_options[1])
        if proof:
            _need(compact and path.is_relative_to(self.root), 'compact project proof required')
            relative = path.relative_to(self.root).as_posix()
            self.proofs[relative] = pin[-1]
        return raw, pin

    def document(self, path, *, expected=None, canonical_raw=False, **ignored):
        raw, pin = self.check(path, expected=expected, compact=True, proof=True)
        value = self.M.old.decode(raw)
        if canonical_raw:
            _need(raw == _canonical(value) + b'\n', 'canonical finite JSON proof required')
        return value, pin[-1]

    def selection_document(self, path, *, expected):
        """The sole32MiB exception: the actual final canonical evidence file."""
        exact = ROOT / RUN_RELATIVE / 'fragments/fragment_007/selection-evidence.json'
        _need(path == exact, 'large JSON exception is limited to the exact final evidence file')
        self.M.old.direct(path)
        before = path.stat()
        _need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
              and 0 < before.st_size <= 32 * 1024**2, 'bounded direct final evidence required')
        with path.open('rb') as stream:
            opened = os.fstat(stream.fileno())
            raw = stream.read(32 * 1024**2 + 1)
            finished = os.fstat(stream.fileno())
        signature = self.M.old.signature
        _need(signature(before) == signature(path.stat()) and signature(opened) == signature(finished)
              and signature(before)[:4] == signature(opened)[:4] and len(raw) == before.st_size,
              'final evidence changed during bounded read')
        digest = hashlib.sha256(raw).hexdigest()
        _need(digest == expected, 'final evidence physical hash differs')
        value = self.M.old.decode(raw)
        _need(raw == _canonical(value) + b'\n', 'canonical finite final JSON required')
        pin = (*signature(before), digest)
        prior = self.seen.setdefault(str(path), pin)
        _need(prior == pin, 'final evidence changed across reads')
        self.raw[str(path)] = raw
        self.options[str(path)] = (True, True)
        self.proofs[path.relative_to(ROOT).as_posix()] = digest
        return value, digest

    def remember(self, path, *, expected=None, compact=False, **ignored):
        return self.check(path, expected=expected, compact=compact, proof=compact)

    def pins(self, pins):
        for relative, expected in pins['files'].items():
            self.check(self.path(relative), expected=expected, single_link=False)
        for path, expected in pins['runtime'].items():
            self.check(Path(path), expected=expected, single_link=False)
        for path, expected in pins.get('baseline', {}).items():
            _, pin = self.check(Path(path), expected=expected)
            _need(expected == BASELINE and pin[2] == 23299672, 'exact audited safe baseline required')

    def modules(self, qualification, count=None):
        mapping = qualification['observed_loaded_module_hashes']
        _need(type(mapping) is dict and bool(mapping)
              and type(qualification['loaded_module_files']) is int
              and qualification['loaded_module_files'] == len(mapping)
              and (count is None or len(mapping) == count),
              'actual observed module map required')
        if count is None:
            critical = ('docs/phase2/cho51_linear_chain_v1/executor.py',
                'docs/phase2/cho51_linear_chain_v1/origin.py', 'docs/phase2/cho51_linear_chain_v1/plan.py',
                'docs/phase2/cho51_linear_chain_v1/selector.py',
                'adaptation/labram_source.py', 'adaptation/labram_manifest.py', 'encoder/labram.py',
                'core/config.py', 'core/provenance.py', 'evaluation/phase2_selection_evidence_binding.py',
                'evaluation/phase2_cho_source_restore.py')
            _need(all(str(ROOT / path) in mapping for path in critical),
                  'actual generic numerical and verification modules missing from observed map')
        for path, expected in mapping.items():
            self.check(Path(path), expected=expected, single_link=False)

    def input_files(self, fixture_origin):
        fixture = Path(fixture_origin['fixture_root'])
        identity, _ = self.document(Path(fixture_origin['input_identity_path']),
            expected=fixture_origin['input_identity_file_sha256'], canonical_raw=True)
        content = dict(identity)
        _need(content.pop('sha256') == INPUT == fixture_origin['input_identity_sha256']
              and _logical(content) == INPUT and len(identity['files']) == 213,
              'fixed213-input logical identity required')
        actual = {path.relative_to(fixture).as_posix() for folder in ('configs', 'data')
                  for path in (fixture / folder).rglob('*') if path.is_file() or path.is_symlink()}
        _need(actual == set(identity['files']), 'physical synthetic input inventory changed')
        total = 0
        for relative, witness in identity['files'].items():
            parts = PurePosixPath(relative)
            _need(not parts.is_absolute() and '..' not in parts.parts and '\\' not in relative,
                  'synthetic input path escaped')
            path = fixture.joinpath(*parts.parts)
            _, pin = self.check(path, expected=witness['sha256'])
            _need(pin[2] == witness['size_bytes'], 'synthetic input size changed')
            self.inputs[str(path)] = pin
            total += pin[2]
        _need(total == 734579463, 'full synthetic input byte count changed')
        return identity

    def finish(self):
        for name, pin in self.seen.items():
            info = Path(name).stat()
            _need((info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns) == pin[:-1],
                  'authenticated dependency changed before release: ' + name)


def _packet(audit, name, expected_manifest, expected_summary, count):
    directory = ROOT / 'evidence' / name
    manifest, _ = audit.document(directory / 'manifest.json', expected=expected_manifest)
    summary, _ = audit.document(directory / 'summary.json', expected=expected_summary)
    audit.check(directory / 'README.md', compact=True, proof=True)
    _need(len(manifest['artifacts']) == count == summary['artifacts'], 'fixed archive inventory changed')
    for row in manifest['artifacts']:
        for path in (audit.path(row['source']), audit.path('evidence/' + name + '/' + row['path'])):
            _, pin = audit.check(path, expected=row['sha256'], compact=True, proof=True)
            _need(pin[2] == row['bytes'], 'historical archive/source size changed')
    return summary


def _folds(audit, pins, pairs):
    records, references = [], []
    _need(len(pins) == len(pairs), 'exact current raw fold witnesses required')
    for witness, pair in zip(pins, pairs, strict=True):
        record, digest = audit.document(Path(witness['path']), expected=witness['file_sha256'], canonical_raw=True)
        content = dict(record)
        declared = content.pop('sha256')
        _need(_logical(content) == declared == witness['evidence_sha256'], 'raw fold envelope hash differs')
        payload = record['payload']
        _need(payload['complete'] is False and payload['selected_candidate'] is None
              and payload['contract_sha256'] == CONTRACT == _logical(payload['contract'])
              and len(payload['folds']) == 1, 'raw incomplete fold/contract differs')
        fold = payload['folds'][0]
        _need((fold['candidate'], fold['validation_subject']) == tuple(pair), 'raw fold pair differs')
        records.append(record)
        references.append({'candidate': pair[0], 'validation_subject': pair[1], 'path': str(Path(witness['path'])),
                           'file_sha256': digest, 'evidence_sha256': declared})
    return records, references


def _collect(audit, records, method):
    return audit.contract.collect_partial(records, method, input_identity_sha256=INPUT,
        template_state_sha256=INITIAL, initial_state_sha256=INITIAL, lineage_recipe_sha256=RECIPE)


def _build_root(audit):
    old_origin = audit.old.build_origin(ROOT)
    for relative, expected in old_origin['proofs'].items():
        audit.check(audit.path(relative), expected=expected, compact=True, proof=True)
    original = ROOT / OLD_RELATIVE
    final, _ = audit.document(original / 'final-review.json', expected=OLD_FINAL)
    audit.M.old.fields(final, {'passed': True, 'metadata_only': True, 'remaining_actionable_findings': [],
        'combined_accepted_folds': 10, 'current_gradient_updates': 408, 'historical_gradient_updates': 102,
        'pending_folds': 92, 'full_selector_verified': False, 'scientific_admission': False})
    pins, _ = audit.document(original / 'pins.json', expected=OLD_PINS)
    _need(len(pins['files']) == 1224 and len(pins['runtime']) == 5, 'exact accepted1224/5 root pins required')
    audit.pins(pins)
    review, _ = audit.document(original / 'source-review.json', expected=OLD_REVIEW)
    audit.M.old.fields(review, {'source_only': True, 'remaining_actionable_findings': [], 'files': pins['reviewed_files']})
    summary = _packet(audit, 'cho51-linear-continuation-20261015',
        '1ceb9f21531ee2738a83b2ad3b1fd1ebc7edbc1670f8fbdde679cf0eb63233f0',
        '518f57468a5e907ba9170d624ca55c4591181e503f66b2d35ac303f4502ed92d', 230)
    _packet(audit, 'cho51-linear-continuation-ready-20261015',
        'e2bf5a60a09ea3fece66c3cc528c058125d84f1369dc57c862e13076480cdc54',
        'b2425df0ba53cc329fceed467a56b0fad63baba985b1c62015e4b51b4e10f944', 206)
    output = original / 'validation_001'
    q, _ = audit.document(output / 'qualification.json', expected=final['qualification_sha256'], canonical_raw=True)
    child, _ = audit.document(output / 'result.json', expected=final['result_sha256'], canonical_raw=True)
    result, _ = audit.document(output / 'probe-result.json', expected=final['probe_result_sha256'], canonical_raw=True)
    _need(q['result'] == child and child['probe'] == result, 'accepted root wrapper/probe binding differs')
    audit.M.old.fields(q, {'passed': True, 'pins_sha256': OLD_PINS, 'source_updates': 400,
        'support_updates': 8, 'actual_gradient_updates': 408, 'unexpected_denials': 0,
        'protected_target_read_attempts': [], 'full_selector_verified': False, 'scientific_admission': False})
    audit.M.old.fields(child, {'passed': True, 'tests_passed': True, 'pytest_exit': 0,
        'collected_tests': 37, 'collected_subtests': 23, 'skipped_reports': [], 'unexpected_reports': []})
    for key, count in (('reports', 37), ('subtest_reports', 23)):
        _need(len(child[key]) == count and all(row['phase'] == 'call' and row['outcome'] == 'passed'
              for row in child[key]), 'all accepted root tests must pass')
    for key, count in {'sgd_step': 408, 'tensor_backward': 408, 'autograd_backward': 408,
            'optimizer_init': 16, 'safetensors_load': 2, 'module_load_state_dict': 2}.items():
        _need(q['observed_numerical_calls'].get(key) == count, 'accepted root numerical count differs')
    audit.modules(q, 4824)
    method, method_file_sha = audit.document(original / 'method-config.json', canonical_raw=True)
    fixture_origin = {key: old_origin[key] for key in
        ('fixture_root', 'input_identity_path', 'input_identity_sha256', 'input_identity_file_sha256')}
    audit.input_files(fixture_origin)
    original_records, original_refs = _folds(audit, old_origin['adopted_fold_records'],
        [(name, 'subject_01') for name in ('lr_1e-3', 'lr_2e-3')])
    current_pairs = tuple(audit.previous.PAIRS)
    current_records, current_refs = _folds(audit, result['fold_evidence'], current_pairs)
    observations, _ = audit.document(output / 'optimizer-observations.json', canonical_raw=True)
    audit.previous.validate_observations(observations, result)
    collection, _ = audit.document(output / 'partial-collection.json', canonical_raw=True)
    records = original_records + current_records
    _need(_collect(audit, records, method) == collection and collection['accepted_folds'] == 10,
          'authenticated ten-fold root collection differs')
    dispatch, _ = audit.document(original / 'dispatch_001.json')
    dispatched, _ = audit.document(original / 'dispatch_result_001.json')
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(original / 'child.py'),
        '--pins', str(original / 'pins.json'), '--expect-pins', OLD_PINS, '--output', str(output)]
    for value in (dispatch, dispatched):
        audit.M.old.fields(value, {'pins_sha256': OLD_PINS, 'child_command': command,
            'expected_output': str(output), 'scientific_admission': False})
    audit.M.old.fields(dispatched, {'guard_exit_code': 0,
        'native_directory': str(ROOT / 'runs/migration/20261015T150509Z_9344e1cd12')})
    operations, runtimes = audit.M.native_pins(pins)
    native = audit.M.old.verify_native(Path(dispatched['native_directory']), command, 600, 4096, 5120,
        operations=operations, runtimes=runtimes, document=audit.document, remember=audit.remember,
        launcher=audit.M.launcher)
    _need(native['elapsed_native_seconds'] == 164.26309 and audit.M.old.source_check(ROOT) == CANONICAL,
          'accepted root interval or canonical432 changed')
    ordered = sorted(zip(original_refs + current_refs, records), key=lambda row: FULL_PAIRS.index(
        (row[0]['candidate'], row[0]['validation_subject'])))
    references, records = [row[0] for row in ordered], [row[1] for row in ordered]
    origin = {'schema': 'cho51_linear_chain_root_v1', 'fixture_origin': fixture_origin,
        'contract_sha256': CONTRACT, 'template_state_sha256': INITIAL, 'initial_state_sha256': INITIAL,
        'lineage_recipe_sha256': RECIPE, 'input_identity_sha256': INPUT,
        'fixture_source_sha256': records[0]['payload']['contract']['source']['source_sha256'],
        'baseline_sha256': BASELINE, 'method_config_path': str(original / 'method-config.json'),
        'method_config_file_sha256': method_file_sha, 'method_config_sha256': _logical(method),
        'root_record_refs': references, 'accepted_pairs': [
            {'candidate': row['candidate'], 'validation_subject': row['validation_subject']} for row in references],
        'accepted_folds': 10, 'historical_source_updates': 500, 'historical_support_updates': 10,
        'historical_gradient_updates': 510, 'pending_folds': 92, 'required_full_gradient_updates': 5253,
        'fresh_final_source_updates_required': 51, 'original_pins_sha256': OLD_PINS,
        'original_final_review_sha256': OLD_FINAL, 'proofs': dict(sorted(audit.proofs.items())),
        'canonical_source_sha256': CANONICAL, 'canonical_files': 432, 'complete': False,
        'selected_candidate': None, 'full_selector_qualified': False, 'scientific_admission': False,
        'original_case_attempts': 0, 'adoption_authority': 'new_flat_engineering_chain_only'}
    audit.finish()
    return _snapshot(origin), _snapshot(records)


def build_root(root: Path) -> dict:
    """Authenticate the immutable ten-fold root; never check mutable resume heads."""
    audit = _Audit(root)
    origin, records = _build_root(audit)
    _ROOT_CACHE[_physical(origin)] = (origin, records, dict(audit.seen), dict(audit.options))
    return _snapshot(origin)


@dataclass(frozen=True)
class VerifiedHistory:
    records: list
    accepted_pairs: list
    head_sha256: str
    proof_identities: dict
    input_identities: dict
    root_origin: dict
    chain: dict
    pins_sha256: str
    _audit: object
    _records_sha256: str
    _token: object


def _plan():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    return _load('_linear_chain_pure_plan', Path(__file__).with_name('plan.py'))


def _current_pins(audit, expected):
    pins, _ = audit.document(ROOT / RUN_RELATIVE / 'pins.json', expected=expected, canonical_raw=True)
    predecessor, _ = audit.document(ROOT / OLD_RELATIVE / 'pins.json', expected=OLD_PINS)
    _need(len(predecessor['files']) == 1224 and len(predecessor['runtime']) == 5
          and all(pins['files'].get(path) == digest for path, digest in predecessor['files'].items())
          and pins['runtime'] == predecessor['runtime'] and pins['baseline'] == predecessor['baseline'],
          'fixed1224/5/1 predecessor extension required for every generic fragment')
    audit.pins(pins)
    review_path = Path(pins.get('source_review_path', str(ROOT / RUN_RELATIVE / 'source-review.json')))
    review, _ = audit.document(review_path, expected=pins['source_review_sha256'])
    audit.M.old.fields(review, {'source_only': True, 'remaining_actionable_findings': [],
                               'files': pins['reviewed_files']})
    candidate = 'docs/phase2/cho51_linear_chain_v1/'
    expected_sources = {candidate + name for name in
        ('executor.py', 'origin.py', 'plan.py', 'test_plan.py', 'selector.py', 'README.md')}
    expected_sources.update(RUN_RELATIVE + '/' + name for name in
        ('runtime.py', 'child.py', 'prepare.py', 'launch.ps1', 'observe.py', 'closeout.py'))
    _need(set(pins['reviewed_files']) == expected_sources
          and all(pins['files'].get(path) == digest for path, digest in pins['reviewed_files'].items()),
          'exact twelve independently reviewed candidate/operation files required')
    _need(audit.M.old.source_check(ROOT) == CANONICAL and pins['runtime'], 'canonical/runtime context changed')
    return pins


def _root_history(root_origin, audit):
    digest = _physical(root_origin)
    cached = _ROOT_CACHE.get(digest)
    if cached is None:
        actual, records = _build_root(audit)
        _need(_canonical(actual) == _canonical(root_origin), 'root adoption manifest differs')
        cached = actual, records, dict(audit.seen), dict(audit.options)
        _ROOT_CACHE[digest] = cached
    else:
        actual, records, identities, options = cached
        _need(_canonical(actual) == _canonical(root_origin), 'root digest collision or mutation')
        for path, identity in identities.items():
            compact, single_link = options[path]
            audit.check(Path(path), expected=identity[-1], compact=compact, single_link=single_link,
                        proof=compact and Path(path).is_relative_to(ROOT))
    audit.input_files(root_origin['fixture_origin'])
    return _snapshot(cached[1])


def verify_chain(root_origin: dict, chain: dict, root: Path, *, pins_sha256: str) -> VerifiedHistory:
    """Iteratively authenticate each leaf exactly once; no recursive ancestor walks."""
    audit = _Audit(root)
    records = _root_history(root_origin, audit)
    pins = _current_pins(audit, pins_sha256)
    plan = _plan()
    plan.validate_chain_metadata(chain)
    _need(chain['root_origin_sha256'] == _physical(root_origin) and chain['pins_sha256'] == pins_sha256,
          'chain root or immutable execution bundle differs')
    prefix = {key: _snapshot(value) for key, value in chain.items()}
    prefix.update(chain_index=0, leaves=[], accepted_pairs=_snapshot(root_origin['accepted_pairs']),
                  head_sha256=_physical(root_origin), complete=False)
    plan.validate_chain_metadata(prefix)
    for descriptor in chain['leaves']:
        leaf, digest = audit.document(audit.path(descriptor['path']), expected=descriptor['sha256'], canonical_raw=True)
        request, _ = audit.document(audit.path(leaf['request_path']), expected=descriptor['request_sha256'], canonical_raw=True)
        history = _history(audit, root_origin, prefix, pins_sha256, records)
        observed, added = _authenticate(history, request, {'native_directory': leaf['native_directory']}, root,
                                         audit=audit, pins=pins)
        _need(_canonical(observed) == _canonical(leaf) and digest == _physical(leaf), 'authenticated leaf bytes differ')
        expected_descriptor = _descriptor(leaf, digest)
        _need(_canonical(expected_descriptor) == _canonical(descriptor), 'leaf descriptor differs from actual proof')
        records.extend(added)
        prefix = plan.advance_chain(prefix, descriptor)
    _need(_canonical(prefix) == _canonical(chain), 'chain catalog differs after iterative authentication')
    audit.finish()
    return _history(audit, root_origin, chain, pins_sha256, records)


def _history(audit, root_origin, chain, pins_sha256, records):
    return VerifiedHistory(_snapshot(records), _snapshot(chain['accepted_pairs']), chain['head_sha256'],
        {str(audit.path(relative)): audit.seen[str(audit.path(relative))] for relative in audit.proofs},
        dict(audit.inputs), _snapshot(root_origin), _snapshot(chain), pins_sha256, audit,
        _logical(records), _TOKEN)


def _test_reports(audit, child, q, request, history, pins):
    first = request['index'] == 1
    expected = pins['expected_tests']
    reuse_sha = None if first else history.chain['leaves'][0]['sha256']
    for value in (child, q):
        audit.M.old.fields(value, {'tests_executed': first, 'tests_reused': not first,
            'tests_passed': True, 'tests_reused_from_leaf_sha256': reuse_sha})
    audit.M.old.fields(child, {'expected_tests': expected, 'expected_subtests': pins['expected_subtests'],
        'collected_tests': expected if first else 0, 'collected_subtests': pins['expected_subtests'] if first else 0,
        'pytest_exit': 0 if first else None, 'skipped_reports': [], 'unexpected_reports': []})
    for key, count in (('reports', expected if first else 0),
                       ('subtest_reports', pins['expected_subtests'] if first else 0)):
        _need(len(child[key]) == count and all(row['phase'] == 'call' and row['outcome'] == 'passed'
              for row in child[key]), 'fresh or explicitly reused generic boundary tests differ')


def _observations(audit, observations, result, request, budget):
    events = observations['events']
    _need(len(events) == budget['gradient_updates'] and events == result['optimizer_updates'],
          'current actual optimizer transcript differs')
    pairs = [(row['candidate'], row['validation_subject']) for row in request['pairs']]
    expected_rows = []
    if request['mode'] == 'folds':
        for candidate, validation in pairs:
            training = [subject for subject in SOURCES if subject != validation]
            expected_rows.extend((candidate, validation, subject, 'source' if index < 50 else 'inner_validation_support', index + 1)
                for index, subject in enumerate((*training, validation)))
    else:
        candidate = result['selected_candidate']
        expected_rows = [(candidate, None, subject, 'final_source', index + 1)
                         for index, subject in enumerate(SOURCES)]
    for index, (row, expected) in enumerate(zip(events, expected_rows, strict=True), 1):
        candidate, validation, subject, role, local_index = expected
        audit.M.old.fields(row, {'update': index, 'fold_update': local_index,
            'candidate': candidate, 'validation_subject': validation, 'subject': subject, 'role': role,
            'selected_parameters': 402, 'selected_tensors': 2,
            'learning_rate': .001 if candidate == 'lr_1e-3' else .002,
            'finite_selected_gradients': True, 'finite_selected_parameters': True,
            'frozen_backbone_and_buffers_unchanged': True})
        before, after = row['selected_state_sha256_before'], row['selected_state_sha256_after']
        audit.M.old.sha(before); audit.M.old.sha(after)
        _need(before != after, 'each actual current SGD update must change head bytes')


def _authenticate(history, request, proof_refs, root, *, audit=None, pins=None):
    _need(isinstance(history, VerifiedHistory) and history._token is _TOKEN
          and _logical(history.records) == history._records_sha256, 'authenticated unchanged history capability required')
    audit = audit or history._audit
    _need(root == ROOT, 'exact project root required')
    plan = _plan()
    plan.validate_request(request, history.chain, pins_sha256=history.pins_sha256,
                          root_origin_sha256=_physical(history.root_origin))
    _need(request['pins_sha256'] == history.pins_sha256 and request['parent_head_sha256'] == history.head_sha256,
          'fragment request substitutes bundle or parent head')
    request_sha = _physical(request)
    run = ROOT / RUN_RELATIVE
    request_path = run / 'requests' / f"fragment_{request['index']:03d}.json"
    persisted_request, _ = audit.document(request_path, expected=request_sha, canonical_raw=True)
    _need(_canonical(persisted_request) == _canonical(request), 'exact persisted request differs')
    snapshot_path = run / request['chain_relative']
    snapshot, _ = audit.document(snapshot_path, canonical_raw=True)
    _need(_canonical(snapshot) == _canonical(history.chain) and _logical(snapshot) == request['chain_sha256'],
          'immutable parent chain snapshot differs')
    pins = pins or _current_pins(audit, history.pins_sha256)
    output = run / request['output_relative']
    expected_paths = {'request_path': request_path, 'qualification_path': output / 'qualification.json',
        'result_path': output / 'result.json', 'probe_result_path': output / 'probe-result.json'}
    _need(type(proof_refs) is dict and set(proof_refs) <= {'native_directory', *expected_paths}
          and 'native_directory' in proof_refs, 'exact current fragment proof references required')
    for key, path in expected_paths.items():
        _need(key not in proof_refs or proof_refs[key] == str(path), 'fragment proof path substitution')
    # Per-leaf references include the current request and parent snapshot, not ancestor proofs.
    own_paths = {request_path, snapshot_path}
    dispatched_paths = [run / 'dispatch' / f"fragment_{request['index']:03d}{suffix}.json"
                        for suffix in ('', '_result')]
    dispatches = [audit.document(path)[0] for path in dispatched_paths]
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(run / 'child.py'),
        '--pins', str(run / 'pins.json'), '--expect-pins', history.pins_sha256,
        '--request', str(request_path), '--expect-request', request_sha, '--output', str(output)]
    for value in dispatches:
        audit.M.old.fields(value, {'pins_sha256': history.pins_sha256, 'request_sha256': request_sha,
            'child_command': command, 'expected_output': str(output), 'scientific_admission': False})
    audit.M.old.fields(dispatches[1], {'guard_exit_code': 0, 'native_directory': proof_refs['native_directory']})
    operations, runtimes = audit.M.native_pins(pins)
    native = audit.M.old.verify_native(Path(proof_refs['native_directory']), command, 600, 4096, 5120,
        operations=operations, runtimes=runtimes, document=audit.document, remember=audit.remember,
        launcher=audit.M.launcher)
    q, q_sha = audit.document(output / 'qualification.json', canonical_raw=True)
    child, child_sha = audit.document(output / 'result.json', canonical_raw=True)
    result, result_sha = audit.document(output / 'probe-result.json', canonical_raw=True)
    _need(q['result'] == child and child['probe'] == result, 'current native qualification/wrapper/probe differs')
    audit.M.old.fields(q, {'schema': 'cho51_linear_chain_qualification_v1', 'passed': True,
        'pins_sha256': history.pins_sha256, 'request_sha256': request_sha, 'unexpected_denials': 0,
        'protected_target_read_attempts': [], 'canonical_source_sha256': CANONICAL,
        'canonical_files': 432, 'source_review_sha256': pins['source_review_sha256'],
        'source_pins_rechecked': len(pins['files']), 'runtime_pins_rechecked': len(pins['runtime']),
        'baseline_pins_rechecked': 1, 'baseline_file_sha256': BASELINE,
        'request_path': str(request_path), 'request_index': request['index'], 'mode': request['mode'],
        'root_origin_sha256': _physical(history.root_origin), 'chain_sha256': request['chain_sha256'],
        'chain_file_sha256': _physical(history.chain), 'parent_head_sha256': history.head_sha256,
        'torch_threads': 1, 'torch_interop_threads': 1, 'gpu_hidden': True,
        'actual_study_data_used': False, 'cohort_lineage_verified': False,
        'full_worker_verified': False, 'scientific_admission': False})
    audit.M.old.fields(child, {'schema': 'cho51_linear_chain_child_result_v1', 'passed': True})
    audit.M.old.fields(result, {'schema': 'cho51_linear_chain_probe_v1', 'passed': True,
        'request_sha256': request_sha, 'root_origin_sha256': _physical(history.root_origin),
        'pins_sha256': history.pins_sha256, 'parent_head_sha256': history.head_sha256,
        'index': request['index'], 'mode': request['mode'], 'contract_sha256': CONTRACT,
        'input_identity_sha256': INPUT, 'template_state_sha256': INITIAL,
        'initial_source_state_sha256': INITIAL, 'model_recipe_sha256': RECIPE,
        'fixture_source_sha256': history.root_origin['fixture_source_sha256'],
        'selected_parameter_count': 402, 'selected_parameter_names': ['head.weight', 'head.bias'],
        'full_backbone_blocks': 12, 'template_parameter_count': 5818138,
        'all_physical_inputs_rehashed_unchanged': True, 'source_backbone_and_buffers_unchanged': True,
        'independent_lineage_verified': True, 'independent_storage_verified': True,
        'finite_losses_gradients_parameters': True, 'torch_numpy_python_rng_unchanged': True,
        'canonical_run_selection_invoked': False, 'public_selected_source_restore_exercised': False,
        'publication_performed': False, 'recorder_used': False, 'measured_cells': 0,
        'cohort_lineage_verified': False, 'scientific_admission': False})
    budget = plan.budget(request)
    for key, count in budget.items():
        if key in ('source_updates', 'support_updates', 'gradient_updates'):
            continue
        _need(q['observed_numerical_calls'].get(key, 0) == count, 'exact current numerical call budget differs: ' + key)
    for key in ('tensor_backward', 'autograd_backward', 'sgd_step'):
        _need(q['observed_numerical_calls'].get(key) == budget['gradient_updates'], 'actual gradient event count differs')
    _need(q['observed_numerical_calls'].get('autograd_grad', 0) == 0, 'undeclared autograd.grad call')
    _need(result['current_gradient_updates'] == budget['gradient_updates']
          and result['actual_gradient_updates'] == budget['gradient_updates']
          and result['source_gradient_updates'] == budget['source_updates']
          and result['support_gradient_updates'] == budget['support_updates'], 'actual current update counts differ')
    audit.M.old.fields(q, {'source_updates': budget['source_updates'],
        'support_updates': budget['support_updates'], 'actual_gradient_updates': budget['gradient_updates'],
        'budget': budget, 'full_selector_verified': request['mode'] == 'final'})
    protected = result['protected_outer_paths']
    _need(len(protected) == 4 and q['protected_target_transitions'] == [
        {'enabled': value, 'paths': protected} for value in (True, False)],
        'exact protected outer-target boundary required')
    _test_reports(audit, child, q, request, history, pins)
    audit.modules(q)
    audit.input_files(history.root_origin['fixture_origin'])
    method, _ = audit.document(Path(history.root_origin['method_config_path']),
        expected=history.root_origin['method_config_file_sha256'], canonical_raw=True)
    pairs = [(row['candidate'], row['validation_subject']) for row in request['pairs']]
    _need(all(witness['path'] == str(output / f'fold_{index:02d}.json')
              for index, witness in enumerate(result['fold_evidence'], 1)),
          'current raw folds must belong to their exact owned output')
    records, references = _folds(audit, result['fold_evidence'], pairs)
    own_paths.update(Path(row['path']) for row in references)
    combined = history.records + records
    collection = _collect(audit, combined, method)
    persisted_collection, _ = audit.document(output / 'partial-collection.json', canonical_raw=True)
    _need(collection == persisted_collection, 'current combined strict fold manifest differs')
    observations, _ = audit.document(output / 'optimizer-observations.json', canonical_raw=True)
    _observations(audit, observations, result, request, budget)
    for field, filename in (('partial_collection', 'partial-collection.json'),
                            ('optimizer_observations', 'optimizer-observations.json')):
        _, actual = audit.check(output / filename, compact=True, proof=True)
        audit.M.old.fields(result[field], {'path': str(output / filename),
            'file_sha256': actual[-1], 'size_bytes': actual[2]})
    final = request['mode'] == 'final'
    if final:
        _need(len(history.records) == 102 and not records and result['final_source_updates'] == 51
              and result['complete_native_origins_capability_exercised'] is True
              and result['public_complete_evidence_verifier_passed'] is True,
              'actual complete-origin/fresh-final/public verification proof required')
        selection_pin = result['selection_evidence']
        selection_path = Path(selection_pin['path'])
        selection, _ = audit.selection_document(selection_path, expected=selection_pin['file_sha256'])
        envelope = dict(selection)
        evidence_sha = envelope.pop('sha256')
        _need(_logical(envelope) == evidence_sha == selection_pin['evidence_sha256'],
              'complete final evidence envelope hash differs')
        payload = selection['payload']
        expected_metadata = audit.contract.require_complete_folds(history.records, method,
            input_identity_sha256=INPUT, template_state_sha256=INITIAL,
            initial_state_sha256=INITIAL, lineage_recipe_sha256=RECIPE)
        _need(payload['complete'] is True and payload['selected_candidate'] == expected_metadata['winner_candidate']
              and len(payload['folds']) == 102 and payload['outer_target_predictions_performed'] is False,
              'complete final evidence winner or coverage differs')
        raw_by_pair = {(record['payload']['folds'][0]['candidate'],
                        record['payload']['folds'][0]['validation_subject']): record['payload']['folds'][0]
                       for record in history.records}
        _need(payload['folds'] == [raw_by_pair[pair] for pair in FULL_PAIRS]
              and payload['contract_sha256'] == CONTRACT == _logical(payload['contract']),
              'complete evidence changed authenticated fold histories or common contract')
        fit = payload['final_source_fit']
        _need(fit['training_subjects'] == list(SOURCES) and fit['validation_subject'] is None
              and fit['initial_state_sha256'] == INITIAL and len(fit['steps']) == 51,
              'fresh final all-source history differs')
        _need(fit['candidate'] == expected_metadata['winner_candidate']
              and fit['mask']['trainable_names'] == ['head.weight', 'head.bias']
              and fit['mask']['trainable_parameters'] == 402
              and fit['optimizer'] == {'name': 'SGD', 'momentum': 0, 'weight_decay': 0, 'fresh': True},
              'fresh final selected candidate, head mask or optimizer differs')
        prior_state = INITIAL
        for number, (subject, step) in enumerate(zip(SOURCES, fit['steps'], strict=True), 1):
            _need(type(step['loss']) in (int, float) and math.isfinite(step['loss'])
                  and step['step'] == number and step['subject'] == subject and step['subject_step'] == 1
                  and step['iterator_wraps'] == 0 and len(set(step['trial_ids'])) == len(step['trial_ids']) == 2
                  and step['state_sha256_after'] != prior_state,
                  'actual ordered finite fresh final history differs')
            audit.M.old.sha(step['state_sha256_after'])
            prior_state = step['state_sha256_after']
        _need(prior_state == fit['fitted_state_sha256'], 'fresh final state differs from its last source step')
        checkpoint_pin = result['checkpoint']
        checkpoint_path = Path(checkpoint_pin['path'])
        _need(checkpoint_path == output / 'selected-source.safetensors', 'exact owned full-state checkpoint required')
        _, checkpoint_identity = audit.check(checkpoint_path, expected=checkpoint_pin['file_sha256'])
        _need(0 < checkpoint_identity[2] <= 64 * 1024**2, 'bounded final checkpoint required')
        selected_recipe = {**result['model_recipe'], 'selected_candidate': expected_metadata['winner_candidate']}
        selected_recipe_sha = _logical(selected_recipe)
        _need(result['selected_model_recipe'] == selected_recipe
              and result['selected_model_recipe_sha256'] == selected_recipe_sha
              and checkpoint_pin['selected_model_recipe_sha256'] == selected_recipe_sha
              and checkpoint_pin['model_state_sha256'] == fit['fitted_state_sha256']
              and checkpoint_pin['weights_format'] == 'full_v1'
              and checkpoint_pin['roundtrip_verified'] is True and checkpoint_pin['published'] is False,
              'selected winner recipe/checkpoint state witness differs')
        verified = result['verified_selection']
        audit.M.old.fields(verified, {'selected_candidate': expected_metadata['winner_candidate'],
            'evidence_sha256': evidence_sha, 'model_state_sha256': fit['fitted_state_sha256'],
            'selected_model_recipe_sha256': selected_recipe_sha,
            'public_complete_evidence_verifier_passed': True, 'source_gradient_updates': 5151,
            'support_gradient_updates': 102, 'total_gradient_updates': 5253,
            'folds': 102, 'fresh_final_source_updates': 51})
        schema_pin = checkpoint_pin['schema_pin']
        _need(schema_pin['path'] == str(output / 'selected-state-schema.json'), 'exact owned checkpoint schema required')
        schema, _ = audit.document(Path(schema_pin['path']), expected=schema_pin['file_sha256'], canonical_raw=True)
        audit.M.old.fields(schema, {'schema': 'cho51_linear_chain_full_state_schema_v1',
            'model_state_sha256': fit['fitted_state_sha256'], 'weights_sha256': checkpoint_pin['weights_sha256'],
            'weights_bytes': checkpoint_identity[2], 'tensor_count': 223, 'elements': 5818138,
            'roundtrip_verified': True, 'all_finite_cpu_float32': True, 'published': False,
            'selected_model_recipe_sha256': selected_recipe_sha})
        _need(checkpoint_pin['weights_sha256'] == checkpoint_identity[-1]
              and len(schema['tensors']) == 223
              and sum(row['elements'] for row in schema['tensors'].values()) == 5818138,
              'full223-tensor checkpoint schema differs')
        own_paths.update((selection_path, Path(schema_pin['path'])))
    else:
        _need(result['final_source_updates'] == 0 and result['selected_candidate'] is None,
              'fold fragment cannot claim a final fit or winner')
        refusals, _ = audit.document(output / 'finalization-refusals.json', canonical_raw=True)
        _need(refusals['actual_final_source_updates'] == 0, 'incomplete fragment performed final-source updates')
        own_paths.add(output / 'finalization-refusals.json')
    refusals_path = output / 'finalization-refusals.json'
    refusals, _ = audit.document(refusals_path, canonical_raw=True)
    _, refusal_identity = audit.check(refusals_path, compact=True, proof=True)
    audit.M.old.fields(result['finalization_refusals'], {'path': str(refusals_path),
        'file_sha256': refusal_identity[-1], 'size_bytes': refusal_identity[2]})
    _need(refusals['actual_final_source_updates'] == (51 if final else 0)
          and refusals['complete_native_origins_capability_exercised'] is final
          and refusals['final_numerical_branch_qualified'] is final,
          'finalization refusal/complete capability witness differs')
    expected_refusals = []
    if not final:
        stages = [('before_current_fragment', len(history.records), 0)]
        if len(combined) < 102:
            stages.append(('after_current_fragment', len(combined), budget['gradient_updates']))
        expected_refusals = [{'stage': stage, 'records': count,
            'reason': 'all 102 distinct canonical folds are required before a fresh final source fit',
            'observed_updates_before': updates, 'observed_updates_after': updates,
            'before_fit': True, 'origin_capability_called': False} for stage, count, updates in stages]
    _need(refusals['refusals'] == expected_refusals
          and result['incomplete_finalization_refusal_count'] == len(expected_refusals),
          'exact incomplete-before-fit refusal history differs')
    own_paths.add(refusals_path)
    own_paths.update(dispatched_paths)
    if request['index'] == 1:
        own_paths.update(output / name for name in ('junit.xml', 'pytest.log'))
    own_paths.update(output / name for name in ('qualification.json', 'result.json', 'probe-result.json',
        'partial-collection.json', 'optimizer-observations.json'))
    native_directory = Path(proof_refs['native_directory'])
    own_paths.update(path for path in native_directory.iterdir() if path.is_file())
    own_proofs = {}
    for path in sorted(own_paths):
        _, pin = audit.check(path, compact=True, proof=True)
        own_proofs[path.relative_to(ROOT).as_posix()] = pin[-1]
    leaf = {'schema': 'cho51_linear_authenticated_leaf_v1', 'index': request['index'], 'mode': request['mode'],
        'root_origin_sha256': _physical(history.root_origin), 'pins_sha256': history.pins_sha256,
        'parent_head_sha256': history.head_sha256, 'request_path': request_path.relative_to(ROOT).as_posix(),
        'request_sha256': request_sha, 'pairs': _snapshot(request['pairs']),
        'accepted_folds_before': len(history.records), 'accepted_folds_after': len(combined),
        'native_directory': str(native_directory), 'native_receipt_sha256': native['receipt_file_sha256'],
        'qualification_sha256': q_sha, 'result_sha256': child_sha, 'probe_result_sha256': result_sha,
        'raw_fold_records': references, 'proofs': dict(sorted(own_proofs.items())),
        'actual_source_updates': budget['source_updates'], 'actual_support_updates': budget['support_updates'],
        'actual_gradient_updates': budget['gradient_updates'], 'final_source_updates': 51 if final else 0,
        'canonical_source_sha256': CANONICAL, 'scientific_admission': False, 'original_case_attempts': 0}
    audit.finish()
    return _snapshot(leaf), _snapshot(records)


def authenticate_fragment(history: VerifiedHistory, request: dict, proof_refs: dict, root: Path) -> dict:
    """Authenticate one current accepted attempt; no writes and no ancestor recursion."""
    return _authenticate(history, request, proof_refs, root)[0]


def _descriptor(leaf, digest):
    return {'index': leaf['index'], 'path': RUN_RELATIVE + f"/fragments/fragment_{leaf['index']:03d}/leaf.json",
        'sha256': digest, 'request_sha256': leaf['request_sha256'],
        'parent_head_sha256': leaf['parent_head_sha256'], 'mode': leaf['mode'], 'pairs': leaf['pairs'],
        'accepted_folds_before': leaf['accepted_folds_before'], 'accepted_folds_after': leaf['accepted_folds_after']}


def close_leaf(history: VerifiedHistory, request: dict, proof_refs: dict, root: Path) -> dict:
    """Create only the accepted leaf once; caller owns locked chain advancement."""
    leaf = authenticate_fragment(history, request, proof_refs, root)
    descriptor = _descriptor(leaf, _physical(leaf))
    path = ROOT / descriptor['path']
    _need(path.parent.resolve(strict=True) == path.parent, 'direct existing fragment output required')
    raw = _canonical(leaf) + b'\n'
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    _need(path.read_bytes() == raw, 'durable leaf bytes differ after publication')
    return _snapshot(descriptor)


def complete_origin_callback(history: VerifiedHistory):
    """Produce the exact frozen selector receipt without reading protected input bytes."""
    _need(isinstance(history, VerifiedHistory) and history._token is _TOKEN
          and history.chain['chain_index'] == 6
          and len(history.records) == 102 and len(history.accepted_pairs) == 102
          and _logical(history.records) == history._records_sha256,
          'complete authenticated102-fold capability required')
    audit = history._audit
    method, _ = audit.document(Path(history.root_origin['method_config_path']),
        expected=history.root_origin['method_config_file_sha256'], canonical_raw=True)
    expected_metadata = audit.contract.require_complete_folds(history.records, method,
        input_identity_sha256=INPUT, template_state_sha256=INITIAL,
        initial_state_sha256=INITIAL, lineage_recipe_sha256=RECIPE)
    expected_records = _logical(history.records)
    proofs = dict(history.proof_identities)
    inputs = dict(history.input_identities)

    def verify_origins(records, metadata):
        _need(_logical(records) == expected_records and _canonical(metadata) == _canonical(expected_metadata),
              'complete records or advisory metadata changed across capability boundary')
        for path, pin in proofs.items():
            _need(audit.M.old.inspect(Path(path), compact=True)[1] == pin,
                  'compact origin proof changed inside final-fit boundary')
        for path, pin in inputs.items():
            info = Path(path).stat()
            _need((info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns) == pin[:-1],
                  'shared input identity changed inside protected final-fit boundary')
        return {'schema': 'cho51_linear_complete_native_origins_v1', 'passed': True,
            'complete_manifest_sha256': metadata['sha256'], 'contract_sha256': CONTRACT,
            'raw_fold_count': 102, 'all_native_receipts_verified': True,
            'record_sha256': _snapshot(metadata['record_sha256'])}
    return verify_origins
