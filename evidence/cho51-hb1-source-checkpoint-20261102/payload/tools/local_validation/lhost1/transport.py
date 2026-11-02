"""Original-pipe multi-frame receiver and explicit stdio/environment adapter."""
import ctypes
import hashlib
import threading
import time
from datetime import datetime,timezone
from ..l1.protocol import need,encode,FrameReader
from ..l1.observation import CollectionLedger

def new_state():
    flags=('limits_set','limits_query_verified','job_created','created_suspended',
           'atomic_job_assignment_requested','atomic_job_assignment_verified','assigned','membership_verified',
           'resumed','job_empty_before_close','job_closed','root_exit_after_job_close','process_handle_closed',
           'thread_handle_closed','assignment_step_seen','owned_job_termination_called')
    state={k:False for k in flags}
    state.update(peak_samples=0,peak_process_commit_bytes=0,peak_job_commit_bytes=0,
                 cleanup_errors=[],peak_sampling_errors=[],report_eof=False)
    return state

def lifecycle_ok(state):
    return all(state.get(k) is True for k in ('limits_query_verified','atomic_job_assignment_verified',
        'membership_verified','job_empty_before_close','job_closed','root_exit_after_job_close',
        'process_handle_closed','thread_handle_closed','result_reader_closed','result_writer_closed',
        'report_eof','stdout_eof','stderr_eof','stdout_reader_closed','stderr_reader_closed',
        'stdout_writer_closed','stderr_writer_closed','stdio_threads_joined')) and not state['cleanup_errors'] and not state['peak_sampling_errors']

class ObservationReceiver:
    def __init__(self,operation,writer,static,sources,checkpoint):
        self.operation,self.writer,self.checkpoint=operation,writer,checkpoint
        self.collection=CollectionLedger(static,sources)
        self.pages=[];self.rows={};self.pending={};self.terminal=None;self.collection_summary=None
        self.bytes=0;self.hash=hashlib.sha256();self.phase='L1'
    def _flush(self,kind):
        rows=self.pending.pop(kind,[])
        if not rows:return
        index=sum(1 for p in self.pages if p['kind']==kind)
        body=dict(schema='cho51_l_observation_page_v1',operation=self.operation,kind=kind,page_index=index,rows=rows)
        raw=encode(body);self.bytes+=len(raw)
        need(self.bytes<=60*1024**2 and len(self.pages)<240,'whole parent page budget')
        descriptor=self.writer.write('observation_'+kind+'_'+str(index)+'.json',raw)
        self.pages.append(dict(kind=kind,page_index=index,row_count=len(rows),ref=descriptor))
    def accept(self,frame):
        need(self.checkpoint() is True,'parent receive checkpoint')
        kind,payload=frame['kind'],frame['payload'];self.phase=frame['phase']
        if kind=='collection_item':self.collection.append(payload)
        if kind=='collection_end':
            need(self.collection_summary is None,'duplicate collection summary')
            self.collection.finish(payload);self.collection_summary=payload
        if kind=='terminal':
            self.terminal=payload
        else:
            self.hash.update(encode(dict(kind=kind,payload=payload)))
        if kind=='denial':
            need(payload['before_effect'] is True and payload['expected_sentinel_id'] is not None,
                 'unexpected candidate/initialization denial')
        self.rows[kind]=self.rows.get(kind,0)+1
        need(self.rows[kind]<=25000,'observation row cap')
        pending=self.pending.setdefault(kind,[]);pending.append(payload)
        if len(pending)>=16 or len(encode(pending))>=512*1024:self._flush(kind)
    def finish(self):
        need(self.terminal is not None and self.terminal['status']=='provisional-complete'
             and self.terminal['observer_shutdown'] is True and self.collection.finished,
             'child terminal/collection/shutdown incomplete')
        need(self.terminal['observations_digest']==self.hash.hexdigest(),'observation stream digest')
        for kind in list(self.pending):self._flush(kind)

