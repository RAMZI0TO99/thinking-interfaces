import hashlib
import types
import unittest
from .protocol import Refusal
from .guards import GuardRegistry,ResourceGate,EffectGate,LoaderFacade,raw_get,native_choice
from .test_support import retained

class GuardTests(unittest.TestCase):
    def make_guard(self):
        module=types.ModuleType('owned'); effects=[]
        module.load=lambda *a:effects.append('forbidden')
        row=dict(guard_id='load',phase_installed='L2',defining_module='owned',symbol='load',equivalents=[],
                 bound_aliases=[dict(module='consumer',symbol='load')],sentinel=dict(args=[],kwargs={}),refusal_event='denial')
        registry=GuardRegistry(lambda:'L2',lambda *a:None)
        return module,effects,row,registry
    def test_sentinel_before_effect(self):
        module,effects,row,registry=self.make_guard(); registry.install(row,{'owned':module})
        self.assertTrue(registry.check_sentinel('load')); self.assertEqual(effects,[])
    def test_missing_required_symbol(self):
        module,_,row,registry=self.make_guard(); del module.load
        with self.assertRaises(Refusal): registry.install(row,{'owned':module})
    def test_alias_stale(self):
        module,_,row,registry=self.make_guard(); consumer=types.ModuleType('consumer'); consumer.load=module.load
        registry.install(row,{'owned':module})
        with self.assertRaises(Refusal): registry.verify_aliases({'owned':module,'consumer':consumer})
    def test_alias_bound_blocker(self):
        module,_,row,registry=self.make_guard(); registry.install(row,{'owned':module})
        consumer=types.ModuleType('consumer'); consumer.load=module.load
        registry.verify_aliases({'owned':module,'consumer':consumer},True)
    def test_unexpected_denial_sticky(self):
        module,_,row,registry=self.make_guard(); registry.install(row,{'owned':module})
        with self.assertRaises(Refusal): module.load()
        with self.assertRaises(Refusal): registry.check_sentinel('load')
    def test_descriptor_not_evaluated(self):
        seen=[]
        class Dummy:
            @property
            def trap(self): seen.append(1); return 7
        self.assertIsInstance(raw_get(Dummy,'trap'),property); self.assertEqual(seen,[])
    def test_resource_exact_read(self):
        raw=b'owned'; pin=retained('D:/fixture/resource.txt',raw,'resource'); events=[]
        row=dict(resource_id='owned',file_ref=pin,caller='owned:1',phase='L2',mode='rb',maximum_bytes=5,
                 mediation='l1.ResourceGate.open',observation_required=True)
        gate=ResourceGate([row],lambda:'L2',lambda:'owned:1',lambda r:raw,lambda *a:None,lambda *e:events.append(e))
        with gate.open(pin['path'],'rb') as stream: self.assertEqual(stream.read(),raw)
        gate.required_complete(); self.assertEqual(events[0][1]['bytes_read'],5)
        with self.assertRaises(Refusal): gate.open('D:/fixture/other.txt','rb')
    def test_native_unmediated_refuses(self):
        row=dict(resource_id='x',file_ref=retained(),caller='x',phase='L2',mode='rb',maximum_bytes=100,
                 mediation='native-only-declared',observation_required=True)
        with self.assertRaises(Refusal): ResourceGate([row],lambda:'L2',lambda:'x',lambda r:b'',lambda *a:None,lambda *a:None)
    def test_network_process_pre_effect(self):
        gate=EffectGate(lambda:'L2')
        with self.assertRaises(Refusal): gate.audit('subprocess.Popen',('git',))
    def test_torch_fallback_pre_effect(self):
        called=[]; facade=LoaderFacade('LoadLibraryW',lambda *a:called.append(a),lambda *a:True)
        facade.argtypes=['owned']; facade.restype='owned'
        with self.assertRaises(Refusal): facade('D:/fixture/x.dll')
        self.assertEqual(called,[])
    def test_loader_signature_facade(self):
        class Function:
            def __call__(self,*args): return args
        original=Function(); facade=LoaderFacade('LoadLibraryExW',original,lambda name,args:args==('D:/x.dll',None,4352))
        facade.argtypes=['path','reserved','flags']; facade.restype=int
        self.assertEqual(facade('D:/x.dll',None,4352),('D:/x.dll',None,4352))
        self.assertIs(original.restype,int)
    def test_dynamic_compile_digest(self):
        gate=EffectGate(lambda:'L2'); gate.allowed_compile=(hashlib.sha256(b'pass').hexdigest(),'D:/owned.py')
        gate.audit('compile',(b'pass','D:/owned.py'))
        with self.assertRaises(Refusal): gate.audit('compile',(b'evil','D:/owned.py'))
