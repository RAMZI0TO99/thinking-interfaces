"""Fixed Q suite and declared transport/timeout controls; no generic command."""
import hashlib
import io
import json
import msvcrt
import os
from pathlib import Path
import sys
import time
import types
import unittest

ROOT = Path(__file__).absolute().parents[3]


def main():
    if len(sys.argv) != 15 or sys.argv[3] not in ("suite", "badframe", "stall", "native-transient", "native-overflow", "native-badreason", "native-badutf16", "native-pathbound"):
        raise ValueError("fixed Q child arguments")
    admission, digest, mode, fixture, writer, origin, qpc, freq, mapping_sha, mapping_identity, mapping_bytes, bundle_sha, bundle_identity, bundle_bytes = sys.argv[1:]
    with Path(admission).open("rb") as stream:
        raw = stream.read(8 * 1024**2 + 1)
    if len(raw) > 8 * 1024**2 or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("child admission byte mismatch")
    request = json.loads(raw)
    relative = "tools/local_validation/lq7/supervisor.py"
    with (ROOT / relative).open("rb") as stream:
        source = stream.read(1024**2 + 1)
    pin = request["sources"][relative]
    if len(source) != pin["bytes"] or hashlib.sha256(source).hexdigest() != pin["sha256"]:
        raise ValueError("child bootstrap source mismatch")
    sup = types.ModuleType("tools.local_validation.lq7.supervisor")
    sup.__file__ = str(ROOT / relative)
    sys.modules[sup.__name__] = sup
    exec(compile(source, sup.__file__, "exec"), sup.__dict__)
    sup.namespaces()
    r = sup.load_source(request, "tools.local_validation.v1.records", "tools/local_validation/v1/records.py")
    sup.load_source(request, "tools.local_validation.lp7.pe", "tools/local_validation/lp7/pe.py")
    sup.load_source(request, "tools.local_validation.lp7.api_mapping", "tools/local_validation/lp7/api_mapping.py")
    sup.load_source(request, 'tools.local_validation.lp7.bootstrap_contract', 'tools/local_validation/lp7/bootstrap_contract.py')
    p = sup.load_source(request, "tools.local_validation.lq7.protocol", "tools/local_validation/lq7/protocol.py")
    request = p.validate_admission(r.strict_loads(raw), ROOT.as_posix(), origin)
    fixture = Path(fixture)
    expected_fixture = sup.BASE / "attempts" / request["operation_id"] / "fixtures"
    if fixture != expected_fixture or not fixture.is_dir():
        raise ValueError("exact owned fixture root")
    cache = sup.BASE / "disabled-bytecode" / request["operation_id"]
    guard = sup.Guard(origin, int(qpc), int(freq), cache)
    guard.checkpoint()
    if sys.pycache_prefix != str(cache) or sys.flags.isolated != 1 or not sys.flags.no_site:
        raise ValueError("child isolated runtime")
    native=sup.load_source(request,'tools.local_validation.lq7.native_reader','tools/local_validation/lq7/native_reader.py')
    l_native=sup.load_source(request,'tools.local_validation.lq7.l_native','tools/local_validation/lq7/l_native.py')
    l_reader=native.RetainedReader(guard.checkpoint)
    l_refs=l_native.load_bundle(l_reader,sup.BASE.as_posix(),request['operation_id'],bundle_sha,bundle_identity,bundle_bytes)
    sup.restrict(request, cache, fixture, [v['path'] for v in l_refs.values()])
    handle = int(writer)
    if handle <= 0:
        raise ValueError("original result handle")
    descriptor = msvcrt.open_osfhandle(handle, os.O_WRONLY | os.O_BINARY)
    with os.fdopen(descriptor, "wb", buffering=0) as pipe:
        if mode == "stall":
            while True:
                time.sleep(.1)
        if mode == "badframe":
            pipe.write(b"\x02\x00\x00\x00{}!")
            return 0
        if mode.startswith('native-'):
            for leaf in ('protocol','observation','native_bridge','native_cases'):
                sup.load_source(request,'tools.local_validation.l1.'+leaf,'tools/local_validation/l1/'+leaf+'.py')
            result=l_native.run_case(mode.removeprefix('native-'),l_reader,l_refs,guard.checkpoint)
            l_native.validate_result(result,mode.removeprefix('native-'))
            encoded=r.canonical_bytes(result)
            packet=len(encoded).to_bytes(4,'little')+encoded
            if pipe.write(packet)!=len(packet):raise ValueError('short native result pipe write')
            pipe.flush();l_reader.close();guard.stop_watchdog.set();return 0
        sup.load_source(request, "tools.local_validation.v1.preparation", "tools/local_validation/v1/preparation.py")
        sup.load_source(request, "tools.local_validation.lq7.native_reader", "tools/local_validation/lq7/native_reader.py")
        sup.load_source(request, "tools.local_validation.q4.native_reader", "tools/local_validation/q4/native_reader.py")
        long_native = sup.load_source(request, "tools.local_validation.lp7.native_reader", "tools/local_validation/lp7/native_reader.py")
        control_native=sys.modules['tools.local_validation.lq7.native_reader']
        with control_native.RetainedReader(guard.checkpoint) as control_reader:
            mapping_path=control_reader.authorize_handoff(sup.BASE.as_posix(),request['operation_id'],'mapping',{'bytes':int(mapping_bytes),'sha256':mapping_sha},mapping_identity)
            mapping_raw=control_reader.read_small(mapping_path,max_bytes=1048576)
            descriptor=control_reader.retain(mapping_path)
            if hashlib.sha256(mapping_raw).hexdigest()!=mapping_sha or descriptor['native_identity']['volume_serial']+':'+descriptor['native_identity']['file_id']!=mapping_identity:
                raise ValueError('exact Q mapping transport')
            plan_relative='tools/local_validation/lp7/api_query_plan.json'
            plan=r.strict_loads(control_reader.read_small(ROOT/plan_relative,request['sources'][plan_relative]))
            observed=r.strict_loads(mapping_raw)
            sys.modules['tools.local_validation.lp7.api_mapping'].validate_receipt(observed,plan,request['operation_id'],observed['native_helper'],mapping_identity,request['sources'][plan_relative]['sha256'])
            diagnostic_ref=observed['native_diagnostic'];diagnostic_identity=observed['native_diagnostic_native_identity']
            diagnostic_path=control_reader.authorize_handoff(sup.BASE.as_posix(),request['operation_id'],'diagnostic',{k:diagnostic_ref[k] for k in ('bytes','sha256')},diagnostic_identity)
            diagnostic_raw=control_reader.read_small(diagnostic_path,{k:diagnostic_ref[k] for k in ('bytes','sha256')},max_bytes=1048576)
            native=control_reader.retain(diagnostic_path)['native_identity']
            r.require(native['volume_serial']+':'+native['file_id']==diagnostic_identity,'diagnostic original identity')
            diagnostic=r.strict_loads(diagnostic_raw)
            sys.modules['tools.local_validation.lp7.api_mapping'].validate_diagnostic(diagnostic,plan,request['operation_id'],observed['native_helper'],diagnostic_identity,request['sources'][plan_relative]['sha256'],True)
            r.require(diagnostic['observation']==observed['observation'] and diagnostic['native_helper_native_identity']==observed['native_helper_native_identity'],'diagnostic/mapping join')
            helper_path=control_reader.authorize_handoff(sup.BASE.as_posix(),request['operation_id'],'helper',{k:observed['native_helper'][k] for k in ('bytes','sha256')},observed['native_helper_native_identity'])
            control_reader.retain(helper_path)
            handoff_capabilities=control_reader.handoff_capabilities()
            policy_relative='tools/local_validation/lp7/native_policy.json'
            policy=r.strict_loads(control_reader.read_small(ROOT/policy_relative,request['sources'][policy_relative]))
            r.require(all(row['host'] in {p['name'] for p in policy['platform_images']} for row in observed['observation']['rows']), 'resident hosts explicitly trusted')
            control_reader.verify()
        mapping_ref={'path':p.PHASE+'/api-mapping_'+request['operation_id']+'.json','bytes':len(mapping_raw),'sha256':mapping_sha}
        sup.load_source(request, "tools.local_validation.p1.preparation", "tools/local_validation/p1/preparation.py")
        for leaf in ('bootstrap_contract','manifest','pe','protocol','supervisor'):
            sup.load_source(request, 'tools.local_validation.lp7.'+leaf, 'tools/local_validation/lp7/'+leaf+'.py')
        # Frozen Lhost1 consumes LP1 retained-reader/Guard library interfaces.
        # Load only their pinned module definitions; no LP1 main/launcher runs.
        for leaf in ('native_reader','manifest','supervisor'):
            sup.load_source(request,'tools.local_validation.lp1.'+leaf,'tools/local_validation/lp1/'+leaf+'.py')
        for package,leaves in (
            ('l1',('protocol','observation','guards','imports','collection','plan','native_bridge','child_entry','test_support')),
            ('lhost1',('authority','abi','runtime','job_adapter','transport','supervisor')),
            ('lplan1',('compiler',))):
            for leaf in leaves:
                sup.load_source(request,'tools.local_validation.'+package+'.'+leaf,'tools/local_validation/'+package+'/'+leaf+'.py')
        for name,relative in p.inventory_modules(request['sources'],sys.modules):
            sup.load_source(request,name,relative)
        modules = []
        for name in ("tools.local_validation.v1.test_foundation", "tools.local_validation.lq7.test_native_reader",
                     "tools.local_validation.lq7.test_protocol", "tools.local_validation.p1.test_preparation",
                     "tools.local_validation.lp7.test_manifest", "tools.local_validation.lp7.test_pe",
                     "tools.local_validation.lp7.test_long_paths",
                     "tools.local_validation.lp7.test_performance",
                     "tools.local_validation.lp7.test_protocol",
                     "tools.local_validation.lp7.test_bootstrap_contract",
                     "tools.local_validation.lq7.test_l_native",
                     "tools.local_validation.l1.test_protocol",
                     "tools.local_validation.l1.test_observation",
                     "tools.local_validation.l1.test_guards",
                     "tools.local_validation.l1.test_imports",
                     "tools.local_validation.l1.test_collection",
                     "tools.local_validation.l1.test_native",
                     "tools.local_validation.lhost1.test_authority",
                     "tools.local_validation.lhost1.test_transport",
                     "tools.local_validation.lplan1.test_compiler",
                     p.INVENTORY_PACKAGE+".test_compiler"):
            module = sup.load_source(request, name, name.replace(".", "/") + ".py")
            if name.endswith(("test_native_reader", "test_preparation", "test_manifest", "test_long_paths", "test_performance")):
                module.FIXTURE_ROOT = fixture
            modules.append(module)
        tests = []
        def flatten(suite):
            for test in suite:
                if isinstance(test, unittest.TestSuite):
                    flatten(test)
                else:
                    tests.append(test)
        for module in modules:
            flatten(unittest.defaultTestLoader.loadTestsFromModule(module))
        tests.sort(key=lambda test: test.id())
        if [test.id() for test in tests] != request["expected_tests"]:
            raise ValueError("Q collection differs from reviewed exact roster")
        class BoundedText(io.StringIO):
            def write(self, text):
                if self.tell() + len(text) > 32768:
                    raise ValueError("test report text cap")
                return super().write(text)
        started = []
        class Result(unittest.TextTestResult):
            def startTest(self, test):
                guard.checkpoint()
                started.append(test.id())
                super().startTest(test)
            def stopTest(self, test):
                super().stopTest(test)
                guard.checkpoint()
        report = BoundedText()
        result = unittest.TextTestRunner(stream=report, verbosity=1, resultclass=Result).run(unittest.TestSuite(tests))
        sharing_methods={
            'cooperative_read_protected':'test_cooperative_read_preserves_unrelated_writer_delete_and_rename_denial',
            'ordinary_reader_strict':'test_ordinary_readers_remain_incompatible_with_live_writer',
            'capability_authentication':'test_capability_rejects_path_role_hash_and_native_identity_mismatch'}
        sharing_controls={key: result.wasSuccessful() and
            'tools.local_validation.lq7.test_native_reader.HandoffSharingTests.'+method in started
            for key,method in sharing_methods.items()}
        guard.checkpoint()
        count = size = 0
        pending = [fixture.as_posix()]
        entries_seen = 0
        while pending:
            current = pending.pop()
            if len(current[len(fixture.as_posix()):].strip("/").split("/")) > 32:
                raise ValueError("fixture depth")
            with os.scandir(long_native.transport(current)) as entries:
                for entry in entries:
                    guard.checkpoint()
                    entries_seen += 1
                    if entries_seen > 50000:
                        raise ValueError("fixture entry cap")
                    path = current + "/" + entry.name
                    info = os.stat(long_native.transport(path), follow_symlinks=False)
                    if info.st_file_attributes & 0x440:
                        raise ValueError("fixture reparse/device")
                    if info.st_file_attributes & 0x10:
                        pending.append(path)
                        continue
                    # Existing refusal controls deliberately leave hardlinked
                    # JSON fixtures. This accounting census is not acceptance
                    # by the strict production reader; its link guards stay on.
                    if not entry.name.endswith(".json"):
                        raise ValueError("unexpected fixture file type")
                    count += 1
                    size += info.st_size
                    if count > 240 or size > 48 * 1024**2:
                        raise ValueError("fixture aggregate cap")
        payload = {"schema": "cho51_q_test_report_v1", "operation_id": request["operation_id"],
                   "tests": started, "tests_run": result.testsRun, "failures": len(result.failures),
                   "errors": len(result.errors), "skipped": len(result.skipped),
                   "expected_failures": len(result.expectedFailures), "unexpected_successes": len(result.unexpectedSuccesses),
                   "successful": result.wasSuccessful() and not result.skipped and not result.expectedFailures,
                   "report": report.getvalue(), "fixture_files": count, "fixture_bytes": size,
                   "api_mapping": mapping_ref, "api_mapping_native_identity": mapping_identity,
                   "native_diagnostic":diagnostic_ref,"native_diagnostic_native_identity":diagnostic_identity,
                   "caller_artifact_capabilities":handoff_capabilities,"sharing_controls":sharing_controls, **p.FALSES}
        encoded = r.canonical_bytes(payload)
        if len(encoded) > 1048576:
            raise ValueError("child frame cap")
        packet = len(encoded).to_bytes(4, "little") + encoded
        if pipe.write(packet) != len(packet):
            raise ValueError("short result pipe write")
        pipe.flush()
        l_reader.verify();l_reader.close()
        guard.stop_watchdog.set()
    return 0  # Parent validates all test outcomes, including retained failures.


if __name__ == "__main__":
    raise SystemExit(main())












