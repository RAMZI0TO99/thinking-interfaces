import io
import struct
import unittest
from . import protocol as p

OP='00000000-0000-4000-8000-000000000001'

class ProtocolTests(unittest.TestCase):
    def test_duplicate_json(self):
        with self.assertRaises(p.Refusal): p.decode(b'{"a":1,"a":2}')
    def test_nonfinite_json(self):
        for raw in (b'NaN',b'Infinity',b'-Infinity'):
            with self.assertRaises(p.Refusal): p.decode(raw)
    def test_bool_integer(self):
        with self.assertRaises(p.Refusal): p.integer(True)
    def test_unicode_limits(self):
        for value in ('\ud800','\udfff','x\0y'):
            with self.assertRaises(p.Refusal): p.string(value)
        self.assertEqual(p.string('😀',4),'😀')
    def test_json_depth(self):
        value=[]
        for _ in range(34): value=[value]
        with self.assertRaises(p.Refusal): p.encode(value)
    def test_phase_sticky(self):
        machine=p.PhaseMachine()
        with self.assertRaises(p.Refusal): machine.advance('L2')
        with self.assertRaises(p.Refusal): machine.advance('L1')
    def test_frame_unknown_keys(self):
        validator=p.FrameValidator(OP)
        with self.assertRaises(p.Refusal): validator.accept(dict(schema='cho51_l_frame_v1',extra=1))
    def test_frame_oversize_before_body(self):
        stream=io.BytesIO(struct.pack('<I',p.FRAME_BYTES+1))
        reader=p.FrameReader(stream.read,OP,lambda:True)
        with self.assertRaises(p.Refusal): reader.next_frame()
        self.assertEqual(stream.tell(),4)
    def test_frame_truncation(self):
        reader=p.FrameReader(io.BytesIO(struct.pack('<I',20)+b'{}').read,OP,lambda:True)
        with self.assertRaises(p.Refusal): reader.next_frame()
    def test_no_terminal_eof(self):
        reader=p.FrameReader(io.BytesIO().read,OP,lambda:True)
        with self.assertRaises(p.Refusal): reader.next_frame()
    def test_digest_encoding_vector(self):
        import hashlib
        rows=['a[é]','a[é0]']
        self.assertEqual(p.roster_digest(rows),hashlib.sha256('["a[é]","a[é0]"]'.encode()).hexdigest())
        with self.assertRaises(p.Refusal): p.roster_digest(['a','a'])
    def test_counters_exact_zero(self):
        counters={k:0 for k in p.COUNTERS}
        p.zero_counters(counters)
        for bad in (True,1):
            counters[p.COUNTERS[0]]=bad
            with self.assertRaises(p.Refusal): p.zero_counters(counters)
