"""Unexecuted supplied-byte/code/collection models, never live loading tests."""
import unittest
from ..hb1 import common as c
from . import retained as r, collection, registry


def yes(): return True


def encoded(value): return c.bounded_bytes(value, 1_048_576, yes)


def manifest():
    raw = b"answer = 1\n"
    return dict(schema="cho51_cm2_retained_model_v1", modules=[
        dict(name="demo", kind="namespace", pin=None, parent=None, package_paths=[],
             phase="SOURCE_LOAD", dependencies=[], object_token="a"*64, loader_token="b"*64, parent_token=None),
        dict(name="demo.mod", kind="source", pin=dict(path="D:/model/demo/mod.py", bytes=len(raw), sha256=c.digest(raw, yes)),
             parent="demo", package_paths=[], phase="SOURCE_LOAD", dependencies=["demo"],
             object_token="c"*64, loader_token="d"*64, parent_token="a"*64)], codes=[
        dict(slot=0, module="demo.mod", parent_slot=None, qualname="<module>", token="e"*64, lines=[1])])


def parsed(value): return r.parse_manifest(encoded(value), check=yes)


def snapshot(facts):
    return encoded(dict(schema="cho51_cm2_loaded_model_v1", manifest_sha256=facts.manifest_sha256,
                        modules=[[m.name, m.object_token, m.loader_token, m.parent_token, m.path,
                                  list(m.package_paths), m.phase] for m in facts.modules],
                        codes=[[x.slot, x.token, x.module] for x in facts.codes]))


def report():
    tests=[]
    for name in registry.expected_ids():
        module, cls, method=name.rsplit(".",2)
        tests.append(dict(id=name,module=module,class_name=cls,method_name=method,source_module=module,
                          source_qualname=cls+"."+method,skipped=False,deselected=False,expected_failure=False,xfail=False))
    return dict(schema="cho51_cm2_supplied_collection_v1",complete=True,tests=tests,
                modules=[dict(module=n,bytes=b,sha256=s,loader=collection.cm1.LOADER,load_tests=False,partial=False)
                         for n,b,s in registry.expected_modules()])


