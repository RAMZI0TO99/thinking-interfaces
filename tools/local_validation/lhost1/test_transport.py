import hashlib
import unittest
import ctypes
import types
import sys
import copy
from unittest import mock
from . import transport,job_adapter,abi
from .runtime import Runtime
from ..l1.guards import LoaderFacade,EffectGate
from ..l1.observation import assess_abi,ABI_SCOPE
from .transport import ObservationReceiver,lifecycle_ok,new_state
from ..l1.protocol import Refusal,encode
from ..l1.test_support import collection_fixture,retained

class ReceiverTests(unittest.TestCase):
    def fixture(self):
        static,sources,rows,summary=collection_fixture();saved=[]
        class Writer:
            def write(self,name,raw):
                saved.append((name,raw));return dict(path='D:/fixture/'+name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        receiver=ObservationReceiver({'operation_id':'00000000-0000-4000-8000-000000000001'},Writer(),static,sources,lambda:True)
        return receiver,rows,summary,saved
    def test_parent_independent_collection_digest(self):
        receiver,rows,summary,saved=self.fixture();sequence=0
        for row in rows:receiver.accept(dict(kind='collection_item',payload=row,phase='L4'))
        receiver.accept(dict(kind='collection_end',payload=summary,phase='L4'))
        terminal=dict(status='provisional-complete',observer_shutdown=True,observations_digest=receiver.hash.hexdigest())
        receiver.accept(dict(kind='terminal',payload=terminal,phase='L5'));receiver.finish()
        self.assertTrue(saved);self.assertTrue(receiver.collection.finished)
    def test_parent_unexpected_denial(self):
        receiver,_,_,_=self.fixture()
        with self.assertRaises(Refusal):receiver.accept(dict(kind='denial',phase='L3',payload=dict(before_effect=True,expected_sentinel_id=None)))
    def test_no_success_by_exit_zero(self):
        receiver,_,_,_=self.fixture()
        with self.assertRaises(Refusal):receiver.finish()
        self.assertFalse(lifecycle_ok(new_state()))
    def test_parent_terminal_hash_drift(self):
        receiver,rows,summary,_=self.fixture()
        for row in rows:receiver.accept(dict(kind='collection_item',payload=row,phase='L4'))
        receiver.accept(dict(kind='collection_end',payload=summary,phase='L4'))
        receiver.accept(dict(kind='terminal',phase='L5',payload=dict(status='provisional-complete',observer_shutdown=True,observations_digest='0'*64)))
        with self.assertRaises(Refusal):receiver.finish()

class TransportCompositionTests(unittest.TestCase):
    def exercise(self,fault=None):
        c=ctypes;native=types.SimpleNamespace(handles=[],closed=[],attributes=[],deleted=0,process_calls=0,pipe_calls=0,set_calls=0)
        class Basic(c.Structure):_fields_=[('LimitFlags',c.c_uint32),('ActiveProcessLimit',c.c_uint32)]
        class Limit(c.Structure):_fields_=[('BasicLimitInformation',Basic),('ProcessMemoryLimit',c.c_size_t),('JobMemoryLimit',c.c_size_t)]
        class Start(c.Structure):_fields_=[('cb',c.c_uint32),('dwFlags',c.c_uint32),('hStdInput',c.c_void_p),('hStdOutput',c.c_void_p),('hStdError',c.c_void_p)]
        class StartEx(c.Structure):_fields_=[('StartupInfo',Start),('lpAttributeList',c.c_void_p)]
        class Info(c.Structure):_fields_=[('hProcess',c.c_void_p),('hThread',c.c_void_p),('dwProcessId',c.c_uint32),('dwThreadId',c.c_uint32)]
        class Security(c.Structure):_fields_=[('size',c.c_uint32),('descriptor',c.c_void_p),('inherit',c.c_int)]
        class ImmediateThread:
            def __init__(self,target,**kwargs):self.target=target;self.alive=False
            def start(self):self.target()
            def join(self,*args):pass
            def is_alive(self):return self.alive
        def key(value):return int(getattr(value,'value',value) or 0)
        def create_pipe(read,write,*args):
            native.pipe_calls+=1
            if fault=='stderr_pipe' and native.pipe_calls==3:return False
            values=[1000+len(native.handles),1001+len(native.handles)];native.handles.extend(values)
            c.cast(read,c.POINTER(c.c_void_p))[0]=values[0];c.cast(write,c.POINTER(c.c_void_p))[0]=values[1];return True
        def set_handle(*args):
            native.set_calls+=1;return not(fault=='stdout_inherit' and native.set_calls==1)
        def read_file(handle,buffer,size,count,*args):c.cast(count,c.POINTER(c.c_uint32))[0]=0;return True
        def close(handle):
            value=key(handle)
            if value in native.closed:raise AssertionError('double-close of owned handle')
            native.closed.append(value);return True
        def init_attributes(ptr,count,flags,size):
            self.assertEqual(count,2)
            if not ptr:c.cast(size,c.POINTER(c.c_size_t))[0]=128;c.set_last_error(122);return False
            return True
        def update(ptr,flags,attribute,value,size,*args):
            values=tuple(key(c.cast(value,c.POINTER(c.c_void_p))[i]) for i in range(size//c.sizeof(c.c_void_p)))
            native.attributes.append((attribute,size,values))
            return not(fault=='job_attribute' and attribute==0x2000D)
        def create_process(app,command,ps,ts,inherit,flags,environment,cwd,start,info):
            native.process_calls+=1;native.flags=flags;native.environment=c.wstring_at(environment,len('PATH=D:/owned\0SystemRoot=C:/Windows\0\0'))
            startup=c.cast(start,c.POINTER(StartEx)).contents
            native.stdout=startup.StartupInfo.hStdOutput;native.stderr=startup.StartupInfo.hStdError
            self.assertEqual(startup.StartupInfo.cb,c.sizeof(StartEx))
            self.assertEqual(startup.StartupInfo.dwFlags&0x100,0x100)
            if fault=='create_process':return False
            value=c.cast(info,c.POINTER(Info)).contents;value.hProcess=2001;value.hThread=2002;value.dwProcessId=1;return True
        def set_job(handle,kind,value,size):native.limits=c.string_at(value,size);return True
        def query_job(handle,kind,value,size,returned):c.memmove(value,native.limits,size);return True
        def in_job(process,job,present):c.cast(present,c.POINTER(c.c_int))[0]=1;return True
        native.create_pipe=create_pipe;native.set_handle=set_handle;native.read_file=read_file;native.close=close
        native.init_attributes=init_attributes;native.update_attribute=update;native.create_process=create_process
        native.create_job=lambda *args:3001;native.set_job=set_job;native.query_job=query_job;native.in_job=in_job
        native.delete_attributes=lambda *args:setattr(native,'deleted',native.deleted+1)
        native.resume=lambda *args:1;native.wait=lambda *args:0;native.terminate_job=lambda *args:True
        primitive=types.ModuleType('owned_primitive')
        primitive._FrameWinApi=lambda:native;primitive._ExtendedLimit=Limit;primitive._StartupInfo=Start;primitive._StartupInfoEx=StartEx
        primitive._ProcessInfo=Info;primitive._SecurityAttributes=Security;primitive.wintypes=types.SimpleNamespace(HANDLE=c.c_void_p,BOOL=c.c_int)
        primitive.SupervisionError=RuntimeError;primitive._error=lambda text:RuntimeError(text)
        for name,value in dict(PROC_THREAD_ATTRIBUTE_HANDLE_LIST=0x20002,CREATE_SUSPENDED=4,CREATE_NO_WINDOW=0x08000000,
            EXTENDED_STARTUPINFO_PRESENT=0x80000,ERROR_INSUFFICIENT_BUFFER=122,HANDLE_FLAG_INHERIT=1,
            JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE=0x2000,JOB_OBJECT_LIMIT_PROCESS_MEMORY=0x100,JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS=9,
            WAIT_FAILED=0xffffffff,WAIT_OBJECT_0=0,ERROR_TERMINATED=125,ERROR_BROKEN_PIPE=109,ERROR_NO_DATA=232).items():setattr(primitive,name,value)
        primitive._job_memory_peaks=lambda *args:(0,0);primitive._read_single_frame=lambda *args:None
        primitive._active_processes=lambda *args:0;primitive._wait_for_empty_job=lambda *args,**kwargs:None
        primitive._cancel_frame_reader=lambda api,thread:setattr(thread,'alive',False)
        state=new_state();state['process_creation_filetime']=1 # exact fixture generation; no OS query
        transport.install_transport(primitive,state,None,{'PATH':'D:/owned','SystemRoot':'C:/Windows'},lambda:True,job_adapter)
        api=primitive._FrameWinApi();job=api.create_job(None,None);read=c.c_void_p();write=c.c_void_p();error=None;created=False
        with mock.patch.object(transport.threading,'Thread',ImmediateThread):
            try:
                primitive._set_job_limits(api,job,4096*1024**2)
                if not api.create_pipe(c.byref(read),c.byref(write),None,0):raise RuntimeError('owned result pipe')
                writers=(c.c_void_p*1)(write.value+1 if fault=='writer_substitution' else write.value)
                self.assertTrue(api.update_attribute(c.c_void_p(1),0,0x20002,c.cast(writers,c.c_void_p),c.sizeof(writers),None,None))
                self.assertTrue(api.set_handle(write,1,1))
                start=StartEx();info=Info()
                launch_flags=4|0x08000000|0x80000|(2 if fault=='extra_flags' else 0)
                created=api.create_process('D:/python.exe','owned',None,None,True,launch_flags,None,'D:/owned',c.byref(start),c.byref(info))
                if not created:raise RuntimeError('owned creation refused')
                self.assertTrue(api.assign(job,info.hProcess));present=c.c_int();self.assertTrue(api.in_job(info.hProcess,job,c.byref(present)))
                self.assertEqual(api.resume(info.hThread),1)
            except (Refusal,RuntimeError) as failure:error=str(failure)
            finally:
                if write:api.close(write)
                api.close(job)
                if read:api.close(read)
                if created:api.close(info.hThread);api.wait(info.hProcess,2000);api.close(info.hProcess)
        return native,state,error
    def test_composed_creation_three_writers_and_unicode(self):
        native,state,error=self.exercise();self.assertIsNone(error)
        rows=[row for row in native.attributes if row[0]==0x20002]
        self.assertEqual([row[1] for row in rows],[3*ctypes.sizeof(ctypes.c_void_p)]*2)
        self.assertEqual(rows[0][2],rows[1][2]);self.assertEqual(rows[1][2][1:],(native.stdout,native.stderr))
        self.assertEqual(native.flags,4|0x08000000|0x80000|0x400)
        self.assertEqual(native.environment,'PATH=D:/owned\0SystemRoot=C:/Windows\0\0')
        self.assertTrue(state['atomic_job_assignment_verified']);self.assertTrue(state['stdio_threads_joined'])
        self.assertTrue(set(native.handles)<=set(native.closed));self.assertFalse(state['cleanup_errors'])
    def test_composed_process_failure_closes_owned_pipes(self):
        native,state,error=self.exercise('create_process');self.assertIsNotNone(error)
        self.assertTrue(set(native.handles)<=set(native.closed));self.assertTrue(state['stdio_threads_joined']);self.assertEqual(native.deleted,1)
    def test_composed_attribute_failure_prevents_creation(self):
        native,state,error=self.exercise('job_attribute');self.assertIsNotNone(error)
        self.assertEqual(native.process_calls,0);self.assertEqual(native.deleted,1);self.assertTrue(set(native.handles)<=set(native.closed))
    def test_composed_inherit_failure_closes_partial_pipes(self):
        native,state,error=self.exercise('stdout_inherit');self.assertIsNotNone(error)
        self.assertEqual(native.process_calls,0);self.assertTrue(set(native.handles)<=set(native.closed))
    def test_composed_second_pipe_failure_closes_first(self):
        native,state,error=self.exercise('stderr_pipe');self.assertIsNotNone(error)
        self.assertEqual(native.process_calls,0);self.assertTrue(set(native.handles)<=set(native.closed))
    def test_composed_report_writer_substitution_pre_effect(self):
        native,state,error=self.exercise('writer_substitution');self.assertIsNotNone(error)
        self.assertEqual(native.process_calls,0);self.assertTrue(set(native.handles)<=set(native.closed))
    def test_composed_extra_creation_flags_pre_effect(self):
        native,state,error=self.exercise('extra_flags');self.assertIsNotNone(error)
        self.assertEqual(native.process_calls,0);self.assertTrue(set(native.handles)<=set(native.closed))

class ABISafeQueryTests(unittest.TestCase):
    def fixture(self,result=7):
        module=types.ModuleType('owned_abi_query');called=[]
        module.version=lambda:called.append('version') or result
        query=dict(module=module.__name__,symbol='version',arguments=[],result=7,effect_budget='noncomputational',rationale='owned literal getter only')
        plan=dict(module=module.__name__,extension_file=retained('D:/fixture/owned.pyd'),machine=0x8664,python_tag='cp312',
             initializer_symbol='PyInit_owned',required_exports=['PyInit_owned'],forwarder_targets={},safe_queries=[query],expected_metadata={},compatibility_scope=ABI_SCOPE)
        return module,called,plan
    def observed(self):
        module,called,plan=self.fixture()
        with mock.patch.dict(sys.modules,{module.__name__:module}):
            scope,observed=abi.after_extension({},module,(plan,{'PyInit_owned':None}),lambda name:{},lambda *args:None)
        self.assertEqual(called,['version']);return plan,observed
    def test_safe_query_matches_production_observation(self):
        plan,observed=self.observed();self.assertEqual(assess_abi(plan,observed),ABI_SCOPE)
        self.assertEqual(observed['safe_queries'],plan['safe_queries'])
    def test_safe_query_wrong_getter_result(self):
        module,called,plan=self.fixture(8)
        with mock.patch.dict(sys.modules,{module.__name__:module}):
            with self.assertRaises(Refusal):abi.after_extension({},module,(plan,{'PyInit_owned':None}),lambda name:{},lambda *args:None)
        self.assertEqual(called,['version'])
    def test_safe_query_missing_observation(self):
        plan,observed=self.observed();observed['safe_queries']=[]
        with self.assertRaises(Refusal):assess_abi(plan,observed)
    def test_safe_query_extra_observation(self):
        plan,observed=self.observed();observed['safe_queries'].append(copy.deepcopy(observed['safe_queries'][0]))
        with self.assertRaises(Refusal):assess_abi(plan,observed)
    def test_safe_query_bool_is_not_integer_result(self):
        plan,observed=self.observed();plan['safe_queries'][0]['result']=1;observed['safe_queries'][0]['result']=True
        with self.assertRaises(Refusal):assess_abi(plan,observed)
    def test_safe_query_unknown_record_field(self):
        plan,observed=self.observed();observed['safe_queries'][0]['unreviewed']=True
        with self.assertRaises(Refusal):assess_abi(plan,observed)
    def test_safe_query_nested_boolean_is_not_integer(self):
        plan,observed=self.observed();plan['safe_queries'][0]['result']={'v':[1]};observed['safe_queries'][0]['result']={'v':[True]}
        with self.assertRaises(Refusal):assess_abi(plan,observed)

class NativeLoaderPreEffectTests(unittest.TestCase):
    def fixture(self):
        runtime=Runtime.__new__(Runtime);runtime.checkpoint=lambda:True;runtime.effects=EffectGate(lambda:'L2')
        row=dict(requester='owned_importer',requested_name='D:/fixture/owned.dll',mechanism='LoadLibraryExW',flags=0x1100,
            search_directories=['D:/fixture'],chosen_file=retained('D:/fixture/owned.dll'),allowed_system_role=None,phase='L2',delay_policy='observed-required')
        runtime.policies={'native_policy':{'rows':[row]}};runtime.bindings=dict(dll_directories=['D:/fixture'],phase=lambda:'L2',platform_images=[])
        runtime.requester=lambda:'owned_importer';verified=[];runtime.verify=lambda reference:verified.append(reference) or True
        called=[]
        class Original:
            def __call__(self,*args):called.append(args);return 9
        facade=LoaderFacade('LoadLibraryExW',Original(),runtime.permit_loader,runtime.effects.latch.refuse)
        return runtime,row,facade,called,verified
    def test_exact_retained_loader_before_effect(self):
        runtime,row,facade,called,verified=self.fixture()
        self.assertEqual(facade(row['requested_name'],None,0x1100),9)
        self.assertEqual(verified,[row['chosen_file']]);self.assertEqual(len(called),1)
    def test_wrong_loader_mechanism_pre_effect(self):
        runtime,row,facade,called,verified=self.fixture();row['mechanism']='ctypes.CDLL'
        with self.assertRaises(Refusal):facade(row['requested_name'],None,0x1100)
        self.assertEqual(called,[]);self.assertEqual(verified,[])
    def test_retained_path_substitution_pre_effect(self):
        runtime,row,facade,called,verified=self.fixture();row['chosen_file']=retained('D:/fixture/other.dll')
        with self.assertRaises(Refusal):facade(row['requested_name'],None,0x1100)
        self.assertEqual(called,[]);self.assertEqual(verified,[])
    def test_retained_identity_failure_pre_effect(self):
        runtime,row,facade,called,verified=self.fixture();runtime.verify=lambda reference:False
        with self.assertRaises(Refusal):facade(row['requested_name'],None,0x1100)
        self.assertEqual(called,[])
    def test_unknown_flags_pre_effect(self):
        runtime,row,facade,called,verified=self.fixture()
        with self.assertRaises(Refusal):facade(row['requested_name'],None,0x800)
        self.assertEqual(called,[])
    def test_platform_basename_resolution_refused(self):
        runtime,row,facade,called,verified=self.fixture();row['chosen_file']=None;row['allowed_system_role']='reviewed_windows';row['requested_name']='owned.dll'
        with self.assertRaises(Refusal):facade(row['requested_name'],None,0x1100)
        self.assertEqual(called,[])
    def test_exact_reviewed_platform_choice(self):
        runtime,row,facade,called,verified=self.fixture();row['chosen_file']=None;row['allowed_system_role']='reviewed_windows'
        runtime.bindings['platform_images']=[dict(path=row['requested_name'],role='reviewed_windows',phases=['L2'],rationale='exact fixture platform trust')]
        self.assertEqual(facade(row['requested_name'],None,0x1100),9);self.assertEqual(verified,[]);self.assertEqual(len(called),1)
    def test_loader_refusal_remains_sticky(self):
        runtime,row,facade,called,verified=self.fixture();row['mechanism']='extension'
        with self.assertRaises(Refusal):facade(row['requested_name'],None,0x1100)
        with self.assertRaises(Refusal):runtime.effects.latch.check()
        self.assertEqual(called,[])
    def test_loader_keyword_refusal_remains_sticky(self):
        runtime,row,facade,called,verified=self.fixture()
        with self.assertRaises(Refusal):facade(row['requested_name'],None,flags=0x1100)
        with self.assertRaises(Refusal):runtime.effects.latch.check()
        self.assertEqual(called,[])
