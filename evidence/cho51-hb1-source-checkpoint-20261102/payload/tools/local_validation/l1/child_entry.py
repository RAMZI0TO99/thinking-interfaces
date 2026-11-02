"""L1 child orchestration over externally authenticated retained capabilities.

There is intentionally no command-line path loader. lhost1 binds this function
to verified bootstrap bytes and an owned report pipe after atomic Job admission.
No supplied JSON pathname can manufacture a VerifiedContext.
"""
import hashlib
import importlib
import sys
from dataclasses import dataclass
from .protocol import need, encode, FailureLatch, PhaseMachine, COUNTERS, SAFETY
from .plan import validate_groups,validate_policies
from .guards import GuardRegistry,EffectGate,ResourceGate,install_python_gates
from .imports import RetainedFinder
from .observation import CollectionLedger,NativeLedger,ABI_SCOPE
from .collection import CollectionPlugin,collect

@dataclass(frozen=True)
class VerifiedContext:
    """lhost1 creates only after chain/identity/containment checks.

    These are source-pinned capability implementations, never names resolved
    from policy strings or callbacks deserialized from JSON. Host callbacks
    remain subject to original deadline/resource controls.
    """
    operation_id: str
    groups: list
    policies: dict
    static_roster: dict
    candidate_refs: dict
    writer: object
    checkpoint: object
    tick: object
    read_retained: object
    publish: object
    caller: object
    native_observer: object
    native_resolver: object
    before_extension: object
    after_extension: object
    install_native_gates: object
    verify_native_gates: object
    manager_gate: object
    final_verify: object
    mechanism_checkpoint: object
    phase_dispatch: object
    bind_emit: object
    bind_effects: object
    bootstrap_modules: tuple
    expected_ids: object = None

