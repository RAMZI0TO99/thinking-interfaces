"""Bounded refusal, accounting and terminal cases; source-only."""
import unittest
from unittest.mock import patch
from ..cm4.terminal import parse_terminal
from .producer import ProducerModel, Refusal, dispatch_runtime
from .test_producer import OP, CHECK, CASE, model, negative, passes, finish

class RefusalTests(unittest.TestCase):
    def test_pre_refusal_preserves_prefix(self):
        m=model()
        with self.assertRaises(Refusal): m.apply(('BEGIN',), 'PRE_REFUSE')
        self.assertEqual(m.raw_prefix(),b''); self.assertEqual(m.facts()['settled'],1)
    def test_post_refusal_preserves_complete_group(self):
        m=model()
        with self.assertRaises(Refusal): m.apply(('BEGIN',), 'POST_REFUSE')
        self.assertEqual(m.facts()['records'],2); self.assertTrue(m.facts()['refused'])
    def test_post_finish_refusal_has_valid_terminal(self):
        m=model(); passes(m)
        with self.assertRaises(Refusal): finish(m, 'POST_REFUSE')
        s=m.seal(); self.assertTrue(parse_terminal(s['terminal'],OP,check=CHECK).refused)
        from ..cm4.events import verify_events
        self.assertFalse(verify_events(s['raw'],OP,codes=((1,10),),check=CHECK).negative)
    def test_reentry_pre_first_observed_two(self):
        m=model()
        with self.assertRaises(Refusal): m.apply(('BEGIN',),'REENTER_PRE')
        self.assertEqual((m.facts()['first_refusal'],m.facts()['settled'],m.raw_prefix()),(2,2,b''))
    def test_reentry_post_retains_output(self):
        m=model()
        with self.assertRaises(Refusal): m.apply(('BEGIN',),'REENTER_POST')
        self.assertEqual((m.facts()['first_refusal'],m.facts()['records'],m.facts()['in_flight']),(2,2,0))
        n=model(); passes(n)
        with self.assertRaises(Refusal): finish(n,'REENTER_POST')
        snapshot=n.seal(); terminal=parse_terminal(snapshot['terminal'],OP,check=CHECK)
        self.assertEqual((terminal.attempts,terminal.settled,terminal.first_refusal,terminal.post_footer_attempts),(1606,1606,1606,1))
        self.assertTrue(terminal.refused); self.assertFalse(snapshot['facts']['busy'])
    def test_invalid_command_settled(self):
        m=model()
        with self.assertRaises(Refusal): m.apply(['BEGIN'])
        self.assertEqual((m.facts()['attempts'],m.facts()['settled']),(1,1))
    def test_invalid_fault_settled(self):
        m=model()
        with self.assertRaises(Refusal): m.apply(('BEGIN',), object())
        self.assertEqual(m.facts()['settled'],1)
    def test_sticky_refusal_counts_later_attempt(self):
        m=model()
        for _ in range(2):
            with self.assertRaises(Refusal): m.apply(('BEGIN',),'PRE_REFUSE')
        self.assertEqual((m.facts()['attempts'],m.facts()['first_refusal']),(2,1))
    def test_65535th_representable(self):
        m=model(); m.attempts=m.settled=65534
        with self.assertRaises(Refusal): m.apply(('BEGIN',),'PRE_REFUSE')
        self.assertEqual((m.facts()['attempts'],m.facts()['settled'],m.facts()['first_refusal']),(65535,65535,65535))
    def test_65536th_invalidates_accounting(self):
        m=model(); m.attempts=m.settled=65535
        with self.assertRaises(Refusal): m.apply(('BEGIN',))
        self.assertFalse(m.facts()['accounting_complete']); self.assertIsNone(m.facts()['first_refusal']); self.assertIsNone(m.seal()['terminal'])
        n=model(); n.attempts=n.settled=65534
        with self.assertRaises(Refusal): n.apply(('BEGIN',),'REENTER_PRE')
        self.assertEqual((n.attempts,n.settled,n.in_flight),(65535,65535,0))
        self.assertIsNone(n.first_refusal); self.assertFalse(n.accounting_complete)
        self.assertIsNone(n.seal()['terminal'])
    def test_group_reserves_footer_record(self):
        m=model(); m._out=(b'',4094,m._out[2])
        with self.assertRaises(Refusal): m.apply(('BEGIN',))
        self.assertEqual(m.facts()['records'],4094)
        n=model(); n._out=(b'x'*(2097152-512),0,n._out[2])
        with self.assertRaises(Refusal): n.apply(('BEGIN',))
        self.assertEqual(len(n.raw_prefix()),2097152-512)
    def test_footer_4096_boundary(self):
        m=model(); m.stage='FOOTER'; m._out=(b'',4095,m._out[2]); m.apply(('FINISH',))
        self.assertEqual(m.facts()['records'],4096)
    def test_encoder_exception_settles_without_commit(self):
        m=model()
        with patch('tools.local_validation.cm5.producer._encoded',side_effect=KeyboardInterrupt):
            with self.assertRaises(Refusal): m.apply(('BEGIN',))
        self.assertEqual((m.raw_prefix(),m.facts()['settled']),(b'',1))
    def test_hash_exception_settles_without_commit(self):
        m=model()
        with patch('tools.local_validation.cm5.producer._digest',side_effect=MemoryError):
            with self.assertRaises(Refusal): m.apply(('BEGIN',))
        self.assertEqual((m.raw_prefix(),m.facts()['settled']),(b'',1))
        n=model()
        with patch.object(n,'_refuse',side_effect=MemoryError):
            with self.assertRaises(MemoryError): n.apply(('BEGIN',),'PRE_REFUSE')
        self.assertFalse(n.facts()['accounting_complete']); self.assertIsNone(n.seal()['terminal'])
        late=model(); negative(late)
        with patch.object(late,'_refuse',side_effect=Refusal('untrusted')):
            with self.assertRaises(Refusal): late.apply(('BEGIN',))
        self.assertFalse(late.accounting_complete); self.assertIsNone(late.seal()['terminal'])
        sticky=model(); passes(sticky)
        with self.assertRaises(Refusal): finish(sticky,'POST_REFUSE')
        first=sticky.first_refusal
        def partial(code, ordinal):
            sticky.refused=True
            sticky.failure_code=code
            raise Refusal('untrusted after partial update')
        with patch.object(sticky,'_refuse',side_effect=partial):
            with self.assertRaises(Refusal): sticky.apply(None)
        self.assertEqual(sticky.first_refusal,first)
        self.assertFalse(sticky.accounting_complete); self.assertIsNone(sticky.seal()['terminal'])
    def test_seal_active_latches(self):
        m=model(); m.attempts=m.in_flight=1; m.busy=True
        with self.assertRaises(Refusal): m.seal()
        self.assertEqual(m.facts()['first_refusal'],1)
        # A supplied active-state seed isolates secondary seal failure after
        # an earlier refusal; it is not actual concurrency or a valid trace.
        n=model(); passes(n)
        with self.assertRaises(Refusal): finish(n,'POST_REFUSE')
        n.attempts+=1; n.in_flight=1; n.busy=True
        with patch.object(n,'_refuse',side_effect=Refusal('untrusted')):
            with self.assertRaises(Refusal): n.seal()
        self.assertFalse(n.accounting_complete)
        n.in_flight=0; n.settled=n.attempts; n.busy=False
        self.assertIsNone(n.seal()['terminal'])
    def test_empty_and_partial_have_no_terminal(self):
        for partial in (False,True):
            m=model()
            if partial: m.apply(('BEGIN',))
            self.assertIsNone(m.seal()['terminal'])
    def test_seal_is_immutable_and_repeated(self):
        m=model(); negative(m); s=m.seal(); self.assertIs(s,m.seal())
        with self.assertRaises(TypeError): s['facts']['refused']=True
        self.assertFalse(s['authenticated']); self.assertFalse(s['execution_accepted'])
        n=model(); negative(n)
        with patch('tools.local_validation.cm5.producer._encoded',side_effect=MemoryError):
            with self.assertRaises(MemoryError): n.seal()
        self.assertIsNone(n.seal()['terminal']); self.assertFalse(n.facts()['accounting_complete'])
    def test_detached_entry_does_not_mutate_snapshot(self):
        m=model(); negative(m); s=m.seal(); before=dict(s['facts'])
        with self.assertRaises(Refusal): m.apply(('BEGIN',))
        self.assertEqual(before,dict(s['facts']))
    def test_post_footer_entry_counted(self):
        m=model(); negative(m)
        with self.assertRaises(Refusal): m.apply(None)
        self.assertEqual(m.facts()['post_footer_attempts'],1); self.assertTrue(parse_terminal(m.seal()['terminal'],OP,check=CHECK).refused)
    def test_runtime_dispatch_and_constructor_refuse(self):
        from . import registry as census
        from ..cm4 import registry as target
        self.assertEqual((len(census.expected_ids()),len(census.expected_modules()),len(census.selected_ids())),(876,38,360))
        self.assertEqual((len(census.NEW_IDS),len(census.NEW_MODULE_PINS),876-360),(40,2,516))
        self.assertEqual((target.FULL_COUNT,target.SELECTED_COUNT),(836,320))
        self.assertEqual(census.roster_digest(CHECK),census.FULL_DIGEST)
        self.assertEqual(census.selection_digest(CHECK),census.SELECTION_DIGEST)
        with self.assertRaises(Refusal): dispatch_runtime()
        with self.assertRaises(Refusal): ProducerModel(OP, [], ())


