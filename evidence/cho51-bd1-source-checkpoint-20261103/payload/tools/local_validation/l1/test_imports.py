import types
import unittest
from .protocol import Refusal
from .guards import EffectGate
from .imports import RetainedLoader
from .test_support import retained

class ImportTests(unittest.TestCase):
    def fixture(self,raw=b'owned_value = 17\n'):
        row=dict(module='owned_source',kind='source',file_ref=retained(raw=raw),namespace_paths=[],phase='L2',initializer_group='owned')
        events=[]
        finder=types.SimpleNamespace(check_row=lambda r:None,read_retained=lambda r:raw,
                 effects=EffectGate(lambda:'L2'),observe=lambda *args:events.append(args))
        return row,finder,events
    def test_retained_source_only(self):
        row,finder,events=self.fixture(); module=types.ModuleType('owned_source')
        RetainedLoader(finder,row).exec_module(module)
        self.assertEqual(module.owned_value,17); self.assertEqual(len(events),1)
    def test_swapped_source_before_exec(self):
        row,finder,_=self.fixture(); finder.read_retained=lambda r:b'owned_value = 19\n'
        module=types.ModuleType('owned_source')
        with self.assertRaises(Refusal): RetainedLoader(finder,row).exec_module(module)
        self.assertNotIn('owned_value',vars(module))
    def test_pyc_source_refused(self):
        row,finder,_=self.fixture(); row['file_ref']['path']='D:/fixture/input.pyc'
        with self.assertRaises(Refusal): RetainedLoader(finder,row).exec_module(types.ModuleType('owned_source'))
    def test_import_gate_phase_before_read(self):
        row,finder,_=self.fixture(); reads=[]
        def check(row): raise Refusal('wrong phase')
        finder.check_row=check; finder.read_retained=lambda r:reads.append(r)
        with self.assertRaises(Refusal): RetainedLoader(finder,row).exec_module(types.ModuleType('owned_source'))
        self.assertEqual(reads,[])
