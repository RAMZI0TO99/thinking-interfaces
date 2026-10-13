"""Versioned adopted-scope metadata planner; no asset, recorder or model execution."""
from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import MappingProxyType, ModuleType

AVAILABLE=tuple(f'subject_{i:02d}' for i in range(1,53))
TARGETS=AVAILABLE[1:]
METHODS=('labram_linear','labram_lora','labram_full','eegnet')
SEEDS=(11,23,37,53,71)
PINS={
    'evidence/cho51-adoption-route-20261013/owner/adoption.json':'ae3295c2aa5acdfad2c9b2d7ffb602ec8b0daddb07b3d433d15dcaf9fd002709',
    'evidence/cho51-adoption-route-20261013/owner/accepted-proposal.json':'26edbf77961af89fdc31941cbf0425c97ebd81ed263dff706a21aac933e9b965',
    'evidence/phase2-readiness-20261012/worker/roster.json':'ab5b4c3f11abab8cc5f91c0d36cfc88e0c857f306f6f7a0510a4214e658b1b16',
    'core/config.py':'1b55c368098a138396f9cd9bfbf1d9d196c2b1e74c718b74d569778c69e52e79',
    'evaluation/phase2_protocol.py':'4547de8f2606aa40f5c901a0c06db473c8eead0a27ac2930581485e4a86eab9f',
    'evaluation/phase2_runner.py':'ed57009e13e6040e86c22b10d98aeb71815ee19212313b63d2576be813a4d428',
}


def _bytes(root,relative):
    path=root/relative
    before=path.stat();raw=path.read_bytes();after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns) or len(raw)!=before.st_size or hashlib.sha256(raw).hexdigest()!=PINS[relative]:
        raise ValueError('route dependency changed: '+relative)
    return raw


def _json(raw):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('duplicate JSON key')
            result[key]=value
        return result
    def constant(value):raise ValueError('nonfinite JSON')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)


def _module(name,path,raw):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    exec(compile(raw,str(path),'exec',dont_inherit=True),module.__dict__)
    return module


def load_dependencies(root):
    root=Path(root).resolve()
    data={rel:_bytes(root,rel) for rel in PINS}
    adoption=_json(data['evidence/cho51-adoption-route-20261013/owner/adoption.json'])
    proposal=_json(data['evidence/cho51-adoption-route-20261013/owner/accepted-proposal.json'])
    roster=_json(data['evidence/phase2-readiness-20261012/worker/roster.json'])
    validate_decision(adoption,proposal,roster)
    if 'core' not in sys.modules:
        core=ModuleType('core');core.__path__=[str(root/'core')];sys.modules['core']=core
    config=_module('core.config',root/'core/config.py',data['core/config.py'])
    protocol=_module('_cho51_protocol',root/'evaluation/phase2_protocol.py',data['evaluation/phase2_protocol.py'])
    tree=ast.parse(data['evaluation/phase2_runner.py'])
    nodes=[node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='CasePlan']
    if len(nodes)!=1:raise ValueError('one original CasePlan class required')
    holder=ModuleType('_cho51_case_plan_ast');sys.modules[holder.__name__]=holder
    holder.__dict__.update(dataclass=dataclass,asdict=asdict,config_digest=config.config_digest)
    body=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),nodes[0]],type_ignores=[])
    exec(compile(ast.fix_missing_locations(body),str(root/'evaluation/phase2_runner.py'),'exec',dont_inherit=True),holder.__dict__)
    return adoption,proposal,roster,protocol,holder.CasePlan


def validate_decision(adoption,proposal,roster):
    if adoption['design_amendment_adopted'] is not True or adoption['authorization']['direct_owner_choice_received'] is not True or adoption['authorization']['verbatim_user_response']!='Adopt 51 targets (Recommended)':
        raise ValueError('direct exact owner adoption required')
    if adoption['accepted_proposal']['json_git_and_local_sha256']!=PINS['evidence/cho51-adoption-route-20261013/owner/accepted-proposal.json']:
        raise ValueError('accepted proposal binding changed')
    if tuple(adoption['available_cohort_subject_ids'])!=AVAILABLE or tuple(adoption['current_evaluation_target_ids'])!=TARGETS or adoption['expected_cells']!=1020:
        raise ValueError('exact52 available and51 target scope required')
    if tuple(adoption['methods'])!=METHODS or tuple(adoption['model_seeds'])!=SEEDS or adoption['shots_per_class']!=5 or adoption['repetition']!=1:
        raise ValueError('unchanged method seed shot repetition required')
    if adoption['experiment_freeze_signed'] is not False or adoption['scientific_execution_budget_admitted'] is not False or adoption['original_case_attempts_remaining']!=0 or adoption['original_case_recovery_reset_third_attempt_or_rename_authorized'] is not False:
        raise ValueError('scope decision supplies no execution or original retry authority')
    primary=adoption['adopted_primary_analysis']
    if primary['ratified'] is not True or primary['subjects']!=51 or primary['paired_mean_interval']['df']!=50 or primary['paired_mean_interval']['sample_variance_denominator']!=50:
        raise ValueError('adopted51 subject analysis binding changed')
    if proposal['adopted'] is not False:raise ValueError('historical proposal bytes must remain unmodified')
    base={r['case_id']:r for r in roster['cases']}
    retained=proposal['proposed_case_rows'];excluded=proposal['excluded_case_rows']
    expected={(s,m,k) for s in TARGETS for m in METHODS for k in SEEDS}
    if len(base)!=1040 or len(retained)!=1020 or len({r['case_id'] for r in retained})!=1020 or {(r['target_subject'],r['method'],r['model_seed']) for r in retained}!=expected:
        raise ValueError('exact complete retained identity roster required')
    if any(base.get(r['case_id'])!=r for r in retained+excluded) or len(excluded)!=20 or any(r['target_subject']!='subject_01' for r in excluded) or {r['case_id'] for r in retained+excluded}!=set(base):
        raise ValueError('original identities or complete subject01 exclusion changed')


