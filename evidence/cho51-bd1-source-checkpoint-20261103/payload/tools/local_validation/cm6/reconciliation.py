"""Conservative supplied predecessor/current reconciliation; no adoption proof."""
from dataclasses import dataclass
from ..hb1 import common as c
from .context import parse_expected_context
from .collection import verify_collection

@dataclass(frozen=True, slots=True)
class ReconciliationFacts:
    prior_operation: str
    current_operation: str
    prior_context: str
    current_context: str
    cohort_pin: tuple
    prior_descriptor_pin: tuple
    current_descriptor_pin: tuple
    prior_collection_pin: tuple
    current_collection_pin: tuple
    preserved: tuple
    additions: tuple
    held: tuple
    @property
    def authenticated(self): return False

    @property
    def execution_accepted(self): return False

    @property
    def debt_discharged(self): return False

    @property
    def independent_adoption_required(self): return True

def reconcile_prior(raw_q, prior_d, current_d, prior_c, current_c, expected_q_pin, expected_prior_d_pin, expected_current_d_pin, prior_operation, current_operation):
    prior = parse_expected_context(raw_q, prior_d, expected_q_pin, expected_prior_d_pin, prior_operation)
    current = parse_expected_context(raw_q, current_d, expected_q_pin, expected_current_d_pin, current_operation)
    prior_report = verify_collection(prior_c, raw_q, prior_d, expected_q_pin, expected_prior_d_pin, prior_operation)
    current_report = verify_collection(current_c, raw_q, current_d, expected_q_pin, expected_current_d_pin, current_operation)
    old_modules = dict((n, (s, h)) for n, s, h in prior.modules)
    new_modules = dict((n, (s, h)) for n, s, h in current.modules)
    c.require(all(new_modules.get(n) == pin for n, pin in old_modules.items()), 'prior module conservation')
    old_rows = {row[0]: row for row in prior.obligations}; new_rows = {row[0]: row for row in current.obligations}
    c.require(all(new_rows.get(n) == row for n, row in old_rows.items()), 'prior debt conservation')
    additions = tuple(row for row in current.obligations if row[0] not in old_rows)
    c.require(all(row[1:3] == ('HELD', 'NEW_TEST_UNQUALIFIED') and row[0].rsplit('.', 2)[0] not in old_modules for row in additions), 'new module held additions')
    return ReconciliationFacts(prior_operation, current_operation, prior.context, current.context, expected_q_pin, expected_prior_d_pin, expected_current_d_pin, prior_report.collection_pin, current_report.collection_pin, prior.obligations, additions, tuple(row for row in current.obligations if row[1] == 'HELD'))

