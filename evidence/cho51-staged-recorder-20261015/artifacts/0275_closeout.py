"""Compact proof archive for one complete synthetic EEGNet source selection.

Only standard-library metadata, receipt and byte verification; no model or
array import, tensor restore, recorder construction, test or process launch.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import re
import stat
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path, PurePosixPath

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
OUT = ROOT / 'evidence/cho51-complete-eegnet-successor-004-20261015'
CANDIDATE = ROOT / 'docs/phase2/cho51_complete_eegnet_v2'
PRIOR = ROOT / 'runs/coordination/cho51_complete_eegnet_20261015_v3/pins.json'
PRIOR_SHA = '5e551c2e90289eef299e96095c5f7c7fba4ed4629d5a895fbcad2ba58d36bc84'
PUBLICATION_PRIOR = ROOT / 'runs/coordination/cho51_complete_eegnet_20261015_v2/pins.json'
PUBLICATION_PRIOR_SHA = '68f582bf8ccb75b2c07690175bcc4af8e11d067db9504d62afb7560331ddb037'
RESTORE_PACKET = ROOT / 'evidence/cho51-complete-eegnet-restore-refusal-20261015'
RESTORE_PACKET_MANIFEST_SHA = '054b20b5d82db96e483ac0c7525c66316ebeab79c162ef6e1cc4c61fa0f88933'
RESTORE_PACKET_SUMMARY_SHA = '8067dcbe63ebdc206d62f2a207d7d23a49a204421d6e1a2c475fda6ab4a187c3'
STARTUP_PRIOR = ROOT / 'runs/coordination/cho51_complete_eegnet_20261015_v1/pins.json'
STARTUP_PRIOR_SHA = 'feb80ac54ea0dfb982f6a86a6dec84315dce5e0593934e155a924b01ecd216f4'
PARTIAL_PACKET = ROOT / 'evidence/cho51-complete-eegnet-publication-refusal-20261015'
PARTIAL_PACKET_MANIFEST_SHA = '304ac336788aea11a424486a1f43aebdd95b3bff133937d47eb8f9496e840fed'
PARTIAL_PACKET_SUMMARY_SHA = 'd4ad8b552a980e1851cb2ad42d4002a570a99a1716d87532686fabe07fa608b8'
PRIOR_NATIVE = ROOT / 'runs/migration/20261015T124552Z_4ab1a7c6a6'
PRIOR_PACKET = ROOT / 'evidence/cho51-complete-eegnet-refusal-20261015'
PRIOR_PACKET_MANIFEST_SHA = '93e0e05617bfaf9e464d7d563cde208b70dc07f0683536fa4e9ae0690632b0f6'
PRIOR_PACKET_SUMMARY_SHA = '4f6b3dd2908ef031334e76aa48df7969e41161b4fa7d04d7a92885c78101406f'
PRIOR_FAILURE_FILES = {
    'runs/coordination/cho51_complete_eegnet_20261015_v1/dispatch_001.json':
        '3dfb62a0412efd89e1de16921cc387e4a5f379084b3a8f804fdef7171739b49d',
    'runs/coordination/cho51_complete_eegnet_20261015_v1/dispatch_result_001.json':
        '9d979fc50b25c12391707228df71bbf639304459e1c4006c3e1530b6035ef545',
    'runs/migration/20261015T124552Z_4ab1a7c6a6/admission.json':
        'a5a92d696903d9042c855a4a79234d35242f59ffadf8c1e5e7bf75e5ef8df489',
    'runs/migration/20261015T124552Z_4ab1a7c6a6/receipt.json':
        '530c7cb6a7c339b418f232980de92cca6a6b69e26e99f1998d55d4cd0bb5f27f',
    'runs/migration/20261015T124552Z_4ab1a7c6a6/command.log':
        '6ca9fc0f733c59e6be87186b1de820389b7c0bc13ad29fca45a53278f1360e42',
    'runs/migration/20261015T124552Z_4ab1a7c6a6/deadline.json':
        '8eb36c9fff3a3d4462352cd4c4a559e2c8bb67afb7dc381ba75db8896e29ca83',
}
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
OWNER = 'ae3295c2aa5acdfad2c9b2d7ffb602ec8b0daddb07b3d433d15dcaf9fd002709'
PAUSE = Path('D:/Aenv/pro2/WORK/resume-20261015-001/coordination/PRO2_REQUEST_PRO3_PAUSE.json')
MAXIMUM_COMPACT = 8 * 1024**2
sys.path.insert(0, str(ROOT / 'tools/migration'))
from common import io_path, source_check


def signature(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def direct(path):
    path = Path(path)
    if not path.is_absolute() or path.resolve(strict=True) != path:
        raise ValueError('direct absolute existing path required: ' + str(path))
    for ancestor in (path, *path.parents):
        info = io_path(ancestor).lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
            raise ValueError('linked/reparse artifact refused: ' + str(path))
    return path


def inspect(path, *, compact=False, single_link=True):
    path = direct(path)
    before = io_path(path).stat()
    if (not stat.S_ISREG(before.st_mode) or single_link and before.st_nlink != 1
            or compact and before.st_size > MAXIMUM_COMPACT):
        raise ValueError('bounded direct regular artifact required: ' + str(path))
    with io_path(path).open('rb') as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(MAXIMUM_COMPACT + 1) if compact else None
        value = hashlib.sha256(raw).hexdigest() if compact else hashlib.file_digest(stream, 'sha256').hexdigest()
        closed = os.fstat(stream.fileno())
    # Windows path stat and fstat can disagree about ctime. Only compare it
    # within the same API; cross-API identity retains dev/ino/size/mtime.
    if (signature(io_path(path).stat()) != signature(before)
            or signature(opened) != signature(closed)
            or signature(opened)[:4] != signature(before)[:4]
            or compact and len(raw) != before.st_size):
        raise ValueError('physical artifact changed while reading: ' + str(path))
    return raw, (*signature(before), value)


def decode(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result

    def constant(value):
        raise ValueError('nonfinite JSON: ' + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(value):
    if type(value) is not str or re.fullmatch('[a-f0-9]{64}', value) is None:
        raise ValueError('plain SHA256 required')
    return value


def fields(value, expected, *, exact=False):
    if (type(value) is not dict or exact and set(value) != set(expected)
            or any(key not in value or type(value[key]) is not type(want)
                   or canonical(value[key]) != canonical(want) for key, want in expected.items())):
        raise ValueError('literal typed evidence fields differ: ' + ','.join(expected))


def utc(value):
    if type(value) is not str:
        raise ValueError('UTC timestamp required')
    parsed = datetime.fromisoformat(value)
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError('explicit UTC timestamp required')
    return parsed


def write(path, value):
    with io_path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def verify_native(directory, command, seconds, process_mib, job_mib, *, operations, runtimes,
                  document, remember, launcher, expected_failure=False):
    directory = direct(Path(directory))
    if (directory.parent != ROOT / 'runs/migration'
            or re.fullmatch(r'\d{8}T\d{6}Z_[a-f0-9]{10}', directory.name) is None):
        raise ValueError('direct independently dispatched native migration directory required')
    admission, _ = document(directory / 'admission.json')
    receipt, receipt_sha = document(directory / 'receipt.json')
    deadline_document, _ = document(directory / 'deadline.json')
    name = 'pro3_migration_' + directory.name
    fields(admission, {
        'schema': 'migration_admission_v1', 'source_sha256': CANONICAL, 'command': command,
        'operation_pins': operations, 'selected_runtime_pins': runtimes,
        'process_mib': process_mib, 'job_mib': job_mib, 'active_ram_gib': 4, 'active_disk_gib': 20,
        'native_threads': 1, 'peer_pause_file': str(PAUSE),
    })
    fields(receipt, {'schema': 'migration_guard_receipt_v1', 'accepted': not expected_failure,
        'job_name': name, 'job_absent': True, 'scientific_admission': False})
    if expected_failure:
        if type(receipt.get('error')) is not str or not receipt['error']:
            raise ValueError('preserved failed native command requires its nonempty error')
    elif receipt.get('error') is not None:
        raise ValueError('accepted native command must have no error')
    state, result = receipt['native_state'], receipt['result']
    flags = ('job_created', 'created_suspended', 'limits_set', 'limits_query_verified',
             'atomic_job_assignment_requested', 'atomic_job_assignment_verified', 'assigned',
             'membership_verified', 'resumed', 'job_empty_before_close', 'job_closed',
             'process_handle_closed', 'thread_handle_closed', 'root_exit_after_job_close', 'assignment_step_seen')
    fields(state, dict.fromkeys(flags, True) | {'job_named': name, 'cleanup_errors': [],
        'peak_sampling_errors': [], 'process_limit_bytes': process_mib * 1024**2,
        'aggregate_limit_bytes': job_mib * 1024**2})
    fields(result, {'reason': 'normal', 'exit_code': 1 if expected_failure else 0})
    if type(state.get('peak_samples')) is not int or state['peak_samples'] < 1:
        raise ValueError('positive actual native peak sample count required')
    for key, result_key, limit in (
        ('peak_process_commit_bytes', 'peak_process_memory_bytes', process_mib * 1024**2),
        ('peak_job_commit_bytes', 'peak_job_memory_bytes', job_mib * 1024**2),
    ):
        if type(state.get(key)) is not int or not 0 < state[key] <= limit:
            raise ValueError('positive actual native peaks within independently declared memory caps required')
        fields(result, {result_key: state[key]})
    if state['peak_job_commit_bytes'] < state['peak_process_commit_bytes']:
        raise ValueError('native aggregate peak cannot be below process peak')
    samples = admission.get('startup_samples')
    if type(samples) is not list or len(samples) != 2 or receipt.get('startup_samples') != samples:
        raise ValueError('two identical fresh native startup observations required')
    for sample in samples:
        if (type(sample) is not dict or type(sample.get('available_ram_bytes')) is not int
                or sample['available_ram_bytes'] < 10 * 1024**3
                or type(sample.get('free_disk_bytes')) is not int or sample['free_disk_bytes'] < 20 * 1024**3):
            raise ValueError('fresh startup RAM10/disk20 resource floors required')
    start, deadline, end = (utc(value) for value in (
        admission['started_utc'], admission['deadline_utc'], receipt['completed_utc']))
    if (deadline - start).total_seconds() != seconds or not start <= end <= deadline:
        raise ValueError('exact timely finite UTC native interval required')
    fields(deadline_document, {'schema': 'phase2_supervision_deadlines_v1',
                              'attempt_deadline_utc': admission['deadline_utc']})
    if (utc(deadline_document['session_deadline_utc']) - deadline).total_seconds() != 5:
        raise ValueError('exact five-second native session margin required')
    for path in directory.iterdir():
        if path.is_file() and path.name.startswith('command'):
            remember(path, compact=True, archive=True)
    launcher._job_absent(name)
    return dict(native_directory=str(directory), job_name=name, seconds=seconds,
        process_mib=process_mib, job_mib=job_mib, started_utc=admission['started_utc'],
        completed_utc=receipt['completed_utc'], elapsed_native_seconds=(end - start).total_seconds(),
        peak_process_bytes=state['peak_process_commit_bytes'], peak_job_bytes=state['peak_job_commit_bytes'],
        receipt_file_sha256=receipt_sha, accepted=not expected_failure, native_job_closed_empty_freshly_absent=True)


def verify_complete_history(record, method_template, *, protocol_sha256, source_selection_sha256,
                            fixture_source_sha256):
    """Independently count complete public evidence and rederive its rational winner."""
    payload = record.get('payload') if type(record) is dict else None
    envelope = dict(schema_version=1, phase=2, kind='engineering_smoke', payload=payload)
    envelope['sha256'] = hashlib.sha256(canonical(envelope)).hexdigest()
    fields(record, envelope, exact=True)
    if type(payload) is not dict or set(payload) != {
        'purpose', 'contract', 'contract_sha256', 'complete', 'folds', 'selected_candidate',
        'scores', 'final_source_fit', 'outer_target_predictions_performed'}:
        raise ValueError('unaltered actual complete public EEGNet evidence schema required')
    fields(payload, dict(purpose='bounded_eegnet_source_selection', complete=True,
                         outer_target_predictions_performed=False))
    contract = payload['contract']
    fields(contract, dict(method='eegnet', dataset='cho2017', outer_target='subject_02',
        shots_per_class=5, maximum_gradient_steps=5253, engineering_only=True, scientific_evaluation=False,
        early_stopping=False, protocol_sha256=protocol_sha256, candidates=method_template['candidates'],
        source_policy=method_template['source_policy'], score=method_template['score'],
        tie_break=method_template['tie_break']))
    if hashlib.sha256(canonical(contract)).hexdigest() != sha(payload['contract_sha256']):
        raise ValueError('complete public selector contract logical digest differs')
    fields(contract.get('source'), {'source_sha256': fixture_source_sha256})
    fields(contract.get('runtime'), dict(device='cpu', torch_threads=1))
    source_subjects = ['subject_01', *[f'subject_{subject:02d}' for subject in range(3, 53)]]
    selection = contract.get('selection')
    if type(selection) is not dict or set(selection) != {
        'dataset', 'target_subject', 'source_subjects', 'inner_folds', 'catalog_sha256'}:
        raise ValueError('complete canonical SourceSelection logical schema required')
    catalogs = selection.get('catalog_sha256')
    if (type(catalogs) is not list or len(catalogs) != 52
            or any(type(row) is not list or len(row) != 2 for row in catalogs)
            or [row[0] for row in catalogs] != [f'subject_{s:02d}' for s in range(1, 53)]):
        raise ValueError('all52 ordered source-catalog digests required')
    for _, value in catalogs:
        sha(value)
    expected_selection = dict(dataset='cho2017', target_subject='subject_02', source_subjects=source_subjects,
        catalog_sha256=catalogs, inner_folds=[dict(validation_subject=validation,
            training_subjects=[subject for subject in source_subjects if subject != validation])
            for validation in source_subjects])
    fields(selection, expected_selection, exact=True)
    if hashlib.sha256(canonical(expected_selection)).hexdigest() != sha(source_selection_sha256):
        raise ValueError('public source selection differs from independently checked fixture identity')
    candidates = method_template['candidates']
    if type(candidates) is not list or len(candidates) != 2:
        raise ValueError('two independently pinned ordered adopted candidates required')
    names = [candidate['name'] for candidate in candidates]
    if len(set(names)) != 2:
        raise ValueError('adopted candidate names must be distinct')

    def fit_history(fit, candidate, validation):
        subjects = [subject for subject in source_subjects if subject != validation]
        fields(fit, dict(candidate=candidate['name'], candidate_sha256=hashlib.sha256(canonical(candidate)).hexdigest(),
            validation_subject=validation, training_subjects=subjects, seed=11,
            settings=candidate['source'], engineering_only=True,
            trainable_parameters='all', normalization_and_dropout='all_modules_eval',
            history_scope='complete_for_this_bounded_fit_only'))
        fields(fit.get('optimizer'), dict(name='SGD', momentum=0, weight_decay=0, fresh=True), exact=True)
        if type(fit.get('input_identities')) is not dict or set(fit['input_identities']) != set(subjects):
            raise ValueError('source fit input identities must cover exactly its permitted source subjects')
        steps = fit.get('steps')
        if type(steps) is not list or len(steps) != len(subjects):
            raise ValueError('complete one-update-per-source fit history required')
        previous = sha(fit['initial_state_sha256'])
        for index, (subject, step) in enumerate(zip(subjects, steps, strict=True), start=1):
            fields(step, dict(step=index, subject=subject, subject_step=1, iterator_wraps=0))
            trial_ids = step.get('trial_ids')
            if (type(trial_ids) is not list or len(trial_ids) != 4 or len(set(trial_ids)) != 4
                    or any(type(trial) is not str or not trial for trial in trial_ids)
                    or type(step.get('loss')) not in (int, float) or not math.isfinite(step['loss'])
                    or sha(step['state_sha256_after']) == previous):
                raise ValueError('one finite changing four-trial source update per subject required')
            previous = step['state_sha256_after']
        if previous != sha(fit['fitted_state_sha256']):
            raise ValueError('complete source-fit terminal state differs from last real update')
        return len(steps)

    folds = payload['folds']
    if type(folds) is not list or len(folds) != 102:
        raise ValueError('actual 102 complete candidate/inner-validation folds required')
    source_updates, support_updates, scores = 0, 0, []
    for candidate_index, candidate in enumerate(candidates):
        values = []
        for validation_index, validation in enumerate(source_subjects):
            fold = folds[candidate_index * 51 + validation_index]
            fields(fold, dict(candidate=candidate['name'], validation_subject=validation))
            source_updates += fit_history(fold['source_fit'], candidate, validation)
            support = fold['support_fit']
            fields(support, dict(source_fit_performed=False, trainable_parameters=2642))
            losses = support.get('support_losses')
            if (type(losses) is not list or len(losses) != 1
                    or type(losses[0]) not in (int, float) or not math.isfinite(losses[0])):
                raise ValueError('one finite actual support update per inner fold required')
            support_updates += 1
            if sha(fold['adapted_state_sha256']) == sha(fold['source_fit']['fitted_state_sha256']):
                raise ValueError('inner support adaptation must change source state')
            if (type(fold.get('support_trial_ids')) is not list or len(fold['support_trial_ids']) != 10
                    or type(fold.get('query_trial_ids')) is not list or len(fold['query_trial_ids']) != 2
                    or set(fold['support_trial_ids']) & set(fold['query_trial_ids'])
                    or type(fold.get('input_identities')) is not dict or set(fold['input_identities']) != {validation}):
                raise ValueError('exact held-out ten-support/two-query inner fold binding required')
            confusion = fold.get('confusion_matrix')
            if (type(confusion) is not list or len(confusion) != 2
                    or any(type(row) is not list or len(row) != 2 or sum(row) != 1
                           or any(type(value) is not int or value < 0 for value in row) for row in confusion)):
                raise ValueError('two actual held-out binary query predictions required')
            value = (Fraction(confusion[0][0], sum(confusion[0]))
                     + Fraction(confusion[1][1], sum(confusion[1]))) / 2
            fields(fold, {'balanced_accuracy': [value.numerator, value.denominator]})
            values.append(value)
        scores.append(sum(values, Fraction()) / 51)
    expected_scores = [dict(candidate=candidate['name'], mean_balanced_accuracy=[value.numerator, value.denominator])
                       for candidate, value in zip(candidates, scores, strict=True)]
    fields(payload, {'scores': expected_scores})
    winner = candidates[max(range(2), key=lambda index: scores[index])]
    fields(payload, {'selected_candidate': winner['name']})
    source_updates += fit_history(payload['final_source_fit'], winner, None)
    if source_updates != 5151 or support_updates != 102:
        raise ValueError('complete selector must contain exactly 5151 source and 102 support updates')
    return dict(evidence_sha256=record['sha256'], contract_sha256=payload['contract_sha256'],
        selected_candidate=winner['name'], selected_state_sha256=payload['final_source_fit']['fitted_state_sha256'],
        source_gradient_updates=source_updates, support_gradient_updates=support_updates,
        actual_gradient_updates=5253, inner_folds=102, final_source_subjects=51, scores=expected_scores)


def main():
    identities, paths, runtime_paths, jobs = {}, set(), set(), []

    def remember(path, *, compact=False, expected=None, archive=False, single_link=True):
        path = Path(path)
        raw, observed = inspect(path, compact=compact, single_link=single_link)
        if expected is not None and observed[-1] != sha(expected):
            raise ValueError('independent physical file SHA differs: ' + str(path))
        if identities.setdefault(path, observed) != observed:
            raise ValueError('physical file identity drifted across verification: ' + str(path))
        if archive:
            if not compact or not path.is_relative_to(ROOT):
                raise ValueError('only bounded owned compact metadata can be archived')
            paths.add(path)
        return raw, observed

    def document(path, *, expected=None, archive=True, canonical_raw=False):
        raw, observed = remember(path, compact=True, expected=expected, archive=archive)
        value = decode(raw)
        if type(value) is not dict or canonical_raw and raw != canonical(value) + b'\n':
            raise ValueError('exact canonical JSON object required: ' + str(path))
        return value, observed[-1]

    def relative_path(relative):
        if (type(relative) is not str or PurePosixPath(relative).is_absolute()
                or PurePosixPath(relative).as_posix() != relative
                or any(part in ('', '.', '..') or part.endswith(('.', ' ')) for part in relative.split('/'))
                or re.search(r'[<>:"\\|?*\x00-\x1f]', relative)):
            raise ValueError('safe canonical relative file path required')
        return PurePosixPath(relative)

    pin_path = RUN / 'pins.json'
    pins, pins_sha = document(pin_path)
    fields(pins, {
        'schema': 'cho51_complete_eegnet_fresh_pins_v1', 'canonical_source_sha256': CANONICAL,
        'canonical_files': 432, 'predecessor_files': 620, 'predecessor_pins_sha256': PRIOR_SHA,
        'owner_decision_sha256': OWNER, 'outer_seconds': 600, 'process_mib': 4096, 'job_mib': 6144,
        'source_seconds': 420, 'source_process_mib': 3072, 'source_job_mib': 4096,
        'detached_seconds': 90, 'detached_process_mib': 2048, 'detached_job_mib': 3072,
        'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20, 'threads': 1, 'gpu_hidden': True,
        'actual_gradient_updates': 5253, 'source_updates': 5151, 'support_updates': 102,
        'fold_count': 102, 'final_source_subjects': 51, 'source_subjects_available': 52,
        'channels': 64, 'samples': 512, 'full_scientific_worker_verified': False,
        'scientific_admission': False, 'original_case_attempts_remaining': 0,
    })
    if (type(pins.get('files')) is not dict or type(pins.get('runtime')) is not dict or len(pins['runtime']) != 5
            or type(pins.get('expected_tests')) is not int or not 20 <= pins['expected_tests'] <= 35):
        raise ValueError('complete independent source/runtime/boundary-test inventories required')
    prior, _ = document(PRIOR, expected=PRIOR_SHA)
    if (len(prior['files']) != 620 or prior['runtime'] != pins['runtime']
            or any(pins['files'].get(name) != digest for name, digest in prior['files'].items())):
        raise ValueError('all 620 predecessor file pins and five runtimes must remain exact')
    canonical_manifest, _ = document(ROOT / 'tools/migration/source-files.json', archive=False)
    if (canonical_manifest.get('source_sha256') != CANONICAL or len(canonical_manifest['files']) != 432
            or any(pins['files'].get(row['path']) != row['sha256'] for row in canonical_manifest['files'])):
        raise ValueError('all exact 432 canonical source pins required')

    def current_pins():
        if source_check(ROOT) != CANONICAL:
            raise ValueError('canonical source changed')
        remember(pin_path, compact=True, expected=pins_sha)
        for relative, expected in pins['files'].items():
            remember(ROOT.joinpath(*relative_path(relative).parts), expected=expected)
        for name, expected in pins['runtime'].items():
            runtime_paths.add(Path(name))
            remember(Path(name), expected=expected, single_link=False)

    current_pins()
    review_path = RUN / 'source-review.json'
    fields(pins, {'source_review_path': str(review_path)})
    review, _ = document(review_path, expected=pins['source_review_sha256'])
    fields(review, {'source_only': True, 'remaining_actionable_findings': [], 'files': pins['reviewed_files']})
    candidate_names = ('inputs.py', 'transaction.py', 'test_transaction.py', 'selection.py', 'README.md')
    operation_names = ('prepare.py', 'parent.py', 'select_child.py', 'verify_child.py', 'launch.ps1', 'observe.py', 'closeout.py')
    reviewed = {path.relative_to(ROOT).as_posix() for path in (
        *(CANDIDATE / name for name in candidate_names), *(RUN / name for name in operation_names))}
    if set(pins['reviewed_files']) != reviewed or set(CANDIDATE.iterdir()) != {CANDIDATE / name for name in candidate_names}:
        raise ValueError('exact twelve candidate/operational source reviews required')
    for relative, expected in pins['reviewed_files'].items():
        remember(ROOT / relative, compact=True, expected=expected, archive=True)
    for path in RUN.iterdir():
        if path.is_file() and path.suffix.lower() in {'.py', '.ps1', '.json'}:
            remember(path, compact=True, archive=True)
    method_path = RUN / 'method-config.json'
    design_path = ROOT / 'docs/phase2/cho_design_decisions_20261012.json'
    fields(pins, {'method_config_path': str(method_path), 'design_decision_path': str(design_path)})
    method_template, method_file_sha = document(method_path, expected=pins['method_config_file_sha256'], canonical_raw=True)
    method_sha = hashlib.sha256(canonical(method_template)).hexdigest()
    if method_sha != sha(pins['method_config_sha256']):
        raise ValueError('independent adopted method logical digest differs')
    expected_candidates = [dict(name=name,
        source=dict(batch_size=4, input_scale=1000000.0, learning_rate=rate, steps_per_subject=1),
        support=dict(input_scale=1000000.0, learning_rate=rate, query_batch_size=8, steps=1))
        for name, rate in (('lr_1e-3', 0.001), ('lr_2e-3', 0.002))]
    fields(method_template, dict(method='eegnet', dataset='cho2017', input_profile='cho_profile_a',
        variant_config_sha256=None, candidates=expected_candidates, source_seed_policy='none',
        source_policy='all_non_target_subjects; inner_validation_also_excluded',
        score='mean_subject_balanced_accuracy_exact_rational', tie_break='first_in_declared_candidate_order',
        early_stopping=False), exact=True)
    design, _ = document(design_path, expected=pins['design_decision_sha256'])
    adopted = [row for row in design['adopted_design']['candidate_template']['methods'] if row.get('method') == 'eegnet']
    if len(adopted) != 1 or canonical(adopted[0]) != canonical(method_template):
        raise ValueError('independently adopted EEGNet method row differs from executed template')
    launcher_path = ROOT / 'docs/phase2/cho51_tensor_verification_v1/launcher.py'
    remember(launcher_path, expected=pins['files'][launcher_path.relative_to(ROOT).as_posix()])
    spec = importlib.util.spec_from_file_location('_complete_eegnet_closeout_stdlib', launcher_path)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    view = {'files': {str(ROOT / name): value for name, value in pins['files'].items()}, 'runtime': pins['runtime']}
    operations, runtimes = launcher._guard_operation_pins(view), launcher._guard_runtime_pins(view)
    startup_pins, _ = document(STARTUP_PRIOR, expected=STARTUP_PRIOR_SHA)
    # Preserve and independently requalify the prior failed parent. Its pytest
    # dots never reached normal session completion; no fixture/case work began.
    for relative, expected in PRIOR_FAILURE_FILES.items():
        remember(ROOT / relative, compact=True, expected=expected, archive=True)
    for relative, expected in startup_pins['reviewed_files'].items():
        remember(ROOT / relative, compact=True, expected=expected, archive=True)
    document(STARTUP_PRIOR.parent / 'source-review.json', expected=startup_pins['source_review_sha256'])
    document(STARTUP_PRIOR.parent / 'method-config.json', expected=startup_pins['method_config_file_sha256'], canonical_raw=True)
    prior_command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(STARTUP_PRIOR.parent / 'parent.py'),
        '--pins', str(STARTUP_PRIOR), '--expect-pins', STARTUP_PRIOR_SHA, '--output', str(STARTUP_PRIOR.parent / 'validation_001')]
    prior_dispatch, _ = document(STARTUP_PRIOR.parent / 'dispatch_001.json')
    prior_dispatch_result, _ = document(STARTUP_PRIOR.parent / 'dispatch_result_001.json')
    prior_common = dict(pins_sha256=STARTUP_PRIOR_SHA, child_command=prior_command,
        expected_output=str(STARTUP_PRIOR.parent / 'validation_001'), scientific_admission=False)
    fields(prior_dispatch, prior_common | {'schema': 'cho51_complete_eegnet_dispatch_v1'})
    fields(prior_dispatch_result, prior_common | {'schema': 'cho51_complete_eegnet_dispatch_result_v1',
        'guard_exit_code': 1, 'native_directory': str(PRIOR_NATIVE)})
    prior_job = verify_native(PRIOR_NATIVE, prior_command, 600, 4096, 6144, operations=operations,
        runtimes=runtimes, document=document, remember=remember, launcher=launcher, expected_failure=True)
    if not utc(prior_dispatch['observed_utc']) <= utc(prior_job['started_utc']) <= utc(prior_job['completed_utc']) <= utc(prior_dispatch_result['observed_utc']):
        raise ValueError('preserved failed native execution differs from its independent dispatch UTC')
    prior_log, _ = remember(PRIOR_NATIVE / 'command.log', compact=True)
    if (not prior_log.startswith(b'.' * 33) or b'PermissionError: complete EEGNet child denied: os.chdir' not in prior_log
            or b'observed_actual_sgd_updates' in prior_log):
        raise ValueError('prior failure must remain the exact pre-fixture pytest cwd refusal')
    prior_packet_manifest, _ = document(PRIOR_PACKET / 'manifest.json', expected=PRIOR_PACKET_MANIFEST_SHA)
    prior_packet_summary, _ = document(PRIOR_PACKET / 'summary.json', expected=PRIOR_PACKET_SUMMARY_SHA)
    fields(prior_packet_summary, dict(schema='cho51_complete_eegnet_startup_refusal_v1',
        accepted=False, actual_complete_selector_gradient_updates=0, artifact_count=24,
        complete_selector_execution_claim_created=False, complete_selector_fixture_created=False,
        source_or_detached_child_launched=False, pytest_session_qualified=False,
        reason='pytest_session_cwd_restore_refused', test_bodies_reported_dots=33,
        pins_sha256=STARTUP_PRIOR_SHA, source_context_pins_rechecked=600, runtime_pins_rechecked=5,
        job_name=prior_job['job_name'], native_directory=str(PRIOR_NATIVE),
        native_job_closed_empty_freshly_absent=True, exit_code=1, cleanup_errors=[], peak_sampling_errors=[],
        measured_cells=0, original_case_attempts_remaining=0, scientific_admission=False))
    prior_packet_rows = prior_packet_manifest.get('artifacts')
    if type(prior_packet_rows) is not list or len(prior_packet_rows) != 24:
        raise ValueError('exact 24-artifact preserved predecessor-refusal packet required')
    prior_packet_paths = set()
    for row in prior_packet_rows:
        if type(row) is not dict or set(row) != {'source', 'path', 'bytes', 'sha256'}:
            raise ValueError('exact preserved predecessor-refusal artifact metadata required')
        relative = relative_path(row['path'])
        if relative.parts[0] != 'artifacts' or len(relative.parts) != 2:
            raise ValueError('short flat predecessor-refusal artifact path required')
        path = PRIOR_PACKET.joinpath(*relative.parts)
        _, observed = remember(path, compact=True, expected=row['sha256'])
        if type(row['bytes']) is not int or row['bytes'] != observed[2] or path in prior_packet_paths:
            raise ValueError('preserved refusal artifact size or identity differs')
        remember(ROOT.joinpath(*relative_path(row['source']).parts), compact=True, expected=row['sha256'])
        prior_packet_paths.add(path)

    def prior_failure_scope():
        old_output = STARTUP_PRIOR.parent / 'validation_001'
        for name in ('fixture', 'cases', 'qualification.json', 'junit.xml'):
            path = old_output / name
            if path.exists() or path.is_symlink():
                raise ValueError('prior refused test session must have no accepted qualification, fixture or numerical cases')
        if set(direct(PRIOR_PACKET / 'artifacts').iterdir()) != prior_packet_paths:
            raise ValueError('preserved 24-artifact refusal packet physical file set changed')
        launcher._job_absent(prior_job['job_name'])

    prior_failure_scope()

    publication_pins, _ = document(PUBLICATION_PRIOR, expected=PUBLICATION_PRIOR_SHA)
    # The second attempt completed a real selector but refused publication.
    # Bind the exact failed source/parent Jobs and its unaccepted raw history;
    # none of these bytes can satisfy the fresh accepted v3 proof below.
    partial_manifest, _ = document(PARTIAL_PACKET / 'manifest.json', expected=PARTIAL_PACKET_MANIFEST_SHA)
    partial_summary, _ = document(PARTIAL_PACKET / 'summary.json', expected=PARTIAL_PACKET_SUMMARY_SHA)
    fields(partial_summary, dict(schema='cho51_complete_eegnet_publication_refusal_v1', accepted=False,
        all_native_jobs_closed_empty_freshly_absent=True, artifact_count=38, boundary_tests_passed=33,
        claims=1, linked_failures=1, cleanup_errors=[], peak_sampling_errors=[],
        complete_record_described_gradient_updates=5253, detached_child_launched=False,
        engineering_successes=0, final_source_subjects=51, inner_folds=102,
        input_blobs_archived=False, measured_cells=0, original_case_attempts_remaining=0,
        pins_sha256=PUBLICATION_PRIOR_SHA, publication_accepted=False, source_qualification_accepted=False,
        selected_weights_persisted=False, source_context_pins_rechecked=610, runtime_pins_rechecked=5,
        reason='exact_owned_canonical_publication_lock_outside_declared_write_scope', scientific_admission=False))
    partial_rows = partial_manifest.get('artifacts')
    if type(partial_rows) is not list or len(partial_rows) != 38:
        raise ValueError('exact38 preserved publication-refusal artifacts required')
    partial_packet_paths = set()
    for row in partial_rows:
        if type(row) is not dict or set(row) != {'source', 'path', 'bytes', 'sha256'}:
            raise ValueError('exact partial-refusal source/copy metadata required')
        relative = relative_path(row['path'])
        if relative.parts[0] != 'artifacts' or len(relative.parts) != 2:
            raise ValueError('short flat publication-refusal artifact path required')
        copy_path = PARTIAL_PACKET.joinpath(*relative.parts)
        _, observed = remember(copy_path, compact=True, expected=row['sha256'])
        if type(row['bytes']) is not int or row['bytes'] != observed[2] or copy_path in partial_packet_paths:
            raise ValueError('publication-refusal copied size or uniqueness differs')
        remember(ROOT.joinpath(*relative_path(row['source']).parts), compact=True, expected=row['sha256'], archive=True)
        partial_packet_paths.add(copy_path)
    partial_plan = dict(dataset='cho2017', target_subject='subject_02', method='eegnet',
                        shots_per_class=5, model_seed=11, repetition=1)
    partial_case = hashlib.sha256(canonical(partial_plan)).hexdigest()
    partial_output = PUBLICATION_PRIOR.parent / 'validation_001'
    partial_fixture = partial_output / 'fixture'
    partial_recorder = partial_fixture / 'runs/phase2/lifecycle'
    partial_workspace = partial_output / 'cases' / partial_case
    partial_request_path = partial_workspace / 'request.json'
    partial_request, partial_request_sha = document(partial_request_path, canonical_raw=True)
    partial_claim_path = partial_recorder / 'claims' / (partial_case + '.attempt1.claim.json')
    partial_claim, partial_claim_sha = document(partial_claim_path,
        expected=partial_request['claim_file_sha256'], canonical_raw=True)

    def partial_envelope(record, payload):
        expected = dict(schema_version=1, phase=2, kind='engineering_smoke', payload=payload)
        expected['sha256'] = hashlib.sha256(canonical(expected)).hexdigest()
        fields(record, expected, exact=True)

    partial_source = partial_claim['payload']['source']
    fields(partial_source, {'source_sha256': partial_request['fixture_source_sha256']})
    if (type(partial_source.get('git_dirty')) is not bool
            or type(partial_source.get('git_commit')) is not str
            or re.fullmatch('[a-f0-9]{40}|[a-f0-9]{64}', partial_source['git_commit']) is None):
        raise ValueError('partial-refusal claim retains real fixture source provenance')
    partial_envelope(partial_claim, dict(purpose='pilot_case_claim', case=partial_plan,
        worker='cho51_synthetic_numerical_engineering', attempt=1,
        environment_sha256=sha(partial_request['environment_sha256']), source=partial_source, engineering_only=True))
    partial_identity_path = partial_fixture / 'synthetic-input-identity.json'
    partial_identity, partial_identity_file_sha = document(partial_identity_path,
        expected=partial_request['fixture_identity_file_sha256'], canonical_raw=True)
    partial_identity_logical = dict(partial_identity)
    partial_identity_sha = sha(partial_identity_logical.pop('sha256'))
    if hashlib.sha256(canonical(partial_identity_logical)).hexdigest() != partial_identity_sha:
        raise ValueError('partial-refusal synthetic input logical identity differs')
    fields(partial_request, dict(schema='cho51_complete_eegnet_request_v1', case_id=partial_case, plan=partial_plan,
        fixture_root=str(partial_fixture), recorder_root=str(partial_recorder), workspace=str(partial_workspace),
        pins_path=str(PUBLICATION_PRIOR), independent_pins_sha256=PUBLICATION_PRIOR_SHA, execution_source_sha256=CANONICAL,
        owner_decision_sha256=OWNER, claim_path=str(partial_claim_path), claim_file_sha256=partial_claim_sha,
        fixture_source_sha256=partial_source['source_sha256'], environment_sha256=partial_request['environment_sha256'],
        fixture_identity_path=str(partial_identity_path), fixture_identity_file_sha256=partial_identity_file_sha,
        fixture_identity_sha256=partial_identity_sha, method_config_path=str(PUBLICATION_PRIOR.parent / 'method-config.json'),
        method_config_file_sha256=publication_pins['method_config_file_sha256'], method_config_sha256=method_sha,
        selection_output=str(partial_workspace / 'source_output'), detached_output=str(partial_workspace / 'detached_output'),
        attempt=1, source_seconds=420, source_process_mib=3072, source_job_mib=4096,
        detached_seconds=90, detached_process_mib=2048, detached_job_mib=3072,
        actual_gradient_updates=5253, source_updates=5151, support_updates=102, fold_count=102, final_source_subjects=51,
        engineering_only=True, scientific_admission=False, original_case_attempts_remaining=0), exact=True)
    partial_inputs = partial_identity.get('files')
    if type(partial_inputs) is not dict or len(partial_inputs) != 213:
        raise ValueError('partial-refusal exact213 synthetic input pins required')
    partial_input_paths = set()
    for relative, pin in partial_inputs.items():
        path = partial_fixture.joinpath(*relative_path(relative).parts)
        if (type(pin) is not dict or set(pin) != {'sha256', 'size_bytes'}
                or type(pin['size_bytes']) is not int or not 0 <= pin['size_bytes'] <= 16 * 1024**2):
            raise ValueError('partial-refusal bounded typed input file pins required')
        _, observed = remember(path, expected=pin['sha256'])
        if observed[2] != pin['size_bytes']:
            raise ValueError('partial-refusal physical input size differs')
        partial_input_paths.add(path)
    partial_configurations = ('configs/base.toml', 'configs/benchmark.toml', 'configs/phase2/protocol.toml',
                             'configs/phase2/selection_ceiling.toml', 'configs/phase2/cho_profile_b_60hz.toml')
    partial_source_sha = hashlib.sha256('\n'.join(f'{name}:{partial_inputs[name]["sha256"]}'
        for name in sorted(partial_configurations)).encode()).hexdigest()
    if partial_source_sha != partial_source['source_sha256']:
        raise ValueError('partial-refusal independent fixture source fingerprint differs')
    partial_evidence_path = partial_fixture / ('runs/phase2/selection_evidence/'
        'c4e5d2ca3c97e50f302eb8dcc03fd7a899b969d1b4eca59ff54825a5e7e7642a.json')
    partial_record, _ = document(partial_evidence_path,
        expected='92d5bd0f79f6394f83ddd7f8ee86322bce2f604f039e74c9b2ffa76c9f22a5c7', canonical_raw=True)
    if identities[partial_evidence_path][2] != 4204515:
        raise ValueError('exact preserved unaccepted complete evidence bytes required')
    partial_history = verify_complete_history(partial_record, method_template,
        protocol_sha256=partial_identity['protocol_sha256'], source_selection_sha256=partial_identity['source_selection_sha256'],
        fixture_source_sha256=partial_source_sha)
    fields(partial_summary, dict(complete_evidence_path=str(partial_evidence_path), complete_evidence_file_bytes=4204515,
        complete_evidence_sha256=partial_record['sha256'], complete_record=partial_history))
    partial_outer_command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(PUBLICATION_PRIOR.parent / 'parent.py'),
        '--pins', str(PUBLICATION_PRIOR), '--expect-pins', PUBLICATION_PRIOR_SHA, '--output', str(partial_output)]
    partial_outer_dispatch, _ = document(PUBLICATION_PRIOR.parent / 'dispatch_001.json')
    partial_outer_result, _ = document(PUBLICATION_PRIOR.parent / 'dispatch_result_001.json')
    partial_common = dict(pins_sha256=PUBLICATION_PRIOR_SHA, child_command=partial_outer_command,
                         expected_output=str(partial_output), scientific_admission=False)
    fields(partial_outer_dispatch, partial_common | {'schema': 'cho51_complete_eegnet_dispatch_v1'})
    fields(partial_outer_result, partial_common | {'schema': 'cho51_complete_eegnet_dispatch_result_v1', 'guard_exit_code': 1})
    partial_outer = verify_native(Path(partial_outer_result['native_directory']), partial_outer_command, 600, 4096, 6144,
        operations=operations, runtimes=runtimes, document=document, remember=remember, launcher=launcher, expected_failure=True)
    partial_source_command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(PUBLICATION_PRIOR.parent / 'select_child.py'),
        '--request', str(partial_request_path), '--expect-request', partial_request_sha]
    partial_source_dispatch, _ = document(partial_workspace / 'source-native-dispatch.json')
    fields(partial_source_dispatch, dict(schema='cho51_complete_eegnet_inner_dispatch_v1', kind='source',
        request_sha256=partial_request_sha, case_id=partial_case, pins_sha256=PUBLICATION_PRIOR_SHA,
        child_command=partial_source_command, guard_exit_code=1, source_result_file_sha256=None, scientific_admission=False))
    partial_native_source = verify_native(Path(partial_source_dispatch['native_directory']), partial_source_command,
        420, 3072, 4096, operations=operations, runtimes=runtimes, document=document, remember=remember,
        launcher=launcher, expected_failure=True)
    if (not utc(partial_outer_dispatch['observed_utc']) <= utc(partial_outer['started_utc']) <= utc(partial_native_source['started_utc'])
            <= utc(partial_native_source['completed_utc']) <= utc(partial_outer['completed_utc']) <= utc(partial_outer_result['observed_utc'])
            or partial_outer['native_directory'] == partial_native_source['native_directory']):
        raise ValueError('preserved failed source/parent native intervals must be distinct and correctly nested')
    source_log, _ = remember(Path(partial_native_source['native_directory']) / 'command.log', compact=True)
    if (b'PermissionError: complete EEGNet child denied: outside_owned_write' not in source_log
            or b'with self._publication_lock()' not in source_log or b'"observed_actual_sgd_updates": 5000' not in source_log):
        raise ValueError('primary preserved refusal must remain the canonical publication-lock audit failure')
    partial_failure_path = partial_recorder / 'attempts' / (partial_case + '.attempt1.failure.json')
    partial_failure, _ = document(partial_failure_path, canonical_raw=True)
    reason = partial_failure['payload']['reason']
    fields(reason, dict(purpose='cho51_complete_eegnet_failure', request_sha256=partial_request_sha,
        engineering_only=True, scientific_admission=False, original_case_attempts_remaining=0))
    if type(reason.get('error')) is not str or not reason['error'].startswith('FileNotFoundError:') or 'qualification.json' not in reason['error']:
        raise ValueError('linked parent failure must preserve its separate missing-qualification symptom')
    partial_envelope(partial_failure, dict(purpose='pilot_case_failure', case=partial_plan, attempt=1,
        reason=reason, environment_sha256=partial_request['environment_sha256'], engineering_only=True))

    def partial_failure_scope():
        if set(direct(PARTIAL_PACKET / 'artifacts').iterdir()) != partial_packet_paths:
            raise ValueError('preserved38 publication-refusal artifacts changed')
        if ({path.name for path in direct(partial_output / 'cases').iterdir()} != {partial_case}
                or set(direct(partial_evidence_path.parent).iterdir()) != {partial_evidence_path}):
            raise ValueError('partial-refusal must retain exactly one original case and raw selector envelope')
        for directory, filename in (('claims', partial_case + '.attempt1.claim.json'),
                                    ('attempts', partial_case + '.attempt1.failure.json')):
            if {path.name for path in direct(partial_recorder / directory).iterdir()} != {filename}:
                raise ValueError('partial-refusal must retain exactly one linked claim/failure')
        for name in ('engineering_intents', 'engineering_successes', 'cells', 'successes', 'publication_intents'):
            path = partial_recorder / name
            if path.exists() or path.is_symlink():
                direct(path)
                if not path.is_dir() or list(path.iterdir()):
                    raise ValueError('partial-refusal may have no accepted engineering/scientific publication')
        for path in (partial_output / 'qualification.json', partial_workspace / 'parent-attestation.json',
            partial_workspace / 'source_output/qualification.json', partial_workspace / 'source_output/source-result.json',
            partial_workspace / 'detached_output', partial_workspace / 'detached-native-dispatch.json',
            partial_fixture / 'runs/phase2/.selected-source-publication.lock'):
            if path.exists() or path.is_symlink():
                raise ValueError('partial-refusal cannot gain a qualification, attestation, detached execution or publication lock')
        for name in ('weights', 'evidence', 'manifests'):
            path = partial_fixture / 'runs/phase2/selected_sources' / name
            if path.exists() or path.is_symlink():
                direct(path)
                if not path.is_dir() or list(path.iterdir()):
                    raise ValueError('partial-refusal selected-source files must remain unpublished')
        observed_inputs = set()
        for folder in (partial_fixture / 'configs', partial_fixture / 'data'):
            for path in direct(folder).rglob('*'):
                info = path.lstat()
                if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
                    raise ValueError('linked/reparse preserved partial fixture refused')
                if stat.S_ISREG(info.st_mode):
                    observed_inputs.add(path)
                elif not stat.S_ISDIR(info.st_mode):
                    raise ValueError('nonregular partial input entry refused')
        if observed_inputs != partial_input_paths:
            raise ValueError('preserved partial213 input inventory changed')
        for old_job in (partial_outer, partial_native_source):
            launcher._job_absent(old_job['job_name'])

    partial_failure_scope()

    # The third attempt has an accepted source/publication but no accepted
    # detached verifier or terminal. Preserve that precise intermediate state.
    restore_manifest, _ = document(RESTORE_PACKET / 'manifest.json', expected=RESTORE_PACKET_MANIFEST_SHA)
    restore_summary, _ = document(RESTORE_PACKET / 'summary.json', expected=RESTORE_PACKET_SUMMARY_SHA)
    fields(restore_summary, dict(schema='cho51_complete_eegnet_restore_refusal_v1', accepted=False,
        actual_gradient_updates=5253, all_native_jobs_closed_empty_freshly_absent=True, artifact_count=51,
        boundary_tests_passed=33, claims=1, linked_failures=1, engineering_completion=False,
        engineering_successes=0, measured_cells=0, cleanup_errors=[], peak_sampling_errors=[],
        detached_qualification_accepted=False, source_qualification_accepted=True, publication_accepted=True,
        final_source_subjects=51, inner_folds=102, input_blobs_archived=False, input_files_rehashed=213,
        original_case_attempts_remaining=0, pins_sha256=PRIOR_SHA, source_context_pins_rechecked=620,
        runtime_pins_rechecked=5, source_loaded_modules_rechecked=4719, source_updates=5151, support_updates=102,
        reason='generic_store_factory_four_gib_read_allocation_under_two_gib_process_limit',
        weights_archived=False, weights_file_bytes=12664, scientific_admission=False))
    restore_rows = restore_manifest.get('artifacts')
    if type(restore_rows) is not list or len(restore_rows) != 51:
        raise ValueError('exact51 immutable restore-refusal artifacts required')
    restore_packet_paths = set()
    for row in restore_rows:
        if type(row) is not dict or set(row) != {'source', 'path', 'bytes', 'sha256'}:
            raise ValueError('exact preserved restore-refusal source/copy metadata required')
        relative = relative_path(row['path'])
        if relative.parts[0] != 'artifacts' or len(relative.parts) != 2:
            raise ValueError('short flat restore-refusal artifact path required')
        copy_path = RESTORE_PACKET.joinpath(*relative.parts)
        _, observed = remember(copy_path, compact=True, expected=row['sha256'])
        if type(row['bytes']) is not int or row['bytes'] != observed[2] or copy_path in restore_packet_paths:
            raise ValueError('restore-refusal copied size/uniqueness differs')
        source_path = ROOT.joinpath(*relative_path(row['source']).parts)
        if source_path.suffix.lower() in {'.safetensors', '.npz', '.npy', '.mat'}:
            raise ValueError('weight or input blobs must remain outside compact restore-refusal archives')
        remember(source_path, compact=True, expected=row['sha256'], archive=True)
        restore_packet_paths.add(copy_path)
    restore_plan = dict(dataset='cho2017', target_subject='subject_02', method='eegnet', shots_per_class=5, model_seed=11, repetition=1)
    restore_case = hashlib.sha256(canonical(restore_plan)).hexdigest()
    restore_output = PRIOR.parent / 'validation_001'
    restore_fixture = restore_output / 'fixture'
    restore_recorder = restore_fixture / 'runs/phase2/lifecycle'
    restore_workspace = restore_output / 'cases' / restore_case
    restore_request_path = restore_workspace / 'request.json'
    restore_request, restore_request_sha = document(restore_request_path, canonical_raw=True)
    restore_claim_path = restore_recorder / 'claims' / (restore_case + '.attempt1.claim.json')
    restore_claim, restore_claim_sha = document(restore_claim_path, expected=restore_request['claim_file_sha256'], canonical_raw=True)
    restore_source = restore_claim['payload']['source']
    partial_envelope(restore_claim, dict(purpose='pilot_case_claim', case=restore_plan,
        worker='cho51_synthetic_numerical_engineering', attempt=1,
        environment_sha256=sha(restore_request['environment_sha256']), source=restore_source, engineering_only=True))
    fields(restore_request, dict(schema='cho51_complete_eegnet_request_v1', case_id=restore_case, plan=restore_plan,
        fixture_root=str(restore_fixture), recorder_root=str(restore_recorder), workspace=str(restore_workspace),
        pins_path=str(PRIOR), independent_pins_sha256=PRIOR_SHA, execution_source_sha256=CANONICAL,
        owner_decision_sha256=OWNER, claim_path=str(restore_claim_path), claim_file_sha256=restore_claim_sha,
        fixture_source_sha256=restore_source['source_sha256'], environment_sha256=restore_request['environment_sha256'],
        fixture_identity_path=str(restore_fixture / 'synthetic-input-identity.json'),
        method_config_path=str(PRIOR.parent / 'method-config.json'),
        method_config_file_sha256=prior['method_config_file_sha256'], method_config_sha256=method_sha,
        selection_output=str(restore_workspace / 'source_output'), detached_output=str(restore_workspace / 'detached_output'),
        attempt=1, source_seconds=420, source_process_mib=3072, source_job_mib=4096,
        detached_seconds=90, detached_process_mib=2048, detached_job_mib=3072,
        actual_gradient_updates=5253, source_updates=5151, support_updates=102, fold_count=102, final_source_subjects=51,
        engineering_only=True, scientific_admission=False, original_case_attempts_remaining=0))
    restore_identity, restore_identity_file_sha = document(restore_fixture / 'synthetic-input-identity.json',
        expected=restore_request['fixture_identity_file_sha256'], canonical_raw=True)
    restore_identity_logical = dict(restore_identity)
    restore_identity_sha = sha(restore_identity_logical.pop('sha256'))
    if (hashlib.sha256(canonical(restore_identity_logical)).hexdigest() != restore_identity_sha
            or restore_request['fixture_identity_sha256'] != restore_identity_sha):
        raise ValueError('restore-refusal physical/logical input identity differs')
    restore_inputs = restore_identity.get('files')
    if type(restore_inputs) is not dict or len(restore_inputs) != 213:
        raise ValueError('restore-refusal exact213 input identity required')
    restore_input_paths = set()
    for relative, pin in restore_inputs.items():
        path = restore_fixture.joinpath(*relative_path(relative).parts)
        if (type(pin) is not dict or set(pin) != {'sha256', 'size_bytes'}
                or type(pin['size_bytes']) is not int or not 0 <= pin['size_bytes'] <= 16 * 1024**2):
            raise ValueError('restore-refusal bounded typed input hash/size required')
        _, observed = remember(path, expected=pin['sha256'])
        if observed[2] != pin['size_bytes']:
            raise ValueError('restore-refusal input physical size differs')
        restore_input_paths.add(path)
    restore_source_sha = hashlib.sha256('\n'.join(f'{name}:{restore_inputs[name]["sha256"]}'
        for name in sorted(partial_configurations)).encode()).hexdigest()
    if restore_source_sha != restore_request['fixture_source_sha256']:
        raise ValueError('restore-refusal independently rehashed fixture source differs')
    restore_source_result_path = restore_workspace / 'source_output/source-result.json'
    restore_result, restore_result_sha = document(restore_source_result_path, canonical_raw=True)
    fields(restore_result, dict(schema='cho51_complete_eegnet_source_result_v1', passed=True,
        request_sha256=restore_request_sha, case=restore_plan, case_id=restore_case,
        claim_file_sha256=restore_claim_sha, pins_sha256=PRIOR_SHA, execution_source_sha256=CANONICAL,
        fixture_source=restore_source, fixture_identity_sha256=restore_identity_sha,
        fixture_identity_file_sha256=restore_identity_file_sha, method_config_sha256=method_sha,
        fold_count=102, final_source_subjects=51, source_updates=5151, support_updates=102,
        actual_gradient_updates=5253, public_run_selection_completed=True, public_selection_verifier_passed=True,
        complete=True, full_selector_verified=True, publication_performed=True, detached_tensor_verified=False,
        full_worker_verified=False, target_prediction_performed=False, measured_cells=0,
        scientific_admission=False, original_case_attempts_remaining=0))
    restore_publication = restore_result['publication']
    fields(restore_summary, {'publication': restore_publication})
    restore_publication_pins = restore_result.get('publication_files')
    if type(restore_publication_pins) is not dict or set(restore_publication_pins) != {'manifest', 'evidence', 'weights', 'selector_evidence'}:
        raise ValueError('accepted predecessor source publication requires exact four-role physical pin map')
    for role, pin in restore_publication_pins.items():
        path = Path(pin['path'])
        if not path.is_relative_to(restore_fixture / 'runs/phase2'):
            raise ValueError('restore-refusal publication must remain in its old owned fixture')
        _, observed = remember(path, compact=role != 'weights', expected=pin['file_sha256'], archive=role != 'weights')
        if pin.get('size_bytes') != observed[2] or pin.get('identity') != list(observed[:5]):
            raise ValueError('restore-refusal accepted publication physical identity changed')
        if role == 'weights' and observed[2] != 12664:
            raise ValueError('preserved refused factory input must remain the exact12664-byte weights file')
    restore_record, _ = document(Path(restore_publication['evidence_path']), canonical_raw=True)
    restore_history = verify_complete_history(restore_record, method_template,
        protocol_sha256=restore_identity['protocol_sha256'], source_selection_sha256=restore_identity['source_selection_sha256'],
        fixture_source_sha256=restore_source_sha)
    fields(restore_publication, dict(resumed=False, weights_format='full_v1', evidence_format='canonical_json_v1',
        evidence_sha256=restore_history['evidence_sha256'], selected_candidate=restore_history['selected_candidate'],
        model_state_sha256=restore_history['selected_state_sha256'], weights_sha256=restore_summary['weights_file_sha256']))
    if restore_publication_pins['weights']['file_sha256'] != restore_publication['weights_sha256']:
        raise ValueError('preserved12664-byte weights must match the accepted publication SHA')
    restore_pub_manifest, _ = document(Path(restore_publication['manifest_path']), canonical_raw=True)
    partial_envelope(restore_pub_manifest, restore_pub_manifest['payload'])
    if restore_pub_manifest['sha256'] != restore_publication['manifest_sha256']:
        raise ValueError('accepted predecessor publication manifest logical identity differs')
    fields(restore_pub_manifest['payload'], dict(evidence_sha256=restore_history['evidence_sha256'],
        selected_candidate=restore_history['selected_candidate'], model_state_sha256=restore_history['selected_state_sha256'],
        weights_sha256=restore_publication['weights_sha256'], source=restore_source,
        protocol_config_sha256=restore_identity['protocol_sha256']))
    restore_outer_command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(PRIOR.parent / 'parent.py'),
        '--pins', str(PRIOR), '--expect-pins', PRIOR_SHA, '--output', str(restore_output)]
    restore_outer_dispatch, _ = document(PRIOR.parent / 'dispatch_001.json')
    restore_outer_result, _ = document(PRIOR.parent / 'dispatch_result_001.json')
    restore_common = dict(pins_sha256=PRIOR_SHA, child_command=restore_outer_command,
                         expected_output=str(restore_output), scientific_admission=False)
    fields(restore_outer_dispatch, restore_common | {'schema': 'cho51_complete_eegnet_dispatch_v1'})
    fields(restore_outer_result, restore_common | {'schema': 'cho51_complete_eegnet_dispatch_result_v1', 'guard_exit_code': 1})
    restore_jobs = [verify_native(Path(restore_outer_result['native_directory']), restore_outer_command,
        600, 4096, 6144, operations=operations, runtimes=runtimes, document=document, remember=remember,
        launcher=launcher, expected_failure=True)]
    for kind, seconds, process, job_cap, accepted in (('source', 420, 3072, 4096, True), ('detached', 90, 2048, 3072, False)):
        child_command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B',
            str(PRIOR.parent / ('select_child.py' if kind == 'source' else 'verify_child.py')),
            '--request', str(restore_request_path), '--expect-request', restore_request_sha]
        if kind == 'detached':
            child_command += ['--source-result', str(restore_source_result_path), '--expect-source-result', restore_result_sha]
        inner_dispatch, _ = document(restore_workspace / (kind + '-native-dispatch.json'))
        fields(inner_dispatch, dict(schema='cho51_complete_eegnet_inner_dispatch_v1', kind=kind,
            request_sha256=restore_request_sha, case_id=restore_case, pins_sha256=PRIOR_SHA,
            child_command=child_command, guard_exit_code=0 if accepted else 1,
            source_result_file_sha256=None if kind == 'source' else restore_result_sha, scientific_admission=False))
        restore_jobs.append(verify_native(Path(inner_dispatch['native_directory']), child_command, seconds, process, job_cap,
            operations=operations, runtimes=runtimes, document=document, remember=remember, launcher=launcher,
            expected_failure=not accepted))
    if (len({job['native_directory'] for job in restore_jobs}) != 3
            or not utc(restore_outer_dispatch['observed_utc']) <= utc(restore_jobs[0]['started_utc'])
            <= utc(restore_jobs[1]['started_utc']) <= utc(restore_jobs[1]['completed_utc'])
            <= utc(restore_jobs[2]['started_utc']) <= utc(restore_jobs[2]['completed_utc'])
            <= utc(restore_jobs[0]['completed_utc']) <= utc(restore_outer_result['observed_utc'])):
        raise ValueError('preserved accepted source and failed detached/parent must remain distinct and sequentially nested')
    restore_q, _ = document(restore_workspace / 'source_output/qualification.json')
    fields(restore_q, dict(schema='cho51_complete_eegnet_source_qualification_v1', passed=True,
        pins_sha256=PRIOR_SHA, request_sha256=restore_request_sha, case_id=restore_case,
        claim_file_sha256=restore_claim_sha, fixture_source_sha256=restore_source_sha, owner_decision_sha256=OWNER,
        environment_sha256=restore_request['environment_sha256'], canonical_source_sha256=CANONICAL, canonical_files=432,
        source_pins_rechecked=620, runtime_pins_rechecked=5, source_review_sha256=prior['source_review_sha256'],
        result=restore_result, source_updates=5151, support_updates=102, torch_threads=1, torch_interop_threads=1,
        gpu_hidden=True, unexpected_denials=0, protected_target_read_attempts=[], scientific_admission=False,
        actual_study_inputs_or_pretrained_weights_used=False, original_case_attempts_remaining=0))
    if not utc(restore_jobs[1]['started_utc']) <= utc(restore_q['observed_utc']) <= utc(restore_jobs[1]['completed_utc']):
        raise ValueError('preserved accepted source qualification lies outside its actual native admission')
    fields(restore_q['observed_numerical_calls'], dict(tensor_backward=5253, autograd_backward=5253, sgd_step=5253))
    if restore_q['observed_numerical_calls'].get('autograd_grad', 0) != 0:
        raise ValueError('preserved complete source must have no extra gradient work')
    loaded = restore_q.get('observed_loaded_module_hashes')
    if type(loaded) is not dict or len(loaded) != 4719 or restore_q.get('loaded_module_files') != len(loaded):
        raise ValueError('all4719 preserved accepted source module byte pins required')
    for name, expected in loaded.items():
        remember(Path(name), expected=expected, single_link=Path(name) not in runtime_paths)
    restore_log, _ = remember(Path(restore_jobs[2]['native_directory']) / 'command.log', compact=True)
    if (b'MemoryError' not in restore_log or b'blob = stream.read(maximum_bytes + 1)' not in restore_log
            or b'restore_cho_selected_source' not in restore_log):
        raise ValueError('preserved detached failure must remain the generic factory full-weight read allocation')
    restore_failure_path = restore_recorder / 'attempts' / (restore_case + '.attempt1.failure.json')
    restore_failure, _ = document(restore_failure_path, canonical_raw=True)
    restore_reason = restore_failure['payload']['reason']
    fields(restore_reason, dict(purpose='cho51_complete_eegnet_failure', request_sha256=restore_request_sha,
        engineering_only=True, scientific_admission=False, original_case_attempts_remaining=0))
    if type(restore_reason.get('error')) is not str or 'detached_output' not in restore_reason['error'] or 'qualification.json' not in restore_reason['error']:
        raise ValueError('linked parent failure must preserve its detached missing-qualification symptom')
    partial_envelope(restore_failure, dict(purpose='pilot_case_failure', case=restore_plan, attempt=1,
        reason=restore_reason, environment_sha256=restore_request['environment_sha256'], engineering_only=True))

    def restore_failure_scope():
        if set(direct(RESTORE_PACKET / 'artifacts').iterdir()) != restore_packet_paths:
            raise ValueError('preserved51 restore-refusal artifact file set changed')
        for directory, filename in (('claims', restore_case + '.attempt1.claim.json'),
                                    ('attempts', restore_case + '.attempt1.failure.json')):
            if {path.name for path in direct(restore_recorder / directory).iterdir()} != {filename}:
                raise ValueError('restore-refusal must retain exactly one linked claim/failure')
        for name in ('engineering_intents', 'engineering_successes', 'cells', 'successes', 'publication_intents'):
            path = restore_recorder / name
            if path.exists() or path.is_symlink():
                direct(path)
                if not path.is_dir() or list(path.iterdir()):
                    raise ValueError('restore-refusal must not gain a terminal engineering/scientific publication')
        for path in (restore_output / 'qualification.json', restore_workspace / 'parent-attestation.json',
                     restore_workspace / 'detached_output/qualification.json', restore_workspace / 'detached_output/detached-result.json'):
            if path.exists() or path.is_symlink():
                raise ValueError('restore-refusal cannot gain an accepted detached qualification or parent attestation')
        observed_inputs = set()
        for folder in (restore_fixture / 'configs', restore_fixture / 'data'):
            for path in direct(folder).rglob('*'):
                info = path.lstat()
                if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
                    raise ValueError('linked/reparse preserved restore-refusal input refused')
                if stat.S_ISREG(info.st_mode):
                    observed_inputs.add(path)
                elif not stat.S_ISDIR(info.st_mode):
                    raise ValueError('nonregular preserved restore-refusal input refused')
        if observed_inputs != restore_input_paths:
            raise ValueError('preserved restore-refusal213 input inventory changed')
        for role, directory in (('manifest', 'manifests'), ('evidence', 'evidence'), ('weights', 'weights')):
            path = restore_fixture / 'runs/phase2/selected_sources' / directory
            if set(direct(path).iterdir()) != {Path(restore_publication_pins[role]['path'])}:
                raise ValueError('preserved accepted source publication inventory must remain exactly one')
        for job in restore_jobs:
            launcher._job_absent(job['job_name'])

    restore_failure_scope()

    def native(directory, command, seconds, process_mib, job_mib):
        value = verify_native(directory, command, seconds, process_mib, job_mib,
            operations=operations, runtimes=runtimes, document=document, remember=remember, launcher=launcher)
        if any(value['native_directory'] == row['native_directory'] for row in jobs):
            raise ValueError('three distinct independently dispatched native Jobs required')
        jobs.append(value)
        return value

    def verify_q(path, schema, job, *, request=None, request_sha=None, numerical=False, parent=False):
        q, q_sha = document(path)
        fields(q, dict(schema=schema, passed=True, pins_sha256=pins_sha,
            canonical_source_sha256=CANONICAL, canonical_files=432,
            source_pins_rechecked=len(pins['files']), runtime_pins_rechecked=len(pins['runtime']),
            source_review_sha256=pins['source_review_sha256'], torch_threads=1, torch_interop_threads=1,
            gpu_hidden=True, unexpected_denials=0, actual_study_inputs_or_pretrained_weights_used=False,
            full_worker_verified=False, scientific_admission=False, experiment_freeze_signed=False,
            original_case_attempts_remaining=0))
        if not utc(job['started_utc']) <= utc(q['observed_utc']) <= utc(job['completed_utc']):
            raise ValueError('qualification UTC lies outside its independently admitted native interval')
        sha(q['environment_sha256'])
        loaded = q.get('observed_loaded_module_hashes')
        if type(loaded) is not dict or not loaded or q.get('loaded_module_files') != len(loaded):
            raise ValueError('complete observed post-import module pin inventory required')
        for name, expected in loaded.items():
            remember(Path(name), expected=expected, single_link=Path(name) not in runtime_paths)
        expected_probe = dict(event='socket.__new__', classification='blocked_optional_ipv6_import_probe',
            source_file=str(ROOT / '.venv/Lib/site-packages/urllib3/util/connection.py'),
            source_sha256=pins['files']['.venv/Lib/site-packages/urllib3/util/connection.py'])
        denied = q.get('denied_operations')
        if type(denied) is not list or len(denied) > 1 or any(row != expected_probe for row in denied):
            raise ValueError('only the exact blocked optional IPv6 import probe may be denied')
        if not parent:
            fields(q, dict(denied_operations=[expected_probe], expected_blocked_ipv6_probes=1,
                           protected_target_read_attempts=[]))
            transitions = q.get('protected_target_transitions')
            if (type(transitions) is not list or len(transitions) != 2
                    or any(type(row.get('enabled')) is not bool for row in transitions)
                    or [row['enabled'] for row in transitions] != [True, False]):
                raise ValueError('exact target-protection enable/disable lifecycle required')
            calls = q.get('observed_numerical_calls')
            if numerical:
                fields(calls, dict(tensor_backward=5253, sgd_step=5253, autograd_backward=5253))
                if type(calls.get('autograd_grad', 0)) is not int or calls.get('autograd_grad', 0) != 0:
                    raise ValueError('complete source must use no additional autograd.grad work')
                fields(q, dict(source_updates=5151, support_updates=102))
            else:
                if type(calls) is not dict or any(calls.get(key, 0) != 0 for key in (
                    'optimizer_init', 'sgd_step', 'tensor_backward', 'autograd_backward', 'autograd_grad')):
                    raise ValueError('detached restoration must perform no fitting or differentiation')
        if request is not None:
            fields(q, dict(request_sha256=request_sha, case_id=request['case_id'],
                claim_file_sha256=request['claim_file_sha256'], fixture_source_sha256=request['fixture_source_sha256'],
                owner_decision_sha256=OWNER, environment_sha256=request['environment_sha256']))
        return q, q_sha

    validation = RUN / 'validation_001'
    fixture_root = validation / 'fixture'
    recorder = fixture_root / 'runs/phase2/lifecycle'
    plan = dict(dataset='cho2017', target_subject='subject_02', method='eegnet', shots_per_class=5, model_seed=11, repetition=1)
    case_id = hashlib.sha256(canonical(plan)).hexdigest()
    workspace = validation / 'cases' / case_id
    request_path = workspace / 'request.json'
    parent_command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'parent.py'),
                      '--pins', str(pin_path), '--expect-pins', pins_sha, '--output', str(validation)]
    dispatch, _ = document(RUN / 'dispatch_001.json')
    dispatch_result, _ = document(RUN / 'dispatch_result_001.json')
    common_dispatch = dict(pins_sha256=pins_sha, child_command=parent_command,
                           expected_output=str(validation), scientific_admission=False)
    fields(dispatch, common_dispatch | {'schema': 'cho51_complete_eegnet_dispatch_v1'})
    fields(dispatch_result, common_dispatch | {'schema': 'cho51_complete_eegnet_dispatch_result_v1', 'guard_exit_code': 0})
    outer = native(dispatch_result['native_directory'], parent_command, 600, 4096, 6144)
    if not utc(dispatch['observed_utc']) <= utc(outer['started_utc']) <= utc(outer['completed_utc']) <= utc(dispatch_result['observed_utc']):
        raise ValueError('outer native UTC interval differs from independent dispatch')
    parent_q, _ = verify_q(validation / 'qualification.json', 'cho51_complete_eegnet_parent_qualification_v1', outer, parent=True)
    parent = parent_q.get('result')
    fields(parent, dict(passed=True, tests_passed=True, pytest_exit=0, collected_tests=pins['expected_tests'],
        expected_tests=pins['expected_tests'], skipped_reports=[], measured_cells=0,
        scientific_admission=False, original_case_attempts_remaining=0,
        request_path=str(request_path), claim_path=str(recorder / 'claims' / (case_id + '.attempt1.claim.json')),
        attestation_path=str(workspace / 'parent-attestation.json'),
        engineering_receipt=str(recorder / 'engineering_successes' / (case_id + '.success.json'))))
    reports = parent.get('reports')
    if (type(reports) is not list or len(reports) != pins['expected_tests']
            or len({row.get('nodeid') for row in reports}) != len(reports)):
        raise ValueError('complete distinct collected/call-passed boundary-test roster required')
    for row in reports:
        fields(row, dict(phase='call', outcome='passed'))
        if (type(row.get('nodeid')) is not str
                or not any(row['nodeid'] == node or row['nodeid'].startswith(node + '[') for node in pins['test_nodes'])):
            raise ValueError('boundary test report is outside independently pinned test nodes')
    completion = parent.get('engineering_completion')
    fields(completion, dict(planned=1, measured=0, engineering_success=1, engineering_pending_recovery=0,
                            claimed_unmeasured=0, failed=0, pending=0))
    fields(completion, {'cases': [dict(case=plan, case_id=case_id, measured=False, engineering_success=True,
        engineering_recovery_pending=False, latest_attempt_failed=False,
        claims=[case_id + '.attempt1.claim.json'], failures=[])]})
    for name in ('pytest.log', 'junit.xml'):
        remember(validation / name, compact=True, archive=True)
    request, request_sha = document(request_path, expected=parent['request_sha256'], canonical_raw=True)
    claim_path = recorder / 'claims' / (case_id + '.attempt1.claim.json')
    claim, claim_sha = document(claim_path, expected=parent['claim_file_sha256'], canonical_raw=True)
    claim_payload = claim.get('payload')
    if type(claim_payload) is not dict or type(claim_payload.get('source')) is not dict:
        raise ValueError('canonical physical claim with complete source provenance required')
    fixture_source = claim_payload['source']
    if (set(fixture_source) != {'git_commit', 'git_dirty', 'source_sha256'}
            or type(fixture_source['git_commit']) is not str
            or re.fullmatch('[a-f0-9]{40}|[a-f0-9]{64}', fixture_source['git_commit']) is None
            or type(fixture_source['git_dirty']) is not bool):
        raise ValueError('real committed fixture source provenance required')
    sha(fixture_source['source_sha256'])
    environment = sha(parent_q['environment_sha256'])

    def envelope(record, payload):
        expected = dict(schema_version=1, phase=2, kind='engineering_smoke', payload=payload)
        expected['sha256'] = hashlib.sha256(canonical(expected)).hexdigest()
        fields(record, expected, exact=True)

    envelope(claim, dict(purpose='pilot_case_claim', case=plan, worker='cho51_synthetic_numerical_engineering',
        attempt=1, environment_sha256=environment, source=fixture_source, engineering_only=True))
    fixture_identity_path = fixture_root / 'synthetic-input-identity.json'
    identity, identity_file_sha = document(fixture_identity_path, expected=request['fixture_identity_file_sha256'], canonical_raw=True)
    logical_identity = dict(identity)
    identity_sha = sha(logical_identity.pop('sha256'))
    if hashlib.sha256(canonical(logical_identity)).hexdigest() != identity_sha:
        raise ValueError('physical fixture identity logical SHA differs')
    fields(identity, dict(schema='cho51_owned_synthetic_fold_inputs_v1', synthetic=True, actual_study_data=False,
        scientific_admission=False, original_case_attempts_remaining=0,
        source_subjects_available=52, adopted_evaluation_targets=51, adopted_case_plan_count=1020,
        outer_target='subject_02', inner_validation_subject='subject_01',
        training_subjects=[f'subject_{s:02d}' for s in range(3, 53)], shots_per_class=5,
        canonical_shot_levels=[1, 5, 10, 20], trials_per_subject=42, trials_per_class=21,
        profile_a_shape=[42, 64, 512], profile_b_shape=[42, 64, 800]))
    request_expected = dict(schema='cho51_complete_eegnet_request_v1', case_id=case_id, plan=plan,
        fixture_root=str(fixture_root), recorder_root=str(recorder), workspace=str(workspace), pins_path=str(pin_path),
        independent_pins_sha256=pins_sha, execution_source_sha256=CANONICAL, owner_decision_sha256=OWNER,
        claim_path=str(claim_path), claim_file_sha256=claim_sha, fixture_source_sha256=fixture_source['source_sha256'],
        environment_sha256=environment, fixture_identity_path=str(fixture_identity_path),
        fixture_identity_file_sha256=identity_file_sha, fixture_identity_sha256=identity_sha,
        method_config_path=str(method_path), method_config_file_sha256=method_file_sha, method_config_sha256=method_sha,
        selection_output=str(workspace / 'source_output'), detached_output=str(workspace / 'detached_output'),
        attempt=1, source_seconds=420, source_process_mib=3072, source_job_mib=4096,
        detached_seconds=90, detached_process_mib=2048, detached_job_mib=3072,
        actual_gradient_updates=5253, source_updates=5151, support_updates=102, fold_count=102, final_source_subjects=51,
        engineering_only=True, scientific_admission=False, original_case_attempts_remaining=0)
    fields(request, request_expected, exact=True)
    configurations = ('configs/base.toml', 'configs/benchmark.toml', 'configs/phase2/protocol.toml',
                      'configs/phase2/selection_ceiling.toml', 'configs/phase2/cho_profile_b_60hz.toml')
    expected_inputs = set(configurations)
    for subject in range(1, 53):
        expected_inputs.update((f'data/processed/cho2017/profile_a/subject_{subject:02d}.npz',
            f'data/processed/cho2017/profile_b_60hz_v1/subject_{subject:02d}.npz',
            f'data/processed/cho2017/profile_b_60hz_v1/subject_{subject:02d}.manifest.json',
            f'data/raw/moabb/cho2017/subject_{subject:02d}.mat'))
    input_files = identity.get('files')
    if type(input_files) is not dict or set(input_files) != expected_inputs or len(input_files) != 213:
        raise ValueError('exact213 all52 synthetic A/B/manifest/raw-marker plus five-config inputs required')
    input_bytes = 0
    for relative, pin in input_files.items():
        path = fixture_root.joinpath(*relative_path(relative).parts)
        if (type(pin) is not dict or set(pin) != {'sha256', 'size_bytes'}
                or type(pin['size_bytes']) is not int or not 0 <= pin['size_bytes'] <= 16 * 1024**2):
            raise ValueError('bounded typed synthetic physical input hash/size required')
        _, observed = remember(path, expected=pin['sha256'])
        if observed[2] != pin['size_bytes']:
            raise ValueError('synthetic physical input size differs')
        input_bytes += observed[2]
    source_digest = hashlib.sha256('\n'.join(f'{name}:{input_files[name]["sha256"]}'
        for name in sorted(configurations)).encode()).hexdigest()
    if source_digest != fixture_source['source_sha256'] or source_digest == CANONICAL:
        raise ValueError('isolated fixture source fingerprint differs from its five configuration byte pins')
    if any(input_files[name]['sha256'] != pins['files'][name] for name in configurations):
        raise ValueError('unchanged independently pinned fixture configuration bytes required')
    source_result_path = workspace / 'source_output/source-result.json'
    source_result, source_result_sha = document(source_result_path, canonical_raw=True)
    source_command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'select_child.py'),
                      '--request', str(request_path), '--expect-request', request_sha]
    detached_command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'verify_child.py'),
        '--request', str(request_path), '--expect-request', request_sha,
        '--source-result', str(source_result_path), '--expect-source-result', source_result_sha]
    inner_jobs, inner_q, inner_results, inner_q_sha = {}, {}, {}, {}
    for kind, command, caps in (('source', source_command, (420, 3072, 4096)),
                                ('detached', detached_command, (90, 2048, 3072))):
        inner_dispatch, _ = document(workspace / (kind + '-native-dispatch.json'))
        fields(inner_dispatch, dict(schema='cho51_complete_eegnet_inner_dispatch_v1', kind=kind,
            request_sha256=request_sha, case_id=case_id, pins_sha256=pins_sha, child_command=command,
            guard_exit_code=0, source_result_file_sha256=None if kind == 'source' else source_result_sha,
            scientific_admission=False))
        job = native(inner_dispatch['native_directory'], command, *caps)
        if not utc(outer['started_utc']) <= utc(job['started_utc']) <= utc(job['completed_utc']) <= utc(outer['completed_utc']):
            raise ValueError('both child native intervals must lie inside admitted parent lifetime')
        child_output = Path(request['selection_output'] if kind == 'source' else request['detached_output'])
        q, q_sha = verify_q(child_output / 'qualification.json', 'cho51_complete_eegnet_' + kind + '_qualification_v1',
            job, request=request, request_sha=request_sha, numerical=kind == 'source')
        result, result_sha = document(child_output / (kind + '-result.json'), canonical_raw=True)
        if canonical(result) != canonical(q['result']):
            raise ValueError('physical child result differs from its admitted qualification')
        inner_jobs[kind], inner_q[kind], inner_results[kind], inner_q_sha[kind] = job, q, (result, result_sha), q_sha
        for suffix in ('stdout', 'stderr'):
            remember(workspace / (kind + '-guard-' + suffix + '.txt'), compact=True, archive=True)
    if not utc(inner_jobs['source']['completed_utc']) <= utc(inner_jobs['detached']['started_utc']):
        raise ValueError('source Job must close before the detached verifier is freshly admitted')
    source, source_result_sha = inner_results['source']
    detached, detached_result_sha = inner_results['detached']
    result_bindings = dict(passed=True, request_sha256=request_sha, case=plan, case_id=case_id,
        claim_file_sha256=claim_sha, pins_sha256=pins_sha, execution_source_sha256=CANONICAL,
        fixture_root=str(fixture_root), fixture_source=fixture_source,
        fixture_identity_file_sha256=identity_file_sha, fixture_identity_sha256=identity_sha,
        method_config_file_sha256=method_file_sha, method_config_sha256=method_sha,
        all_physical_inputs_rehashed_unchanged=True, fixture_source_context_unchanged=True,
        torch_numpy_python_rng_unchanged=True, full_worker_verified=False,
        target_prediction_performed=False, recorder_used=False, measured_cells=0,
        synthetic=True, actual_study_data_loaded=False, pretrained_weights_loaded=False,
        engineering_only=True, scientific_admission=False, original_case_attempts_remaining=0)
    fields(source, result_bindings | dict(schema='cho51_complete_eegnet_source_result_v1',
        fixture_identity_path=str(fixture_identity_path), method_config_path=str(method_path),
        source_subjects_available=52, source_subjects=['subject_01', *[f'subject_{s:02d}' for s in range(3, 53)]],
        adopted_evaluation_targets=51, adopted_case_plan_count=1020, outer_target='subject_02',
        input_file_count=213, input_files=input_files,
        physical_inputs={name: str(fixture_root.joinpath(*PurePosixPath(name).parts)) for name in input_files},
        fold_count=102, final_source_subjects=51, source_updates=5151, support_updates=102,
        actual_gradient_updates=5253, source_gradient_updates=5151, support_gradient_updates=102,
        maximum_gradient_steps=5253, selected_parameters=2642, public_run_selection_completed=True,
        public_selection_verifier_passed=True, complete=True, full_selector_verified=True,
        finite_losses_gradients_parameters=True, canonical_source_exclusion_verified=True,
        publication_performed=True, detached_tensor_verified=False))
    fields(detached, result_bindings | dict(schema='cho51_complete_eegnet_detached_result_v1',
        source_result_path=str(source_result_path), source_result_file_sha256=source_result_sha,
        source_result_identity=list(identities[source_result_path][:5]),
        all_tensors_equal=True, full_state_digest_matches=True,
        tensor_equality_boundary='two_public_full_state_restores_and_external_full_state_digest',
        initial_lineage_reconstructed=True, public_restore_adapter_released=True,
        public_selection_verifier_passed=True, full_selector_verified=True,
        verified_source_gradient_updates=5253, verified_source_updates=5151, verified_support_updates=102,
        verified_fold_count=102, verified_final_source_subjects=51, actual_gradient_updates=0,
        detached_tensor_verified=True, publication_performed=False))
    publication = source.get('publication')
    fields(publication, dict(resumed=False, weights_format='full_v1', evidence_format='canonical_json_v1'))
    fields(detached, dict(publication=publication, publication_files=source['publication_files'],
        restored_publication=publication | {'resumed': True}))
    selected_root = fixture_root / 'runs/phase2/selected_sources'
    publication_paths, publication_file_sha = {}, {}
    publication_files = source.get('publication_files')
    if type(publication_files) is not dict or set(publication_files) != {'manifest', 'evidence', 'weights', 'selector_evidence'}:
        raise ValueError('exact actual manifest/evidence/weights/raw-selector physical pin map required')
    for name, pin in publication_files.items():
        if type(pin) is not dict or set(pin) != {'path', 'file_sha256', 'size_bytes', 'identity'}:
            raise ValueError('exact publication physical hash/size/five-field identity pin required')
        path = Path(pin['path'])
        if not path.is_relative_to(selected_root if name != 'selector_evidence' else fixture_root / 'runs/phase2/selection_evidence'):
            raise ValueError('publication file escapes its dedicated owned synthetic namespace')
        raw, observed = remember(path, compact=name != 'weights', expected=pin['file_sha256'], archive=name != 'weights')
        if type(pin['size_bytes']) is not int or pin['size_bytes'] != observed[2] or pin['identity'] != list(observed[:5]):
            raise ValueError('actual publication physical identity/bytes changed')
        if name == 'weights' and not 0 < observed[2] <= 1024**2:
            raise ValueError('bounded full-state EEGNet weights required without archival')
        publication_paths[name], publication_file_sha[name] = path, observed[-1]
        if name != 'selector_evidence':
            fields(publication, {name + '_path': str(path)})
    fields(detached.get('bounded_store'), dict(schema='cho51_eegnet_full_state_bound_v1',
        base_class='evaluation.phase2_selected_source_store.SelectedSourceStore', maximum_weights_bytes=1024**2,
        actual_weights_bytes=identities[publication_paths['weights']][2], restore_limits_bytes=[1024**2, 1024**2],
        generic_restore_default_bytes=4 * 1024**3, generic_restore_default_avoided=True,
        canonical_restore_delegated=True, public_factory_store_injection=True), exact=True)
    fields(publication, dict(manifest_path=str(selected_root / 'manifests' / (sha(publication['manifest_sha256']) + '.json')),
        evidence_path=str(selected_root / 'evidence' / (sha(publication['evidence_sha256']) + '.json')),
        weights_path=str(selected_root / 'weights' / (sha(publication['weights_sha256']) + '.safetensors'))))
    record, evidence_file_sha = document(publication_paths['evidence'], expected=publication_file_sha['evidence'], canonical_raw=True)
    raw_record, _ = document(publication_paths['selector_evidence'], expected=publication_file_sha['selector_evidence'], canonical_raw=True)
    if canonical(raw_record) != canonical(record):
        raise ValueError('fresh public selector evidence differs from its published complete evidence')
    history = verify_complete_history(record, method_template, protocol_sha256=identity['protocol_sha256'],
        source_selection_sha256=identity['source_selection_sha256'], fixture_source_sha256=source_digest)
    fields(publication, dict(evidence_sha256=history['evidence_sha256'], selected_candidate=history['selected_candidate'],
        model_state_sha256=history['selected_state_sha256'], weights_sha256=publication_file_sha['weights']))
    for result in (source, detached):
        fields(result, dict(selected_candidate=history['selected_candidate'],
            selection_evidence_sha256=history['evidence_sha256'], selection_contract_sha256=history['contract_sha256'],
            model_state_sha256=history['selected_state_sha256']))
    fields(source, dict(selection_evidence_path=str(publication_paths['selector_evidence']),
        fitted_state_sha256=history['selected_state_sha256'], scores=history['scores']))
    manifest, _ = document(publication_paths['manifest'], expected=publication_file_sha['manifest'], canonical_raw=True)
    manifest_payload = manifest.get('payload')
    if type(manifest_payload) is not dict:
        raise ValueError('canonical selected-source manifest payload required')
    envelope(manifest, manifest_payload)
    if manifest['sha256'] != publication['manifest_sha256']:
        raise ValueError('actual selected-source manifest logical identity differs')
    recipe_sha = hashlib.sha256(canonical(manifest_payload['model_recipe'])).hexdigest()
    fields(manifest_payload, dict(purpose='selected_source_snapshot', scope='engineering_only', scientific_evaluation=False,
        evidence_sha256=history['evidence_sha256'], selected_candidate=history['selected_candidate'],
        selection_contract_sha256=history['contract_sha256'], protocol_config_sha256=identity['protocol_sha256'],
        source=fixture_source, model_recipe_sha256=recipe_sha, model_state_sha256=history['selected_state_sha256'],
        weights_sha256=publication_file_sha['weights'], weights_file='weights/' + publication_paths['weights'].name,
        evidence_file='evidence/' + publication_paths['evidence'].name))
    for result in (source, detached):
        fields(result, {'model_recipe_sha256': recipe_sha})
    tensor_schema = manifest_payload.get('tensor_schema')
    if type(tensor_schema) is not dict or not tensor_schema or detached.get('tensor_count') != len(tensor_schema):
        raise ValueError('all restored tensor schemas must match the complete manifest count')
    fields(detached.get('tensor_witness'), dict(manifest_sha256=publication['manifest_sha256'],
        evidence_sha256=history['evidence_sha256'], selected_candidate=history['selected_candidate'],
        model_recipe_sha256=recipe_sha, model_state_sha256=history['selected_state_sha256'],
        weights_sha256=publication_file_sha['weights']), exact=True)
    for result in (source, detached):
        witness = result.get('publication_witness')
        fields(witness, dict(project_root=str(fixture_root), manifest_path=str(publication_paths['manifest']),
            manifest_sha256=publication['manifest_sha256'], manifest_file_sha256=publication_file_sha['manifest'],
            manifest_identity=list(identities[publication_paths['manifest']][:4]),
            evidence_path=str(publication_paths['evidence']), evidence_file_sha256=evidence_file_sha,
            evidence_identity=list(identities[publication_paths['evidence']][:4]),
            weights_path=str(publication_paths['weights']), weights_sha256=publication_file_sha['weights'],
            weights_identity=list(identities[publication_paths['weights']][:4])))
    trace_path = workspace / 'source_output/optimizer-observations.json'
    fields(source, {'optimizer_trace_path': str(trace_path)})
    trace, _ = document(trace_path, expected=source['optimizer_trace_file_sha256'], canonical_raw=True)
    fields(trace, dict(schema='cho51_complete_eegnet_optimizer_observations_v1', actual_gradient_updates=5253))
    if identities[trace_path][2] != source['optimizer_trace_file_bytes'] or type(trace.get('events')) is not list or len(trace['events']) != 5253:
        raise ValueError('complete independently pinned actual optimizer transcript required')
    expected_phases = []
    source_subjects = record['payload']['contract']['selection']['source_subjects']
    for candidate in method_template['candidates']:
        for validation_subject in source_subjects:
            expected_phases.extend(['source', candidate['name'], validation_subject, subject, index]
                for index, subject in enumerate((s for s in source_subjects if s != validation_subject), start=1))
            expected_phases.append(['inner_validation_support', candidate['name'], validation_subject, validation_subject, 1])
    expected_phases.extend(['source', history['selected_candidate'], None, subject, index]
                           for index, subject in enumerate(source_subjects, start=1))
    for index, (event, phase) in enumerate(zip(trace['events'], expected_phases, strict=True), start=1):
        fields(event, dict(update=index, phase=phase, selected_parameters=2642,
                           finite_selected_gradients=True, finite_selected_parameters=True))
        if sha(event['selected_state_sha256_before']) == sha(event['selected_state_sha256_after']):
            raise ValueError('each actual public selector optimizer update must change selected state')
    protected = [str(fixture_root / name) for name in (
        'data/processed/cho2017/profile_a/subject_02.npz',
        'data/processed/cho2017/profile_b_60hz_v1/subject_02.npz',
        'data/processed/cho2017/profile_b_60hz_v1/subject_02.manifest.json',
        'data/raw/moabb/cho2017/subject_02.mat')]
    fields(source, {'protected_outer_paths': protected})
    for q in inner_q.values():
        fields(q, {'protected_target_transitions': [dict(enabled=enabled, paths=protected) for enabled in (True, False)]})
        phases = q.get('fixture_input_read_phases')
        if type(phases) is not dict or any(name not in phases for name in protected):
            raise ValueError('both child phase-read witnesses must retain all four protected target paths')
        for name, counts in phases.items():
            if (not Path(name).is_relative_to(fixture_root) or type(counts) is not dict
                    or set(counts) != {'before_protection', 'during_computation', 'after_protection'}
                    or any(type(value) is not int or value < 0 for value in counts.values())):
                raise ValueError('owned typed nonnegative fixture-read phase counters required')
        if any(phases[name]['during_computation'] != 0 for name in protected):
            raise ValueError('outer-target input was read during source selection or detached restoration')
    proof_expected = dict(request_sha256=request_sha, case_id=case_id, claim_file_sha256=claim_sha,
        execution_source_sha256=CANONICAL, independent_pins_sha256=pins_sha, owner_decision_sha256=OWNER,
        environment_sha256=environment, source_native_directory=inner_jobs['source']['native_directory'],
        source_native_receipt_file_sha256=inner_jobs['source']['receipt_file_sha256'],
        source_qualification_path=str(workspace / 'source_output/qualification.json'),
        source_qualification_file_sha256=inner_q_sha['source'],
        detached_native_directory=inner_jobs['detached']['native_directory'],
        detached_native_receipt_file_sha256=inner_jobs['detached']['receipt_file_sha256'],
        detached_qualification_path=str(workspace / 'detached_output/qualification.json'),
        detached_qualification_file_sha256=inner_q_sha['detached'],
        source_result_path=str(source_result_path), source_result_file_sha256=source_result_sha,
        detached_result_path=str(workspace / 'detached_output/detached-result.json'),
        detached_result_file_sha256=detached_result_sha,
        manifest_path=str(publication_paths['manifest']), manifest_file_sha256=publication_file_sha['manifest'],
        evidence_path=str(publication_paths['evidence']), evidence_file_sha256=evidence_file_sha,
        evidence_sha256=history['evidence_sha256'], weights_path=str(publication_paths['weights']),
        weights_file_sha256=publication_file_sha['weights'], selected_state_sha256=history['selected_state_sha256'],
        source_peak_process_bytes=inner_jobs['source']['peak_process_bytes'],
        source_peak_job_bytes=inner_jobs['source']['peak_job_bytes'],
        detached_peak_process_bytes=inner_jobs['detached']['peak_process_bytes'],
        detached_peak_job_bytes=inner_jobs['detached']['peak_job_bytes'],
        actual_gradient_updates=5253, source_updates=5151, support_updates=102, fold_count=102, final_source_subjects=51,
        source_job_closed_empty_absent=True, detached_job_closed_empty_absent=True,
        engineering_only=True, scientific_admission=False, original_case_attempts_remaining=0)
    fields(parent.get('proof'), proof_expected, exact=True)
    attestation_path = workspace / 'parent-attestation.json'
    attestation, attestation_sha = document(attestation_path, expected=parent['attestation_file_sha256'], canonical_raw=True)
    fields(attestation, dict(schema='cho51_complete_eegnet_parent_attestation_v1', request_sha256=request_sha,
        case_id=case_id, claim_file_sha256=claim_sha, proof=proof_expected, engineering_only=True,
        scientific_admission=False, original_case_attempts_remaining=0), exact=True)
    for directory, purpose, suffix in (
        ('engineering_intents', 'pilot_case_engineering_success_intent', '.intent.json'),
        ('engineering_successes', 'pilot_case_engineering_success', '.success.json'),
    ):
        record, _ = document(recorder / directory / (case_id + suffix), canonical_raw=True)
        envelope(record, dict(purpose=purpose, case=plan, attempt=1,
                              attested_evidence_sha256=attestation_sha, engineering_only=True))

    def exact_inventories():
        expected = {fixture_root.joinpath(*PurePosixPath(name).parts) for name in input_files}
        actual = set()
        for folder in (fixture_root / 'configs', fixture_root / 'data'):
            direct(folder)
            for path in folder.rglob('*'):
                info = path.lstat()
                if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
                    raise ValueError('linked/reparse synthetic input directory refused')
                if stat.S_ISREG(info.st_mode):
                    actual.add(path)
                elif not stat.S_ISDIR(info.st_mode):
                    raise ValueError('nonregular synthetic input entry refused')
        if actual != expected:
            raise ValueError('all213 independently pinned physical synthetic inputs must remain exact')
        for name, suffix in (('claims', '.attempt1.claim.json'), ('engineering_intents', '.intent.json'),
                             ('engineering_successes', '.success.json')):
            directory = direct(recorder / name)
            if {path.name for path in directory.iterdir()} != {case_id + suffix}:
                raise ValueError('exact one-claim/intent/engineering-success recorder inventory required')
        for name in ('cells', 'successes', 'publication_intents', 'attempts'):
            directory = recorder / name
            if directory.exists() or directory.is_symlink():
                direct(directory)
                if not directory.is_dir() or list(directory.iterdir()):
                    raise ValueError('scientific cell/success/intent and failure inventories must stay empty')
        if {path.name for path in direct(validation / 'cases').iterdir()} != {case_id}:
            raise ValueError('exact one owned complete-selector case workspace required')
        for directory, expected_files in (
            (selected_root / 'manifests', {publication_paths['manifest']}),
            (selected_root / 'evidence', {publication_paths['evidence']}),
            (selected_root / 'weights', {publication_paths['weights']}),
            (fixture_root / 'runs/phase2/selection_evidence', {publication_paths['selector_evidence']}),
        ):
            if set(direct(directory).iterdir()) != expected_files:
                raise ValueError('exact one actual complete selected-source publication inventory required')

    exact_inventories()
    current_pins()
    prior_failure_scope()
    partial_failure_scope()
    restore_failure_scope()
    artifacts = [(path, *remember(path, compact=True)) for path in sorted(paths)]
    OUT.mkdir(exist_ok=False)
    manifest_rows, copies = [], {}
    for index, (path, raw, observed) in enumerate(artifacts, start=1):
        target = OUT / 'artifacts' / f'{index:04d}_{path.name}'
        target.parent.mkdir(exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        copied_raw, copied_identity = inspect(target, compact=True)
        if copied_raw != raw or copied_identity[-1] != observed[-1]:
            raise ValueError('short-named compact evidence copy differs')
        copies[target] = copied_identity
        remember(path, compact=True)
        manifest_rows.append(dict(source=path.relative_to(ROOT).as_posix(), path=target.relative_to(OUT).as_posix(),
                                  bytes=len(raw), sha256=observed[-1]))
    current_pins()
    exact_inventories()
    prior_failure_scope()
    partial_failure_scope()
    restore_failure_scope()
    for path, observed in tuple(identities.items()):
        if inspect(path, single_link=path not in runtime_paths)[1] != observed:
            raise ValueError('validated source/input/native/publication/claim identity changed across archival')
    for path, observed in copies.items():
        if inspect(path, compact=True)[1] != observed:
            raise ValueError('archived compact evidence physical identity changed before final manifest')
    for job in jobs:
        launcher._job_absent(job['job_name'])
    if len(jobs) != 3:
        raise ValueError('three independently accepted finite native Jobs required')
    summary = dict(schema='cho51_complete_eegnet_successor_closeout_v4', observed_utc=datetime.now(timezone.utc).isoformat(),
        preserved_predecessor_pins_sha256=PRIOR_SHA, preserved_predecessor_source_files=620, preserved_startup_pins_sha256=STARTUP_PRIOR_SHA, preserved_publication_pins_sha256=PUBLICATION_PRIOR_SHA,
        preserved_startup_native_failure=prior_job, startup_boundary_session_accepted=False,
        startup_owned_complete_fixture_or_case_created=False, startup_numerical_work_started=False,
        preserved_startup_refusal_packet=str(PRIOR_PACKET),
        preserved_startup_refusal_manifest_sha256=PRIOR_PACKET_MANIFEST_SHA,
        preserved_startup_refusal_summary_sha256=PRIOR_PACKET_SUMMARY_SHA,
        preserved_publication_refusal_packet=str(PARTIAL_PACKET),
        preserved_publication_refusal_manifest_sha256=PARTIAL_PACKET_MANIFEST_SHA,
        preserved_publication_refusal_summary_sha256=PARTIAL_PACKET_SUMMARY_SHA,
        preserved_publication_refusal_native_jobs=[partial_outer, partial_native_source],
        preserved_publication_refusal_raw_history=partial_history,
        publication_refusal_publication_accepted=False, publication_refusal_selected_weights_persisted=False,
        publication_refusal_detached_child_launched=False, publication_refusal_claims=1, publication_refusal_linked_failures=1,
        publication_refusal_raw_history_reused_for_execution=False,
        preserved_restore_refusal_packet=str(RESTORE_PACKET),
        preserved_restore_refusal_manifest_sha256=RESTORE_PACKET_MANIFEST_SHA,
        preserved_restore_refusal_summary_sha256=RESTORE_PACKET_SUMMARY_SHA,
        preserved_restore_refusal_native_jobs=restore_jobs,
        preserved_restore_refusal_raw_history=restore_history,
        restore_refusal_source_publication_accepted=True, restore_refusal_detached_qualification_accepted=False,
        restore_refusal_engineering_completion=False, restore_refusal_claims=1, restore_refusal_linked_failures=1,
        passed=True, method='eegnet', case=plan, case_id=case_id, jobs=jobs, boundary_tests=pins['expected_tests'],
        canonical_source_sha256=CANONICAL, canonical_files=432, pins_sha256=pins_sha,
        source_context_pins_rechecked=len(pins['files']), runtime_pins_rechecked=len(pins['runtime']),
        request_sha256=request_sha, claim_file_sha256=claim_sha, parent_attestation_file_sha256=attestation_sha,
        method_config_file_sha256=method_file_sha, method_config_sha256=method_sha,
        engineering_completion=1, claims=1, engineering_intents=1, engineering_successes=1,
        measured_cells=0, scientific_successes=0, scientific_publication_intents=0, failures=0,
        physical_input_files=213, physical_input_bytes=input_bytes, fixture_identity_file_sha256=identity_file_sha,
        fixture_identity_sha256=identity_sha, input_blobs_archived=False,
        publication_manifest_sha256=publication['manifest_sha256'], model_recipe_sha256=recipe_sha,
        selected_state_sha256=history['selected_state_sha256'], selected_candidate=history['selected_candidate'],
        selected_weights_sha256=publication_file_sha['weights'], selected_weights_bytes=identities[publication_paths['weights']][2],
        selected_weights_archived=False, source_result_file_sha256=source_result_sha,
        detached_result_file_sha256=detached_result_sha, actual_gradient_updates=5253,
        source_gradient_updates=5151, support_gradient_updates=102, inner_folds=102, final_source_subjects=51,
        complete=True, full_eegnet_synthetic_selector_verified=True, detached_tensor_verified=True,
        actual_public_restore_maximum_weights_bytes=1024**2,
        actual_public_restore_limits_bytes=[1024**2, 1024**2], canonical_store_injection_verified=True,
        real_publication_verified=True, source_subjects_available=52, adopted_evaluation_targets=51,
        adopted_case_plan_count=1020, other_methods_complete_selectors_verified=False,
        full_worker_verified=False, complete_1020_case_roster_verified=False, target_prediction_performed=False,
        actual_study_data_loaded=False, pretrained_weights_loaded=False, experiment_freeze_signed=False,
        original_case_attempts_remaining=0, scientific_admission=False,
        peer_release_or_host_quiet_inferred=False, artifact_count=len(manifest_rows))
    write(OUT / 'manifest.json', {'artifacts': manifest_rows})
    write(OUT / 'summary.json', summary)
    print(json.dumps(summary, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
