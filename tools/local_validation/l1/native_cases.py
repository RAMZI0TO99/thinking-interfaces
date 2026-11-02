"""Separately admitted native Q fixtures, each in a fresh owned Q child.

The caller supplies strict retained native refs after reviewed compiler output
custody transfer. This module neither compiles nor opens an arbitrary DLL path.
"""
from .protocol import need,integer,ref
from .native_bridge import NativeObserver,structures
from .observation import NativeLedger

def transient_case(helper,target,capabilities):
    """Registration, real benign load/unload, final drain and exact release."""
    ref(helper,retained=True); ref(target,retained=True)
    observer=NativeObserver(helper,capabilities.verify,capabilities.checkpoint,lambda:'L2',1,
                            capabilities.load_exact,capabilities.release_exact)
    target_dll=None; shutdown=False
    try:
        boundary=observer.start();baseline=boundary['snapshots'][-1]
        # Fixture-only platform trust is scoped to these observed tuples; it is
        # no installed-image identity/ABI assertion. The target still joins the
        # exact retained Q artifact and must replay through the production ledger.
        observed={(r['full_path'],r['image_size']) for r in baseline+boundary['events']}
        def resolve(path,size,phase):
            if path==target['path']:
                need(capabilities.verify(target) is True,'ledger exact Q target identity')
                return dict(retained_ref=target,system_role=None,requester_choice='q_owned_target_exact')
            need((path,size) in observed,'new unplanned Q baseline image')
            return dict(retained_ref=None,system_role='q_fixture_observed_bootstrap_tuple_only',requester_choice='no image attestation claim')
        ledger=NativeLedger(1,resolve);ledger.establish(boundary)
        initial=boundary['events']+observer.drain()
        for row in initial[len(boundary['events']):]:ledger.event(row)
        need(not any(r['full_path']==target['path'] for r in baseline),'target unexpectedly resident')
        need(capabilities.verify(target) is True,'target original retained bytes')
        target_dll=capabilities.load_exact(target)
        # Own export metadata is pinned; this benign getter is the only fixture
        # invocation authorized here and is not an installed-library ABI probe.
        import ctypes
        function=target_dll.l1_fixture_value; function.argtypes=[]; function.restype=ctypes.c_uint32
        need(function()==0x4c315146,'owned fixture getter')
        need(capabilities.release_exact(target_dll,target) is True,'target reference release')
        target_dll=None
        latest=observer.drain()
        for row in latest:ledger.event(row)
        rows=initial+latest
        matching=[r for r in rows if r['full_path']==target['path']]
        need([r['reason'] for r in matching]==['load','unload'],'transient load/unload lost or ambiguous')
        first,second=observer.snapshot(),observer.snapshot()
        need(first==second and not any(r['full_path']==target['path'] for r in second),'transient absent stable snapshots')
        ledger.reconcile([first,second])
        final=observer.stop()
        for row in final:ledger.event(row)
        rows+=final; shutdown=True; observer.release()
        need(capabilities.verify(helper) is True and capabilities.verify(target) is True,'final native inputs')
        return dict(case='transient',events=len(rows),transient_events=2,observer_shutdown=True,reference_released=True)
    finally:
        if target_dll is not None:
            need(capabilities.release_exact(target_dll,target) is True,'failure target reference release')
        if not shutdown and observer.started and not observer.closed:
            observer.stop(); observer.release()

def injection_case(helper,mode,capabilities):
    """Distinct L1_FIXTURE observer, never the production helper; one use/child."""
    need(mode in ('overflow','badreason','badutf16','pathbound'),'closed injection mode')
    ref(helper,retained=True); need(capabilities.verify(helper) is True,'fixture retained identity')
    import ctypes
    Event,Image,State=structures(ctypes)
    dll=capabilities.load_exact(helper); stopped=False
    try:
        dll.l1_start.argtypes=[ctypes.c_uint32,ctypes.c_uint64];dll.l1_start.restype=ctypes.c_int
        dll.l1_fixture_notify.argtypes=[ctypes.c_uint32,ctypes.POINTER(ctypes.c_uint16),ctypes.c_uint32,ctypes.c_uint64,ctypes.c_uint32]
        dll.l1_fixture_notify.restype=ctypes.c_int
        dll.l1_state.argtypes=[ctypes.POINTER(State)];dll.l1_state.restype=ctypes.c_int
        dll.l1_stop.argtypes=[ctypes.POINTER(ctypes.c_uint32)];dll.l1_stop.restype=ctypes.c_int
        need(dll.l1_start(1,1)==1,'fixture register')
        raw='D:/owned/injected.dll'.encode('utf-16-le'); units=len(raw)//2
        path=(ctypes.c_uint16*1025)()
        for i in range(units): path[i]=int.from_bytes(raw[2*i:2*i+2],'little')
        reason=1
        if mode=='badreason':reason=3
        if mode=='badutf16':path[0]=0xD800;units=1
        if mode=='pathbound':units=1024
        loops=8193 if mode=='overflow' else 1
        for i in range(loops):
            need(capabilities.checkpoint() is True,'native injection deadline/resource')
            need(dll.l1_fixture_notify(reason,path,units,4096,4096)==1,'owned injected call')
        state=State(); need(dll.l1_state(ctypes.byref(state))==1,'fixture state')
        expected=1 if mode=='overflow' else 2 if mode=='badreason' else 4
        need(state.faults&expected==expected,'expected native sticky fault absent')
        # A faulted observer reports failure even after known unregister. Check
        # the distinct physical stopped/active state rather than claiming success.
        faults=ctypes.c_uint32(); result=dll.l1_stop(ctypes.byref(faults))
        need(result==0 and faults.value&expected==expected,'fault disappeared on stop')
        need(dll.l1_state(ctypes.byref(state))==1 and state.stopped==1 and state.active_callbacks==0,'faulted observer unregister unknown')
        stopped=True
        return dict(case=mode,expected_fault=expected,faults=state.faults,observer_shutdown=True,operation_refused=True)
    finally:
        if not stopped:
            faults=ctypes.c_uint32();dll.l1_stop(ctypes.byref(faults))
            state=State();need(dll.l1_state(ctypes.byref(state))==1 and state.stopped==1 and state.active_callbacks==0,'fixture cleanup unknown')
        need(capabilities.release_exact(dll,helper) is True,'fixture helper release')
