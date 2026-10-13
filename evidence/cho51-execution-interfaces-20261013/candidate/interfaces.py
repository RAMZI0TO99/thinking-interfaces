"""Adopted51 read-only planning, identity and externally verified score interfaces.

These functions neither execute a sweep nor authenticate a writable recorder,
selected checkpoint, tensor state, environment, cohort review or final freeze.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from fractions import Fraction
import json

from core.config import canonical_config_json, config_digest
from core.provenance import SourceProvenance
from docs.phase2.cho51_worker_bridge_v1.worker_bridge import (
    Cho51WorkerRoute, from_verified_full_route,
)
from evaluation.phase2_cell_aggregation_bridge import PinnedCaseCell
from evaluation.phase2_cho_analysis_identity import _protocol
from evaluation.phase2_cho_case_inputs import SELECTED_METHODS, SELECTED_SEEDS
from evaluation.phase2_profile_binding import ChoProfileAssets60Hz
from evaluation.phase2_protocol import nested_episode, source_selection, require_digest
from evaluation.phase2_records import envelope
from evaluation.phase2_subject_aggregation import (
    ExpectedCell, ScoreRow, SubjectAggregation, aggregate_subject_methods,
)

TARGETS = tuple(f'subject_{i:02d}' for i in range(2, 53))


def verify_route(root, route):
    """Recheck adopted scope and full metadata; actual assets need separate checks."""
    if type(route) is not Cho51WorkerRoute:
        raise ValueError('actual adopted51 worker route required')
    expected = from_verified_full_route(root, route._full_route)
    # The pinned planner is reloaded privately, producing a fresh dataclass type.
    # Compare every contract value rather than relying on cross-load class identity.
    fields = ('plans', 'catalogs', 'selections', 'method_config_sha256', 'owner_decision_sha256')
    if any(getattr(route.contract, name) != getattr(expected.contract, name) for name in fields):
        raise ValueError('route differs from fully rederived adopted scope')
    if tuple(sorted({p.target_subject for p in route.plans})) != TARGETS:
        raise ValueError('exact51 evaluation targets required')
    full = route._full_route
    _protocol(full)  # Retain canonical52 available-subject protocol checks.
    available = {c.subject for c in route.catalogs}
    if (set(full.selection_records_json) != available
            or set(full.episode_records_json) != available
            or any(type(a) is not ChoProfileAssets60Hz for a in route.labram_assets.values())
            or len({c.preprocessing_sha256 for c in route.catalogs}) != 1
            or len({a.variant_config_sha256 for a in route.labram_assets.values()}) != 1):
        raise ValueError('complete unchanged available-subject metadata required')


def select_plans(root, route, *, method=None, subject=None, seed=None, case_limit=None):
    """Return retained actual CasePlans; every broad selection needs a finite bound."""
    verify_route(root, route)
    if method is not None and method not in SELECTED_METHODS:
        raise ValueError('unknown Cho method')
    if subject is not None and subject not in TARGETS:
        raise ValueError('subject is outside adopted51 evaluation targets')
    if seed is not None and (type(seed) is not int or seed not in SELECTED_SEEDS):
        raise ValueError('unknown Cho seed')
    if case_limit is not None and (type(case_limit) is not int or not 1 <= case_limit <= 1020):
        raise ValueError('case limit must be an integer from1 to1020')
    if any(value is None for value in (method, subject, seed)) and case_limit is None:
        raise ValueError('complete method/subject/seed or explicit case limit required')
    plans = tuple(p for p in route.plans
                  if (method is None or p.method == method)
                  and (subject is None or p.target_subject == subject)
                  and (seed is None or p.model_seed == seed))
    return plans if case_limit is None else plans[:case_limit]


def sweep_schedule(root, route, *, case_limit, skip_case_ids=()):
    """Produce bounded planning data; caller-supplied skips are not verified resume."""
    plans = select_plans(root, route, case_limit=case_limit)
    if not isinstance(skip_case_ids, Sequence) or isinstance(skip_case_ids, (str, bytes)):
        raise ValueError('skip IDs must be an explicit sequence')
    skips = tuple(skip_case_ids)
    available = {p.case_id for p in route.plans}
    if any(type(v) is not str or v not in available for v in skips) or len(set(skips)) != len(skips):
        raise ValueError('skip IDs must be distinct retained IDs')
    skip_set = set(skips)
    return {
        'schema': 'cho51_bounded_sweep_schedule_v1',
        'owner_decision_sha256': route.contract.owner_decision_sha256,
        'available_subjects': 52, 'evaluation_targets': 51, 'roster_cases': 1020,
        'bounded_selected_case_ids': [p.case_id for p in plans],
        'planned_case_ids': [p.case_id for p in plans if p.case_id not in skip_set],
        'caller_reported_skip_case_ids': list(skips),
        'verified_resume_or_record_admission': False,
        'model_or_recorder_executed': False,
        'scientific_execution_budget_admitted': False,
        'experiment_freeze_signed': False, 'original_case_attempts_remaining': 0,
    }


def verify_case_identity_bindings(root, route, pins, *, method_config_sha256, expected_source):
    """Check exact1020 identity coverage before independent publication/tensor checks."""
    verify_route(root, route)
    if (not isinstance(expected_source, SourceProvenance)
            or type(expected_source.git_dirty) is not bool
            or not isinstance(expected_source.git_commit, str)
            or len(expected_source.git_commit) not in (40, 64)
            or any(c not in '0123456789abcdef' for c in expected_source.git_commit)):
        raise ValueError('independently supplied source provenance required')
    require_digest(expected_source.source_sha256, 'expected source')
    if (not isinstance(method_config_sha256, Mapping)
            or dict(method_config_sha256) != dict(route.contract.method_config_sha256)):
        raise ValueError('unchanged adopted four-method digest map required')
    if (not isinstance(pins, Sequence) or isinstance(pins, (str, bytes))
            or len(pins) != 1020 or any(type(p) is not PinnedCaseCell for p in pins)):
        raise ValueError('exact1020 typed case pins required')
    full = route._full_route
    config = json.loads(full.protocol_config_json)
    if canonical_config_json(config) != full.protocol_config_json:
        raise ValueError('canonical protocol required')
    protocol_sha = config_digest(config)
    catalogs = {c.subject: c for c in route.catalogs}
    expected_selection, expected_episode = {}, {}
    for subject in catalogs:
        selection = envelope('source_selection', asdict(source_selection(route.catalogs, target=subject)))
        episode = envelope('episode_manifest', nested_episode(catalogs[subject], shots=(1, 5, 10, 20), protocol_sha256=protocol_sha).payload())
        if (full.selection_records_json[subject] != canonical_config_json(selection)
                or full.episode_records_json[subject] != canonical_config_json(episode)):
            raise ValueError('route records differ from rederived available-subject records')
        expected_selection[subject], expected_episode[subject] = selection['sha256'], episode['sha256']
    plans = {p.case_id: p for p in route.plans}
    seen = set()
    for pin in pins:
        plan, identity = pin.plan, pin.identity
        if plan.case_id not in plans or plan != plans[plan.case_id] or plan.case_id in seen:
            raise ValueError('pins repeat or exceed adopted51 roster')
        seen.add(plan.case_id)
        subject = plan.target_subject
        if (pin.key != ExpectedCell(*plan.identity_key)
                or (identity.dataset, identity.target_subject, identity.method, identity.shots_per_class, identity.model_seed) != plan.identity_key
                or identity.support_draw_seed is not None or identity.montage_seed is not None
                or identity.protocol_sha256 != protocol_sha
                or identity.selection_sha256 != expected_selection[subject]
                or identity.episode_sha256 != expected_episode[subject]
                or identity.preprocessing_sha256 != catalogs[subject].preprocessing_sha256
                or identity.method_config_sha256 != method_config_sha256[plan.method]):
            raise ValueError('case identity differs from rederived protocol/episode/selection/method')
        if (identity.source_sha256 != expected_source.source_sha256
                or identity.git_commit != expected_source.git_commit
                or identity.git_dirty is not expected_source.git_dirty):
            raise ValueError('case source differs from independently supplied source')
    if seen != set(plans):
        raise ValueError('case pins do not cover adopted51 roster')


@dataclass(frozen=True, slots=True)
class Cho51PairedInputs:
    aggregation: SubjectAggregation
    paired_differences: tuple[tuple[str, Fraction], ...]


def build_paired_inputs(root, route, rows):
    """Aggregate complete externally verified ScoreRows; no recorder authentication."""
    verify_route(root, route)
    roster = tuple(ExpectedCell(*p.identity_key) for p in route.plans)
    result = aggregate_subject_methods(roster, rows)
    if (len(result.admitted_digests) != 1020 or len(result.means) != 204
            or any(v.contributing_cells != 5 for v in result.means)):
        raise ValueError('complete1020 cells and204 five-seed means required')
    means = {(v.subject, v.method): Fraction(v.numerator, v.denominator) for v in result.means}
    expected = {(s, m) for s in TARGETS for m in SELECTED_METHODS}
    if set(means) != expected:
        raise ValueError('exact51-target four-method groups required')
    return Cho51PairedInputs(result, tuple(
        (s, means[(s, 'labram_lora')] - means[(s, 'labram_linear')]) for s in TARGETS))