def install_transport(primitive,state,receiver,environment,checkpoint,job_adapter):
    """Extend the reviewed atomic Job adapter with three exact inherited pipes.

    Stdout/stderr are independent bounded readers; report frames are processed
    sequentially with no unbounded queue. Cancellation uses original threads.
    """
    job_adapter.install_job_adapter(primitive,state,None)
    old_api=primitive._FrameWinApi
    c=ctypes
    class Pipe:
        def __init__(self,api,name):
            self.api,self.name=api,name;self.read=c.c_void_p();self.write=c.c_void_p()
            self.data=bytearray();self.thread=None;self.eof=False;self.error=None
            state[name+'_reader_closed']=False;state[name+'_writer_closed']=False
        def open(self):
            security=primitive._SecurityAttributes(c.sizeof(primitive._SecurityAttributes),None,False)
            try:
                need(self.api.create_pipe(c.byref(self.read),c.byref(self.write),c.byref(security),0),'stdio pipe creation')
                need(self.api.set_handle(self.write,primitive.HANDLE_FLAG_INHERIT,primitive.HANDLE_FLAG_INHERIT),'stdio writer inheritance')
            except BaseException:
                self.finish(require_eof=False)
                raise
        def start(self):
            self.thread=threading.Thread(target=self.loop,name='L-'+self.name,daemon=True);self.thread.start()
        def loop(self):
            try:
                while True:
                    buffer=c.create_string_buffer(4096);count=c.c_uint32()
                    if not self.api.read_file(self.read,buffer,4096,c.byref(count),None):
                        need(c.get_last_error() in (primitive.ERROR_BROKEN_PIPE,primitive.ERROR_NO_DATA),'stdio read failure');break
                    if count.value==0:break
                    need(count.value<=4096,'stdio native read count')
                    self.data.extend(buffer.raw[:count.value]);need(len(self.data)<=1024**2,'stdio cap')
                self.eof=True;state[self.name+'_eof']=True
            except BaseException as error:
                self.error=str(error);state['cleanup_errors'].append(self.name+': '+str(error))
        def close_writer(self):
            if self.write:
                need(self.api.close(self.write),'stdio original writer close');self.write=c.c_void_p();state[self.name+'_writer_closed']=True
        def finish(self,require_eof=True):
            errors=[]
            try:self.close_writer()
            except BaseException as error:errors.append(str(error))
            if self.thread:
                self.thread.join(.2)
                if self.thread.is_alive():
                    try:primitive._cancel_frame_reader(self.api,self.thread)
                    except BaseException as error:errors.append(str(error))
                if self.thread.is_alive():errors.append('stdio thread unjoined')
            if self.read:
                if self.api.close(self.read):self.read=c.c_void_p();state[self.name+'_reader_closed']=True
                else:errors.append('stdio original reader close')
            if require_eof and (self.error is not None or not self.eof):errors.append('stdio EOF/reader failure')
            need(not errors,'; '.join(errors))
    class Api:
        def __init__(self):
            self.observed=old_api();self.base=self.observed.api;self.stdout=None;self.stderr=None
        def __getattr__(self,name):return getattr(self.observed,name)
        def create_pipe(self,*args):
            result=self.observed.create_pipe(*args)
            if result:
                try:
                    self.stdout=Pipe(self.base,'stdout');self.stdout.open()
                    self.stderr=Pipe(self.base,'stderr');self.stderr.open()
                    self.stdout.start();self.stderr.start()
                except BaseException:
                    self.finish_stdio(require_eof=False)
                    # The primitive already holds the original result handles
                    # populated by CreatePipe, including when this wrapper raises.
                    # Its finally closes those once; never close them twice here.
                    raise
            return result
        def update_attribute(self,attributes,flags,attribute,value,size,old,returned):
            if attribute==primitive.PROC_THREAD_ATTRIBUTE_HANDLE_LIST:
                need(size==c.sizeof(c.c_void_p),'original report writer list shape')
                report=c.cast(value,c.POINTER(c.c_void_p))[0]
                self.observed.bind_transport((report,self.stdout.write,self.stderr.write))
                self.handles=(c.c_void_p*3)(report,self.stdout.write.value,self.stderr.write.value)
                return self.observed.update_attribute(attributes,flags,attribute,c.cast(self.handles,c.c_void_p),c.sizeof(self.handles),old,returned)
            return self.observed.update_attribute(attributes,flags,attribute,value,size,old,returned)
        def create_process(self,app,command,ps,ts,inherit,flags,env,cwd,startup,info):
            need(env is None and inherit is True,'explicit inherited environment contract')
            values=[]
            for key in sorted(environment,key=str.upper):
                value=environment[key]
                need(type(key) is str and type(value) is str and key and '=' not in key and '\0' not in key+value,'environment entry')
                values.append(key+'='+value)
            self.environment=c.create_unicode_buffer('\0'.join(values)+'\0\0')
            start=c.cast(startup,c.POINTER(primitive._StartupInfo)).contents
            start.dwFlags|=0x100;start.hStdInput=None;start.hStdOutput=self.stdout.write;start.hStdError=self.stderr.write
            try:
                return self.observed.create_process(app,command,ps,ts,inherit,flags|0x400,c.cast(self.environment,c.c_void_p),cwd,startup,info)
            finally:
                self.stdout.close_writer();self.stderr.close_writer()
        def finish_stdio(self,require_eof=True):
            for pipe in (self.stdout,self.stderr):
                if pipe is None:continue
                try:pipe.finish(require_eof=require_eof)
                except BaseException as error:state['cleanup_errors'].append(str(error))
            pipes=[p for p in (self.stdout,self.stderr) if p is not None]
            state['stdio_threads_joined']=all(p.thread is None or not p.thread.is_alive() for p in pipes)
            for pipe in pipes:state[pipe.name+'_bytes']=bytes(pipe.data)
        def close(self,handle):
            try:return self.observed.close(handle)
            finally:
                if state.get('job_closed'):self.finish_stdio()
    def read_frames(api,pipe,maximum,frame_state):
        def read(size):
            buffer=c.create_string_buffer(min(size,65536));count=c.c_uint32()
            if not api.read_file(pipe,buffer,len(buffer),c.byref(count),None):
                need(c.get_last_error() in (primitive.ERROR_BROKEN_PIPE,primitive.ERROR_NO_DATA),'report original read failure');return b''
            return buffer.raw[:count.value]
        try:
            reader=FrameReader(read,receiver.operation['operation_id'],checkpoint)
            while True:
                frame=reader.next_frame()
                if frame is None:break
                receiver.accept(frame)
            receiver.finish();state['report_eof']=True;frame_state.frame=b'L1-authenticated-multiframe-complete'
        except BaseException as error:
            frame_state.error=primitive.SupervisionError(str(error))
        finally:
            frame_state.finished_utc=datetime.now(timezone.utc);frame_state.finished_mono=time.monotonic();frame_state.done.set()
    primitive._FrameWinApi=Api;primitive._read_single_frame=read_frames
