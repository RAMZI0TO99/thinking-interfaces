"""Fresh native-child confinement for one synthetic linear target route.

The audit hook confines all writes and sensitive reads. Exact canonical call
stacks and fixed budgets distinguish baseline reconstruction, one selected
restore, one support update, and the sole two-row query inference batch.
"""
from __future__ import annotations
import ctypes
import functools
import hashlib
import io
import json
import msvcrt
import os
import re
import shutil
import socket
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
SITE = ROOT / '.venv/Lib/site-packages'
CANDIDATE = ROOT / 'docs/phase2/cho51_linear_target_route_v1'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
PAUSES = tuple(Path('D:/Aenv/pro2/WORK')/f'resume-{day}-001'/'coordination/PRO2_REQUEST_PRO3_PAUSE.json'
    for day in ('20261007','20261012','20261013','20261015'))


def digest(path):
    path=Path(path);before=path.stat()
    key=lambda info:(info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)
    git_exception=(path==Path('C:/Users/aladdin-alyanai/AppData/Local/Programs/Git/cmd/git.exe')
        and before.st_nlink==2 and before.st_size==46480)
    if (path.resolve(strict=True)!=path or not stat.S_ISREG(before.st_mode)
            or before.st_nlink!=1 and not git_exception
            or not 0<=before.st_size<=512*1024**2):raise ValueError('direct bounded single-link pinned file required')
    for ancestor in (path,*path.parents):
        info=ancestor.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&1024:
            raise ValueError('linked/reparse pinned-file ancestor refused')
    with Path(path).open('rb') as stream:
        opened=os.fstat(stream.fileno());sha=hashlib.file_digest(stream,'sha256').hexdigest()
        finished=os.fstat(stream.fileno())
    if (key(before)!=key(path.stat()) or key(opened)!=key(finished)
            or key(before)[:4]!=key(opened)[:4]):raise ValueError('pinned file physical identity changed')
    if git_exception and sha!='da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f':
        raise ValueError('exact unchanged two-link Git exception differs')
    return sha


def read_json(path, maximum=8*1024**2):
    path=Path(path); before=path.stat()
    if (path.resolve(strict=True)!=path or path.is_symlink() or not stat.S_ISREG(before.st_mode)
            or before.st_nlink!=1 or not 0<before.st_size<=maximum):
        raise ValueError('direct bounded single-link JSON required')
    with path.open('rb') as stream:
        opened=os.fstat(stream.fileno()); raw=stream.read(maximum+1); finished=os.fstat(stream.fileno())
    key=lambda info:(info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)
    if (key(before)!=key(path.stat()) or key(opened)!=key(finished)
            or key(before)[:4]!=key(opened)[:4] or len(raw)!=before.st_size):
        raise ValueError('JSON physical identity changed')
    def unique(rows):
        d={}
        for k,v in rows:
            if k in d: raise ValueError('duplicate JSON key')
            d[k]=v
        return d
    return json.loads(raw,object_pairs_hook=unique,
        parse_constant=lambda value:(_ for _ in ()).throw(ValueError('nonfinite JSON')))


def write_json(path,value):
    raw=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('utf-8')
    with Path(path).open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return hashlib.sha256(raw).hexdigest()


def path_of(value):
    value=os.fsdecode(value)
    return Path(value[4:] if value.startswith('\\\\?\\') else value).resolve()


def stack_has(name,path):
    frame=sys._getframe(1)
    while frame:
        if frame.f_code.co_name==name and path_of(frame.f_code.co_filename)==path: return True
        frame=frame.f_back
    return False


def pause_check():
    if any(path.exists() for path in PAUSES): raise RuntimeError('genuine peer pause requested')