@dataclass(frozen=True,slots=True)
class Cho51RouteContract:
    plans:tuple
    catalogs:tuple
    selections:object
    method_config_sha256:object
    owner_decision_sha256:str

    def plan_for(self,case_id):
        for plan in self.plans:
            if plan.case_id==case_id:return plan
        raise ValueError('case is outside the adopted51 target plan')


def prepare_route_contract(deps,catalogs):
    adoption,proposal,roster,protocol,CasePlan=deps
    validate_decision(adoption,proposal,roster)
    if not isinstance(catalogs,tuple) or len(catalogs)!=52 or any(not isinstance(c,protocol.TrialCatalog) for c in catalogs) or tuple(c.subject for c in catalogs)!=AVAILABLE:
        raise ValueError('complete ordered52 typed source catalogs required')
    if any(c.dataset!='cho2017' or c.classes!=('left_hand','right_hand') for c in catalogs):
        raise ValueError('Cho left/right catalog inventory required')
    plans=tuple(CasePlan('cho2017',s,m,5,k,1) for s in TARGETS for m in METHODS for k in SEEDS)
    rows=proposal['proposed_case_rows']
    if tuple(p.case_id for p in plans)!=tuple(r['case_id'] for r in rows):
        raise ValueError('rederived actual CasePlan IDs differ from retained rows')
    templates={}
    for row in rows:
        existing=templates.setdefault(row['method'],row['method_config_sha256'])
        if existing!=row['method_config_sha256']:raise ValueError('method template changes within the retained roster')
    selections={s:protocol.source_selection(catalogs,target=s) for s in TARGETS}
    for target,selection in selections.items():
        expected=tuple(s for s in AVAILABLE if s!=target)
        if selection.source_subjects!=expected or len(selection.inner_folds)!=51:
            raise ValueError('complete51 source pool required')
        for fold in selection.inner_folds:
            if fold.training_subjects!=tuple(s for s in expected if s!=fold.validation_subject) or len(fold.training_subjects)!=50 or target in fold.training_subjects or target==fold.validation_subject:
                raise ValueError('outer target or inner validation leakage')
    return Cho51RouteContract(plans,catalogs,MappingProxyType(selections),MappingProxyType(templates),PINS['evidence/cho51-adoption-route-20261013/owner/adoption.json'])


def fixture_catalogs(protocol):
    preprocessing=hashlib.sha256(b'fabricated common preprocessing').hexdigest()
    return tuple(protocol.TrialCatalog('cho2017',s,('left0','left1','right0','right1'),('left_hand','left_hand','right_hand','right_hand'),('left_hand','right_hand'),hashlib.sha256(('fabricated:'+s).encode()).hexdigest(),preprocessing) for s in AVAILABLE)


def summary(deps,route):
    if not isinstance(route,Cho51RouteContract) or route!=prepare_route_contract(deps,route.catalogs):
        raise ValueError('route differs from its fully rederived adopted contract')
    selections=[]
    for target,selection in route.selections.items():
        selections.append({'target':target,'source_subjects':list(selection.source_subjects),'inner_validation_subjects':[f.validation_subject for f in selection.inner_folds],'inner_training_subject_count':50,'selection_record_sha256':selection.sha256})
    return {'schema':'cho51_route_contract_fixture_v1','study_design_adopted':True,'scope':'fabricated_catalog_metadata_qualification_only','available_subject_count':len(route.catalogs),'target_count':len(route.selections),'planned_cases':len(route.plans),'case_ids':[p.case_id for p in route.plans],'method_configuration_sha256':dict(route.method_config_sha256),'owner_decision_sha256':route.owner_decision_sha256,'selections':selections,'inner_folds_verified':sum(len(s.inner_folds) for s in route.selections.values()),'inner_training_memberships_verified':sum(len(f.training_subjects) for s in route.selections.values() for f in s.inner_folds),'selection_steps_per_case':5253,'planned_selection_steps_total':5253*len(route.plans),'target_support_steps_total':len(route.plans),'catalog_artifact_bytes_verified':False,'trial_episodes_or_real_assets_qualified':False,'full_worker_CasePlan_class_interoperability_qualified':False,'production_recorder_or_sweep_qualified':False,'experiment_freeze_signed':False,'scientific_execution_budget_admitted':False,'original_case_attempts_remaining':0}
