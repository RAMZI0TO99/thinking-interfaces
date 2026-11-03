"""Fresh Q-only strict native artifact transport; no production L admission."""
import ctypes
import re
import struct
from ..v1.records import require, closed, strict_loads

CASES=('transient','overflow','badreason','badutf16','pathbound')
EXPORTS={'observer':{'l1_start','l1_drain','l1_snapshot','l1_stop','l1_state'},
         'injection':{'l1_start','l1_drain','l1_snapshot','l1_stop','l1_state','l1_fixture_notify'},
         'target':{'l1_fixture_value'}}

def identity(descriptor):
    value=descriptor['native_identity']
    return value['volume_serial']+':'+value['file_id']

def exports(raw):
    """Bounded x64 PE named/ordinal export grammar; forwarded exports refused."""
    require(type(raw) is bytes and 512<=len(raw)<=1048576,'native PE size')
    def span(at,n):
        require(type(at) is int and type(n) is int and at>=0 and n>=0 and at+n<=len(raw),'native PE range')
        return raw[at:at+n]
    def u16(at):return struct.unpack('<H',span(at,2))[0]
    def u32(at):return struct.unpack('<I',span(at,4))[0]
    require(span(0,2)==b'MZ','native DOS signature');header=u32(60)
    require(span(header,4)==b'PE\0\0' and u16(header+4)==0x8664,'native PE machine')
    n=u16(header+6);optional=u16(header+20);start=header+24
    require(1<=n<=16 and optional==240 and u16(start)==0x20b,'native PE64 layout')
    require(u32(start+108)>=16,'native PE directories')
    require(u32(start+112+9*8)==0 and u32(start+116+9*8)==0,'native TLS callback directory denied')
    sections=[]
    for i in range(n):
        at=start+optional+i*40
        sections.append((u32(at+12),u32(at+16),u32(at+20)))
    def rva(address,size):
        matches=[off+address-base for base,length,off in sections if base<=address and address+size<=base+length]
        require(len(matches)==1,'native unique raw RVA');span(matches[0],size);return matches[0]
    address,size=u32(start+112),u32(start+116)
    require(address>0 and 40<=size<=65536,'native export directory')
    table=rva(address,40);functions,names=u32(table+20),u32(table+24)
    require(1<=functions==names<=8,'native named-only finite exports')
    eat=rva(u32(table+28),4*functions);nt=rva(u32(table+32),4*names);ot=rva(u32(table+36),2*names)
    result=set();ordinals=set()
    for i in range(names):
        at=rva(u32(nt+4*i),1);end=raw.find(b'\0',at,min(at+128,len(raw)))
        require(end>at,'native export name terminator')
        name=raw[at:end].decode('ascii');require(re.fullmatch(r'l1_[a-z_]+',name) is not None,'native export name')
        ordinal=u16(ot+2*i);require(ordinal<functions and ordinal not in ordinals and name not in result,'native unique export')
        target=u32(eat+4*ordinal);require(target>0 and not address<=target<address+size,'native forwarder denied');rva(target,1)
        ordinals.add(ordinal);result.add(name)
    return result

