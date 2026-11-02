"""Pure observation joins; no package imports, native calls or execution grants."""
from .protocol import (need, integer, string, closed, ref, digest, roster_digest,
                       zero_counters, safety)

ABI_SCOPE = 'observed initialization and required-symbol compatibility for the exact declared path'

def typed_result_equal(left,right):
    if type(left) is not type(right):return False
    if type(left) is dict:
        return set(left)==set(right) and all(typed_result_equal(left[key],right[key]) for key in left)
    if type(left) is list:
        return len(left)==len(right) and all(typed_result_equal(a,b) for a,b in zip(left,right))
    return left==right

class CollectionLedger:
    def __init__(self, static_roster, source_refs, expected_ids=None):
        need(static_roster['schema'] == 'cho51_p3_local_validation_test_roster_v1'
             and static_roster['expected_total'] == 117 and static_roster['function_count'] == 25,
             'fixed static roster')
        self.expected = {}
        self.sources = source_refs
        for row in static_roster['functions']:
            closed(row, 'module node_prefix expected_cases')
            module = string(row['module'], 2048)
            prefix = string(row['node_prefix'], 2048)
            need(prefix.startswith(module+'::') and prefix.count('::') == 1, 'static function identity')
            key = (module, prefix[len(module)+2:])
            need(key not in self.expected, 'duplicate static function')
            self.expected[key] = integer(row['expected_cases'], 1, 117)
            ref(source_refs[module], retained=True)
            pin = static_roster['candidate_source_pins'][module]
            need(all(source_refs[module][k] == pin[k] for k in ('bytes','sha256')), 'candidate retained pin')
        need(len(self.expected) == 25 and sum(self.expected.values()) == 117, 'static totals')
        self.modules = list(dict.fromkeys(row['module'] for row in static_roster['functions']))
        need(len(self.modules) == 2 and sum(n for (m,_),n in self.expected.items() if m == self.modules[0]) == 39,
             'mapping then telemetry static contract')
        self.rows, self.counts = [], {key:0 for key in self.expected}
        self.expected_ids = expected_ids
        self.finished = False
    def append(self, row):
        closed(row, 'ordinal nodeid module original_function_name parameter_id source_ref item_type collection_sequence')
        need(not self.finished and len(self.rows)<117, 'collection already ended/too many items')
        integer(row['ordinal'], len(self.rows), len(self.rows))
        integer(row['collection_sequence'], len(self.rows), len(self.rows))
        nodeid = string(row['nodeid'], 2048)
        parameter = row['parameter_id']
        if parameter is not None:
            string(parameter, 1024, empty=True)
        key = (row['module'], row['original_function_name'])
        need(key in self.expected and row['source_ref'] == self.sources[row['module']], 'function/source identity')
        need(row['item_type'] == '_pytest.python.Function', 'pinned item type')
        prefix = key[0]+'::'+key[1]
        need(nodeid == prefix + ('' if parameter is None else '['+parameter+']'), 'raw parameter/node identity')
        need(nodeid not in [r['nodeid'] for r in self.rows], 'duplicate collected ID')
        if self.rows:
            need(self.modules.index(row['module']) >= self.modules.index(self.rows[-1]['module']), 'module collection order')
        if self.expected_ids is not None:
            need(len(self.rows)<len(self.expected_ids) and nodeid == self.expected_ids[len(self.rows)], 'L/V roster order')
        self.counts[key] += 1
        need(self.counts[key] <= self.expected[key], 'function multiplicity exceeded')
        self.rows.append(dict(row))
    def finish(self, summary):
        closed(summary, 'pytest_exit_code collection_errors collection_skips deselected item_count function_counts ordered_roster_sha256 fixture_setup_calls runtest_protocol_calls phase_report_calls')
        need(not self.finished and len(self.rows)==117 and self.counts==self.expected, 'incomplete exact roster')
        for key in ('pytest_exit_code','collection_errors','collection_skips','deselected',
                    'fixture_setup_calls','runtest_protocol_calls','phase_report_calls'):
            integer(summary[key],0,0)
        integer(summary['item_count'],117,117)
        counts = {m+'::'+f:n for (m,f),n in self.counts.items()}
        need(summary['function_counts']==counts and all(type(v) is int for v in summary['function_counts'].values()), 'parent function counts')
        actual = roster_digest([r['nodeid'] for r in self.rows])
        need(summary['ordered_roster_sha256']==actual, 'independent ordered digest')
        self.finished=True
        return actual