class CM2RetainedTests(unittest.TestCase):
    def test_exact_supplied_bytes_and_pin(self):
        value=manifest(); facts=r.verify_bytes(encoded(value),"demo.mod",b"answer = 1\n",check=yes)
        self.assertEqual(facts.locations,((0,1),)); self.assertFalse(facts.authenticated)
        self.assertFalse(facts.execution_accepted)

    def test_changed_bytes_refuse(self):
        for raw in (b"answer = 2\n",b"answer = 1",bytearray(b"answer = 1\n")):
            with self.subTest(kind=type(raw)),self.assertRaises(c.Refusal):
                r.verify_bytes(encoded(manifest()),"demo.mod",raw,check=yes)

    def test_size_hash_and_exact_types(self):
        for key,value in (("bytes",True),("bytes",0),("sha256","g"*64),("bytes",1048577)):
            data=manifest(); data["modules"][1]["pin"][key]=value
            with self.subTest(key=key),self.assertRaises(c.Refusal): parsed(data)

    def test_closed_manifest_and_bounds(self):
        for raw in (b'{}',b'{"schema":1,"schema":1}',b'x'*1048577,encoded(manifest())[:-1]):
            with self.subTest(size=len(raw)),self.assertRaises(c.Refusal): r.parse_manifest(raw,check=yes)
        data=manifest(); data["authority"]=True
        with self.assertRaises(c.Refusal): parsed(data)

    def test_names_parents_dependencies(self):
        for key,value in (("name","demo..mod"),("parent",None),("dependencies",["unknown"]),
                          ("dependencies",["demo","demo"]),("parent_token","f"*64)):
            data=manifest(); data["modules"][1][key]=value
            with self.subTest(key=key),self.assertRaises(c.Refusal): parsed(data)
        data=manifest(); data["modules"][0]["dependencies"]=["demo.mod"]
        with self.assertRaises(c.Refusal): parsed(data)

    def test_module_kinds_and_phases(self):
        for kind in ("extension","builtin","frozen","unknown"):
            data=manifest(); data["modules"][1]["kind"]=kind
            with self.subTest(kind=kind),self.assertRaises(c.Refusal): parsed(data)
        data=manifest(); data["modules"][1]["phase"]="SELECTED_EXECUTION"
        with self.assertRaises(c.Refusal): parsed(data)

    def test_package_paths_no_fallback(self):
        data=manifest(); data["modules"][0]["package_paths"]=["D:/search"]
        with self.assertRaises(c.Refusal): parsed(data)
        data=manifest(); row=data["modules"][1]; row["kind"]="source_package"
        row["pin"]["path"]="D:/model/demo/mod/__init__.py"; row["package_paths"]=["D:/model/demo/mod"]
        self.assertEqual(parsed(data).modules[1].kind,"source_package")
        row["package_paths"]=["D:/elsewhere"]
        with self.assertRaises(c.Refusal): parsed(data)

    def test_code_owner_and_location_join(self):
        for key,value in (("module","demo"),("module","foreign"),("lines",[True]),("slot",True),
                          ("lines",[0]),("parent_slot",False)):
            data=manifest(); data["codes"][0][key]=value
            with self.subTest(key=key),self.assertRaises(c.Refusal): parsed(data)

    def test_code_graph_depth_and_cycles(self):
        data=manifest(); data["codes"]=[]
        for n in range(128):
            data["codes"].append(dict(slot=n,module="demo.mod",parent_slot=n-1 if n else None,
                                      qualname="nested",token=format(n,"064x"),lines=[1]))
        self.assertEqual(parsed(data).codes[-1].depth,128)
        data["codes"].append(dict(slot=128,module="demo.mod",parent_slot=127,qualname="too_deep",token=format(128,"064x"),lines=[1]))
        with self.assertRaises(c.Refusal): parsed(data)
        data=manifest(); data["codes"][0]["parent_slot"]=0
        with self.assertRaises(c.Refusal): parsed(data)

    def test_duplicate_code_and_locations(self):
        for mode in ("slot","line","token","limit"):
            data=manifest()
            if mode=="slot": data["codes"].append(dict(data["codes"][0]))
            if mode=="line": data["codes"][0]["lines"]=[1,1]
            if mode=="token": data["codes"].append(dict(data["codes"][0],slot=1))
            if mode=="limit": data["codes"][0]["lines"]=list(range(1,4098))
            with self.subTest(mode=mode),self.assertRaises(c.Refusal): parsed(data)
        data=manifest(); data["codes"][0]["lines"]=list(range(1,4097))
        self.assertEqual(len(parsed(data).locations),4096)
        data["codes"].append(dict(slot=1,module="demo.mod",parent_slot=None,
                                  qualname="extra",token="f"*64,lines=[1]))
        with self.assertRaises(c.Refusal): parsed(data)

    def test_loaded_token_reconciliation(self):
        raw=encoded(manifest()); facts=r.parse_manifest(raw,check=yes); snap=snapshot(facts)
        joined=r.reconcile(raw,snap,snap,check=yes)
        self.assertEqual(joined.manifest_sha256,facts.manifest_sha256)
        changed=c.strict_json(snap,1048576,yes); changed["codes"][0][0]=False
        with self.assertRaises(c.Refusal): r.reconcile(raw,snap,encoded(changed),check=yes)

    def test_before_after_drift_refuse(self):
        raw=encoded(manifest()); snap=snapshot(r.parse_manifest(raw,check=yes))
        for field in (1,2,3,4,6):
            changed=c.strict_json(snap,1048576,yes); changed["modules"][1][field]="drift"
            with self.subTest(field=field),self.assertRaises(c.Refusal): r.reconcile(raw,snap,encoded(changed),check=yes)

    def test_checkpoints_and_no_live_authority(self):
        for check in (None,lambda:1,lambda:False):
            with self.subTest(check=check),self.assertRaises(c.Refusal): r.parse_manifest(encoded(manifest()),check=check)
        facts=parsed(manifest())
        with self.assertRaises(AttributeError): facts.modules=()
        self.assertFalse(hasattr(facts,"load_module"))

    def test_complete_roster_before_projection(self):
        facts=collection.verify_collection(encoded(report()),check=yes)
        self.assertEqual((len(facts.ids),len(facts.selection)),(764,248)); self.assertFalse(facts.execution_accepted)
        for mode in ("missing","duplicate","alias","hook","pin","skip"):
            value=report()
            if mode=="missing": value["tests"].pop()
            if mode=="duplicate": value["tests"][-1]=dict(value["tests"][0])
            if mode=="alias": value["tests"][0]["source_module"]="alias"
            if mode=="hook": value["modules"][0]["load_tests"]=True
            if mode=="pin": value["modules"][0]["sha256"]="0"*64
            if mode=="skip": value["tests"][0]["skipped"]=True
            with self.subTest(mode=mode),self.assertRaises(c.Refusal): collection.verify_collection(encoded(value),check=yes)

    def test_new_methods_and_frozen_baseline(self):
        self.assertEqual(len(registry.NEW_IDS),32)
        self.assertTrue(set(registry.NEW_IDS).issubset(registry.selected_ids()))
        facts=collection.verify_collection(encoded(report()),check=yes)
        self.assertNotEqual(facts.report_sha256,facts.cm1_projection_sha256)
        self.assertNotEqual(facts.cm1_projection_sha256,facts.hb1_projection_sha256)
        self.assertEqual(len(set(facts.ids)-set(facts.selection)),516)

    def test_unavailable_runtime_refuses(self):
        with self.assertRaises(c.Refusal): r.dispatch()
        with self.assertRaises(c.Refusal): r.dispatch(parsed(manifest()),approved=True)