def load_bundle(reader,base,operation,digest,native_identity,size):
    path=base+'/l-bundle_'+operation+'.json'
    expected={'bytes':int(size),'sha256':digest}
    raw=reader.read_small(path,expected,max_bytes=1048576)
    require(identity(reader.retain(path))==native_identity,'native bundle original identity')
    value=strict_loads(raw)
    closed(value,'schema operation_id artifacts operations production_exports qualification_pending scientific_admission'.split())
    require(value['schema']=='cho51_l_native_bundle_v1' and value['operation_id']==operation
            and value['qualification_pending'] is True and value['scientific_admission'] is False,'native bundle scope')
    require(set(value['artifacts'])=={'observer','injection','target','callback'}
            and value['production_exports']==['l1_start','l1_drain','l1_snapshot','l1_stop','l1_state'],'native artifact roles')
    refs={}
    for role,cap in value['artifacts'].items():
        closed(cap,('reference','native_identity','owner','sharing'))
        item=cap['reference'];closed(item,('path','bytes','sha256','role'))
        suffix='txt' if role=='callback' else 'dll'
        require(item['path']==base+'/l-'+role+'_'+operation+'.'+suffix
                and item['role']==('l-callback-disassembly' if role=='callback' else 'l-'+role),'exact native artifact path/role')
        require(cap['owner']=='q_original_strict_receiver' and cap['sharing']=={'read':True,'write':False,'delete':False}
                and all(type(v) is bool for v in cap['sharing'].values()),'native strict retained transport')
        data=reader.read_small(item['path'],{k:item[k] for k in ('bytes','sha256')},max_bytes=1048576)
        descriptor=reader.retain(item['path'])
        require(identity(descriptor)==cap['native_identity'],'native artifact identity')
        if role!='callback':require(exports(data)==EXPORTS[role],'exact generated helper exports')
        refs[role]=dict(item,native_identity=descriptor['native_identity'],owner='q_strict_retained',sharing=cap['sharing'])
    reader.verify()
    return refs

class Capabilities:
    def __init__(self,reader,refs,checkpoint):
        self.reader,self.refs,self.checkpoint=reader,refs,checkpoint
        self.live={}
        self.kernel=ctypes.WinDLL('kernel32.dll',use_last_error=True,winmode=0x800)
        self.kernel.FreeLibrary.argtypes=[ctypes.c_void_p];self.kernel.FreeLibrary.restype=ctypes.c_int
    def verify(self,ref):
        require(ref in self.refs.values(),'native capability provenance')
        self.checkpoint()
        descriptor=self.reader.retain(ref['path'],{k:ref[k] for k in ('bytes','sha256')})
        require(identity(descriptor)==identity(ref),'native retained original identity')
        self.reader.verify();return True
    def load_exact(self,ref):
        self.verify(ref)
        require(ref['role'] in ('l-observer','l-injection','l-target') and ref['path'] not in self.live,'closed once-live native load')
        dll=ctypes.CDLL(ref['path'],winmode=0x1100)
        self.live[ref['path']]=dll
        return dll
    def release_exact(self,dll,ref):
        require(self.live.get(ref['path']) is dll,'owned exact native reference')
        require(self.kernel.FreeLibrary(dll._handle)==1,'owned native release')
        del self.live[ref['path']];return True

def run_case(mode,reader,refs,checkpoint):
    from ..l1 import native_cases
    require(mode in CASES,'closed native Q mode')
    capabilities=Capabilities(reader,refs,checkpoint)
    result=(native_cases.transient_case(refs['observer'],refs['target'],capabilities) if mode=='transient'
            else native_cases.injection_case(refs['injection'],mode,capabilities))
    require(not capabilities.live,'native references remain')
    reader.verify()
    return dict(schema='cho51_lq_native_case_v1',case=mode,result=result,strict_inputs_verified=True,
                live_references=0,scientific_admission=False)

def validate_result(value,mode):
    closed(value,'schema case result strict_inputs_verified live_references scientific_admission'.split())
    require(value['schema']=='cho51_lq_native_case_v1' and value['case']==mode and mode in CASES
            and value['strict_inputs_verified'] is True and type(value['live_references']) is int
            and value['live_references']==0 and value['scientific_admission'] is False,'native case custody')
    result=value['result']
    if mode=='transient':
        closed(result,'case events transient_events observer_shutdown reference_released'.split())
        require(type(result['events']) is int and 2<=result['events']<=8192 and type(result['transient_events']) is int and result['transient_events']==2
                and result['reference_released'] is True,'transient native evidence')
    else:
        closed(result,'case expected_fault faults observer_shutdown operation_refused'.split())
        expected=1 if mode=='overflow' else 2 if mode=='badreason' else 4
        require(type(result['faults']) is int and result['faults']&expected==expected
                and type(result['expected_fault']) is int and result['expected_fault']==expected
                and result['operation_refused'] is True,'sticky native fault evidence')
    require(result['case']==mode and result['observer_shutdown'] is True,'native unregister completion')
