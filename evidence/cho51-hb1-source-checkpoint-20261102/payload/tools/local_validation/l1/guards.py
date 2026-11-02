"""Pre-effect gates installed before dependency/canonical initialization.

These gates implement the reviewed cooperative source trust model, not a native
security sandbox. All bypassable native branches require separate plan mediation.
"""
import hashlib
import io
import types
from pathlib import Path,WindowsPath,PosixPath
from .protocol import need, integer, string, closed, encode, FailureLatch

def raw_get(root, dotted):
    """Resolve only module/class dictionaries; never evaluate a descriptor."""
    current=root
    for component in dotted.split('.'):
        need(type(current) in (types.ModuleType,type), 'guard owner must be exact module/plain-metaclass class')
        values=vars(current)
        need(component in values,'required guard symbol absent')
        current=values[component]
    return current

def raw_owner(root,dotted):
    parts=dotted.rsplit('.',1)
    return (root,parts[0]) if len(parts)==1 else (raw_get(root,parts[0]),parts[1])

class GuardRegistry:
    def __init__(self, phase, emit, latch=None):
        self.phase,self.emit=phase,emit
        self.latch=latch or FailureLatch()
        self.guards={}; self.denials=[]; self.sentinel=None
    def blocker(self,guard_id):
        def blocked(*args,**kwargs):
            ordinal=len(self.denials)
            expected=self.sentinel
            event=dict(ordinal=ordinal,phase=self.phase(),mechanism='api_blocker',operation=guard_id,
                       target_role='forbidden_effect',expected_sentinel_id=expected,before_effect=True)
            self.denials.append(event)
            self.emit('denial',event)
            if expected is None or expected!=guard_id:
                self.latch.refuse('unplanned denied attempt: '+guard_id)
            raise SentinelDenied(guard_id)
        return blocked
    def install(self,row,modules):
        closed(row,'guard_id phase_installed defining_module symbol equivalents bound_aliases sentinel refusal_event')
        key=string(row['guard_id'],256)
        need(key not in self.guards and self.phase()==row['phase_installed'],'guard install phase/duplicate')
        need(row['defining_module'] in modules,'guard defining module missing')
        module=modules[row['defining_module']]
        target=raw_get(module,row['symbol'])
        need(callable(target),'guarded callable required')
        blocker=self.blocker(key)
        owner,name=raw_owner(module,row['symbol'])
        setattr(owner,name,blocker)
        for equivalent in row['equivalents']:
            closed(equivalent,'module symbol')
            other=modules[equivalent['module']]
            raw_get(other,equivalent['symbol'])
            owner,name=raw_owner(other,equivalent['symbol']); setattr(owner,name,blocker)
        self.guards[key]=(row,blocker)
        return blocker
    def verify_aliases(self,modules,require_all=False):
        for row,blocker in self.guards.values():
            need(raw_get(modules[row['defining_module']],row['symbol']) is blocker,'guard overwritten')
            for alias in row['bound_aliases']:
                closed(alias,'module symbol')
                if alias['module'] not in modules and not require_all:
                    continue
                need(alias['module'] in modules,'required canonical alias consumer absent')
                need(raw_get(modules[alias['module']],alias['symbol']) is blocker,'stale canonical by-value alias')
    def check_sentinel(self,key):
        need(key in self.guards and self.sentinel is None,'sentinel guard identity')
        row,blocker=self.guards[key]
        closed(row['sentinel'],'args kwargs')
        need(type(row['sentinel']['args']) is list and type(row['sentinel']['kwargs']) is dict,'finite sentinel arguments')
        # Only JSON values reach the blocker; it never examines or invokes them.
        encode(row['sentinel'])
        before=len(self.denials); self.sentinel=key
        try:
            blocker(*row['sentinel']['args'],**row['sentinel']['kwargs'])
            self.latch.refuse('sentinel was not denied')
        except SentinelDenied as denied:
            need(str(denied)==key and len(self.denials)==before+1,'sentinel event mismatch')
        finally:
            self.sentinel=None
        self.latch.check()
        return True

class SentinelDenied(Exception):
    pass

