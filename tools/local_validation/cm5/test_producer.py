"""Source-only supplied lifecycle cases; none executed in implementation phase."""
import unittest
from ..cm4 import registry
from ..cm4.events import verify_events
from ..cm4.terminal import parse_terminal
from .producer import ProducerModel, Refusal

OP = '11111111-1111-1111-1111-111111111111'
CHECK = lambda: True
CODES = ((1, 10),)
CASE = registry.selected_ordinals()[0]


def model(): return ProducerModel(OP, CODES)
def finish(m, fault='NONE'):
    for command in (('CLOSE_SUITE',), ('RESTORED',), ('INPUTS_VERIFIED',)): m.apply(command)
    m.apply(('FINISH',), fault)
def passes(m):
    m.apply(('BEGIN',))
    for case in registry.selected_ordinals():
        for command in (('START',case), ('CLEANUP',case), ('DURATION',case,0), ('OUTCOME',case,'PASS','NONE',()), ('END',case)):
            m.apply(command)
def negative(m, event='FAIL', kind='ASSERT', trace=((1,10),), finish_fault='NONE'):
    m.apply(('BEGIN',)); m.apply(('START', CASE)); m.apply(('OUTCOME', CASE, event, kind, trace))
    for command in (('CLEANUP', CASE), ('DURATION', CASE, 0), ('END', CASE)): m.apply(command)
    finish(m, finish_fault)
def verified(m):
    seal = m.seal()
    return verify_events(seal['raw'], OP, codes=CODES, check=CHECK), parse_terminal(seal['terminal'], OP, check=CHECK)

