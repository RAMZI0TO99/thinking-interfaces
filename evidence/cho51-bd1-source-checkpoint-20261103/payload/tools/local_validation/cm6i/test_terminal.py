import unittest
import json
import hashlib
from ..hb1.common import Refusal
from .terminal import parse_terminal
from .fixtures import bundle, wire

class TerminalTests(unittest.TestCase):
    def check(self,b): return parse_terminal(b[6],b[1],b[2],b[7],b[8],b[9])
    def change(self,key,value):
        b=list(bundle(True)); v=json.loads(b[6]); v[key]=value; b[6]=wire(v); return b
    def test_terminal_complete(self):
        b=bundle(True); f=self.check(b)
        self.assertGreater(f.attempts,0); self.assertEqual(f.attempts,f.settled)
        self.assertEqual(f.events,(len(b[5]),hashlib.sha256(b[5]).hexdigest()))
        self.assertEqual(f.inputs,tuple((len(x),hashlib.sha256(x).hexdigest()) for x in b[1:5]))
    def test_events_pin(self):
        b=bundle(True); self.assertEqual(self.check(b).events[0],len(b[5]))
    def test_inputs_pin(self):
        b=bundle(True); self.assertEqual(self.check(b).inputs[:2],(b[7],b[8]))
    def test_context(self):
        with self.assertRaises(Refusal): self.check(self.change('context','0'*64))
    def test_operation(self):
        with self.assertRaises(Refusal): self.check(self.change('operation','bad'))
    def test_schema(self):
        with self.assertRaises(Refusal): self.check(self.change('schema','old'))
    def test_boundary(self):
        with self.assertRaises(Refusal): self.check(self.change('boundary','AUTHENTICATED'))
    def test_detached(self):
        with self.assertRaises(Refusal): self.check(self.change('producer_detached',False))
    def test_bool_attempts(self):
        with self.assertRaises(Refusal): self.check(self.change('attempts',True))
    def test_attempt_overflow(self):
        with self.assertRaises(Refusal): self.check(self.change('attempts',65536))
    def test_unsettled(self):
        with self.assertRaises(Refusal): self.check(self.change('settled',0))
    def test_inflight(self):
        with self.assertRaises(Refusal): self.check(self.change('in_flight',1))
    def test_latch(self):
        with self.assertRaises(Refusal): self.check(self.change('refused',True))
    def test_first_refusal(self):
        with self.assertRaises(Refusal): self.check(self.change('first_refusal',1))
    def test_late_without_refusal(self):
        with self.assertRaises(Refusal): self.check(self.change('post_footer_attempts',1))
    def test_extra_field(self):
        with self.assertRaises(Refusal): self.check(self.change('extra',1))
    def test_wrong_event_pin_shape(self):
        with self.assertRaises(Refusal): self.check(self.change('events',{'bytes':True,'sha256':'a'*64}))
    def test_bad_input_shape(self):
        with self.assertRaises(Refusal): self.check(self.change('inputs',{}))
    def test_noncanonical(self):
        b=list(bundle(True)); b[6]+=b' '
        with self.assertRaises(Refusal): self.check(b)
    def test_unauthenticated(self): self.assertFalse(self.check(bundle(True)).authenticated)

