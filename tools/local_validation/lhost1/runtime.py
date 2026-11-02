"""Concrete child capabilities, finite DLL/resource mediation and plugin gate."""
import ctypes
import hashlib
import os
import sys
import types
from ..l1.protocol import need,encode,Refusal,ref
from ..l1.guards import raw_get,raw_owner,LoaderFacade,native_choice
from ..v1.records import windows_path
from . import abi

class Runtime:
    def __init__(self,reader,physical,policies,bindings,checkpoint,tick,emit):
        self.reader,self.physical,self.policies,self.bindings=reader,physical,policies,bindings
        self.checkpoint,self.tick,self.emit=checkpoint,tick,emit
        self.native_installed=False;self.directory_cookies={};self.before={};self.abi_observed=[]
        self.current_phase='L1'
        self.effects=None
        self.bindings=dict(bindings,phase=lambda:self.current_phase)
        self.original_cdll,self.original_windll=ctypes.CDLL,ctypes.WinDLL
        self.original_add=os.add_dll_directory
        self.environment=dict(os.environ)
        self.kernel=self.original_windll('kernel32.dll',use_last_error=True,winmode=0x800)
        self.kernel.FreeLibrary.argtypes=[ctypes.c_void_p];self.kernel.FreeLibrary.restype=ctypes.c_int
        self.kernel.SetDefaultDllDirectories.argtypes=[ctypes.c_uint32];self.kernel.SetDefaultDllDirectories.restype=ctypes.c_int
    def read(self,reference):
        need(self.checkpoint() is True,'retained capability checkpoint')
        value=self.reader.retain(reference['path'],{k:reference[k] for k in ('bytes','sha256')})
        need(value['native_identity']==reference['native_identity'],'retained native identity changed')
        if reference['bytes']<=8*1024**2:
            return self.reader.read_small(reference['path'],{k:reference[k] for k in ('bytes','sha256')})
        # Large extension PE input remains original-handle backed. This explicit
        # operation cap bounds the temporary full export parser input; larger
        # files require a future range-parser successor rather than overcommit.
        need(reference['bytes']<=64*1024**2,'L1 full-byte parser 64MiB operation cap')
        handle,descriptor,facts=self.reader._files[reference['path']]
        observed,raw=self.reader._hash(handle,descriptor['bytes'],collect=True)
        need(observed=={k:reference[k] for k in ('bytes','sha256')}
             and self.reader._facts(handle,reference['path'],False)==facts,'original-handle large read drift')
        return raw
    def verify(self,reference):
        raw=self.read(reference)
        return len(raw)==reference['bytes'] and hashlib.sha256(raw).hexdigest()==reference['sha256']
    def load_exact(self,reference):
        need(self.verify(reference) is True,'strict retained native artifact')
        return self.original_cdll(reference['path'],winmode=0x1100)
    def release_exact(self,dll,reference):
        need(self.verify(reference) is True,'native artifact before owned reference release')
        return self.kernel.FreeLibrary(dll._handle)==1
    def caller(self):
        frame=sys._getframe(1)
        for _ in range(32):
            filename=frame.f_code.co_filename.replace('\\','/')
            if '/tools/local_validation/l1/' not in filename and '/tools/local_validation/lhost1/' not in filename:
                return filename+':'+str(frame.f_lineno)
            frame=frame.f_back
            if frame is None:break
        raise Refusal('no finite resource call site')
    def refuse_write(self,*args):raise Refusal('no package write capability declared')
    def native_resolver(self,path,size,phase):
        rows=self.policies['native_policy']['rows']
        matches=[r for r in rows if r['phase']==phase and r['chosen_file'] is not None and r['chosen_file']['path']==path]
        if matches:
            need(len(matches)==1,'ambiguous event/importer search choice')
            row=matches[0];need(self.verify(row['chosen_file']) is True,'native path/hash/ID join')
            return dict(retained_ref=row['chosen_file'],system_role=None,requester_choice=hashlib.sha256(encode(row)).hexdigest())
        system=[r for r in self.bindings['platform_images'] if r['path']==path and r['image_size']==size and phase in r['phases']]
        need(len(system)==1,'unknown native/platform image')
        return dict(retained_ref=None,system_role=system[0]['role'],requester_choice=system[0]['rationale'])
    def install_native(self,native_policy,native_branches):
        need(not self.native_installed,'native gates duplicate')
        need(all(r['mediated_by']=='l1.ResourceGate.open' for r in native_branches),'native resource branch lacks implemented mediator')
        need(self.kernel.SetDefaultDllDirectories(0x1000)==1,'restricted default DLL search policy')
        runtime=self
        class KernelFacade:
            def __getattr__(self,name):
                if name in ('LoadLibraryW','LoadLibraryExW'):
                    original=getattr(runtime.kernel,name)
                    return LoaderFacade(name,original,runtime.permit_loader,runtime.effects.latch.refuse)
                need(name in runtime.bindings['kernel_symbols'],'unreviewed kernel function')
                return getattr(runtime.kernel,name)
        facade=KernelFacade()
        def windll(name,*args,**kwargs):
            if name=='kernel32.dll':return facade
            return runtime.load_library(name,args,kwargs,'ctypes.WinDLL')
        def cdll(name,*args,**kwargs):return runtime.load_library(name,args,kwargs,'ctypes.CDLL')
        def add(path):
            need(path in runtime.bindings['dll_directories'] and path not in runtime.directory_cookies,'unplanned/duplicate DLL search directory')
            runtime.effects.allowed_directory=path
            try:cookie=runtime.original_add(path)
            finally:runtime.effects.allowed_directory=None
            runtime.directory_cookies[path]=cookie;return cookie
        ctypes.WinDLL=windll;ctypes.CDLL=cdll;os.add_dll_directory=add
        class WindowsLibraries:
            def __getattr__(self,name):
                need(name=='kernel32','unreviewed ctypes.windll library');return facade
        ctypes.windll=WindowsLibraries()
        self.native_installed=True;return True
    def requester(self):
        frame=sys._getframe(2)
        for _ in range(32):
            module=frame.f_globals.get('__name__')
            if type(module) is str and not module.startswith('tools.local_validation.'):
                return module
            frame=frame.f_back
            if frame is None:break
        raise Refusal('native requester unidentified')
    def permit_loader(self,name,args):
        try:
            need(name=='LoadLibraryExW' and len(args)==3 and args[1] in (None,0) and type(args[1]) is not bool,'native loader shape/fallback')
            requested=args[0];need(type(requested) is str,'native requested path')
            row=native_choice(self.policies['native_policy']['rows'],self.requester(),requested,args[2],self.bindings['dll_directories'],self.bindings['phase']())
            self.native_preflight(row,requested,name)
            return True
        except BaseException as error:
            if self.effects is not None:self.effects.latch.refuse(str(error))
            raise
    def native_preflight(self,row,requested,mechanism):
        need(self.checkpoint() is True,'native pre-effect checkpoint')
        need(row['mechanism']==mechanism and type(requested) is str,'exact native mechanism')
        canonical=requested.replace('\\','/')
        need(windows_path(canonical,absolute=True)==canonical,'canonical native file path')
        need(len(canonical)>3 and canonical[0] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' and canonical[1:3]==':/'
             and all(part not in ('','.','..') for part in canonical[3:].split('/')) and '\0' not in canonical,'native absolute exact path')
        chosen=row['chosen_file']
        if chosen is not None:
            ref(chosen,retained=True)
            need(chosen['path']==canonical and row['allowed_system_role'] is None,'native retained path choice')
            need(self.verify(chosen) is True,'native pre-effect retained identity')
        else:
            matches=[p for p in self.bindings['platform_images'] if p['path']==canonical and p['role']==row['allowed_system_role']
                     and self.bindings['phase']() in p['phases']]
            need(len(matches)==1 and type(matches[0]['rationale']) is str and bool(matches[0]['rationale']),'exact reviewed platform loader choice')
        return row
    def load_library(self,name,args,kwargs,mechanism):
        try:
            need(not args and set(kwargs)<= {'winmode','use_errno','use_last_error'},'finite ctypes load arguments')
            flags=kwargs.get('winmode',0x1100)
            row=native_choice(self.policies['native_policy']['rows'],self.requester(),name,flags,self.bindings['dll_directories'],self.bindings['phase']())
            self.native_preflight(row,name,mechanism)
            loader=self.original_cdll if mechanism=='ctypes.CDLL' else self.original_windll
            self.effects.allowed_native=name
            try:return loader(name,**kwargs)
            finally:self.effects.allowed_native=None
        except BaseException as error:
            if self.effects is not None:self.effects.latch.refuse(str(error))
            raise
    def verify_native(self,policy):
        need(self.native_installed and dict(os.environ)==self.environment,'PATH/environment mutation/fallback')
        need(set(self.directory_cookies)<=set(self.bindings['dll_directories']),'unplanned DLL directories')
        return True
    def before_extension(self,row):
        self.before[row['module']]=abi.before_extension(row,self.policies['abi_policy']['rows'],self.read)
    def after_extension(self,row,module):
        def metadata(name):
            distributions=[]
            for reference in self.bindings['metadata_refs'][name]:
                text=self.read(reference).decode('utf-8','strict');fields={}
                for line in text.splitlines():
                    if not line:break
                    key,sep,value=line.partition(':')
                    if key in ('Name','Version'):
                        need(sep and key not in fields,'unique METADATA name/version');fields[key]=value.strip()
                need(set(fields)=={'Name','Version'},'METADATA name/version missing')
                distributions.append(dict(path=reference['path'],name=fields['Name'],version=fields['Version']))
            return dict(distributions=distributions)
        scope,observed=abi.after_extension(row,module,self.before.pop(row['module']),metadata,self.emit)
        self.abi_observed.append(observed)
        self.emit('abi_row',dict(module=row['module'],phase=self.bindings['phase'](),interpreter_identity=self.bindings['interpreter_identity'],
            extension_ref=row['file_ref'],metadata_refs=self.bindings['metadata_refs'][row['module']],symbol_results=observed['exports'],
            safe_query_results=observed['safe_queries'],loaded_image_refs=[row['file_ref']],scope=scope,unqualified_paths=observed['unqualified_paths']))
    def manager_gate(self,pytest,policy,plugin):
        from ..l1.collection import install_registration_gate
        config=sys.modules['_pytest.config'];klass=config.PytestPluginManager
        original=klass.__init__;runtime=self
        allowed={}
        for name,selector in policy['builtin_plugins'].items():
            need(type(selector) is str,'finite plugin selector')
            if selector.startswith('type:'):
                module,symbol=selector[5:].split(':')
                allowed[name]=raw_get(sys.modules[module],symbol)
                need(type(allowed[name]) is type,'pinned plugin type selector')
            else:
                allowed[name]=sys.modules[selector]
        allowed['l1_collection']=plugin
        def initialize(manager,*args,**kwargs):
            instance_allowed=dict(allowed)
            instance_allowed['l1_pytest_pluginmanager']=manager
            # Config is a finite pinned core type; capture its exact object at
            # the first registration, before any of its hooks are admitted.
            register=install_registration_gate(manager,instance_allowed,runtime.fail,policy['reviewed_hook_wrappers'])
            def internal_register(obj,name=None):
                if obj is manager and name is None:name='l1_pytest_pluginmanager'
                if name=='pytestconfig':
                    need(type(obj) is config.Config and obj.pluginmanager is manager,'pinned pytest Config object')
                    need('pytestconfig' not in instance_allowed,'duplicate pytestconfig')
                    instance_allowed['pytestconfig']=obj
                return register(obj,name)
            manager.register=internal_register
            original(manager,*args,**kwargs)
        klass.__init__=initialize
        # pytest.main's plugins=[plugin] normally derives an id-based name.
        # Pin get_canonical_name for this exact owned object only.
        canonical=klass.get_canonical_name
        klass.get_canonical_name=lambda manager,obj:'l1_collection' if obj is plugin else canonical(manager,obj)
        def restore():klass.__init__=original;klass.get_canonical_name=canonical
        return restore
    def fail(self,message):
        raise Refusal(message)
    def phase_dispatch(self,phase):
        need(phase in ('L1','L2','L3','L4','L5'),'runtime phase')
        self.current_phase=phase
    def bind_emit(self,emit):
        self.emit=emit
    def bind_effects(self,effects):
        self.effects=effects
