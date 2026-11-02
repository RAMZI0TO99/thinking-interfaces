"""Supplied-byte native transport/PE refusal controls; no DLL is loaded here."""
import copy
import hashlib
import json
import struct
import unittest
from . import l_native as n
from .test_protocol import request
from . import protocol

def image(names):
    raw=bytearray(2048)
    def h(at,value):struct.pack_into('<H',raw,at,value)
    def i(at,value):struct.pack_into('<I',raw,at,value)
    raw[:2]=b'MZ';i(60,128);raw[128:132]=b'PE\0\0';h(132,0x8664);h(134,1);h(148,240)
    h(152,0x20b);i(260,16);i(264,0x1000);i(268,512)
    raw[392:397]=b'.text';i(404,0x1000);i(408,1536);i(412,512)
    i(532,len(names));i(536,len(names));i(540,0x1040);i(544,0x1080);i(548,0x10c0)
    cursor=768
    for index,name in enumerate(names):
        i(576+4*index,0x1400+index);i(640+4*index,0x1000+cursor-512);h(704+2*index,index)
        value=name.encode('ascii')+b'\0';raw[cursor:cursor+len(value)]=value;cursor+=len(value)
    return bytes(raw)

class NativeTransportTests(unittest.TestCase):
    def test_bundle_enriches_typed_retained_identity_and_refuses_rebinding(self):
        from ..l1.protocol import ref
        base='D:/fixture';operation='11111111-1111-4111-8111-111111111111'
        ident=dict(schema='cho51_lv_native_identity_v1',volume_serial='a'*16,file_id='b'*32,volume_kind='local_fixed',filesystem='NTFS')
        data={};artifacts={}
        for role in ('observer','injection','target','callback'):
            path=base+'/l-'+role+'_'+operation+('.txt' if role=='callback' else '.dll')
            raw=b'owned disassembly fixture' if role=='callback' else image(sorted(n.EXPORTS[role]));data[path]=raw
            item=dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),role='l-callback-disassembly' if role=='callback' else 'l-'+role)
            artifacts[role]=dict(reference=item,native_identity='a'*16+':'+'b'*32,owner='q_original_strict_receiver',sharing=dict(read=True,write=False,delete=False))
        value=dict(schema='cho51_l_native_bundle_v1',operation_id=operation,artifacts=artifacts,operations=[],
            production_exports=['l1_start','l1_drain','l1_snapshot','l1_stop','l1_state'],qualification_pending=True,scientific_admission=False)
        raw=json.dumps(value).encode();path=base+'/l-bundle_'+operation+'.json';data[path]=raw
        class Reader:
            def read_small(self,path,expected=None,max_bytes=None):return data[path]
            def retain(self,path,expected=None):return dict(native_identity=copy.deepcopy(ident))
            def verify(self):return True
        reader=Reader();args=(reader,base,operation,hashlib.sha256(raw).hexdigest(),'a'*16+':'+'b'*32,len(raw))
        refs=n.load_bundle(*args)
        for item in refs.values():ref(item,retained=True)
        value['artifacts']['observer']['native_identity']='c'*16+':'+'d'*32;data[path]=json.dumps(value).encode()
        with self.assertRaises(ValueError):n.load_bundle(*args)

    def test_exact_production_and_injection_exports(self):
        for role,names in n.EXPORTS.items():self.assertEqual(n.exports(image(sorted(names))),names)

    def test_malformed_headers_and_truncated_image_refuse(self):
        for data in (b'',b'MZ',image(['l1_start'])[:700],b'ZZ'+image(['l1_start'])[2:]):
            with self.assertRaises(ValueError):n.exports(data)

    def test_x86_and_tls_callbacks_refuse(self):
        for at,fmt,value in ((132,'H',0x14c),(264+9*8,'I',0x1100)):
            data=bytearray(image(['l1_start']));struct.pack_into('<'+fmt,data,at,value)
            with self.assertRaises(ValueError):n.exports(bytes(data))

    def test_forwarders_ordinals_and_duplicate_names_refuse(self):
        for at,fmt,value in ((576,'I',0x1100),(704,'H',2),(536,'I',0)):
            data=bytearray(image(['l1_start']));struct.pack_into('<'+fmt,data,at,value)
            with self.assertRaises(ValueError):n.exports(bytes(data))
        with self.assertRaises(ValueError):n.exports(image(['l1_start','l1_start']))

    def test_native_fault_report_requires_unregister(self):
        value=dict(schema='cho51_lq_native_case_v1',case='overflow',result=dict(case='overflow',expected_fault=1,
            faults=1,observer_shutdown=True,operation_refused=True),strict_inputs_verified=True,live_references=0,scientific_admission=False)
        n.validate_result(value,'overflow')
        for key,replacement in (('observer_shutdown',False),('faults',0),('expected_fault',4),('operation_refused',False)):
            bad=copy.deepcopy(value);bad['result'][key]=replacement
            with self.assertRaises(ValueError):n.validate_result(bad,'overflow')

    def test_native_report_disallows_remaining_refs_or_scientific_claim(self):
        value=dict(schema='cho51_lq_native_case_v1',case='transient',result=dict(case='transient',events=2,
            transient_events=2,observer_shutdown=True,reference_released=True),strict_inputs_verified=True,live_references=0,scientific_admission=False)
        n.validate_result(value,'transient')
        for key,replacement in (('live_references',True),('live_references',1),('scientific_admission',True),('strict_inputs_verified',False)):
            bad=copy.deepcopy(value);bad[key]=replacement
            with self.assertRaises(ValueError):n.validate_result(bad,'transient')

    def test_separate_tool_size_role_preserves_source_cap(self):
        value=request();value['native_compiler']['files']['C:/LLVM/clang.exe']['bytes']=123520512
        protocol.validate_admission(value,'D:/Aenv/pro3','2026-10-29T00:00:10Z')
        value['sources'][protocol.REQUIRED[0]]['bytes']=123520512
        with self.assertRaises(ValueError):protocol.validate_admission(value,'D:/Aenv/pro3','2026-10-29T00:00:10Z')

    def test_tool_scope_extras_and_missing_required_refuse(self):
        for change in ('outside','missing','huge','bool','recipe'):
            value=request();files=value['native_compiler']['files']
            if change=='outside':files['C:/Other/x.dll']={'bytes':1,'sha256':'1'*64}
            elif change=='missing':del files['C:/LLVM/lld-link.exe']
            elif change=='huge':files['C:/LLVM/clang.exe']['bytes']=256*1024**2+1
            elif change=='bool':files['C:/LLVM/clang.exe']['bytes']=True
            else:value['native_compiler']['recipe']='unreviewed'
            with self.assertRaises(ValueError):protocol.validate_admission(value,'D:/Aenv/pro3','2026-10-29T00:00:10Z')
