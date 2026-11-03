import unittest
from ..hb1.common import Refusal
from .fixtures import model, inputs, passing, negative, finish
from .producer import ProducerModel, dispatch_runtime

class ProducerTests(unittest.TestCase):
    def test_constructor_bad_collection(self):
        q,d,c,t,qp,dp,op=inputs()
        with self.assertRaises(Refusal): ProducerModel(q,d,b'{}\n',t,qp,dp,op)
    def test_constructor_bad_tables(self):
        q,d,c,t,qp,dp,op=inputs()
        with self.assertRaises(Refusal): ProducerModel(q,d,c,b'{}\n',qp,dp,op)
    def test_begin_emits_two(self):
        m=model(); m.apply(('BEGIN',)); self.assertEqual(m.facts()['records'],2)
    def test_full_pass_count(self):
        m=model(); passing(m); finish(m); self.assertEqual(m.facts()['records'],1806)
    def test_wrong_ordinal(self):
        m=model(); m.apply(('BEGIN',))
        with self.assertRaises(Refusal): m.apply(('START',1))
    def test_out_of_range_ordinal(self):
        m=model(); m.apply(('BEGIN',))
        with self.assertRaises(Refusal): m.apply(('START',360))
    def test_negative_lifecycle(self):
        m=model(); negative(m); self.assertIsNotNone(m.seal()['terminal'])
    def test_invalid_trace_is_atomic(self):
        m=model(); m.apply(('BEGIN',)); m.apply(('START',0)); before=m.raw_prefix()
        with self.assertRaises(Refusal): m.apply(('OUTCOME',0,'FAIL','ASSERT',((2,10),)))
        self.assertEqual(m.raw_prefix(),before)
    def test_subcase_interval(self):
        m=model(); m.apply(('BEGIN',)); m.apply(('START',0)); m.apply(('SUB_ENTER',0,1))
        with self.assertRaises(Refusal): m.apply(('CLEANUP',0))
    def test_cleanup_required(self):
        m=model(); m.apply(('BEGIN',)); m.apply(('START',0))
        with self.assertRaises(Refusal): m.apply(('DURATION',0,0))
    def test_pre_refusal(self):
        m=model()
        with self.assertRaises(Refusal): m.apply(('BEGIN',),'PRE_REFUSE')
        self.assertEqual(m.raw_prefix(),b'')
    def test_post_refusal(self):
        m=model()
        with self.assertRaises(Refusal): m.apply(('BEGIN',),'POST_REFUSE')
        self.assertEqual(m.facts()['records'],2)
    def test_nested_pre_settled(self):
        m=model()
        with self.assertRaises(Refusal): m.apply(('BEGIN',),'REENTER_PRE')
        self.assertEqual((m.attempts,m.settled,m.first_refusal),(2,2,2))
    def test_nested_post_settled(self):
        m=model()
        with self.assertRaises(Refusal): m.apply(('BEGIN',),'REENTER_POST')
        self.assertEqual((m.attempts,m.settled,m.first_refusal),(2,2,2))
    def test_nested_postfooter_accounted(self):
        m=model(); passing(m)
        with self.assertRaises(Refusal): finish(m,'REENTER_POST')
        self.assertEqual((m.post_footer_attempts,m.in_flight),(1,0))
    def test_secondary_reject_helper_failure(self):
        m=model()
        def fail(*args):
            m.refused=True
            raise Refusal('secondary')
        m._refuse=fail
        with self.assertRaises(Refusal): m.apply(('BEGIN',),'PRE_REFUSE')
        self.assertFalse(m.accounting_complete); self.assertIsNone(m.seal()['terminal'])
        n=model()
        with self.assertRaises(Refusal): n.apply(('BEGIN',),'PRE_REFUSE')
        def fail_again(*args):
            n.refused=True
            raise Refusal('secondary')
        n._refuse=fail_again
        with self.assertRaises(Refusal): n.apply(('BEGIN',))
        self.assertFalse(n.accounting_complete); self.assertIsNone(n.seal()['terminal'])
    def test_secondary_settle_failure(self):
        m=model()
        def fail(): raise RuntimeError()
        m._settle=fail
        with self.assertRaises(RuntimeError): m.apply(('BEGIN',))
        self.assertFalse(m.accounting_complete)
    def test_partial_seal_has_no_terminal(self):
        m=model(); m.apply(('BEGIN',)); self.assertIsNone(m.seal()['terminal'])
    def test_seal_is_stable(self):
        m=model(); negative(m); self.assertIs(m.seal(),m.seal())
        f=m.facts(); self.assertFalse(f['authenticated'] or f['execution_accepted'] or f['debt_discharged'])
        with self.assertRaises(TypeError): f['authenticated']=True
    def test_runtime_refuses(self):
        with self.assertRaises(Refusal): dispatch_runtime()


