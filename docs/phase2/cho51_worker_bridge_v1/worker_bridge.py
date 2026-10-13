"""Read-only adopted51 wrapper over the unchanged complete real input loader."""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import sys

from evaluation.phase2_cho_case_inputs import ChoCaseInputPins, ChoFirstTrancheRoute, prepare_cho_first_tranche
from evaluation.phase2_protocol import TrialCatalog
from evaluation.phase2_runner import CasePlan
import evaluation.phase2_protocol as protocol

PLANNER='docs/phase2/cho51_route_candidate_v1/route_contract.py'
PLANNER_SHA='9c168cdb19ad882759d1b73ec23b821b1a2c7045bf7807cee3b9682a01d9a1e3'


def _context(root):
    import hashlib
    path=root/PLANNER
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PLANNER_SHA:raise ValueError('reviewed route planner changed')
    spec=importlib.util.spec_from_file_location('_cho51_worker_planner',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
    exec(compile(raw,str(path),'exec',dont_inherit=True),module.__dict__)
    values={rel:module._bytes(root,rel) for rel in module.PINS}
    adoption=module._json(values['evidence/cho51-adoption-route-20261013/owner/adoption.json'])
    proposal=module._json(values['evidence/cho51-adoption-route-20261013/owner/accepted-proposal.json'])
    roster=module._json(values['evidence/phase2-readiness-20261012/worker/roster.json'])
    deps=(adoption,proposal,roster,protocol,CasePlan)
    module.validate_decision(adoption,proposal,roster)
    return module,deps


@dataclass(frozen=True,slots=True)
class Cho51WorkerRoute:
    contract:object
    _full_route:ChoFirstTrancheRoute

    @property
    def plans(self):return self.contract.plans

    @property
    def catalogs(self):return self._full_route.catalogs

    @property
    def labram_assets(self):return self._full_route.labram_assets

    @property
    def protocol_config_json(self):return self._full_route.protocol_config_json

    def inputs_for(self,plan):
        if type(plan) is not CasePlan or plan not in self.plans:
            raise ValueError('case is outside the adopted51 worker route')
        return self._full_route.inputs_for(plan)


def from_verified_full_route(root,full_route):
    """Caller must independently verify real inputs; this also checks exact scope."""
    if type(full_route) is not ChoFirstTrancheRoute:raise ValueError('actual full input route required')
    planner,deps=_context(Path(root).resolve())
    expected_all=tuple(CasePlan('cho2017',s,m,5,k,1) for s in planner.AVAILABLE for m in planner.METHODS for k in planner.SEEDS)
    if full_route.plans!=expected_all or any(type(p) is not CasePlan for p in full_route.plans):raise ValueError('complete unchanged original plan required')
    if any(type(c) is not TrialCatalog for c in full_route.catalogs):raise ValueError('actual worker catalog classes required')
    contract=planner.prepare_route_contract(deps,full_route.catalogs)
    expected_kept=tuple(p for p in full_route.plans if p.target_subject in planner.TARGETS)
    if contract.plans!=expected_kept or set(full_route.labram_assets)!=set(planner.AVAILABLE):raise ValueError('retained plans or complete52 asset pool differ')
    return Cho51WorkerRoute(contract,full_route)


def prepare_cho51_worker_route(root,*,input_pins:ChoCaseInputPins):
    """Reverify all52 real A catalogs/B asset bytes, then expose1020 retained plans."""
    return from_verified_full_route(root,prepare_cho_first_tranche(Path(root),pins=input_pins))


def route_summary(route):
    return {'schema':'cho51_actual_worker_input_route_v1','evaluation_targets':sorted({p.target_subject for p in route.plans}),'planned_cases':len(route.plans),'available_catalogs':len(route.catalogs),'available_labram_assets':len(route.labram_assets),'actual_worker_CasePlan_class':CasePlan.__module__+'.'+CasePlan.__name__,'actual_worker_TrialCatalog_class':TrialCatalog.__module__+'.'+TrialCatalog.__name__,'owner_decision_sha256':route.contract.owner_decision_sha256,'method_configuration_sha256':dict(route.contract.method_config_sha256),'case_ids':[p.case_id for p in route.plans],'legacy1040_sweep_or_collector_compatible':False,'scientific_execution_budget_admitted':False,'experiment_freeze_signed':False,'original_case_attempts_remaining':0}