class ProducerTests(unittest.TestCase):
    def test_normal_all_selected_and_independent_parsers(self):
        m = model(); passes(m)
        finish(m); events, terminal = verified(m)
        self.assertEqual((events.records, events.passed, terminal.attempts), (1606,320,1605))
    def test_negative_failure_and_trace(self):
        m = model(); negative(m); events, terminal = verified(m)
        self.assertTrue(events.negative); self.assertFalse(terminal.refused)
    def test_skip_zero_trace(self):
        m = model(); negative(m,'SKIP','NONE',()); self.assertTrue(verified(m)[0].negative)
    def test_xpass_after_cleanup(self):
        m=model(); m.apply(('BEGIN',)); m.apply(('START',CASE)); m.apply(('CLEANUP',CASE)); m.apply(('DURATION',CASE,0)); m.apply(('OUTCOME',CASE,'XPASS','NONE',())); m.apply(('END',CASE)); finish(m)
        self.assertTrue(verified(m)[0].negative)
    def test_xfail_trace_after_cleanup(self):
        m=model(); m.apply(('BEGIN',)); m.apply(('START',CASE)); m.apply(('CLEANUP',CASE)); m.apply(('DURATION',CASE,0)); m.apply(('OUTCOME',CASE,'XFAIL','ASSERT',((1,10),))); m.apply(('END',CASE)); finish(m)
        self.assertTrue(verified(m)[0].negative)
    def test_subpass_closed_interval(self):
        m=model(); m.apply(('BEGIN',)); m.apply(('START',CASE)); m.apply(('SUB_ENTER',CASE,1)); m.apply(('SUB_OUTCOME',CASE,1,'SUBPASS','NONE',())); m.apply(('SUB_EXIT',CASE,1)); m.apply(('OUTCOME',CASE,'FAIL','ASSERT',((1,10),))); m.apply(('CLEANUP',CASE)); m.apply(('DURATION',CASE,0)); m.apply(('END',CASE)); finish(m)
        self.assertEqual(verified(m)[0].subcases,1)
    def test_subfail_no_fabricated_primary(self):
        m=model(); m.apply(('BEGIN',)); m.apply(('START',CASE)); m.apply(('SUB_ENTER',CASE,1)); m.apply(('SUB_OUTCOME',CASE,1,'SUBFAIL','ASSERT',((1,10),))); m.apply(('SUB_EXIT',CASE,1)); m.apply(('CLEANUP',CASE)); m.apply(('DURATION',CASE,0)); m.apply(('END',CASE)); finish(m)
        self.assertTrue(verified(m)[0].negative)
    def test_interval_rejects_parent_failure(self):
        m=model(); m.apply(('BEGIN',)); m.apply(('START',CASE)); m.apply(('SUB_ENTER',CASE,1)); m.apply(('SUB_OUTCOME',CASE,1,'SUBPASS','NONE',()))
        with self.assertRaises(Refusal): m.apply(('OUTCOME',CASE,'FAIL','ASSERT',((1,10),)))
    def test_failfast_rejects_new_case(self):
        m=model(); m.apply(('BEGIN',)); m.apply(('START',CASE)); m.apply(('OUTCOME',CASE,'FAIL','ASSERT',((1,10),))); m.apply(('CLEANUP',CASE)); m.apply(('DURATION',CASE,0)); m.apply(('END',CASE))
        with self.assertRaises(Refusal): m.apply(('START',registry.selected_ordinals()[1]))
    def test_failfast_rejects_new_subcase(self):
        m=model(); m.apply(('BEGIN',)); m.apply(('START',CASE)); m.apply(('OUTCOME',CASE,'FAIL','ASSERT',((1,10),)))
        with self.assertRaises(Refusal): m.apply(('SUB_ENTER',CASE,1))
    def test_skip_then_cleanup_failures(self):
        m=model(); m.apply(('BEGIN',)); m.apply(('START',CASE)); m.apply(('OUTCOME',CASE,'SKIP','NONE',())); m.apply(('OUTCOME',CASE,'ERROR','SYSTEM_EXIT',((1,10),))); m.apply(('CLEANUP',CASE)); m.apply(('DURATION',CASE,0)); m.apply(('END',CASE)); finish(m)
        self.assertTrue(verified(m)[0].negative)
    def test_xfail_forbids_later_failure(self):
        m=model(); m.apply(('BEGIN',)); m.apply(('START',CASE)); m.apply(('CLEANUP',CASE)); m.apply(('DURATION',CASE,0)); m.apply(('OUTCOME',CASE,'XFAIL','ASSERT',((1,10),)))
        with self.assertRaises(Refusal): m.apply(('OUTCOME',CASE,'FAIL','ASSERT',((1,10),)))
    def test_fixture_setup_negative(self):
        ids=registry.expected_ids(); owner=ids[CASE].rsplit('.',1)[0]; affected=tuple(i for i in registry.selected_ordinals() if ids[i].rsplit('.',1)[0]==owner or ids[i].rsplit('.',2)[0]==owner)
        m=ProducerModel(OP,CODES,((1,owner,'setup',affected),)); m.apply(('BEGIN',)); m.apply(('FIXTURE',1,'NONE',())); finish(m); s=m.seal()
        self.assertTrue(verify_events(s['raw'],OP,codes=CODES,fixtures=((1,owner,'setup',affected),),check=CHECK).negative)
        fixture=(2,owner,'teardown',affected); n=ProducerModel(OP,CODES,(fixture,))
        passes(n); n.apply(('FIXTURE',2,'NONE',())); finish(n)
        facts=verify_events(n.seal()['raw'],OP,codes=CODES,fixtures=(fixture,),check=CHECK)
        self.assertTrue(facts.negative); self.assertEqual(facts.passed,320)
    def test_fixture_duplicate_refused(self):
        ids=registry.expected_ids(); owner=ids[CASE].rsplit('.',1)[0]; affected=tuple(i for i in registry.selected_ordinals() if ids[i].rsplit('.',1)[0]==owner or ids[i].rsplit('.',2)[0]==owner)
        m=ProducerModel(OP,CODES,((1,owner,'setup',affected),)); m.apply(('BEGIN',)); m.apply(('FIXTURE',1,'NONE',()))
        with self.assertRaises(Refusal): m.apply(('FIXTURE',1,'NONE',()))
    def test_duration_requires_cleanup(self):
        m=model(); m.apply(('BEGIN',)); m.apply(('START',CASE))
        with self.assertRaises(Refusal): m.apply(('DURATION',CASE,0))
    def test_end_requires_outcome(self):
        m=model(); m.apply(('BEGIN',)); m.apply(('START',CASE)); m.apply(('CLEANUP',CASE)); m.apply(('DURATION',CASE,0))
        with self.assertRaises(Refusal): m.apply(('END',CASE))
    def test_invalid_trace_rejected_without_output(self):
        m=model(); m.apply(('BEGIN',)); m.apply(('START',CASE)); raw=m.raw_prefix()
        with self.assertRaises(Refusal): m.apply(('OUTCOME',CASE,'FAIL','ASSERT',((2,20),)))
        self.assertEqual(raw,m.raw_prefix())
        for pair in ((True,10),(1,10.0)):
            n=model(); n.apply(('BEGIN',)); n.apply(('START',CASE))
            with self.assertRaises(Refusal): n.apply(('OUTCOME',CASE,'FAIL','ASSERT',(pair,)))
    def test_trace_128_complete_group(self):
        m=model(); m.apply(('BEGIN',)); m.apply(('START',CASE)); before=m.facts()['records']; m.apply(('OUTCOME',CASE,'FAIL','ASSERT',((1,10),)*128))
        self.assertEqual(m.facts()['records']-before,129)
        m.apply(('CLEANUP',CASE)); m.apply(('DURATION',CASE,0)); m.apply(('END',CASE)); finish(m)
        self.assertTrue(verified(m)[0].negative)
    def test_trace_129_rejected(self):
        m=model(); m.apply(('BEGIN',)); m.apply(('START',CASE)); raw=m.raw_prefix()
        with self.assertRaises(Refusal): m.apply(('OUTCOME',CASE,'FAIL','ASSERT',((1,10),)*129))
        self.assertEqual(raw,m.raw_prefix())
    def test_wrong_selection_rejected(self):
        m=model(); m.apply(('BEGIN',))
        with self.assertRaises(Refusal): m.apply(('START',registry.selected_ordinals()[1]))


