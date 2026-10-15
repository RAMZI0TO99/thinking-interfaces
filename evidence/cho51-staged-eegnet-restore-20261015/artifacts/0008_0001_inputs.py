"""Authenticate and reconstruct an already-created owned synthetic Cho fixture.

Preparation occurs before the recorder claim.  Loading never regenerates or
rewrites an input, and it does not substitute any canonical loader or selector.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from core.config import config_digest, load_toml
from docs.phase2.cho51_source_fold_probe_v1 import fixture as F
from docs.phase2.cho51_worker_lifecycle_v1 import lifecycle as L
from evaluation.phase2_protocol import nested_episode, source_selection
from evaluation.phase2_records import envelope
from scripts.audit_phase2_protocol import read_catalog, validate_protocol


def load_existing_fixture(request):
    """Return the frozen fixture interface from independently pinned inputs.

    ``request`` is the exact serialized CompleteRequest, already reconstructed
    by the child entry point.  Its physical and logical identity pins are both
    mandatory.  All 213 input files are checked before catalogs are parsed and
    again after reconstruction; arrays are read one subject at a time.
    """
    if hasattr(request, 'payload'):
        request = request.payload()
    if (type(request) is not dict or request.get('schema') != 'cho51_complete_eegnet_request_v1'
            or request.get('plan', {}).get('method') != 'eegnet'):
        raise ValueError('exact complete synthetic EEGNet request required')
    root = Path(request['fixture_root'])
    identity_path = Path(request['fixture_identity_path'])
    if identity_path != root / 'synthetic-input-identity.json':
        raise ValueError('fixture identity is outside the fixed owned namespace')
    raw, _ = L._read(identity_path, request['fixture_identity_file_sha256'])
    identity = json.loads(raw)
    if raw != L._encoded(identity):
        raise ValueError('fixture identity must have exact canonical physical bytes')
    expected = {
        'schema': 'cho51_owned_synthetic_fold_inputs_v1',
        'synthetic': True, 'actual_study_data': False, 'scientific_admission': False,
        'original_case_attempts_remaining': 0,
        'source_subjects_available': 52, 'adopted_evaluation_targets': 51,
        'adopted_case_plan_count': 1020, 'outer_target': 'subject_02',
        'inner_validation_subject': 'subject_01', 'training_subjects': list(F.TRAINING_SUBJECTS),
        'shots_per_class': 5, 'canonical_shot_levels': [1, 5, 10, 20],
        'trials_per_subject': 42, 'trials_per_class': 21,
        'profile_a_shape': [42, 64, 512], 'profile_b_shape': [42, 64, 800],
    }
    if (type(identity) is not dict
            or set(identity) != set(expected) | {'protocol_sha256', 'source_selection_sha256', 'files', 'sha256'}
            or config_digest({key: identity.get(key) for key in expected}) != config_digest(expected)
            or identity['sha256'] != request['fixture_identity_sha256']
            or config_digest({key: value for key, value in identity.items() if key != 'sha256'}) != identity['sha256']):
        raise ValueError('fixture identity differs from complete synthetic 52-subject scope')
    paths = tuple(sorted(
        [root / relative for relative in F.CONFIGURATIONS]
        + [path for subject in F.SUBJECTS for path in F._subject_paths(root, subject)],
        key=lambda path: path.relative_to(root).as_posix(),
    ))
    expected_names = {path.relative_to(root).as_posix() for path in paths}
    if (len(paths) != 213 or type(identity['files']) is not dict
            or set(identity['files']) != expected_names):
        raise ValueError('fixture must contain exactly all 213 independently pinned inputs')
    for path in paths:
        if F._input_pin(path) != identity['files'][path.relative_to(root).as_posix()]:
            raise ValueError('fixture physical input differs from its independent identity')
    protocol = load_toml(root / 'configs/phase2/protocol.toml')
    if (validate_protocol(protocol) != (1, 5, 10, 20)
            or protocol['datasets']['cho2017']['expected_subjects'] != 52
            or config_digest(protocol) != identity['protocol_sha256']):
        raise ValueError('fixture protocol or complete 52-subject cohort changed')
    threshold_path = root / 'configs/benchmark.toml'
    threshold = load_toml(threshold_path)['datasets']['cho2017']['artifact_threshold_volts']
    preprocessing = config_digest({
        'profile_identity': protocol['preparation']['profile_identity'],
        'threshold_config_sha256': identity['files']['configs/benchmark.toml']['sha256'],
        'dataset': 'cho2017', 'threshold': threshold,
    })
    catalogs, assets, episodes = [], {}, {}
    for subject in F.SUBJECTS:
        a, b, manifest, _ = F._subject_paths(root, subject)
        catalog, metadata = read_catalog(a, dataset='cho2017', classes=F.CHO_CLASSES,
            threshold=threshold, preprocessing_sha256=preprocessing)
        if (catalog.subject != subject or metadata['retained_trials'] != 42
                or metadata['rejected_trials'] != 0
                or metadata['retained_class_counts'] != {label: 21 for label in F.CHO_CLASSES}):
            raise ValueError('reconstructed synthetic catalog differs from all 42 retained trials')
        catalogs.append(catalog)
        assets[subject] = F.ChoProfileAssets60Hz(
            identity['files'][b.relative_to(root).as_posix()]['sha256'],
            identity['files'][manifest.relative_to(root).as_posix()]['sha256'],
            identity['files']['configs/phase2/cho_profile_b_60hz.toml']['sha256'])
        episodes[subject] = envelope('episode_manifest', nested_episode(catalog,
            shots=(1, 5, 10, 20), protocol_sha256=config_digest(protocol)).payload())
    selection = source_selection(tuple(catalogs), target='subject_02')
    if selection.sha256 != identity['source_selection_sha256']:
        raise ValueError('reconstructed source selection differs from independent fixture identity')
    result = F.Fixture(root, protocol, tuple(catalogs), envelope('source_selection', asdict(selection)),
        assets, episodes, identity, paths, F._subject_paths(root, 'subject_02'),
        'eegnet', 'cho_profile_a', identity_path, request['fixture_identity_file_sha256'])
    result.verify_inputs()
    return result