class NativeLedger:
    """Replay native notifications over a stable bootstrap baseline.

    resolver(path, size, phase) must return an exact retained physical/system
    choice already joined to the P index; matching path strings alone cannot
    satisfy that injected obligation.
    """
    def __init__(self, generation, resolver):
        self.generation=integer(generation,1)
        need(callable(resolver), 'native resolver')
        self.resolver=resolver
        self.active={}; self.sequence=1; self.events=[]; self.started=False
    @staticmethod
    def image(row):
        closed(row, 'base image_size full_path')
        integer(row['base'],1,2**64-1); integer(row['image_size'],1,2**32-1)
        path=string(row['full_path'],4096)
        need(len(path.encode('utf-16-le'))//2<=1023, 'native path copy bound')
        return (row['image_size'],path)
    def baseline(self, rows):
        need(not self.started and type(rows) is list and len(rows)<=4096, 'native baseline')
        for row in rows:
            value=self.image(row)
            need(row['base'] not in self.active, 'duplicate base')
            self.resolver(value[1],value[0],'L1')
            self.active[row['base']]=value
        self.started=True
    def establish(self,boundary):
        """Reverse/replay a complete registration-prefix at a stable cut.

        The snapshots represent state at cut N, not state before event1. Reverse
        loads/unloads to recover the registration state, then replay *all* N
        events with the ordinary strict ledger and trust joins. No notification
        is relabelled as bootstrap or dropped because its image is resident.
        """
        closed(boundary,'snapshots events cut_sequence')
        need(not self.started,'native baseline already established')
        snapshots=boundary['snapshots'];events=boundary['events']
        need(type(snapshots) is list and len(snapshots)==2 and snapshots[0]==snapshots[1],'stable bootstrap snapshots')
        integer(boundary['cut_sequence'],0,8192)
        need(type(events) is list and len(events)==boundary['cut_sequence'],'complete bootstrap prefix')
        final={}
        for row in snapshots[0]:
            value=self.image(row);need(row['base'] not in final,'duplicate bootstrap snapshot base');final[row['base']]=value
        need(len(final)<=4096,'bootstrap image cap')
        initial=dict(final)
        for ordinal,row in reversed(list(enumerate(events,1))):
            integer(row['event_sequence'],ordinal,ordinal)
            value=self.image({k:row[k] for k in ('base','image_size','full_path')})
            if row['reason']=='load':
                need(initial.get(row['base'])==value,'bootstrap reverse load mismatch');del initial[row['base']]
            else:
                need(row['reason']=='unload' and row['base'] not in initial,'bootstrap reverse unload mismatch')
                initial[row['base']]=value
            need(len(initial)<=4096,'bootstrap reverse image cap')
        self.baseline([dict(base=base,image_size=value[0],full_path=value[1]) for base,value in initial.items()])
        joined=[self.event(row) for row in events]
        need(self.active==final and self.sequence==boundary['cut_sequence']+1,'bootstrap replay cut mismatch')
        return joined
    def event(self,row):
        closed(row,'event_sequence reason phase base image_size full_path native_observer_generation fault_flags')
        need(self.started,'event before baseline')
        integer(row['event_sequence'],self.sequence,self.sequence)
        integer(row['native_observer_generation'],self.generation,self.generation)
        integer(row['fault_flags'],0,0)
        need(row['phase'] in ('L1','L2','L3','L4','L5') and row['reason'] in ('load','unload'),'event phase/reason')
        image={k:row[k] for k in ('base','image_size','full_path')}
        value=self.image(image)
        joined=self.resolver(value[1],value[0],row['phase'])
        closed(joined,'retained_ref system_role requester_choice')
        need((joined['retained_ref'] is None) != (joined['system_role'] is None),'one native trust join')
        if joined['retained_ref'] is not None:
            ref(joined['retained_ref'],retained=True)
        else:
            string(joined['system_role'],256)
        string(joined['requester_choice'],1024)
        if row['reason']=='load':
            need(row['base'] not in self.active,'duplicate/unbalanced load')
            self.active[row['base']]=value
        else:
            need(self.active.get(row['base'])==value,'unbalanced/substituted unload')
            del self.active[row['base']]
        self.sequence+=1; self.events.append(dict(row))
        return joined
    def reconcile(self, snapshots):
        need(type(snapshots) is list and 2<=len(snapshots)<=3,'bounded stable snapshots')
        normalized=[]
        for rows in snapshots:
            need(type(rows) is list and len(rows)<=4096,'snapshot cap')
            current={}
            for row in rows:
                value=self.image(row)
                need(row['base'] not in current,'duplicate snapshot base')
                current[row['base']]=value
            normalized.append(current)
        need(normalized[-1]==normalized[-2]==self.active,'unstable/gapped snapshot stream')
        return True

def assess_abi(plan, observed):
    closed(plan,'module extension_file machine python_tag initializer_symbol required_exports forwarder_targets safe_queries expected_metadata compatibility_scope')
    closed(observed,'module extension_file machine python_tag initializer_symbol exports forwarder_targets safe_queries metadata initialized unqualified_paths')
    for key in ('module','extension_file','machine','python_tag','initializer_symbol'):
        need(observed[key]==plan[key], 'ABI identity '+key)
    need(type(observed['machine']) is int and observed['machine'] in (0x8664,0xaa64,0x14c),'PE machine')
    need(observed['initialized'] is True and plan['compatibility_scope']==ABI_SCOPE,'narrow ABI scope')
    need(type(plan['required_exports']) is list and len(set(plan['required_exports']))==len(plan['required_exports']),'required export set')
    need(set(plan['required_exports'])<=set(observed['exports']), 'missing required export')
    need(observed['forwarder_targets']==plan['forwarder_targets'] and observed['metadata']==plan['expected_metadata'],'forwarder/metadata identity')
    need(type(observed['safe_queries']) is list and len(observed['safe_queries'])==len(plan['safe_queries']),'exact safe-query count')
    query_keys='module symbol arguments result effect_budget rationale'
    for expected,actual in zip(plan['safe_queries'],observed['safe_queries']):
        closed(expected,query_keys);closed(actual,query_keys)
        need(expected['effect_budget']=='noncomputational' and expected['arguments']==[],'finite safe query')
        for key in ('module','symbol','arguments','effect_budget','rationale'):
            need(type(actual[key]) is type(expected[key]) and actual[key]==expected[key],'safe-query identity '+key)
        need(typed_result_equal(actual['result'],expected['result']),'typed safe-query result')
    need(type(observed['unqualified_paths']) is list and 'dormant exports' in observed['unqualified_paths']
         and 'numerical kernels' in observed['unqualified_paths'] and 'GPU operation' in observed['unqualified_paths']
         and 'unexercised delay imports' in observed['unqualified_paths'], 'explicit unqualified ABI paths')
    return ABI_SCOPE

def require_result(result):
    need(result['publication_status']=='provisional', 'immutable provisional output')
    zero_counters(result['counters']); safety(result['safety'])
    need(not result['failures'], 'failed result')
    for row in result['resource_coverage']:
        need(row['mediation'] and row['observed'] is True,'unmediated/unobserved resource')
    need(result['abi_scope']==ABI_SCOPE,'ABI overclaim')

def workload_equal(left,right):
    keys=('candidates','dependencies','resources','native','initialization','guards','pytest','environment','roster','abi')
    closed(left,keys); closed(right,keys)
    need(left==right,'changed common L/V workload')
    return True
