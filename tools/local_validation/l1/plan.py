"""Typed finite policy validation. No invented module/package compatibility."""
from .protocol import need, integer, string, closed, ref, safety, encode
from .observation import ABI_SCOPE

POLICIES=('import_policy','native_policy','resource_policy','abi_policy','guard_policy','pytest_policy')

def validate_groups(groups):
    need(type(groups) is list and 1<=len(groups)<=2048,'finite initialization groups')
    seen=set(); modules=set(); phase=2
    for ordinal,row in enumerate(groups):
        closed(row,'ordinal group_id phase modules predecessor_groups allowed_effect_ids postcondition_ids')
        integer(row['ordinal'],ordinal,ordinal); string(row['group_id'],256)
        need(row['group_id'] not in seen and row['phase'] in ('L2','L3'),'unique initialization group')
        need(int(row['phase'][1])>=phase,'initialization phase order'); phase=int(row['phase'][1])
        need(type(row['modules']) is list and bool(row['modules']),'explicit initialization module list')
        need(type(row['predecessor_groups']) is list and set(row['predecessor_groups'])<=seen,'predecessor group order')
        for key in ('allowed_effect_ids','postcondition_ids'):
            need(type(row[key]) is list and len(set(row[key]))==len(row[key]),'finite group effects/postconditions')
            for value in row[key]: string(value,256)
        for module in row['modules']:
            string(module,2048); need(module not in modules,'module scheduled twice'); modules.add(module)
        seen.add(row['group_id'])
    return groups

def validate_policies(policies,groups):
    closed(policies,POLICIES)
    imports=policies['import_policy']; natives=policies['native_policy']; resources=policies['resource_policy']
    closed(imports,'rows ordered_sys_path bootstrap_modules')
    need(type(imports['rows']) is list and len(imports['rows'])<=25000,'import count')
    group_map={row['group_id']:row for row in groups}; names=set()
    for row in imports['rows']:
        closed(row,'module kind file_ref namespace_paths phase initializer_group')
        string(row['module'],2048); need(row['module'] not in names,'duplicate import module'); names.add(row['module'])
        need(row['kind'] in ('source','extension','builtin','frozen','namespace'),'import kind')
        need(type(row['namespace_paths']) is list and len(set(row['namespace_paths']))==len(row['namespace_paths']),'ordered namespace paths')
        if row['kind'] in ('source','extension'):
            ref(row['file_ref'],retained=True)
        else:
            need(row['file_ref'] is None,'nonfile import reference')
        if row['phase']=='L4':
            need(row['initializer_group']=='collection' and row['kind']=='source','collection source import binding')
        else:
            need(row['initializer_group'] in group_map and row['phase']==group_map[row['initializer_group']]['phase'],'import group binding')
    need(all(set(row['modules'])<=names for row in groups),'group import closure')
    closed(natives,'rows search_policy environment_snapshot')
    need(natives['search_policy']=='restricted-process-local-no-PATH-fallback','native search policy')
    for row in natives['rows']:
        closed(row,'requester requested_name mechanism flags search_directories chosen_file allowed_system_role phase delay_policy')
        need(row['requester'] in names and row['mechanism'] in ('LoadLibraryExW','ctypes.CDLL','ctypes.WinDLL','extension','torch.ops.load_library'),'native requester/mechanism')
        integer(row['flags'],0,2**32-1)
        need(row['phase'] in ('L1','L2','L3') and row['delay_policy'] in ('observed-required','unexercised-unqualified'),'native phase/delay')
        need((row['chosen_file'] is None)!=(row['allowed_system_role'] is None),'native file/system choice')
        if row['chosen_file'] is not None: ref(row['chosen_file'],retained=True)
        need(type(row['search_directories']) is list and len(set(row['search_directories']))==len(row['search_directories']),'search directories')
    closed(resources,'rows native_branches platform_trust')
    for row in resources['rows']:
        closed(row,'resource_id file_ref caller phase mode maximum_bytes mediation observation_required')
        ref(row['file_ref'],retained=True)
        need(row['mode']=='rb' and row['mediation']=='l1.ResourceGate.open','read-only mediated resource')
        integer(row['maximum_bytes'],0,2*1024**3)
        need(type(row['observation_required']) is bool,'resource required boolean')
    for row in resources['native_branches']:
        closed(row,'branch_id caller phase mediated_by evidence_kind')
        need(row['mediated_by'] in ('l1.ResourceGate.open','reviewed-native-mediator')
             and row['evidence_kind']=='operation-specific-observed','native branch mediation/evidence')
    closed(policies['abi_policy'],'rows')
    for row in policies['abi_policy']['rows']:
        closed(row,'module extension_file machine python_tag initializer_symbol required_exports forwarder_targets safe_queries expected_metadata compatibility_scope')
        ref(row['extension_file'],retained=True); integer(row['machine'],0x8664,0x8664)
        need(row['compatibility_scope']==ABI_SCOPE,'limited ABI claim')
        for query in row['safe_queries']:
            closed(query,'module symbol arguments result effect_budget rationale')
            need(query['effect_budget']=='noncomputational' and query['arguments']==[],'safe zero-argument ABI query')
            string(query['rationale'],4096)
    closed(policies['guard_policy'],'rows early_aliases effect_aliases constructor_epoch')
    need(policies['guard_policy']['constructor_epoch']=='L2-only-exact-groups','finite constructor epoch')
    guard_symbols={(r['defining_module'],r['symbol']) for r in policies['guard_policy']['rows']}
    for symbol in ('load','save','load_file','save_file'):
        need(('safetensors.torch',symbol) in guard_symbols,'safetensors by-value/file guard missing')
    for row in policies['guard_policy']['rows']:
        closed(row,'guard_id phase_installed defining_module symbol equivalents bound_aliases sentinel refusal_event')
        need(row['phase_installed'] in ('L2','L3'),'guard phase')
    pytest=policies['pytest_policy']
    closed(pytest,'version config_ref ordered_arguments builtin_plugins custom_plugin_refs blocked_plugins hooks candidate_modules static_roster id_limits no_fixture_or_test_execution root candidate_paths autoload_disabled ambient_addopts reviewed_hook_wrappers')
    for row in pytest['reviewed_hook_wrappers']:
        closed(row,'plugin symbol qualname file_ref hookwrapper wrapper')
        ref(row['file_ref'],retained=True)
        need(type(row['hookwrapper']) is bool and type(row['wrapper']) is bool and (row['hookwrapper'] or row['wrapper']), 'explicit pinned wrapper flags')
    need(type(pytest['builtin_plugins']) is dict and bool(pytest['builtin_plugins']),'version-specific plugin identity map')
    need(pytest['no_fixture_or_test_execution'] is True and pytest['autoload_disabled'] is True,'pytest execution boundary')
    need(pytest['id_limits']=={'nodeid_bytes':2048,'parameter_id_bytes':1024},'exact pytest ID limits')
    need(set(('pytest_fixture_setup','pytest_runtest_protocol','pytest_runtest_logreport','pytest_runtest_makereport'))<=set(pytest['hooks']),'pre-effect execution hooks')
    encode(policies)
    return policies
