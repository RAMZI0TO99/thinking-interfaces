import unittest
from ..hb1.common import Refusal
from . import fixtures as f
from .producer import dispatch_runtime

class ProducerTests(unittest.TestCase):
    def test_begin(self):
        m=f.model(); m.apply(('BEGIN',)); self.assertEqual(m.facts()['records'],2)
    def test_wrong_ordinal_refused(self):
        m=f.model(); m.apply(('BEGIN',))
        with self.assertRaises(Refusal): m.apply(('START',140))
    def test_partial_cannot_seal(self):
        m=f.model(); m.apply(('BEGIN',)); self.assertIsNone(m.seal()['terminal'])
    def test_pre_refusal_settled(self):
        m=f.model()
        with self.assertRaises(Refusal): m.apply(('BEGIN',),'PRE_REFUSE')
        self.assertEqual(m.facts()['attempts'],m.facts()['settled']); self.assertTrue(m.facts()['refused'])
    def test_ordinary_postfooter_accounted(self):
        m=f.model(); f.negative(m)
        with self.assertRaises(Refusal): m.apply(('BEGIN',),'REENTER_POST')
        self.assertEqual(m.facts()['post_footer_attempts'],1); self.assertIsNotNone(m.seal()['terminal'])
    def test_constructor_bad_collection(self):
        a=list(f.inputs()); a[4]=b'{}\n'
        with self.assertRaises(Refusal): f.ProducerModel(*a)
    def test_secondary_failure_cannot_seal(self):
        m=f.model()
        def broken(*args): raise RuntimeError('secondary')
        m._refuse=broken
        with self.assertRaises(RuntimeError): m.apply(('BEGIN',),'PRE_REFUSE')
        self.assertIsNone(m.seal()['terminal'])
    def test_dispatch_refused(self):
        with self.assertRaises(Refusal): dispatch_runtime()

    def test_nested_postfooter_from_finish(self):
        m=f.model(); m.apply(('BEGIN',)); m.apply(('START',0)); m.apply(('OUTCOME',0,'FAIL','ASSERT',((1,10),))); m.apply(('CLEANUP',0)); m.apply(('DURATION',0,0)); m.apply(('END',0)); m.apply(('CLOSE_SUITE',)); m.apply(('RESTORED',)); m.apply(('INPUTS_VERIFIED',))
        with self.assertRaises(Refusal): m.apply(('FINISH',),'REENTER_POST')
        self.assertEqual(m.facts()['post_footer_attempts'],1); self.assertEqual(m.facts()['attempts'],m.facts()['settled'])


    def test_secondary_refusal_after_sticky_latch(self):
        m=f.model()
        with self.assertRaises(Refusal): m.apply(('BEGIN',),'PRE_REFUSE')
        def broken(code, ordinal=None):
            m.refused=True
            raise Refusal('secondary')
        m._refuse=broken
        with self.assertRaises(Refusal): m.apply(('BEGIN',))
        self.assertFalse(m.facts()['accounting_complete']); self.assertIsNone(m.seal()['terminal'])
