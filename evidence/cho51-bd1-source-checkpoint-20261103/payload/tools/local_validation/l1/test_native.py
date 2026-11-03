"""Pure ABI/layout and copy tests. Real native tests are native_cases.py.

No DLL is loaded by this unittest module.
"""
import unittest
from .protocol import Refusal
from .native_bridge import NativeObserver,structures,copied_path
from types import SimpleNamespace

class NativePureTests(unittest.TestCase):
    def test_layout(self):
        import ctypes
        event,image,state=structures(ctypes)
        self.assertEqual((ctypes.sizeof(event),ctypes.sizeof(image),ctypes.sizeof(state)),(2088,2064,56))
    def test_utf16_copy(self):
        import ctypes
        _,image,_=structures(ctypes); row=image()
        path='D:\\owned\\a.dll'; raw=path.encode('utf-16-le'); row.path_units=len(raw)//2
        for i in range(row.path_units): row.path[i]=int.from_bytes(raw[2*i:2*i+2],'little')
        self.assertEqual(copied_path(row),'D:/owned/a.dll')
    def test_utf16_surrogate(self):
        import ctypes
        _,image,_=structures(ctypes); row=image(); row.path_units=1; row.path[0]=0xD800
        with self.assertRaises(Refusal): copied_path(row)
    def test_overlong_copy(self):
        import ctypes
        _,image,_=structures(ctypes); row=image(); row.path_units=1024
        with self.assertRaises(Refusal): copied_path(row)
    def observer(self,states,snapshots,events):
        # Faithful scheduling fixture around production start(), no native API.
        observer=NativeObserver.__new__(NativeObserver)
        observer.closed=False;observer.started=False;observer.generation=1;observer.checkpoint=lambda:True
        observer.dll=SimpleNamespace(l1_start=lambda *args:1)
        state_iter=iter(states);snapshot_iter=iter(snapshots)
        observer.state=lambda:next(state_iter);observer.snapshot=lambda:next(snapshot_iter)
        observer.drain=lambda:list(events)
        return observer
    def stamp(self,sequence,active=0):return SimpleNamespace(produced=sequence,active_callbacks=active)
    def test_bootstrap_cut_retains_later_suffix(self):
        events=[dict(event_sequence=1),dict(event_sequence=2)]
        observer=self.observer([self.stamp(1),self.stamp(1)],[[],[]],events)
        boundary=observer.start()
        self.assertEqual(boundary['events'],events[:1]);self.assertEqual(boundary['cut_sequence'],1)
        self.assertEqual(observer.pending_events,events[1:])
    def test_bootstrap_race_retries_without_event_loss(self):
        events=[dict(event_sequence=1),dict(event_sequence=2)]
        observer=self.observer([self.stamp(0),self.stamp(1),self.stamp(2),self.stamp(2)],[[],[],[],[]],events)
        boundary=observer.start()
        self.assertEqual(boundary['events'],events);self.assertEqual(boundary['cut_sequence'],2)
    def test_bootstrap_continuous_callback_refused(self):
        observer=self.observer([self.stamp(0,1)]*6,[[]]*6,[])
        with self.assertRaises(Refusal):observer.start()
        self.assertTrue(observer.started)
