"""Explicit pytest invocation and pre-effect fixture/run/plugin gates.

pytest is supplied only after L2 initialization; this module never imports it.
"""
import types
from .protocol import need, integer, roster_digest

REQUIRED_OPTIONS=('--collect-only','--import-mode=importlib','--noconftest','--assert=plain',
                  '-p','no:cacheprovider','-p','no:stepwise')

def validate_arguments(policy):
    args=policy['ordered_arguments']
    need(type(args) is list and all(type(a) is str for a in args),'exact pytest argument array')
    need(args[:len(REQUIRED_OPTIONS)]==list(REQUIRED_OPTIONS),'collect-only option prefix')
    need(args[len(REQUIRED_OPTIONS):]==['-c',policy['config_ref']['path'],
          '--rootdir='+policy['root'],*policy['candidate_paths']],'exact pytest config/root/candidates')
    need(len(policy['candidate_paths'])==2 and policy['no_fixture_or_test_execution'] is True,'two candidate modules/no execution')
    need(policy['autoload_disabled'] is True and policy['ambient_addopts']==[],'ambient pytest state')
    return list(args)

def install_registration_gate(manager,allowed,refuse,reviewed_wrappers=()):
    """Must run in PluginManager.__init__, before its first register call.

    allowed maps exact registration name to the pinned module/plugin object.
    Register wrappers/foreign hooks are rejected before original registration.
    """
    original=manager.register
    def register(plugin,name=None):
        key=name if name is not None else manager.get_canonical_name(plugin)
        if key not in allowed or not (allowed[key] is plugin or type(allowed[key]) is type and type(plugin) is allowed[key]):
            refuse('unapproved pytest plugin registration: '+str(key))
        values=vars(plugin)
        for hook,value in values.items():
            if hook.startswith('pytest_'):
                markers=vars(value).get('pytest_impl',{}) if hasattr(value,'__dict__') else {}
                if markers.get('hookwrapper') or markers.get('wrapper'):
                    matches=[r for r in reviewed_wrappers if r['plugin']==key and r['symbol']==hook]
                    if len(matches)!=1:
                        refuse('unapproved pytest hook wrapper')
                    row=matches[0]
                    code=getattr(value,'__code__',None)
                    if code is None or value.__qualname__!=row['qualname'] or code.co_filename.replace('\\','/')!=row['file_ref']['path'] \
                       or bool(markers.get('hookwrapper',False)) is not row['hookwrapper'] or bool(markers.get('wrapper',False)) is not row['wrapper']:
                        refuse('changed pinned pytest hook wrapper')
        return original(plugin,name)
    manager.register=register
    return register

class CollectionPlugin:
    def __init__(self,ledger,emit,refuse):
        self.ledger,self.emit,self.refuse=ledger,emit,refuse
        self.errors=self.skips=self.deselected=0
        self.fixture_calls=self.protocol_calls=self.report_calls=0
        self.session_finished=False
    def pytest_fixture_setup(self,fixturedef,request):
        self.fixture_calls+=1; self.refuse('fixture setup attempted during L')
    def pytest_runtest_protocol(self,item,nextitem):
        self.protocol_calls+=1; self.refuse('test protocol attempted during L')
    def pytest_runtest_logreport(self,report):
        self.report_calls+=1; self.refuse('test phase report during L')
    def pytest_runtest_makereport(self,item,call):
        self.report_calls+=1; self.refuse('test phase attempted during L')
    def pytest_collectreport(self,report):
        if report.failed:
            self.errors+=1; self.refuse('collection error')
        if report.skipped:
            self.skips+=1; self.refuse('collection skip')
    def pytest_deselected(self,items):
        self.deselected+=len(items); self.refuse('collection deselection')
    def pytest_collection_modifyitems(self,session,config,items):
        need(len(items)==117,'exact collection item count')
        for item in items:
            item_type=type(item).__module__+'.'+type(item).__name__
            need(item_type=='_pytest.python.Function','pinned pytest function type')
            original=item.originalname
            need(type(original) is str,'original function name required')
            path=str(item.path).replace('\\','/')
            matches=[key for key,value in self.ledger.sources.items() if value['path']==path]
            need(len(matches)==1,'candidate source file join')
            # Access original function through pytest's own collected function;
            # never execute fixture resolution or the function.
            obj=item.obj
            need(type(obj) is types.FunctionType and obj.__name__==original
                 and obj.__code__.co_filename.replace('\\','/')==path,'collected function code identity')
            callspec=vars(item).get('callspec')
            parameter=None if callspec is None else callspec.id
            row=dict(ordinal=len(self.ledger.rows),nodeid=item.nodeid,module=matches[0],
                     original_function_name=original,parameter_id=parameter,source_ref=self.ledger.sources[matches[0]],
                     item_type=item_type,collection_sequence=len(self.ledger.rows))
            self.ledger.append(row); self.emit('collection_item',row)
    def summary(self,exitcode):
        return dict(pytest_exit_code=int(exitcode),collection_errors=self.errors,collection_skips=self.skips,
                    deselected=self.deselected,item_count=len(self.ledger.rows),
                    function_counts={m+'::'+f:n for (m,f),n in self.ledger.counts.items()},
                    ordered_roster_sha256=roster_digest([r['nodeid'] for r in self.ledger.rows]),
                    fixture_setup_calls=self.fixture_calls,runtest_protocol_calls=self.protocol_calls,
                    phase_report_calls=self.report_calls)

def collect(pytest_module,policy,plugin,manager_gate):
    need(pytest_module.__version__==policy['version'],'pinned pytest version')
    args=validate_arguments(policy)
    # manager_gate installs the instance gate in the pinned PytestPluginManager
    # constructor before original __init__ registers mark/main/helpconfig.
    restore=manager_gate(pytest_module,policy,plugin)
    try:
        exitcode=pytest_module.main(args,plugins=[plugin])
        summary=plugin.summary(exitcode)
        plugin.ledger.finish(summary)
        plugin.emit('collection_end',summary)
        return summary
    finally:
        restore()
