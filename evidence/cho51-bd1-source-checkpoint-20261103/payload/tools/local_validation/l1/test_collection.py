import types
import unittest
from .protocol import Refusal
from .collection import validate_arguments,REQUIRED_OPTIONS,install_registration_gate,CollectionPlugin
from .observation import CollectionLedger
from .test_support import collection_fixture

def refuse(message): raise Refusal(message)

class CollectionTests(unittest.TestCase):
    def test_exact_arguments(self):
        policy=dict(ordered_arguments=list(REQUIRED_OPTIONS)+['-c','D:/owned/pytest.ini','--rootdir=D:/project','D:/mapping.py','D:/telemetry.py'],
                    config_ref={'path':'D:/owned/pytest.ini'},root='D:/project',candidate_paths=['D:/mapping.py','D:/telemetry.py'],
                    no_fixture_or_test_execution=True,autoload_disabled=True,ambient_addopts=[])
        self.assertEqual(validate_arguments(policy),policy['ordered_arguments'])
        policy['ordered_arguments']+=['-k','owned']
        with self.assertRaises(Refusal): validate_arguments(policy)
    def test_unknown_plugin_before_registration(self):
        called=[]; manager=types.SimpleNamespace(register=lambda *a:called.append(a),get_canonical_name=lambda p:'foreign')
        install_registration_gate(manager,{},refuse)
        with self.assertRaises(Refusal): manager.register(types.ModuleType('foreign'))
        self.assertEqual(called,[])
    def test_hookwrapper_before_registration(self):
        called=[]; module=types.ModuleType('owned')
        def hook(): pass
        hook.pytest_impl={'hookwrapper':True}; module.pytest_owned=hook
        manager=types.SimpleNamespace(register=lambda *a:called.append(a),get_canonical_name=lambda p:'owned')
        install_registration_gate(manager,{'owned':module},refuse)
        with self.assertRaises(Refusal): manager.register(module)
        self.assertEqual(called,[])
    def test_fixture_test_phase_pre_effect(self):
        static,sources,_,_=collection_fixture()
        plugin=CollectionPlugin(CollectionLedger(static,sources),lambda *a:None,refuse)
        with self.assertRaises(Refusal): plugin.pytest_fixture_setup(None,None)
        with self.assertRaises(Refusal): plugin.pytest_runtest_protocol(None,None)
        with self.assertRaises(Refusal): plugin.pytest_runtest_makereport(None,None)
        self.assertEqual((plugin.fixture_calls,plugin.protocol_calls,plugin.report_calls),(1,1,1))
    def test_pinned_wrapper_allowed(self):
        called=[];module=types.ModuleType('owned')
        def hook():pass
        hook.pytest_impl={'wrapper':True};module.pytest_owned=hook
        manager=types.SimpleNamespace(register=lambda *a:called.append(a),get_canonical_name=lambda p:'owned')
        row=dict(plugin='owned',symbol='pytest_owned',qualname=hook.__qualname__,file_ref={'path':hook.__code__.co_filename.replace('\\','/')},hookwrapper=False,wrapper=True)
        install_registration_gate(manager,{'owned':module},refuse,[row]);manager.register(module)
        self.assertEqual(len(called),1)
    def test_collection_skip_denied(self):
        static,sources,_,_=collection_fixture()
        plugin=CollectionPlugin(CollectionLedger(static,sources),lambda *a:None,refuse)
        with self.assertRaises(Refusal): plugin.pytest_collectreport(types.SimpleNamespace(failed=False,skipped=True))
