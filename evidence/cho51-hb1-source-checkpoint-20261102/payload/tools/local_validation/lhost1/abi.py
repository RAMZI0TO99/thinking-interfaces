"""Bounded PE export observation and finite safe-query comparison."""
import struct
import sys
from ..l1.protocol import need,integer,closed
from ..l1.guards import raw_get
from ..l1.observation import assess_abi,ABI_SCOPE,typed_result_equal

def exports(raw):
    need(type(raw) is bytes and 64<=len(raw)<=2*1024**3,'retained PE bytes')
    def span(offset,count):
        integer(offset,0,len(raw));integer(count,0,len(raw));need(offset+count<=len(raw),'PE range');return raw[offset:offset+count]
    need(span(0,2)==b'MZ','PE DOS')
    start=struct.unpack('<I',span(60,4))[0];need(64<=start<=1024**2,'PE header bound')
    need(span(start,4)==b'PE\0\0','PE signature')
    machine,sections=struct.unpack('<HH',span(start+4,4));need(1<=sections<=96,'PE sections')
    optional=struct.unpack('<H',span(start+20,2))[0];need(112<=optional<=4096,'PE optional bytes')
    header=span(start+24,optional);magic=struct.unpack_from('<H',header)[0]
    need(magic==0x20b and machine==0x8664,'reviewed x64 PE')
    directories=struct.unpack_from('<I',header,108)[0];need(1<=directories<=16 and optional>=112+8*directories,'PE directory count')
    export_rva,export_size=struct.unpack_from('<II',header,112)
    header_size=struct.unpack_from('<I',header,60)[0]
    table=span(start+24+optional,sections*40);segments=[]
    for i in range(sections):
        virtual_size,virtual,raw_size,physical=struct.unpack_from('<IIII',table,i*40+8)
        span(physical,raw_size);segments.append((virtual,max(virtual_size,raw_size),physical,raw_size))
    def physical(rva,count):
        choices=[]
        if rva<header_size and rva+count<=header_size:choices.append(rva)
        for base,size,offset,backed in segments:
            if base<=rva and rva+count<=base+size:
                need(rva-base+count<=backed,'PE unbacked RVA');choices.append(offset+rva-base)
        need(len(choices)==1,'PE ambiguous RVA');return choices[0]
    def read(rva,count):return span(physical(rva,count),count)
    def name(rva):
        result=bytearray()
        for i in range(512):
            char=read(rva+i,1)[0]
            if char==0:
                need(bool(result) and all(32<v<127 for v in result),'PE export name');return result.decode('ascii')
            result.append(char)
        need(False,'PE export name cap')
    need(export_rva and 40<=export_size<=16*1024**2,'PE export directory')
    directory=read(export_rva,40)
    base,functions,names,address,names_rva,ordinals=struct.unpack_from('<6I',directory,16)
    need(0<functions<=65536 and names<=4096 and names<=functions,'PE export counts')
    function_rows=read(address,4*functions);name_rows=read(names_rva,4*names);ordinal_rows=read(ordinals,2*names)
    result={}
    for i in range(names):
        label=name(struct.unpack_from('<I',name_rows,4*i)[0]);ordinal=struct.unpack_from('<H',ordinal_rows,2*i)[0]
        need(ordinal<functions and label not in result,'PE ordinal/duplicate export')
        rva=struct.unpack_from('<I',function_rows,4*ordinal)[0];need(rva>0,'PE null export')
        result[label]=name(rva) if export_rva<=rva<export_rva+export_size else None
    return machine,result

def before_extension(row,abi_rows,read_retained):
    matches=[p for p in abi_rows if p['module']==row['module']]
    need(len(matches)==1,'every selected extension requires exact ABI plan')
    plan=matches[0];need(plan['extension_file']==row['file_ref'],'extension retained ABI join')
    machine,names=exports(read_retained(row['file_ref']))
    need(machine==plan['machine'] and plan['python_tag']=='cp'+str(sys.version_info.major)+str(sys.version_info.minor),'interpreter PE tag')
    need(plan['initializer_symbol']=='PyInit_'+row['module'].rsplit('.',1)[-1]
         and plan['initializer_symbol'] in names,'extension initializer export')
    need(set(plan['required_exports'])<=set(names),'required exports missing')
    actual_forwarders={name:target for name,target in names.items() if name in plan['required_exports'] and target is not None}
    need(actual_forwarders==plan['forwarder_targets'],'exact reviewed export forwarders')
    return plan,names

def after_extension(row,module,before,metadata,emit):
    plan,names=before
    queries=[]
    for spec in plan['safe_queries']:
        closed(spec,'module symbol arguments result effect_budget rationale')
        need(spec['module'] in sys.modules and spec['arguments']==[] and spec['effect_budget']=='noncomputational','finite ABI getter')
        function=raw_get(sys.modules[spec['module']],spec['symbol'])
        need(callable(function),'ABI getter callable')
        result=function()
        need(typed_result_equal(result,spec['result']),'ABI getter result')
        queries.append(dict(module=spec['module'],symbol=spec['symbol'],arguments=list(spec['arguments']),result=result,
                            effect_budget=spec['effect_budget'],rationale=spec['rationale']))
    actual_metadata=metadata(plan['module'])
    observed=dict(module=plan['module'],extension_file=plan['extension_file'],machine=plan['machine'],python_tag=plan['python_tag'],
                  initializer_symbol=plan['initializer_symbol'],exports=list(names),forwarder_targets=plan['forwarder_targets'],
                  safe_queries=queries,metadata=actual_metadata,initialized=True,
                  unqualified_paths=['dormant exports','numerical kernels','GPU operation','unexercised delay imports'])
    return assess_abi(plan,observed),observed
