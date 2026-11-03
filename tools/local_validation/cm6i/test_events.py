import unittest
import json
import hashlib
from ..hb1.common import Refusal
from . import events
from .fixtures import bundle, inputs, wire

class EventTests(unittest.TestCase):
    def check(self, b): return events.verify_events(b[5],b[4],b[3],b[1],b[2],b[7],b[8],b[9])
    def rebuild(self, b, rows):
        prefix=b''.join(wire(row) for row in rows[:-1]); rows[-1]['count']=len(rows)-1; rows[-1]['prefix']=hashlib.sha256(prefix).hexdigest()
        b[5]=prefix+wire(rows[-1]); return b
    def changed(self, field, value):
        b=list(bundle()); rows=[json.loads(line) for line in b[5].splitlines()]; rows[0][field]=value
        return self.rebuild(b,rows)
    def hand_negative(self):
        q,d,collected,t,qp,dp,op=inputs()
        b=[b'',q,d,collected,t,b'',b'',qp,dp,op]
        context=json.loads(collected)['context']; rows=[]
        def emit(event, **fields):
            row=dict(schema='cho51_cm6_event_v1',seq=len(rows)+1,op=b[9],context=context,event=event,case=None,sub=None,fixture=None,kind='NONE',code=None,line=None,count=None,prefix=None)
            row.update(fields); rows.append(row)
        emit('HEADER',count=360); emit('SUITE_OPEN'); emit('CASE_START',case=0)
        emit('SUB_ENTER',case=0,sub=1); emit('SUBFAIL',case=0,sub=1,kind='ASSERT',count=1)
        emit('TRACE',case=0,sub=1,kind='ASSERT',code=1,line=10,count=1); emit('SUB_EXIT',case=0,sub=1)
        emit('CLEANUP_DONE',case=0); emit('DURATION',case=0,count=0); emit('CASE_END',case=0,count=1)
        emit('SUITE_CLOSE'); emit('RESTORED'); emit('INPUTS_VERIFIED'); emit('FOOTER')
        return self.rebuild(b,rows)
    def test_pass_count(self): self.assertEqual(self.check(bundle()).passed,360)
    def test_negative_suffix(self): self.assertEqual(len(self.check(bundle(True)).not_started),359)
    def test_negative_disposition(self):
        b=self.hand_negative(); f=self.check(b); self.assertTrue(f.negative); self.assertEqual(f.subcases,1)
        self.assertFalse(f.authenticated or f.execution_accepted or f.debt_discharged)
        with self.assertRaises((AttributeError,TypeError)): f.negative=False
    def test_sequence(self):
        with self.assertRaises(Refusal): self.check(self.changed('seq',2))
    def test_schema(self):
        with self.assertRaises(Refusal): self.check(self.changed('schema','old'))
    def test_context(self):
        with self.assertRaises(Refusal): self.check(self.changed('context','0'*64))
    def test_operation(self):
        with self.assertRaises(Refusal): self.check(self.changed('op','0'))
    def test_header_count(self):
        with self.assertRaises(Refusal): self.check(self.changed('count',320))
    def test_header_owner(self):
        with self.assertRaises(Refusal): self.check(self.changed('case',0))
        b=self.hand_negative(); rows=[json.loads(line) for line in b[5].splitlines()]; rows[5]['sub']=2
        with self.assertRaises(Refusal): self.check(self.rebuild(b,rows))
    def test_header_kind(self):
        with self.assertRaises(Refusal): self.check(self.changed('kind','ASSERT'))
        b=self.hand_negative(); rows=[json.loads(line) for line in b[5].splitlines()]; rows[7]['event']='FIXTURE_ERROR'
        with self.assertRaises(Refusal): self.check(self.rebuild(b,rows))
    def test_bool_sequence(self):
        with self.assertRaises(Refusal): self.check(self.changed('seq',True))
    def test_extra_field(self):
        with self.assertRaises(Refusal): self.check(self.changed('extra',1))
        b=self.hand_negative(); rows=[json.loads(line) for line in b[5].splitlines()]; rows[7]['event']='DURATION'; rows[7]['count']=0
        with self.assertRaises(Refusal): self.check(self.rebuild(b,rows))
    def test_noncanonical(self):
        b=list(bundle()); b[5]=b[5].replace(b'\n',b' \n',1)
        with self.assertRaises(Refusal): self.check(b)
    def test_truncated_footer(self):
        b=list(bundle()); b[5]=b[5][:-1]
        with self.assertRaises(Refusal): self.check(b)
    def test_whole_digest(self):
        b=bundle(); self.assertEqual(self.check(b).whole_sha256,hashlib.sha256(b[5]).hexdigest())
    def test_bad_collection_precedes_events(self):
        b=list(bundle()); b[3]=b'{}\n'; b[5]=b'broken'
        with self.assertRaises(Refusal): self.check(b)
    def test_bad_tables(self):
        from .tables import parse_tables
        b=list(bundle()); table=json.loads(b[4]); owner='tools.local_validation.cm5.test_producer.ProducerTests'
        from ..cm5.registry import selected_ids
        expected=[i for i,n in enumerate(selected_ids()) if n.rsplit('.',1)[0]==owner]
        table['fixtures']=[dict(slot=0,owner=owner,phase='setup',affected=expected)]
        valid=wire(table); facts=parse_tables(valid,b[1],b[2],b[3],b[7],b[8],b[9]); self.assertEqual(facts.fixtures[0][3],tuple(expected))
        table['fixtures'][0]['affected']=expected[:-1]; b[4]=wire(table)
        with self.assertRaises(Refusal): self.check(b)
        table['fixtures'][0]['affected']=expected; table['fixtures'][0]['owner']='a'*129; b[4]=wire(table)
        with self.assertRaises(Refusal): self.check(b)
    def test_empty_stream(self):
        b=list(bundle()); b[5]=b''
        with self.assertRaises(Refusal): self.check(b)
    def test_mutable_stream(self):
        b=list(bundle()); b[5]=bytearray(b[5])
        with self.assertRaises(Refusal): self.check(b)
    def test_dispatch_refusal(self):
        with self.assertRaises(Refusal): events.dispatch()




