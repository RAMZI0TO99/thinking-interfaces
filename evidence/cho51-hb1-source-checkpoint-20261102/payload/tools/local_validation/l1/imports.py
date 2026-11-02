"""Finite import finder using retained source bytes and exact extension paths."""
import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import sys
from .protocol import need, closed, string

def sticky(function):
    def checked(self,*args,**kwargs):
        finder=getattr(self,'finder',self)
        try:
            return function(self,*args,**kwargs)
        except BaseException as error:
            finder.effects.latch.refuse(str(error))
    return checked

class RetainedLoader(importlib.abc.Loader):
    def __init__(self,finder,row):
        self.finder,self.row=finder,row
    def create_module(self,spec):
        return None
    @sticky
    def exec_module(self,module):
        finder,row=self.finder,self.row
        finder.check_row(row)
        raw=finder.read_retained(row['file_ref'])
        need(type(raw) is bytes and len(raw)==row['file_ref']['bytes']
             and hashlib.sha256(raw).hexdigest()==row['file_ref']['sha256'],'retained source identity')
        need(row['file_ref']['path'].endswith('.py'),'source suffix')
        previous=finder.effects.allowed_compile
        finder.effects.allowed_compile=(row['file_ref']['sha256'],row['file_ref']['path'])
        previous_exec=finder.effects.allowed_exec
        try:
            code=compile(raw,row['file_ref']['path'],'exec',dont_inherit=True,optimize=0)
            finder.effects.allowed_exec=code
            exec(code,module.__dict__)
        finally:
            finder.effects.allowed_compile=previous
            finder.effects.allowed_exec=previous_exec
        finder.observe(row,module,type(self).__module__+'.'+type(self).__name__)

class ExtensionLoader(importlib.abc.Loader):
    def __init__(self,finder,row,spec):
        self.finder,self.row=finder,row
        self.delegate=importlib.machinery.ExtensionFileLoader(row['module'],row['file_ref']['path'])
    @sticky
    def create_module(self,spec):
        self.finder.check_row(self.row)
        self.finder.before_extension(self.row)
        return self.delegate.create_module(spec)
    @sticky
    def exec_module(self,module):
        self.finder.check_row(self.row)
        self.delegate.exec_module(module)
        self.finder.after_extension(self.row,module)
        self.finder.observe(self.row,module,type(self.delegate).__module__+'.'+type(self.delegate).__name__)

class RetainedFinder(importlib.abc.MetaPathFinder):
    def __init__(self,rows,path,phase,group,read_retained,effects,emit,before_extension,after_extension):
        self.rows={}; self.path=list(path); self.phase=phase; self.group=group
        self.read_retained,self.effects,self.emit=read_retained,effects,emit
        self.before_extension,self.after_extension=before_extension,after_extension
        self.observed={}; self.bootstrap={}; self.meta=None
        for row in rows:
            closed(row,'module kind file_ref namespace_paths phase initializer_group')
            name=string(row['module'],2048)
            need(name not in self.rows and row['kind'] in ('source','extension','builtin','frozen','namespace'),'finite import entry')
            need(type(row['namespace_paths']) is list,'namespace ordered paths')
            if row['kind'] in ('source','extension'):
                need(type(row['file_ref']) is dict,'file-backed import entry')
            else:
                need(row['file_ref'] is None,'nonfile import entry')
            self.rows[name]=row
    def install(self,bootstrap_names):
        need(set(sys.modules)==set(bootstrap_names),'unreviewed bootstrap module')
        self.bootstrap={name:sys.modules[name] for name in bootstrap_names}
        sys.path[:]=self.path
        sys.path_hooks[:]=[]
        sys.path_importer_cache.clear()
        sys.meta_path[:]=[self]
        self.meta=(self,)
    def check_row(self,row):
        need(row['phase']==self.phase() and row['initializer_group']==self.group(),'import phase/group gate')
        self.reconcile()
    @sticky
    def find_spec(self,fullname,path=None,target=None):
        need(target is None,'module reload refused')
        need(fullname in self.rows,'module outside finite import policy: '+fullname)
        row=self.rows[fullname]; self.check_row(row)
        if row['kind']=='source':
            loader=RetainedLoader(self,row)
            spec=importlib.util.spec_from_file_location(fullname,row['file_ref']['path'],loader=loader,
                    submodule_search_locations=row['namespace_paths'] or None)
        elif row['kind']=='extension':
            need(any(row['file_ref']['path'].endswith(s) for s in importlib.machinery.EXTENSION_SUFFIXES),'extension suffix')
            spec=importlib.util.spec_from_file_location(fullname,row['file_ref']['path'])
            spec.loader=ExtensionLoader(self,row,spec)
        elif row['kind']=='namespace':
            need(bool(row['namespace_paths']),'nonempty namespace')
            spec=importlib.machinery.ModuleSpec(fullname,None,is_package=True)
            spec.submodule_search_locations=list(row['namespace_paths'])
        elif row['kind']=='builtin':
            spec=importlib.machinery.BuiltinImporter.find_spec(fullname)
        else:
            spec=importlib.machinery.FrozenImporter.find_spec(fullname)
        need(spec is not None,'declared importer failed')
        if row['kind'] in ('builtin','frozen','namespace'):
            self.observed[fullname]=None
        return spec
    def observe(self,row,module,loader_type):
        need(module.__spec__.origin==row['file_ref']['path'],'module origin changed')
        namespace=list(vars(module).get('__path__',[]))
        need(namespace==row['namespace_paths'],'namespace ordered identity')
        self.observed[row['module']]=module
        self.emit('import_row',dict(module=row['module'],phase=self.phase(),origin=row['file_ref']['path'],
             kind=row['kind'],loader_type=loader_type,namespace_paths=namespace,
             retained_ref=row['file_ref'],initializer_group=self.group()))
    def reconcile(self):
        need(sys.path==self.path and tuple(sys.meta_path)==self.meta
             and sys.path_hooks==[] and sys.path_importer_cache=={},'import machinery mutation')
        for name,module in sys.modules.copy().items():
            if name in self.bootstrap:
                need(module is self.bootstrap[name],'bootstrap module replaced')
                continue
            need(name in self.rows,'unexpected sys.modules entry: '+name)
            row=self.rows[name]
            # Import machinery inserts an initializing module before exec_module.
            spec=vars(module).get('__spec__') if module is not None else None
            need(spec is not None and spec.name==name,'invalid module/spec')
            if row['file_ref'] is not None:
                need(spec.origin==row['file_ref']['path'],'module origin substitution')
            if name in self.observed and self.observed[name] is not None:
                need(module is self.observed[name],'module object replaced')
            if not getattr(spec,'_initializing',False):
                need(list(vars(module).get('__path__',[]))==row['namespace_paths'],'namespace paths changed')