def run_child(context):
    need(type(context) is VerifiedContext,'authenticated host context required')
    ctx=context
    groups=validate_groups(ctx.groups); policies=validate_policies(ctx.policies,groups)
    need(ctx.operation_id==ctx.writer.validator.operation_id,'report pipe operation join')
    latch=FailureLatch(); machine=PhaseMachine(latch); group=[None]
    counters={k:0 for k in COUNTERS}
    safe={k:False for k in SAFETY[:5]}; safe.update({k:0 for k in SAFETY[5:]})
    observation_hash=hashlib.sha256(); observer_shutdown=False
    def checkpoint():
        latch.check(); need(ctx.checkpoint() is True,'host child checkpoint'); return True
    def emit(kind,payload):
        checkpoint()
        if kind=='denial' and 'tick' not in payload: payload=dict(payload,tick=ctx.tick())
        observation_hash.update(encode({'kind':kind,'payload':payload}))
        ctx.writer.emit(machine.state,kind,payload)
    ctx.bind_emit(emit)
    registry=GuardRegistry(lambda:machine.state,emit,latch)
    effects=EffectGate(lambda:machine.state,latch)
    ctx.bind_effects(effects)
    resource_policy=policies['resource_policy']
    resources=ResourceGate(resource_policy['rows'],lambda:machine.state,ctx.caller,
                           ctx.read_retained,ctx.publish,emit,latch)
    observer=ctx.native_observer
    native=NativeLedger(observer.generation,ctx.native_resolver)
    imported=[]
    guard_rows=policies['guard_policy']['rows']
    def install_available():
        for row in guard_rows:
            if row['guard_id'] not in registry.guards and row['phase_installed']==machine.state and row['defining_module'] in sys.modules:
                registry.install(row,sys.modules)
    def after_import(kind,row):
        emit(kind,row); imported.append(row)
        # Safetensors load/save/file APIs are replaced during loader completion,
        # before a canonical from-import can capture the original callable.
        install_available()
    def native_checkpoint(final=False):
        for row in observer.drain():
            joined=native.event(row); emit('native_event',row)
            emit('native_join',dict(event_sequence=row['event_sequence'],**joined,snapshot_membership='event-replay'))
        snapshots=[]
        for attempt in range(3):
            checkpoint(); snapshots.append(observer.snapshot())
            for row in observer.drain():
                joined=native.event(row); emit('native_event',row)
                emit('native_join',dict(event_sequence=row['event_sequence'],**joined,snapshot_membership='event-replay'))
            if len(snapshots)>=2 and snapshots[-1]==snapshots[-2]:
                native.reconcile(snapshots[-2:]); return
        latch.refuse('native snapshots unstable after three attempts')
    def state_checkpoint(finder):
        checkpoint(); finder.reconcile(); native_checkpoint()
        need(ctx.verify_native_gates(policies['native_policy']) is True,'native policy/environment mutation')
        ctx.mechanism_checkpoint(machine.state,resources,registry)
        emit('checkpoint',dict(state=machine.state,tick=ctx.tick(),
             imports_digest=hashlib.sha256(encode(imported)).hexdigest(),native_sequence=native.sequence-1,
             resources_digest=hashlib.sha256(encode(resources.observed)).hexdigest(),
             guard_digest=hashlib.sha256(encode(sorted(registry.guards))).hexdigest(),counters=counters.copy()))
    try:
        machine.advance('L1'); ctx.phase_dispatch('L1'); checkpoint()
        boundary=observer.start()
        for row,joined in zip(boundary['events'],native.establish(boundary)):
            emit('native_event',row)
            emit('native_join',dict(event_sequence=row['event_sequence'],**joined,snapshot_membership='registration-prefix-replay'))
        need(ctx.install_native_gates(policies['native_policy'],resource_policy['native_branches']) is True,
             'native loading/resource mediation not established')
        import_policy=policies['import_policy']
        finder=RetainedFinder(import_policy['rows'],import_policy['ordered_sys_path'],lambda:machine.state,
            lambda:group[0],ctx.read_retained,effects,after_import,ctx.before_extension,ctx.after_extension)
        finder.install(ctx.bootstrap_modules)
        install_python_gates(resources,effects,policies['guard_policy']['early_aliases'],sys.modules)
        state_checkpoint(finder)
        for row in groups:
            if row['phase']!=machine.state:
                machine.advance(row['phase'])
                ctx.phase_dispatch(machine.state)
            group[0]=row['group_id']; checkpoint(); install_available()
            for module in row['modules']:
                checkpoint(); importlib.import_module(module); install_available()
            registry.verify_aliases(sys.modules)
            state_checkpoint(finder)
        need(machine.state=='L3','missing canonical initialization phase')
        need(set(registry.guards)=={r['guard_id'] for r in guard_rows},'required blocker missing')
        for key in registry.guards:
            registry.check_sentinel(key)
            guard_row,blocker=registry.guards[key]
            emit('guard_row',dict(guard_id=key,phase=machine.state,
                 defining_symbol=guard_row['defining_module']+'.'+guard_row['symbol'],blocker_identity=hex(id(blocker)),
                 aliases=guard_row['bound_aliases'],sentinel_result=True,denial_sequence=len(registry.denials)-1))
        registry.verify_aliases(sys.modules,require_all=True)
        machine.advance('L4'); ctx.phase_dispatch('L4'); group[0]='collection'
        ledger=CollectionLedger(ctx.static_roster,ctx.candidate_refs,ctx.expected_ids)
        plugin=CollectionPlugin(ledger,emit,latch.refuse)
        pytest=sys.modules.get('pytest'); need(pytest is not None,'pytest was not explicitly initialized')
        summary=collect(pytest,policies['pytest_policy'],plugin,ctx.manager_gate)
        state_checkpoint(finder)
        machine.advance('L5'); ctx.phase_dispatch('L5'); checkpoint()
        resources.required_complete(); registry.verify_aliases(sys.modules,require_all=True)
        state_checkpoint(finder)
        need(ctx.final_verify() is True,'original retained final verification incomplete')
        for row in observer.stop():
            joined=native.event(row); emit('native_event',row)
            emit('native_join',dict(event_sequence=row['event_sequence'],**joined,snapshot_membership='final-drain'))
        observer_shutdown=True
        observer.release()
        checkpoint()
        ctx.writer.emit('L5','terminal',dict(status='provisional-complete',first_failure=None,completed_state='L5',
            observations_digest=observation_hash.hexdigest(),counters=counters,observer_shutdown=True,safety=safe))
        return summary
    except BaseException as error:
        # Failure cannot be turned into success by caught candidate exceptions or
        # successful shutdown. Parent retains partial frames and unknown custody.
        if latch.first is None: latch.first=type(error).__name__+': '+str(error)[:3000]
        try:
            if observer.started and not observer.closed:
                observer.stop(); observer_shutdown=True; observer.release()
        except BaseException:
            observer_shutdown=False
        try:
            ctx.writer.emit(machine.state,'terminal',dict(status='refused',first_failure=latch.first,
                completed_state=machine.state,observations_digest=observation_hash.hexdigest(),counters=counters,
                observer_shutdown=observer_shutdown,safety=safe))
        except BaseException:
            pass
        raise
