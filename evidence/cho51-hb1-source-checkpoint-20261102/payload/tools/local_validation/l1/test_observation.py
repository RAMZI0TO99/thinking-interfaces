import copy
import unittest
from .protocol import Refusal
from .observation import CollectionLedger,NativeLedger,assess_abi,ABI_SCOPE,workload_equal
from .test_support import retained,collection_fixture

class ObservationTests(unittest.TestCase):
    def test_exact_collection_117(self):
        static,sources,rows,summary=collection_fixture(); ledger=CollectionLedger(static,sources)
        for row in rows: ledger.append(row)
        self.assertEqual(ledger.finish(summary),summary['ordered_roster_sha256'])
    def test_duplicate_item(self):
        static,sources,rows,_=collection_fixture(); ledger=CollectionLedger(static,sources)
        ledger.append(rows[0]); bad=dict(rows[0],ordinal=1,collection_sequence=1)
        with self.assertRaises(Refusal): ledger.append(bad)
    def test_foreign_original_function(self):
        static,sources,rows,_=collection_fixture(); ledger=CollectionLedger(static,sources)
        with self.assertRaises(Refusal): ledger.append(dict(rows[0],original_function_name='foreign'))
    def test_parameter_identity(self):
        static,sources,rows,_=collection_fixture(); ledger=CollectionLedger(static,sources)
        for row in rows[:6]: ledger.append(row)
        with self.assertRaises(Refusal): ledger.append(dict(rows[6],parameter_id='changed'))
    def test_wrong_candidate_pin(self):
        static,sources,_,_=collection_fixture(); sources=copy.deepcopy(sources)
        sources[next(iter(sources))]['sha256']='f'*64
        with self.assertRaises(Refusal): CollectionLedger(static,sources)
    def test_reordered_v_roster(self):
        static,sources,rows,_=collection_fixture()
        ledger=CollectionLedger(static,sources,[r['nodeid'] for r in reversed(rows)])
        with self.assertRaises(Refusal): ledger.append(rows[0])
    def test_incomplete_roster(self):
        static,sources,rows,summary=collection_fixture(); ledger=CollectionLedger(static,sources)
        for row in rows[:-1]: ledger.append(row)
        with self.assertRaises(Refusal): ledger.finish(summary)
    def test_collection_nonzero_execution(self):
        static,sources,rows,summary=collection_fixture(); ledger=CollectionLedger(static,sources)
        for row in rows: ledger.append(row)
        with self.assertRaises(Refusal): ledger.finish(dict(summary,fixture_setup_calls=1))
    def test_native_transient_replay(self):
        ledger=NativeLedger(1,lambda *args:dict(retained_ref=retained('D:/fixture/a.dll'),system_role=None,requester_choice='fixture'))
        ledger.baseline([])
        row=dict(event_sequence=1,reason='load',phase='L2',base=4096,image_size=4096,
                 full_path='D:/fixture/a.dll',native_observer_generation=1,fault_flags=0)
        ledger.event(row); ledger.event(dict(row,event_sequence=2,reason='unload'))
        self.assertTrue(ledger.reconcile([[],[]])); self.assertEqual(len(ledger.events),2)
    def test_native_sequence_gap(self):
        ledger=NativeLedger(1,lambda *args:None); ledger.baseline([])
        row=dict(event_sequence=2,reason='load',phase='L2',base=1,image_size=1,full_path='D:/a.dll',native_observer_generation=1,fault_flags=0)
        with self.assertRaises(Refusal): ledger.event(row)
    def test_native_unstable_snapshot(self):
        ledger=NativeLedger(1,lambda *args:None); ledger.baseline([])
        with self.assertRaises(Refusal): ledger.reconcile([[],[dict(base=1,image_size=1,full_path='D:/a.dll')]])
    def boundary(self,rows,events):
        ledger=NativeLedger(1,lambda *args:dict(retained_ref=None,system_role='owned_fixture',requester_choice='exact injected row'))
        return ledger,dict(snapshots=[rows,copy.deepcopy(rows)],events=events,cut_sequence=len(events))
    def image(self,path='D:/fixture/a.dll'):
        return dict(base=4096,image_size=4096,full_path=path)
    def event(self,sequence,reason,path='D:/fixture/a.dll'):
        return dict(self.image(path),event_sequence=sequence,reason=reason,phase='L1',native_observer_generation=1,fault_flags=0)
    def test_bootstrap_load_already_in_snapshot(self):
        ledger,boundary=self.boundary([self.image()],[self.event(1,'load')])
        joins=ledger.establish(boundary)
        self.assertEqual(len(joins),1);self.assertEqual(ledger.sequence,2)
        self.assertTrue(ledger.reconcile(boundary['snapshots']))
    def test_bootstrap_unload_already_absent(self):
        ledger,boundary=self.boundary([],[self.event(1,'unload')]);ledger.establish(boundary)
        self.assertEqual(ledger.active,{});self.assertEqual(len(ledger.events),1)
    def test_bootstrap_transient_preserved(self):
        ledger,boundary=self.boundary([],[self.event(1,'load'),self.event(2,'unload')]);ledger.establish(boundary)
        self.assertEqual([row['reason'] for row in ledger.events],['load','unload']);self.assertEqual(ledger.active,{})
    def test_bootstrap_base_reuse_preserved(self):
        events=[self.event(1,'unload'),self.event(2,'load','D:/fixture/b.dll')]
        ledger,boundary=self.boundary([self.image('D:/fixture/b.dll')],events);ledger.establish(boundary)
        self.assertEqual(ledger.active[4096],(4096,'D:/fixture/b.dll'));self.assertEqual(ledger.sequence,3)
    def test_bootstrap_prefix_gap_refused(self):
        ledger,boundary=self.boundary([self.image()],[self.event(2,'load')])
        with self.assertRaises(Refusal):ledger.establish(boundary)
    def test_bootstrap_reverse_mismatch_refused(self):
        ledger,boundary=self.boundary([],[self.event(1,'load')])
        with self.assertRaises(Refusal):ledger.establish(boundary)
    def test_bootstrap_duplicate_snapshot_refused(self):
        ledger,boundary=self.boundary([self.image(),self.image()],[])
        with self.assertRaises(Refusal):ledger.establish(boundary)
    def test_bootstrap_wrong_generation_refused(self):
        ledger,boundary=self.boundary([self.image()],[dict(self.event(1,'load'),native_observer_generation=2)])
        with self.assertRaises(Refusal):ledger.establish(boundary)
    def test_workload_drift(self):
        left={k:[] for k in ('candidates','dependencies','resources','native','initialization','guards','pytest','environment','roster','abi')}
        self.assertTrue(workload_equal(left,copy.deepcopy(left)))
        with self.assertRaises(Refusal): workload_equal(left,dict(left,native=['changed']))
