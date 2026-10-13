"""Unadopted 51-target fixture collector; no scientific admission or real-data CLI."""
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

SUBJECTS = tuple(f'subject_{i:02d}' for i in range(2, 53))
METHODS = ('labram_linear', 'labram_lora', 'labram_full', 'eegnet')
SEEDS = (11, 23, 37, 53, 71)
PINS = {
    'docs/phase2/cho_51_target_amendment_proposal_20261012.json': '26edbf77961af89fdc31941cbf0425c97ebd81ed263dff706a21aac933e9b965',
    'evidence/phase2-readiness-20261012/worker/roster.json': 'ab5b4c3f11abab8cc5f91c0d36cfc88e0c857f306f6f7a0510a4214e658b1b16',
    'docs/phase2/cho_synthetic_report_candidate/v2/synthetic_report.py': '88b813baf1358abbfab2a345edc42caf238fff80ad5b86f7b2edff4ac7ae7cc0',
}
AUTHORITY = {
    'design_amendment_adopted': False,
    'experiment_freeze_signed': False,
    'scientific_cells_admitted': False,
    'scientific_claim_issued': False,
    'real_training_or_case_admitted': False,
    'checkpoint_training_coverage_verified': False,
    'actual_checkpoint_target_overlap_verified': False,
    'original_case_attempts_remaining': 0,
}


def load_file(name, path, expected=None):
    data = Path(path).read_bytes()
    if expected is not None and hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('candidate dependency bytes changed')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(data, str(path), 'exec', dont_inherit=True), module.__dict__)
    return module


def dependencies(root):
    root = Path(root).resolve()
    helper = load_file('_cho51_pinned_52_helper', root/'docs/phase2/cho_synthetic_report_candidate/v2/synthetic_report.py', PINS['docs/phase2/cho_synthetic_report_candidate/v2/synthetic_report.py'])
    proposal_raw = helper.read_small(root/'docs/phase2/cho_51_target_amendment_proposal_20261012.json')
    roster_raw = helper.read_small(root/'evidence/phase2-readiness-20261012/worker/roster.json')
    for path, raw in (('docs/phase2/cho_51_target_amendment_proposal_20261012.json', proposal_raw), ('evidence/phase2-readiness-20261012/worker/roster.json', roster_raw)):
        if helper.sha(raw) != PINS[path]:
            raise ValueError('proposal or baseline roster bytes changed')
    proposal, roster = helper.decoded(proposal_raw), helper.decoded(roster_raw)
    validate_scope(proposal, roster)
    aggregation, original_inference, _ = helper._load_calculators(root)
    candidate = load_file('_cho51_paired', Path(__file__).parent/'paired_inference.py')
    return helper, aggregation, original_inference, candidate, proposal, roster


def validate_scope(proposal, roster):
    if proposal['adopted'] is not False or proposal['experiment_freeze_signed'] is not False or proposal['scientific_execution_budget_admitted'] is not False:
        raise ValueError('this fixture candidate requires the exact unadopted proposal')
    if tuple(proposal['evaluation_target_ids']) != SUBJECTS or proposal['available_cohort_subject_count'] != 52 or proposal['evaluation_target_count'] != 51:
        raise ValueError('exact proposed target scope required')
    if tuple(proposal['methods']) != METHODS or tuple(proposal['model_seeds']) != SEEDS or proposal['shots_per_class'] != 5:
        raise ValueError('unchanged methods seeds and shots required')
    base = {row['case_id']: row for row in roster['cases']}
    retained = proposal['proposed_case_rows']
    excluded = proposal['excluded_case_rows']
    expected = {(s,m,k) for s in SUBJECTS for m in METHODS for k in SEEDS}
    actual = {(r['target_subject'],r['method'],r['model_seed']) for r in retained}
    if len(base) != 1040 or len(retained) != 1020 or len({r['case_id'] for r in retained}) != 1020 or actual != expected:
        raise ValueError('complete exact1020 proposed roster required')
    if any(base.get(row['case_id']) != row for row in retained + excluded):
        raise ValueError('retained or excluded case identity changed')
    if len(excluded) != 20 or any(row['target_subject'] != 'subject_01' for row in excluded) or {r['case_id'] for r in retained + excluded} != set(base):
        raise ValueError('all20 original subject01 rows must remain excluded')
    if proposal['original_case_attempts_remaining'] != 0 or proposal['original_case_recovery_reset_third_attempt_or_rename_authorized'] is not False:
        raise ValueError('original case authority must remain zero')
    primary = proposal['proposed_primary_analysis']
    if primary['subjects'] != 51 or primary['complete_verified_cells_required'] != 1020 or primary['paired_mean_interval']['df'] != 50 or primary['paired_mean_interval']['sample_variance_denominator'] != 50 or primary['imputation_allowed'] is not False or primary['ratified'] is not False:
        raise ValueError('exact proposed51 subject analysis required')