class EffectGate:
    PROCESS=('subprocess.Popen','os.system','os.fork','os.posix_spawn','os.spawn','os.startfile','pty.spawn')
    NETWORK=('socket.__new__','socket.connect','socket.bind','socket.getaddrinfo','urllib.Request')
    def __init__(self,phase,latch=None):
        self.phase=phase; self.latch=latch or FailureLatch(); self.allowed_compile=None; self.allowed_exec=None
        self.allowed_native=None;self.allowed_directory=None
    def audit(self,event,args):
        try:
            return self._audit(event,args)
        except Exception as error:
            self.latch.refuse(str(error))
    def _audit(self,event,args):
        if event=='open':
            self.latch.refuse('unmediated builtin/io/raw file open')
        if event in ('os.putenv','os.unsetenv'):
            self.latch.refuse('environment/PATH mutation')
        if event=='ctypes.dlopen':
            need(len(args)==1 and args[0]==self.allowed_native and self.allowed_native is not None,'undeclared native load audit')
        if event=='os.add_dll_directory':
            need(len(args)==1 and args[0]==self.allowed_directory and self.allowed_directory is not None,'undeclared DLL directory audit')
        if event in self.PROCESS or event in self.NETWORK or event.startswith(('os.exec','os.spawn')):
            self.latch.refuse('forbidden process/network audit: '+event)
        if event=='compile':
            need(self.allowed_compile is not None and len(args)==2,'dynamic compile outside retained import gate')
            raw,filename=args
            need(type(raw) is bytes and filename==self.allowed_compile[1]
                 and hashlib.sha256(raw).hexdigest()==self.allowed_compile[0], 'unplanned dynamic compilation')
        if event=='exec':
            need(len(args)==1 and args[0] is self.allowed_exec,'dynamic exec outside retained import gate')
    def deny(self,*args,**kwargs):
        self.latch.refuse('forbidden process/network/diagnostic API')

class ResourceGate:
    """Reads only from original retained bytes; writes use parent capability.

    read_retained(ref) returns fully verified bytes from an original handle.
    publish(path, mode) owns create-new/identity/limits; ambient open is never used.
    """
    def __init__(self,rows,phase,caller,read_retained,publish,emit,latch=None):
        self.rows={}; self.phase=phase; self.caller=caller
        self.read_retained,self.publish,self.emit=read_retained,publish,emit
        self.latch=latch or FailureLatch(); self.observed=[]
        for row in rows:
            closed(row,'resource_id file_ref caller phase mode maximum_bytes mediation observation_required')
            path=row['file_ref']['path']
            need(path not in self.rows and '*' not in path and row['mode']=='rb','finite exact read resource')
            need(row['mediation']=='l1.ResourceGate.open','qualified resource mediation required')
            integer(row['maximum_bytes'],0,2*1024**3)
            need(type(row['observation_required']) is bool,'resource observation flag')
            self.rows[path]=row
    def open(self,file,mode='r',buffering=-1,encoding=None,errors=None,newline=None,closefd=True,opener=None):
        try:
            return self._open(file,mode,buffering,encoding,errors,newline,closefd,opener)
        except Exception as error:
            self.latch.refuse(str(error))
    def _open(self,file,mode='r',buffering=-1,encoding=None,errors=None,newline=None,closefd=True,opener=None):
        if type(file) in (Path,WindowsPath,PosixPath):file=str(file).replace('\\','/')
        need(type(file) is str and type(mode) is str and opener is None and closefd is True,'resource open shape')
        if mode not in ('r','rt','rb'):
            # Exact write grants are supplied by the parent, never a prefix test.
            return self.publish(file,mode)
        row=self.rows.get(file)
        if row is None or row['phase']!=self.phase() or row['caller']!=self.caller():
            self.latch.refuse('undeclared resource read/call site')
        raw=self.read_retained(row['file_ref'])
        need(type(raw) is bytes and len(raw)==row['file_ref']['bytes']
             and len(raw)<=row['maximum_bytes'] and hashlib.sha256(raw).hexdigest()==row['file_ref']['sha256'],'resource retained bytes')
        stream=ObservedBytes(raw,self,row)
        if mode=='rb':
            need(encoding is None and errors is None and newline is None,'binary resource options')
            return stream
        need(encoding in (None,'utf-8','utf8') and errors in (None,'strict'),'finite text resource encoding')
        return io.TextIOWrapper(stream,encoding='utf-8',errors='strict',newline=newline)
    def required_complete(self):
        seen={r['resource_id'] for r in self.observed}
        need(all(not r['observation_required'] or r['resource_id'] in seen for r in self.rows.values()),'unobserved required resource')

