"""Lazy ctypes binding to one retained native helper; no import-time native I/O."""
from .protocol import need, integer, string

def structures(ctypes):
    class Event(ctypes.Structure):
        _fields_=[('sequence',ctypes.c_uint64),('base',ctypes.c_uint64),('generation',ctypes.c_uint64),
                  ('reason',ctypes.c_uint32),('image_size',ctypes.c_uint32),('path_units',ctypes.c_uint32),
                  ('faults',ctypes.c_uint32),('path',ctypes.c_uint16*1024)]
    class Image(ctypes.Structure):
        _fields_=[('base',ctypes.c_uint64),('image_size',ctypes.c_uint32),('path_units',ctypes.c_uint32),
                  ('path',ctypes.c_uint16*1024)]
    class State(ctypes.Structure):
        _fields_=[(n,ctypes.c_uint32) for n in ('abi','event_size','image_size','state_size','started',
                  'stopped','active_callbacks','faults','produced','consumed','capacity','path_capacity')]+[('generation',ctypes.c_uint64)]
    need(ctypes.sizeof(Event)==2088 and ctypes.sizeof(Image)==2064 and ctypes.sizeof(State)==56,'native ABI sizes')
    need(Event.path.offset==40 and Image.path.offset==16 and State.generation.offset==48,'native ABI offsets')
    return Event,Image,State

def copied_path(row):
    integer(row.path_units,1,1023)
    need(row.path[row.path_units]==0,'native terminated path')
    raw=b''.join(int(row.path[i]).to_bytes(2,'little') for i in range(row.path_units))
    try:
        value=raw.decode('utf-16-le','strict')
    except UnicodeError as error:
        from .protocol import Refusal
        raise Refusal('malformed native UTF16') from error
    string(value,4096)
    # Normalization is a representation step only; exact P path/identity join is
    # still required, and case aliases cannot be rescued by this conversion.
    return value.replace('\\','/')

class NativeObserver:
    def __init__(self,retained_helper,verify_same_handle,checkpoint,phase,generation,load_exact=None,release_exact=None):
        self.ref=retained_helper; self.verify=verify_same_handle; self.checkpoint=checkpoint
        self.phase=phase; self.generation=integer(generation,1); self.release_exact=release_exact
        self.closed=False; self.started=False; self.next_sequence=1; self.reference_released=False
        need(self.verify(self.ref) is True,'helper retained same-handle verification')
        import ctypes
        self.ctypes=ctypes; self.Event,self.Image,self.State=structures(ctypes)
        # load_exact exists solely for injected Q native fixtures; production
        # caller supplies the newly qualified exact retained capability.
        need(load_exact is not None and release_exact is not None,'qualified helper load/release capabilities required')
        self.dll=load_exact(self.ref)
        signatures={
          'l1_start':([ctypes.c_uint32,ctypes.c_uint64],ctypes.c_int),
          'l1_drain':([ctypes.POINTER(self.Event),ctypes.c_uint32,ctypes.POINTER(ctypes.c_uint32),ctypes.POINTER(ctypes.c_uint32)],ctypes.c_int),
          'l1_snapshot':([ctypes.POINTER(self.Image),ctypes.c_uint32,ctypes.POINTER(ctypes.c_uint32)],ctypes.c_int),
          'l1_stop':([ctypes.POINTER(ctypes.c_uint32)],ctypes.c_int),
          'l1_state':([ctypes.POINTER(self.State)],ctypes.c_int)}
        for name,(args,result) in signatures.items():
            function=getattr(self.dll,name); function.argtypes=args; function.restype=result
        state=self.state()
        need(state.abi==1 and state.event_size==2088 and state.image_size==2064 and state.state_size==56
             and state.capacity==8192 and state.path_capacity==1024,'helper ABI self description')
    def _check(self):
        need(self.checkpoint() is True and not self.closed,'observer checkpoint/closed')
    def state(self):
        self._check(); value=self.State()
        need(self.dll.l1_state(self.ctypes.byref(value))==1,'observer state API')
        need(value.faults==0,'sticky native fault')
        return value
    def start(self):
        self._check(); need(not self.started,'observer already started')
        need(self.dll.l1_start(1,self.generation)==1,'notification registration failed')
        self.started=True
        # A snapshot after registration is a state *after* some notifications,
        # not the registration baseline. Find a bounded quiescent sequence cut;
        # retain every earlier event so the ledger can reverse/replay the prefix.
        for attempt in range(3):
            before=self.state()
            first=self.snapshot();second=self.snapshot()
            after=self.state()
            if before.active_callbacks or after.active_callbacks or before.produced!=after.produced or first!=second:
                continue
            cut=after.produced;rows=self.drain()
            need(len(rows)<=8192,'bootstrap event cap')
            # drain may include later events. Split at the observed cut and keep
            # the suffix for ordinary replay instead of discarding a transient.
            prefix=[r for r in rows if r['event_sequence']<=cut]
            self.pending_events=[r for r in rows if r['event_sequence']>cut]
            need(len(prefix)==cut,'bootstrap notification prefix gap')
            return dict(snapshots=[first,second],events=prefix,cut_sequence=cut)
        need(False,'native bootstrap snapshot/event cut unstable')
    def drain(self):
        self._check(); need(self.started,'drain before start')
        rows=getattr(self,'pending_events',[]);self.pending_events=[]
        while True:
            self._check()
            page=(self.Event*32)(); count=self.ctypes.c_uint32(); faults=self.ctypes.c_uint32()
            need(self.dll.l1_drain(page,32,self.ctypes.byref(count),self.ctypes.byref(faults))==1
                 and faults.value==0 and count.value<=32,'native drain/overflow')
            for event in page[:count.value]:
                integer(event.sequence,self.next_sequence,self.next_sequence)
                need(event.generation==self.generation and event.faults==0 and event.reason in (1,2),'native event fields')
                rows.append(dict(event_sequence=event.sequence,reason='load' if event.reason==1 else 'unload',
                      phase=self.phase(),base=event.base,image_size=event.image_size,full_path=copied_path(event),
                      native_observer_generation=event.generation,fault_flags=0))
                self.next_sequence+=1
            need(len(rows)<=8192,'native whole event cap')
            if count.value<32:
                return rows
    def snapshot(self):
        self._check(); page=(self.Image*4096)(); count=self.ctypes.c_uint32()
        need(self.dll.l1_snapshot(page,4096,self.ctypes.byref(count))==1 and count.value<=4096,'native snapshot failed/oversized')
        return [dict(base=r.base,image_size=r.image_size,full_path=copied_path(r)) for r in page[:count.value]]
    def stop(self):
        self._check(); faults=self.ctypes.c_uint32()
        need(self.dll.l1_stop(self.ctypes.byref(faults))==1 and faults.value==0,'unregister/callback completion unknown')
        final=self.drain(); state=self.state()
        need(state.stopped==1 and state.active_callbacks==0 and state.consumed==state.produced,'native final drain incomplete')
        need(self.verify(self.ref) is True,'final helper retained identity')
        self.closed=True
        return final
    def release(self):
        need(self.closed and not self.reference_released,'helper release before shutdown/duplicate')
        need(self.release_exact(self.dll,self.ref) is True,'owned helper reference release unknown')
        self.reference_released=True