def expected_roster(aggregation):
    return tuple(aggregation.ExpectedCell('cho2017', s, m, 5, k) for s in SUBJECTS for m in METHODS for k in SEEDS)


def difference(fixture, index):
    if fixture == 'zero': return Fraction()
    if fixture == 'positive': return Fraction(1,10)
    if fixture == 'negative': return Fraction(-1,10)
    if fixture == 'ties': return (Fraction(),Fraction(1,10),Fraction(-1,10),Fraction(1,5))[index % 4]
    if fixture == 'rank_mean_disagree': return Fraction(1,1000) if index < 50 else Fraction(-1,2)
    if fixture == 'ramp': return Fraction(index,100)
    raise ValueError('unknown internal fixture')


def fabricate(aggregation, proposal, fixture):
    identities = {(r['target_subject'],r['method'],r['model_seed']):r['case_id'] for r in proposal['proposed_case_rows']}
    rows = []
    for index, subject in enumerate(SUBJECTS):
        for method in METHODS:
            value = {'labram_linear':Fraction(1,2), 'labram_lora':Fraction(1,2)+difference(fixture,index), 'labram_full':Fraction(9,20), 'eegnet':Fraction(11,20)}[method]
            for seed_index, seed in enumerate(SEEDS):
                score = value + (Fraction(seed_index-2,1000) if 0 < value < 1 else Fraction())
                key = aggregation.ExpectedCell('cho2017',subject,method,5,seed)
                raw = json.dumps({'fixture':fixture,'case_id':identities[(subject,method,seed)],'numerator':score.numerator,'denominator':score.denominator,'fabricated':True},sort_keys=True).encode()
                rows.append(aggregation.ScoreRow(key,score.numerator,score.denominator,hashlib.sha256(raw).hexdigest()))
    return rows


def collect(aggregation, rows):
    result = aggregation.aggregate_subject_methods(expected_roster(aggregation), rows)
    if len(result.means) != 204 or any(item.contributing_cells != 5 for item in result.means):
        raise ValueError('exactly204 five-seed means required')
    means = {(item.subject,item.method):Fraction(item.numerator,item.denominator) for item in result.means}
    pairs = tuple((subject,means[(subject,'labram_lora')]-means[(subject,'labram_linear')]) for subject in SUBJECTS)
    return result,pairs


def fraction(value):
    return {'numerator':value.numerator,'denominator':value.denominator}


def build_fixture_report(deps, fixture):
    helper, aggregation, _, candidate, proposal, _ = deps
    rows = fabricate(aggregation,proposal,fixture)
    aggregated, pairs = collect(aggregation, rows)
    result = candidate.calculate_51_target_paired_inference(pairs,expected_subjects=SUBJECTS)
    return {
        'schema':'cho51_unadopted_synthetic_analysis_v1',
        'scope':'fabricated_fixture_engineering_only',
        'fixture':fixture,
        'authority':dict(AUTHORITY),
        'available_cohort_subjects':52,
        'evaluation_target_ids':list(SUBJECTS),
        'fabricated_cells':len(rows),
        'five_seed_means':len(aggregated.means),
        'subject_count':result.subject_count,
        'student_t_df':50,
        'sample_variance_denominator':50,
        'exact_mean_difference':fraction(result.mean_difference),
        'exact_sample_variance':fraction(result.sample_variance),
        'paired_differences':[{'subject':s,'difference':fraction(d)} for s,d in pairs],
        'signed_rank_levels':list(result.signed_rank_levels),
        'zero_count':result.zero_difference_count,
        'nonzero_tied_subject_count':result.nonzero_tied_subject_count,
        'nonzero_absolute_tie_class_count':result.nonzero_absolute_tie_class_count,
        'wilcoxon_p_value_unrounded':result.wilcoxon_p_value,
        'wilcoxon_statistic':result.wilcoxon_statistic,
        'paired_mean_ci_95':list(result.paired_mean_ci_95),
        'paired_mean_ci_90':list(result.paired_mean_ci_90),
        'synthetic_numeric_conditions_met':result.wilcoxon_p_value < 0.05 and result.mean_difference > 0,
        'secondary_superiority_p_values':[],
        'formal_equivalence_decision':None,
        'proposal_sha256':PINS['docs/phase2/cho_51_target_amendment_proposal_20261012.json'],
        'baseline_roster_sha256':PINS['evidence/phase2-readiness-20261012/worker/roster.json'],
        'gate_a_acceptance_changed_or_supplied_by_candidate':False,
        'production_route_recorder_or_real_cell_admission_qualified':False,
    }