class ObservedBytes(io.BytesIO):
    def __init__(self,raw,gate,row):
        super().__init__(raw); self.gate,self.row,self.count=gate,row,0; self.reported=False
    def _count(self,n):
        self.count+=n
        if self.count>self.row['maximum_bytes']:
            self.gate.latch.refuse('resource cumulative read byte cap')
    def read(self,size=-1):
        raw=super().read(size); self._count(len(raw)); return raw
    def read1(self,size=-1):
        return self.read(size)
    def readinto(self,buffer):
        n=super().readinto(buffer); self._count(n); return n
    def readline(self,size=-1):
        raw=super().readline(size); self._count(len(raw)); return raw
    def getvalue(self):
        raw=super().getvalue(); self._count(len(raw)); return raw
    def getbuffer(self):
        self.gate.latch.refuse('unmediated resource memoryview')
    def readlines(self,hint=-1):
        rows=[];size=0
        while True:
            raw=self.readline()
            if not raw:return rows
            rows.append(raw);size+=len(raw)
            if hint>0 and size>=hint:return rows
    def close(self):
        if not self.reported:
            self.reported=True
            row=dict(resource_id=self.row['resource_id'],phase=self.gate.phase(),caller=self.row['caller'],
                     retained_ref=self.row['file_ref'],mode='rb',bytes_read=self.count,
                     mechanism='l1.ResourceGate.open',outcome='observed')
            self.gate.observed.append(row); self.gate.emit('resource_row',row)
        super().close()

class LoaderFacade:
    """Callable permits exact reviewed invocations and signature assignment.

    The original callable is held in a closure rather than exposed as an
    attribute. Python introspection is outside the cooperative trust boundary.
    """
    __slots__=('argtypes','restype','_invoke','_refuse')
    def __init__(self,name,original,permit,refuse=None):
        self.argtypes=None; self.restype=None
        self._refuse=refuse or (lambda message:need(False,message))
        def invoke(args):
            if name=='LoadLibraryW':self._refuse('Torch legacy PATH/LoadLibraryW fallback refused')
            need(permit(name,args) is True,'native loader request outside finite plan')
            original.argtypes=self.argtypes; original.restype=self.restype
            return original(*args)
        self._invoke=invoke
    def __call__(self,*args,**kwargs):
        if kwargs:self._refuse('native loader positional shape')
        return self._invoke(args)

def native_choice(rows,requester,name,flags,directories,phase):
    matches=[r for r in rows if r['requester']==requester and r['requested_name']==name
             and r['flags']==flags and type(flags) is int and r['search_directories']==directories and r['phase']==phase]
    need(len(matches)==1,'unique exact importer native choice')
    chosen=matches[0]
    need((chosen['chosen_file'] is None)!=(chosen['allowed_system_role'] is None),'native trust choice')
    basenames={}
    for row in rows:
        file=row['chosen_file']
        if file is not None:
            basename=file['path'].rsplit('/',1)[-1].lower()
            existing=basenames.setdefault(basename,file['path'])
            need(existing==file['path'],'competing USER_DIRS basename')
    return chosen

def install_python_gates(resource_gate,effects,aliases,modules):
    """Install ordinary reads/process gates and verify reviewed early aliases.

    All original-handle capabilities must already be captured by the parent.
    Native loader/resource mediation is an additional required host capability.
    """
    import builtins
    import os
    import sys
    originals={('builtins','open'):builtins.open,('io','open'):io.open,
               ('os','open'):os.open,('os','system'):os.system}
    for row in aliases:
        closed(row,'module symbol original_module original_symbol replacement')
        need((row['original_module'],row['original_symbol']) in originals,'reviewed early alias origin')
        owner=modules[row['module']]
        need(raw_get(owner,row['symbol']) is originals[(row['original_module'],row['original_symbol'])],
             'early alias identity mismatch')
        target,name=raw_owner(owner,row['symbol'])
        need(row['replacement'] in ('resource_open','deny'),'alias replacement role')
        setattr(target,name,resource_gate.open if row['replacement']=='resource_open' else effects.deny)
    builtins.open=resource_gate.open; io.open=resource_gate.open
    os.open=effects.deny; os.system=effects.deny
    # os fd primitives would expose unobserved reads/writes or descriptor aliases.
    for name in ('read','write','pread','pwrite','readv','writev','fdopen','dup','dup2',
                 'truncate','remove','unlink','rename','replace','mkdir','makedirs','rmdir',
                 'chmod','chown','link','symlink','startfile','spawnl','spawnv','execv','putenv','unsetenv'):
        if name in vars(os): setattr(os,name,effects.deny)
    sys.addaudithook(effects.audit)
    return originals