class Runtime:
    def __init__(self,pins_path,pins_sha256,output):
        if (pins_path!=RUN/'pins.json' or re.fullmatch('[a-f0-9]{64}',pins_sha256) is None
                or digest(pins_path)!=pins_sha256): raise ValueError('external exact fresh pins required')
        self.pins_path,self.pins_sha256,self.output=pins_path,pins_sha256,output
        self.pins=read_json(pins_path); p=self.pins
        expected={'schema':'cho51_linear_target_route_pins_v3','canonical_source_sha256':CANONICAL,
            'canonical_files':432,'predecessor_files':2230,'seconds':600,'process_mib':4096,'job_mib':5120,
            'startup_ram_gib':10,'active_ram_gib':4,'disk_gib':20,'threads':1,'gpu_hidden':True,
            'source_training_replayed':False,'current_source_updates':0,'current_support_updates':1,
            'current_gradient_updates':1,'historical_gradient_updates':5253,'operational_version':3,
            'full_model_constructions':1,'parameterless_clone_reinitializations':4,'empty_mask_containers':2,
            'scientific_admission':False,'original_case_attempts_remaining':0}
        if (any(type(p.get(k)) is not type(v) or p[k]!=v for k,v in expected.items())
                or len(p.get('runtime',{}))!=5 or not 10<=p.get('expected_tests',0)<=100):
            raise ValueError('exact one-update synthetic target scope required')
        if output!=RUN/'validation_001' or output.resolve()!=output: raise ValueError('direct unused output required')
        output.mkdir(exist_ok=False)
        self.contract=read_json(RUN/'origin-contract.json')
        if self.contract['schema']!='cho51_linear_target_route_origin_v3': raise ValueError('target origin schema differs')
        self.origin_files={Path(k):v for k,v in self.contract['files'].items()}
        self.origin_roles={Path(k):v for k,v in self.contract['roles'].items()}
        sys.path.insert(0,str(RUN)); import origin
        previous,self.fixture,inputs=origin.original_inventory()
        self.input_pins={self.fixture/k:v['sha256'] for k,v in inputs.items()}
        self.input_sizes={self.fixture/k:v['size_bytes'] for k,v in inputs.items()}
        self.target_paths=frozenset(self.fixture/name for name in (
            'data/processed/cho2017/profile_a/subject_02.npz',
            'data/processed/cho2017/profile_b_60hz_v1/subject_02.npz',
            'data/processed/cho2017/profile_b_60hz_v1/subject_02.manifest.json',
            'data/raw/moabb/cho2017/subject_02.mat'))
        self.baseline=Path(next(iter(p['baseline'])))
        self.selected=Path(next(iter(p['selected_weights'])))
        self.verify_pins()
        directories={'TEMP':'temp','TMP':'temp','TMPDIR':'temp','MPLCONFIGDIR':'mpl','HF_HOME':'hf',
            '_MNE_FAKE_HOME_DIR':'mne-home','HF_HUB_CACHE':'hf/hub','HUGGINGFACE_HUB_CACHE':'hf/hub',
            'TRANSFORMERS_CACHE':'hf/transformers','TORCH_HOME':'torch','NUMBA_CACHE_DIR':'numba',
            'JOBLIB_TEMP_FOLDER':'joblib','XDG_CACHE_HOME':'cache'}
        for folder in sorted(set(directories.values()),key=lambda v:(v.count('/'),v)): (output/folder).mkdir()
        for name,folder in directories.items(): os.environ[name]=str(output/folder)
        for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
            os.environ[name]='1'
        os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
            PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
        sys.dont_write_bytecode=True; sys.path[:0]=[str(ROOT),str(SITE)]
        from tools.migration.common import source_check
        if source_check(ROOT)!=CANONICAL: raise ValueError('canonical432 sources changed')
        self.git_command=shutil.which('git')
        self.git_path=Path(self.git_command).resolve() if self.git_command else None
        if self.git_path is None or str(self.git_path) not in p['runtime']: raise ValueError('pinned Git required')
        self.connection=SITE/'urllib3/util/connection.py'
        self.mne=SITE/'mne/data/fsaverage/fsaverage-fiducials.fif'
        self.denied=[]; self.git_queries=self.hostname_queries=self.existing_mkdir_refusals=0
        self.active=False; self.numerical_calls={}; self.constructor_dummy_forward_calls=0
        self.model_constructions=0
        self.clone_reinitializations={}
        self.clone_reinitialization_details=[]
        self.empty_mask_containers={}
        self.classifier_forward_calls=self.backbone_forward_calls=0
        self.sensitive_reads={}; self.current_restore_count=0
        self.numpy_loads={}
        self.api=ctypes.WinDLL('kernel32',use_last_error=True)
        self.api.GetFinalPathNameByHandleW.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_ulong,ctypes.c_ulong]
        self.api.GetFinalPathNameByHandleW.restype=ctypes.c_ulong
        sys.addaudithook(self.audit); pause_check(); self.started=time.monotonic()

    def verify_pins(self):
        pause_check(); p=self.pins
        if digest(self.pins_path)!=self.pins_sha256: raise ValueError('fresh pins changed')
        for name,sha in p['files'].items():
            if digest(ROOT/name)!=sha: raise ValueError('source/context pin changed: '+name)
        for group in ('runtime','runtime_modules','supporting_runtime_sources'):
            for name,sha in p.get(group,{}).items():
                if digest(name)!=sha: raise ValueError('fresh runtime pin changed: '+name)
        expected_clone_sources={
            str(SITE/'einops/layers/__init__.py'):'8e28f0118d3b62bdeb071f0de73c19fb9a9f6e5f8a5f605c4432bc3491436960',
            str(SITE/'einops/layers/torch.py'):'055f8fce3a228c653d44679ad47085b88331e3271c89ccfbebb3348c90c81fa5',
            str(SITE/'torch/nn/modules/container.py'):'d8c2b56bfa2204e8c2dc2466549a7b2299a14324c03a1d563e2b32072ced9a0b',
            str(Path(sys.base_prefix)/'Lib/copy.py'):'cbd25547933176fcf6bb05c2adc9f4796d15ac20b9b82dcf890daea7203daeab'}
        if p.get('supporting_runtime_sources')!=expected_clone_sources:
            raise ValueError('exact four reviewed clone/container implementation sources required')
        if (digest(RUN/'runtime-transition.json')!=p['runtime_transition_sha256']
                or read_json(RUN/'runtime-transition.json')!=p['runtime_transition']
                or len(p.get('runtime_modules',{}))!=18):
            raise ValueError('exact separately observed runtime transition changed')
        if digest(RUN/'origin-contract.json')!=p['origin_contract_file_sha256']: raise ValueError('origin changed')
        review=read_json(RUN/'source-review.json')
        if (digest(RUN/'source-review.json')!=p['source_review_sha256'] or review['source_only'] is not True
                or review['remaining_actionable_findings']!=[] or review['files']!=p['reviewed_files']):
            raise ValueError('settled source review changed')

    def refuse(self,event,detail=None):
        self.denied.append({'event':event,'detail':repr(detail)[:500]})
        raise PermissionError('target route denied: '+event)

    def fd_path(self,descriptor):
        if type(descriptor) is not int:return None
        try:
            buffer=ctypes.create_unicode_buffer(32768)
            n=self.api.GetFinalPathNameByHandleW(msvcrt.get_osfhandle(descriptor),buffer,len(buffer),0)
            return path_of(buffer.value) if 0<n<len(buffer) else None
        except OSError:return None

    def writable(self,path):return path.is_relative_to(self.output)

    def audit(self,event,values):
        if event=='socket.gethostname':self.hostname_queries+=1
        elif event.startswith('socket.'):
            if (event=='socket.__new__' and values[1:]==(socket.AF_INET6,socket.SOCK_STREAM,0)
                    and stack_has('_has_ipv6',self.connection)):
                self.denied.append({'event':event,'classification':'blocked_optional_ipv6_import_probe',
                    'source_file':str(self.connection),'source_sha256':self.pins['files'][self.connection.relative_to(ROOT).as_posix()]})
                raise PermissionError('optional IPv6 import socket creation blocked')
            self.refuse(event,values)
        elif event=='subprocess.Popen':
            executable,arguments,cwd,environment=values
            forms=[[self.git_command,'--no-optional-locks',*tail] for tail in (
                ['rev-parse','--verify','HEAD'],['status','--porcelain','--untracked-files=all'])]
            if (any(arguments==form or arguments==subprocess.list2cmdline(form) for form in forms)
                    and (executable is None and os.name=='nt' or isinstance(executable,(str,bytes,os.PathLike)) and path_of(executable)==self.git_path)
                    and cwd is not None and path_of(cwd) in {ROOT,self.fixture}
                    and environment is None and stack_has('capture_source',ROOT/'core/provenance.py')):
                self.git_queries+=1
            else:self.refuse(event,values)
        elif event in {'os.system','os.startfile','os.posix_spawn','os.fork','os.forkpty','pty.spawn'} or event.startswith(('os.exec','os.spawn')):
            self.refuse(event,values)
        elif event=='open':
            mode=values[1] if isinstance(values[1],str) else ''; flags=values[2] if isinstance(values[2],int) else 0
            writing=any(c in mode for c in 'wax+') or bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            path=path_of(values[0]) if isinstance(values[0],(str,bytes,os.PathLike)) else self.fd_path(values[0])
            if path is None:
                if writing:self.refuse('unbound_descriptor_write',values)
                return
            if writing:
                if not self.writable(path):self.refuse('outside_owned_write',path)
                return
            parts=tuple(part.lower() for part in path.parts)
            sensitive=(any(parts[i:i+2] in {('data','raw'),('data','processed'),('data','interim')} for i in range(len(parts)-1))
                or 'weights' in parts or 'checkpoints' in parts or path.suffix.lower() in
                {'.npz','.npy','.mat','.edf','.gdf','.fif','.set','.pt','.pth','.ckpt','.safetensors'})
            if not sensitive:return
            if path==self.mne and path.stat().st_size==260:return
            if path.suffix.lower()=='.pth' and path.is_relative_to(SITE):return
            metadata_hash=(path in self.origin_files and self.origin_roles[path]=='metadata'
                and (stack_has('asset',RUN/'origin.py') or stack_has('verify_pins',RUN/'runtime.py')))
            origin_hash=(path in self.origin_files or path in self.input_pins) and stack_has('asset',RUN/'origin.py')
            baseline=(path==self.baseline and self.active and stack_has('restore_adapter',RUN/'parent.py')
                and any(stack_has(name,ROOT/'evaluation/phase2_cho_source_restore.py') for name in (
                    '_new_model','prepare_cho_source_restore','_check_labram_baseline')))
            selected=(path==self.selected and self.active and stack_has('restore_adapter',RUN/'parent.py'))
            target=(path in self.target_paths and self.active
                and stack_has('run_target_route',CANDIDATE/'target_route.py')
                and stack_has('load_cho_profile_b_episode',ROOT/'evaluation/phase2_profile_binding.py'))
            if metadata_hash or origin_hash or baseline or selected or target:
                purpose=('metadata_hash' if metadata_hash else 'origin_stream_hash' if origin_hash else
                    'baseline_restore' if baseline else 'selected_restore' if selected else 'target_episode_loader')
                row=self.sensitive_reads.setdefault(str(path),{});row[purpose]=row.get(purpose,0)+1
                return
            self.refuse('unbound_signal_or_weight_read',path)
        elif event in {'os.mkdir','os.remove','os.rmdir','os.rename','os.replace','os.link','os.symlink','os.chmod','os.utime','os.truncate'}:
            count=2 if event in {'os.rename','os.replace','os.link','os.symlink'} else 1
            for value in values[:count]:
                if not isinstance(value,(str,bytes,os.PathLike)):self.refuse('unbound_mutation',values)
                path=path_of(value)
                if event=='os.mkdir' and not self.writable(path) and path.is_dir():
                    self.existing_mkdir_refusals+=1
                    raise FileExistsError(17,'existing outside directory creation refused',os.fsdecode(value))
                if not self.writable(path):self.refuse('outside_owned_mutation',path)
        elif event=='os.chdir' and not self.writable(path_of(values[0])):self.refuse(event,values)

    def numerical_allowed(self,name,module=None):
        if not self.active or not stack_has('run_target_route',CANDIDATE/'target_route.py'):
            self.refuse('numerics_outside_route',name)
        approved={'model_module_init','module_load_state_dict','safetensors_load','optimizer_init',
                  'sgd_step','tensor_backward','autograd_backward'}
        if name not in approved:self.refuse('unbound_numerical_operation',name)
        if name=='model_module_init' and not stack_has('_new_model',ROOT/'evaluation/phase2_cho_source_restore.py'):
            import torch
            if (type(module) is not torch.nn.CrossEntropyLoss
                    or not stack_has('adapt_labram_tuning_support',ROOT/'adaptation/labram_tuning.py')):
                self.refuse('unbound_model_constructor',name)
        if name in {'optimizer_init','sgd_step','tensor_backward','autograd_backward'} and not stack_has(
                'adapt_labram_tuning_support',ROOT/'adaptation/labram_tuning.py'):
            self.refuse('source_or_unbound_training',name)
        pause_check(); self.numerical_calls[name]=self.numerical_calls.get(name,0)+1
        limits={'module_load_state_dict':2,'safetensors_load':2,'optimizer_init':1,'sgd_step':1,'tensor_backward':1,'autograd_backward':1}
        if name in limits and self.numerical_calls[name]>limits[name]:self.refuse('numerical_budget_exceeded',name)

    def install_torch_guards(self):
        import torch
        torch.set_num_threads(1);torch.set_num_interop_threads(1)
        def forbidden(*a,**k):self.refuse('pickle_serialization_remote_or_unbound_numerics',None)
        torch.load=torch.serialization.load=torch.jit.load=torch.hub.load=forbidden
        torch.save=torch.serialization.save=forbidden;torch.autograd.grad=forbidden
        original_init=torch.nn.Module.__init__
        from einops.layers.torch import Rearrange
        einops_mixin=SITE/'einops/layers/__init__.py'
        copy_source=Path(sys.base_prefix)/'Lib/copy.py'
        patterns=frozenset({'Batch chs npat spatch -> Batch () (chs npat) spatch',
                           'Batch C NA T -> Batch NA (T C)'})
        container_source=SITE/'torch/nn/modules/container.py'
        def empty_mask_container(module):
            if (not self.active or not stack_has('run_target_route',CANDIDATE/'target_route.py')
                    or type(module) is not torch.nn.ModuleList or module.__dict__!={}):
                self.refuse('empty_container_outside_exact_target_mask',None)
            init_frame=getitem_frame=depth_frame=phase_frame=None;phase=None
            frame=sys._getframe(1)
            while frame:
                name=frame.f_code.co_name;path=path_of(frame.f_code.co_filename)
                if path==container_source:
                    if name=='__init__' and frame.f_locals.get('self') is module:init_frame=frame
                    elif name=='__getitem__':getitem_frame=frame
                if path==ROOT/'encoder/labram.py' and name=='configure_trainable_depth':depth_frame=frame
                if path==ROOT/'adaptation/labram_manifest.py' and name=='__init__':
                    runner_type=getattr(sys.modules.get('adaptation.labram_manifest'),'LaBraMTuningManifestRunner',None)
                    if runner_type is not None and type(frame.f_locals.get('self')) is runner_type:
                        if phase is not None:self.refuse('nested_empty_container_scope',None)
                        phase,phase_frame='runner_owned_source',frame
                if path==ROOT/'adaptation/labram_tuning.py' and name=='adapt_labram_tuning_support':
                    if phase is not None:self.refuse('nested_empty_container_scope',None)
                    phase,phase_frame='support_adapted_model',frame
                frame=frame.f_back
            if None in (init_frame,getitem_frame,depth_frame,phase_frame):
                self.refuse('unbound_empty_mask_container',None)
            values=init_frame.f_locals.get('modules');idx=getitem_frame.f_locals.get('idx')
            blocks=getitem_frame.f_locals.get('self');local=depth_frame.f_locals;model=local.get('model')
            from encoder.labram import LaBraMClassifier
            from braindecode.models.labram import _WindowsAttentionBlock
            from evaluation.labram_parity import state_digest
            if (type(values) is not list or values!=[] or type(idx) is not slice
                    or (idx.start,idx.stop,idx.step)!=(12,None,None) or type(blocks) is not torch.nn.ModuleList
                    or len(blocks)!=12 or tuple(blocks._modules)!=tuple(str(i) for i in range(12))
                    or any(type(block) is not _WindowsAttentionBlock for block in blocks)
                    or local.get('blocks') is not blocks or type(local.get('depth')) is not int or local['depth']!=0
                    or type(local.get('selected')) is not int or local['selected']!=0
                    or local.get('include_non_blocks') is not False or type(model) is not LaBraMClassifier
                    or model.backbone.blocks is not blocks or state_digest(model)!=
                       '8de802bc0577864edcfc857fa93cf24db527b09ecf0eded0b3e980a82a7b4c01'
                    or not stack_has('configure_labram_tuning',ROOT/'adaptation/labram_tuning.py')):
                self.refuse('empty_mask_container_source_or_slice',None)
            expected_model=phase_frame.f_locals.get('owned' if phase=='runner_owned_source' else 'model')
            if expected_model is not model or phase in self.empty_mask_containers:
                self.refuse('empty_mask_container_scope_budget',None)
            pause_check();original_init(module)
            if (module._parameters!={} or module._buffers!={} or module._modules!={}
                    or tuple(module.parameters())!=() or tuple(module.buffers())!=() or len(module)!=0):
                self.refuse('empty_mask_container_acquired_state',None)
            self.empty_mask_containers[phase]=1
        def clone_reinitialization(module):
            if not self.active or not stack_has('run_target_route',CANDIDATE/'target_route.py'):
                self.refuse('parameterless_clone_outside_route',None)
            init_frame=setstate_frame=reconstruct_frame=phase_frame=None
            phase=None;frames=[];frame=sys._getframe(1)
            while frame:
                frames.append(frame)
                name=frame.f_code.co_name;path=path_of(frame.f_code.co_filename)
                if path==einops_mixin and frame.f_locals.get('self') is module:
                    if name=='__init__':init_frame=frame
                    elif name=='__setstate__':setstate_frame=frame
                if path==copy_source and name=='_reconstruct' and frame.f_locals.get('y') is module:
                    reconstruct_frame=frame
                if path==ROOT/'adaptation/labram_manifest.py' and name=='__init__':
                    runner_module=sys.modules.get('adaptation.labram_manifest')
                    runner_type=getattr(runner_module,'LaBraMTuningManifestRunner',None)
                    if runner_type is not None and type(frame.f_locals.get('self')) is runner_type:
                        if phase is not None:self.refuse('nested_clone_scopes',None)
                        phase,phase_frame='runner_owned_source',frame
                if path==ROOT/'adaptation/labram_tuning.py' and name=='adapt_labram_tuning_support':
                    if phase is not None:self.refuse('nested_clone_scopes',None)
                    phase,phase_frame='support_adapted_model',frame
                frame=frame.f_back
            if (type(module) is not Rearrange or init_frame is None or setstate_frame is None
                    or reconstruct_frame is None or phase_frame is None or module.__dict__!={}):
                self.refuse('unbound_parameterless_reinitialization',None)
            state=setstate_frame.f_locals.get('state')
            pattern=init_frame.f_locals.get('pattern');axes=init_frame.f_locals.get('axes_lengths')
            old=reconstruct_frame.f_locals.get('x')
            source=phase_frame.f_locals.get('source_template' if phase=='runner_owned_source' else 'source_model')
            from encoder.labram import LaBraMClassifier
            from evaluation.labram_parity import state_digest
            if (pattern not in patterns or type(axes) is not dict or axes!={}
                    or type(state) is not dict or state!={'pattern':pattern,'axes_lengths':{}}
                    or reconstruct_frame.f_locals.get('state')!=state
                    or reconstruct_frame.f_locals.get('deep') is not True or type(old) is not Rearrange
                    or old.pattern!=pattern or old.axes_lengths!={} or old._axes_lengths!=()
                    or old._parameters!={} or old._buffers!={} or old._modules!={}
                    or tuple(old.parameters())!=() or tuple(old.buffers())!=() or old.training is not False
                    or type(source) is not LaBraMClassifier or state_digest(source)!=
                       '8de802bc0577864edcfc857fa93cf24db527b09ecf0eded0b3e980a82a7b4c01'
                    or not any(old is child for child in source.modules())
                    or not any(f.f_code.co_name=='deepcopy' and path_of(f.f_code.co_filename)==copy_source
                        and f.f_locals.get('x') is source for f in frames)):
                self.refuse('parameterless_clone_pattern_state_or_source',None)
            key=phase+'|'+pattern
            if key in self.clone_reinitializations:self.refuse('parameterless_clone_reinitialization_budget',key)
            pause_check()
            original_init(module)
            if (module._parameters!={} or module._buffers!={} or module._modules!={}
                    or tuple(module.parameters())!=() or tuple(module.buffers())!=()):
                self.refuse('parameterless_clone_acquired_tensor_state',None)
            self.clone_reinitializations[key]=1
            self.clone_reinitialization_details.append({'scope':phase,'class':'einops.layers.torch.Rearrange',
                'pattern':pattern,'axes_lengths':{},'parameters':0,'buffers':0,'child_modules':0,
                'original_layer_in_exact_source':True,'source_state_sha256':
                '8de802bc0577864edcfc857fa93cf24db527b09ecf0eded0b3e980a82a7b4c01'})
        @functools.wraps(original_init)
        def module_init(module,*a,**k):
            cloning=(type(module) is Rearrange and stack_has('__setstate__',einops_mixin))
            if cloning:
                if a or k:self.refuse('parameterless_clone_init_arguments',None)
                return clone_reinitialization(module)
            if (type(module) is torch.nn.ModuleList and stack_has('__getitem__',container_source)
                    and not stack_has('_new_model',ROOT/'evaluation/phase2_cho_source_restore.py')):
                if a or k:self.refuse('empty_mask_container_init_arguments',None)
                return empty_mask_container(module)
            self.numerical_allowed('model_module_init',module)
            if type(module).__name__=='Labram':
                self.model_constructions+=1
                if self.model_constructions>1:self.refuse('fresh_full_model_constructor_budget',None)
            return original_init(module,*a,**k)
        torch.nn.Module.__init__=module_init
        original_state=torch.nn.Module.load_state_dict
        def strict_load(model,state,*a,**k):
            strict=a[0] if a else k.get('strict',True);assign=a[1] if len(a)>1 else k.get('assign',False)
            if strict is not True or assign is not False or len(a)>2 or not stack_has('restore_adapter',RUN/'parent.py'):
                self.refuse('unbound_nonstrict_state_load',None)
            self.numerical_allowed('module_load_state_dict');return original_state(model,state,*a,**k)
        torch.nn.Module.load_state_dict=strict_load
        original_call=torch.nn.Module._call_impl
        def model_call(module,*a,**k):
            if self.active and stack_has('run_target_route',CANDIDATE/'target_route.py'):
                if stack_has('_new_model',ROOT/'evaluation/phase2_cho_source_restore.py'):
                    frame=sys._getframe(1);constructor=dummy=None
                    while frame:
                        if frame.f_code.co_name=='__init__' and path_of(frame.f_code.co_filename)==SITE/'braindecode/models/labram.py':
                            constructor,dummy=frame.f_locals.get('self'),frame.f_locals.get('dummy');break
                        frame=frame.f_back
                    if (constructor is None or not hasattr(constructor,'patch_embed')
                            or not any(module is member for member in constructor.patch_embed.modules())
                            or torch.is_grad_enabled() or not isinstance(dummy,torch.Tensor)
                            or tuple(dummy.shape)!=(1,int(constructor.n_chans),3000)
                            or dummy.device.type!='cpu' or dummy.dtype!=torch.float32 or dummy.requires_grad
                            or torch.count_nonzero(dummy).item()!=0):self.refuse('unbound_constructor_forward',type(module).__name__)
                    if module is constructor.patch_embed:self.constructor_dummy_forward_calls+=1
                    return original_call(module,*a,**k)
                support=stack_has('adapt_labram_tuning_support',ROOT/'adaptation/labram_tuning.py')
                query=stack_has('_predict',ROOT/'adaptation/labram_manifest.py')
                if support or query:
                    pause_check()
                    if type(module).__name__=='LaBraMClassifier':
                        expected=(10,64,800) if support else (2,64,800)
                        if (not a or not isinstance(a[0],torch.Tensor) or tuple(a[0].shape)!=expected
                                or any(part.training for part in module.modules())
                                or (not support and (torch.is_grad_enabled() or not torch.is_inference_mode_enabled()))):
                            self.refuse('target_classifier_shape_or_mode',None)
                        self.classifier_forward_calls+=1
                        if self.classifier_forward_calls>2:self.refuse('target_classifier_budget',None)
                    if type(module).__name__=='Labram':self.backbone_forward_calls+=1
                    return original_call(module,*a,**k)
            self.refuse('unbound_model_forward',type(module).__name__)
        torch.nn.Module._call_impl=model_call
        original_optimizer=torch.optim.Optimizer.__init__
        @functools.wraps(original_optimizer)
        def sgd_only(optimizer,parameters,defaults):
            self.numerical_allowed('optimizer_init')
            if type(optimizer) is not torch.optim.SGD or defaults.get('momentum',0)!=0 or defaults.get('lr')!=0.001:
                self.refuse('optimizer_policy',None)
            return original_optimizer(optimizer,parameters,defaults)
        torch.optim.Optimizer.__init__=sgd_only
        def guarded(name,original):
            @functools.wraps(original)
            def call(*a,**k):self.numerical_allowed(name);return original(*a,**k)
            return call
        torch.optim.SGD.step=guarded('sgd_step',torch.optim.SGD.step)
        torch.Tensor.backward=guarded('tensor_backward',torch.Tensor.backward)
        torch.autograd.backward=guarded('autograd_backward',torch.autograd.backward)
        import safetensors
        import safetensors.torch
        original_load=safetensors.torch.load;original_deserialize=safetensors.torch.deserialize
        def valid(raw):
            if type(raw) is not bytes:return False
            sha=hashlib.sha256(raw).hexdigest()
            return ((len(raw)==23299672 and sha=='53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8'
                     and stack_has('_new_model',ROOT/'evaluation/phase2_cho_source_restore.py'))
                or (len(raw)==23294624 and sha=='3033608533114fc1d484aa37b2c8ccf492ada90b28bef9e0ef617aa467ec8048'
                    and stack_has('restore_adapter',RUN/'parent.py')))
        def load_checked(raw):
            self.numerical_allowed('safetensors_load')
            if not valid(raw):self.refuse('unbound_safe_tensor_decode',None)
            return original_load(raw)
        def deserialize_checked(raw):
            if not stack_has('load_checked',RUN/'runtime.py') or not valid(raw):self.refuse('unbound_low_level_decode',None)
            return original_deserialize(raw)
        for name in ('serialize','serialize_file','deserialize','safe_open'):setattr(safetensors,name,forbidden)
        for name in ('save','save_file','save_model','load_file','load_model','safe_open','serialize','serialize_file'):
            setattr(safetensors.torch,name,forbidden)
        safetensors.torch.load=load_checked;safetensors.torch.deserialize=deserialize_checked
        import numpy as np
        original_numpy_load=np.load
        @functools.wraps(original_numpy_load)
        def numpy_load(path,*a,**k):
            actual=path_of(path) if isinstance(path,(str,bytes,os.PathLike)) else None
            canonical_binding=stack_has('load_cho_profile_b_episode',ROOT/'evaluation/phase2_profile_binding.py')
            if type(path) is io.BytesIO:
                frame=sys._getframe(1);bound=None
                while frame:
                    if frame.f_code.co_name=='_read_artifact' and path_of(frame.f_code.co_filename)==ROOT/'evaluation/phase2_profile_binding.py':
                        bound=frame.f_locals;break
                    frame=frame.f_back
                if bound is not None and bound.get('source') is path and isinstance(bound.get('path'),Path):
                    actual=bound['path']
                    buffer=path.getbuffer()
                    try:
                        if (actual not in self.input_pins or actual not in self.target_paths
                                or actual.suffix!='.npz' or path.tell()!=0
                                or bound.get('expected_sha256')!=self.input_pins[actual]
                                or len(buffer)!=self.input_sizes[actual] or len(buffer)>16*1024**2
                                or hashlib.sha256(buffer).hexdigest()!=self.input_pins[actual]):
                            self.refuse('unbound_numpy_artifact_buffer',actual)
                    finally:buffer.release()
                else:self.refuse('numpy_buffer_outside_canonical_reader',None)
            elif not stack_has('read_catalog',ROOT/'scripts/audit_phase2_protocol.py'):
                self.refuse('numpy_path_outside_canonical_catalogue',actual)
            if (not self.active or not stack_has('run_target_route',CANDIDATE/'target_route.py')
                    or not canonical_binding or actual not in self.target_paths or actual.suffix!='.npz'
                    or a or k.get('allow_pickle') is not False or k.get('mmap_mode') is not None):
                self.refuse('unbound_numpy_signal_decode',actual)
            row=self.numpy_loads.setdefault(str(actual),0)+1;self.numpy_loads[str(actual)]=row
            limit=4 if actual.parent.name=='profile_a' else 2
            if row>limit:self.refuse('target_numpy_decode_budget',actual)
            pause_check();return original_numpy_load(path,*a,**k)
        np.load=numpy_load
        for name in ('save','savez','savez_compressed','fromfile','loadtxt','genfromtxt'):setattr(np,name,forbidden)
        from braindecode.models import EEGNet,Labram
        EEGNet.from_pretrained=Labram.from_pretrained=classmethod(forbidden)
        from huggingface_hub import PyTorchModelHubMixin
        PyTorchModelHubMixin.from_pretrained=classmethod(forbidden)
        import data.runtime as scientific_runtime
        original_runtime=scientific_runtime.configure_scientific_runtime
        scientific_runtime.configure_scientific_runtime=lambda project_root=self.output:original_runtime(self.output)
        from evaluation.phase2_runner import CaseRecorder
        CaseRecorder.__init__=CaseRecorder.record_cell=forbidden
        return torch

    def clean(self):
        expected={'event':'socket.__new__','classification':'blocked_optional_ipv6_import_probe',
            'source_file':str(self.connection),'source_sha256':self.pins['files'][self.connection.relative_to(ROOT).as_posix()]}
        if self.denied not in ([],[expected]) or self.active:raise RuntimeError('unexpected denial or open numerical scope')

    def finish(self,result):
        import torch
        from tools.migration.common import source_check
        from evaluation.phase2_runner import environment_digest
        self.clean();self.verify_pins();pause_check()
        if (source_check(ROOT)!=CANONICAL or torch.get_num_threads()!=1 or torch.get_num_interop_threads()!=1
                or os.environ.get('CUDA_VISIBLE_DEVICES')!=''):raise ValueError('source/CPU controls changed')
        required={'module_load_state_dict':2,'safetensors_load':2,'optimizer_init':1,'sgd_step':1,'tensor_backward':1,'autograd_backward':1}
        if result['passed'] and (any(self.numerical_calls.get(k)!=v for k,v in required.items())
                or self.constructor_dummy_forward_calls!=1 or self.classifier_forward_calls!=2
                or self.backbone_forward_calls!=2 or self.current_restore_count!=1 or self.model_constructions!=1):
            raise ValueError('exact restore/support/query numerical counters differ')
        expected_reinitializations={scope+'|'+pattern:1 for scope in ('runner_owned_source','support_adapted_model')
            for pattern in ('Batch chs npat spatch -> Batch () (chs npat) spatch','Batch C NA T -> Batch NA (T C)')}
        if result['passed'] and (self.clone_reinitializations!=expected_reinitializations
                or len(self.clone_reinitialization_details)!=4):
            raise ValueError('exact four parameterless clone reinitializations required')
        if result['passed'] and self.empty_mask_containers!={'runner_owned_source':1,'support_adapted_model':1}:
            raise ValueError('exact two empty zero-depth mask containers required')
        expected_numpy={str(self.fixture/'data/processed/cho2017/profile_a/subject_02.npz'):4,
            str(self.fixture/'data/processed/cho2017/profile_b_60hz_v1/subject_02.npz'):2}
        if result['passed'] and self.numpy_loads!=expected_numpy:raise ValueError('exact six target-only NPZ decodes required')
        loaded={}
        for module in tuple(sys.modules.values()):
            name=getattr(module,'__file__',None)
            if name and Path(name).is_file() and not Path(name).resolve().is_relative_to(self.output):
                loaded[str(Path(name).resolve())]=digest(name)
        q={'schema':'cho51_linear_target_route_qualification_v3','passed':result['passed'],'result':result,
            'observed_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-self.started,
            'pins_sha256':self.pins_sha256,'canonical_files':432,'canonical_source_sha256':CANONICAL,
            'source_pins_rechecked':len(self.pins['files']),'runtime_pins_rechecked':5,
            'runtime_module_pins_rechecked':len(self.pins.get('runtime_modules',{})),
            'source_review_sha256':self.pins['source_review_sha256'],'environment_sha256':environment_digest(),
            'observed_loaded_module_hashes':loaded,'loaded_module_files':len(loaded),
            'denied_operations':self.denied,'unexpected_denials':0,'expected_blocked_ipv6_probes':len(self.denied),
            'read_only_git_queries':self.git_queries,'hostname_metadata_queries':self.hostname_queries,
            'existing_directory_mkdir_refusals':self.existing_mkdir_refusals,'sensitive_reads':self.sensitive_reads,
            'numpy_loads':self.numpy_loads,'numpy_load_count':sum(self.numpy_loads.values()),
            'observed_numerical_calls':self.numerical_calls,'constructor_dummy_forward_calls':self.constructor_dummy_forward_calls,
            'model_constructions':self.model_constructions,
            'supporting_runtime_sources_rechecked':4,'operational_version':3,
            'empty_mask_containers':self.empty_mask_containers,
            'empty_mask_container_count':sum(self.empty_mask_containers.values()),
            'parameterless_clone_reinitializations':self.clone_reinitializations,
            'parameterless_clone_reinitialization_count':sum(self.clone_reinitializations.values()),
            'parameterless_clone_reinitialization_details':self.clone_reinitialization_details,
            'classifier_forward_calls':self.classifier_forward_calls,'backbone_forward_calls':self.backbone_forward_calls,
            'current_restore_count':self.current_restore_count,'current_source_updates':0,
            'current_support_updates':result.get('current_support_updates',0),
            'current_gradient_updates':result.get('current_gradient_updates',0),
            'historical_gradient_updates':5253,'measured_cells':0,'scientific_admission':False,
            'full_worker_verified':False,'experiment_freeze_signed':False,'original_case_attempts_remaining':0,
            'torch_threads':1,'torch_interop_threads':1,'gpu_hidden':True,'actual_study_data_used':False}
        write_json(self.output/'qualification.json',q)
        for path,sha in loaded.items():
            if digest(path)!=sha:raise ValueError('loaded module changed during qualification')
        self.clean();return q
