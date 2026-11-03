"""Synthetic supplied fixtures only; registry pins are separate source inputs."""
import hashlib
import json
from ..cm1.collection import LOADER
from ..cm5 import registry as baseline
from ..cm6.context import Q_PIN, Q_DIGEST, parse_expected_context
from . import registry
from .producer import ProducerModel

OP = '11111111-1111-1111-1111-111111111111'
def wire(value): return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode('ascii')
def pin(raw): return (len(raw),hashlib.sha256(raw).hexdigest())
def pinobj(raw):
    size, sha = pin(raw); return dict(bytes=size,sha256=sha)
def inputs():
    selected=baseline.selected_ids(); ids=registry.expected_ids(); old=set(baseline.expected_ids())
    q=wire(dict(schema='cho51_cm6_qualification_cohort_v1',name='CM6-Q360-20261103',count=360,ids=list(selected),ids_sha256=Q_DIGEST))
    rows=[]
    for name in ids:
        debt=None if name in selected else dict(kind='BASELINE_HELD' if name in old else 'NEW_TEST_UNQUALIFIED',id_sha256=hashlib.sha256(name.encode('ascii')).hexdigest())
        rows.append(dict(id=name,schedule='COHORT' if name in selected else 'HELD',obligation=debt))
    digest=hashlib.sha256(('\n'.join(ids)+'\n').encode('ascii')).hexdigest()
    d=wire(dict(schema='cho51_cm6_expected_census_v1',cohort=dict(name='CM6-Q360-20261103',count=360,ids_sha256=Q_DIGEST,bytes=Q_PIN[0],sha256=Q_PIN[1]),census=dict(count=len(ids),module_count=len(registry.expected_modules()),ids_sha256=digest),modules=[dict(module=n,bytes=s,sha256=h) for n,s,h in registry.expected_modules()],tests=rows,source_set='a'*64,runtime_set='b'*64,producer_set='c'*64))
    context=parse_expected_context(q,d,Q_PIN,pin(d),OP)
    modules=[dict(module=n,bytes=s,sha256=h,loader=LOADER,load_tests=False,partial=False) for n,s,h in context.modules]
    tests=[]
    for name in ids:
        mod,cls,method=name.rsplit('.',2)
        tests.append(dict(id=name,module=mod,class_name=cls,method_name=method,source_module=mod,source_qualname=cls+'.'+method,skipped=False,deselected=False,expected_failure=False,xfail=False))
    coll=wire(dict(schema='cho51_cm6_supplied_collection_v1',operation=OP,context=context.context,complete=True,modules=modules,tests=tests))
    tables=wire(dict(schema='cho51_cm6_supplied_tables_v1',operation=OP,context=context.context,codes=[[1,10]],fixtures=[]))
    return q,d,coll,tables,Q_PIN,pin(d),OP

def model(): return ProducerModel(*inputs())
def finish(m, fault='NONE'):
    for command in (('CLOSE_SUITE',),('RESTORED',),('INPUTS_VERIFIED',)): m.apply(command)
    m.apply(('FINISH',),fault)
def passing(m):
    m.apply(('BEGIN',))
    for i in range(360):
        for cmd in (('START',i),('CLEANUP',i),('DURATION',i,0),('OUTCOME',i,'PASS','NONE',()),('END',i)): m.apply(cmd)
def negative(m):
    for cmd in (('BEGIN',),('START',0),('OUTCOME',0,'FAIL','ASSERT',((1,10),)),('CLEANUP',0),('DURATION',0,0),('END',0)): m.apply(cmd)
    finish(m)
def bundle(negative_case=False):
    q,d,c,t,qp,dp,op=inputs(); m=ProducerModel(q,d,c,t,qp,dp,op)
    if negative_case: negative(m)
    else: passing(m); finish(m)
    seal=m.seal(); events=seal['raw']; terminal=seal['terminal']
    context=parse_expected_context(q,d,qp,dp,op).context
    join=wire(dict(schema='cho51_cm6_supplied_join_v1',operation=op,context=context,cohort=pinobj(q),descriptor=pinobj(d),collection=pinobj(c),tables=pinobj(t),events=pinobj(events),terminal=pinobj(terminal)))
    return join,q,d,c,t,events,terminal,qp,dp,op
