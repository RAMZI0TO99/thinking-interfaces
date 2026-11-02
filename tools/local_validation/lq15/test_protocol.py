"""Q protocol adversarial cases. In-memory only; no admissions are issued."""
import copy
import hashlib
import unittest
from . import protocol as p
from ..v1 import records as r


def request():
    digest = "1" * 64
    item = {"bytes": 1, "sha256": digest}
    return {"schema": "cho51_q_admission_v1", "stage": "Q",
      "operation_id": "11111111-1111-4111-8111-111111111111",
      "created_utc": "2026-10-29T00:00:00Z", "expires_utc": "2026-10-29T00:10:00Z",
      "root": "D:/Aenv/pro3", "python": "C:/Python/python.exe",
      "caller_runtime": {"path": "C:/PowerShell/pwsh.exe", "bytes": 1, "sha256": digest, "version": "7.6.5"},
      "runtime": {"root": "C:/Python", "files": {"C:/Python/python.exe": item.copy()},
      "recipe": "python.exe+root-dll+Lib-py-without-site-packages-or-pycache+DLLs-pyd-dll",
      "platform_trust": "reviewed-local-Windows-and-PowerShell-host-no-loaded-code-attestation"},
      "sources": {name: item.copy() for name in p.REQUIRED},
      "compiler": {"root":"C:/PowerShell", "files":{p:item.copy() for p in
          ('C:/PowerShell/Microsoft.CodeAnalysis.dll','C:/PowerShell/Microsoft.CodeAnalysis.CSharp.dll','C:/PowerShell/ref/System.Runtime.dll')}},
      "native_compiler": {"root":"C:/LLVM", "recipe":"clang-cc1-closed-header-lld-stdout-v1", "import_library":"C:/SDK/kernel32.lib",
          "files":{n:item.copy() for n in ('C:/LLVM/clang.exe','C:/LLVM/lld-link.exe','C:/LLVM/llvm-objdump.exe','C:/SDK/kernel32.lib')}},
      "review": {"path": "source-review.json", **item},
      "adoption": {"path": "contract-adoption.json", **item},
      "predecessor": {"path": "runs/coordination/cho51_p3_q_qualification_20261029_q4/root-qualification.json", **item},
      "bootstrap_qualification": {"path": p.bc.QUALIFICATION, **item},
      "bootstrap_controls": list(p.bc.CONTROLS),
      "limits": p.LIMITS.copy(), "modes": list(p.MODES),
      "expected_tests": ["tools.local_validation.lq15.test_protocol.ProtocolTests.test_fixture_%03d" % i for i in range(384)],
      "forbidden": p.FORBIDDEN.copy(), "scientific_admission": False}


def adoption(value):
    return {"schema": "cho51_q_contract_adoption_v2", "author": "project_root", "status": "ADOPTED_Q_ONLY",
      "created_utc": "2026-10-28T23:59:00Z", "contract_sha256": value["sources"][p.CONTRACT]["sha256"],
      "source_review_sha256": value["review"]["sha256"],
      "design_review_sha256": value["sources"][p.DESIGN_REVIEW]["sha256"],
      "supplement_sha256": value["sources"][p.SUPPLEMENT]["sha256"],
      "bootstrap_qualification_sha256": value["bootstrap_qualification"]["sha256"],
      "query_plan_sha256": value['sources']['tools/local_validation/lp15/api_query_plan.json']['sha256'], **p.FALSES}


class ProtocolTests(unittest.TestCase):
    def validate(self, value):
        return p.validate_admission(value, "D:/Aenv/pro3", "2026-10-29T00:00:10Z")

    def test_complete_window(self):
        self.validate(request())
        # Exact successor module is allowed; neighboring/wildcard identities are not.
        value = request()
        value['expected_tests'][0] = 'tools.local_validation.lplan12.test_compiler.InventoryTests.test_pages_and_no_authority'
        self.validate(value)
        resolver = ['tools.local_validation.lplan12.test_compiler.ResolverTests.test_fixture_%02d' % i for i in range(40)]
        resolver += ['tools.local_validation.lplan12.test_compiler.FrontierTests.test_fixture_%02d' % i for i in range(32)]
        resolver += ['tools.local_validation.lplan12.test_compiler.LosslessTests.test_fixture_%02d' % i for i in range(28)]
        self.assertEqual(p.qualification_cohort(resolver), 'lossless')
        probe = ['tools.local_validation.lplan12.test_compiler.SourceProbeTests.test_fixture_%02d' % i for i in range(32)]
        self.assertEqual(p.qualification_cohort(probe), 'probe')
        for bad in (probe[:-1], probe+probe[:1], probe[:-1]+resolver[:1]):
            with self.assertRaises(ValueError): p.qualification_cohort(bad)
        for bad in (resolver[:-1], resolver + resolver[:1], value['expected_tests'][:-1],
                    resolver[:-1] + [value['expected_tests'][0]]):
            with self.assertRaises(ValueError): p.qualification_cohort(bad)
        modules = p.inventory_modules(value['sources'], ('tools.local_validation.lplan12',))
        self.assertEqual([name.rsplit('.',1)[1] for name,_ in modules], ['compiler','migration'])
        for missing in ('compiler.py','migration.py','test_compiler.py'):
            sources = dict(value['sources'])
            sources.pop('tools/local_validation/lplan12/'+missing)
            sources['tools/local_validation/lplan2/'+missing] = {'bytes':1,'sha256':'1'*64}
            with self.assertRaises(ValueError):
                p.inventory_modules(sources, ('tools.local_validation.lplan12',))
        with self.assertRaises(ValueError):
            p.inventory_modules(value['sources'], ('tools.local_validation.lplan2',))
        for module in ('tools.local_validation.lplan2.test_compiler.',
                       'tools.local_validation.lplan3.test_compiler.',
                       'tools.local_validation.lplan4.test_compiler.',
                       'tools.local_validation.lplan12.test_other.',
                       'tools.local_validation.lplan12.test_compiler_extra.'):
            value = request()
            value['expected_tests'][0] = module+'InventoryTests.test_pages_and_no_authority'
            with self.assertRaises(ValueError):
                self.validate(value)
        p.window("2026-10-29T00:00:00Z", "2026-10-29T00:01:30Z", "2026-10-29T00:00:00Z")
        with self.assertRaises(ValueError):
            p.window("2026-10-29T00:00:00Z", "2026-10-29T00:01:29Z", "2026-10-29T00:00:00Z")

    def test_original_origin_not_reset_at_dispatch(self):
        with self.assertRaises(ValueError):
            p.window("2026-10-29T00:00:00Z", "2026-10-29T00:01:30Z", "2026-10-29T00:00:01Z")

    def test_closed_admission_and_wrong_stage(self):
        for key, value in (("unexpected", True), ("stage", "V"), ("scientific_admission", True),
                           ("operation_id", "11111111111141118111111111111111"), ("root", "D:/Aenv/pro3/sub")):
            item = request()
            item[key] = value
            with self.assertRaises(ValueError):
                self.validate(item)

    def test_limits_exact_types_and_no_relaxation(self):
        for key, value in (("threads", True), ("gpu_visible", 0), ("work_seconds", 61), ("startup_ram_gib", 3)):
            item = request()
            item["limits"][key] = value
            with self.assertRaises(ValueError):
                self.validate(item)

    def test_source_roster_missing_extra_or_boolean_pin(self):
        for mode in ("missing", "extra", "bool"):
            item = request()
            if mode == "missing":
                del item["sources"][p.REQUIRED[0]]
            elif mode == "extra":
                item["sources"]["outside.py"] = {"bytes": 1, "sha256": "1"*64}
            else:
                item["sources"][p.REQUIRED[0]]["bytes"] = True
            with self.assertRaises(ValueError):
                self.validate(item)

    def test_runtime_path_alias_outside_recipe(self):
        for name in ("C:/Other/x.py", "C:/Python/../x.py", "c:/Python/x.py"):
            item = request()
            item["runtime"]["files"][name] = {"bytes": 1, "sha256": "1"*64}
            with self.assertRaises(ValueError):
                self.validate(item)

    def test_runtime_executable_modes_and_effects(self):
        for key, value in (("python", "C:/Python/pythonw.exe"), ("modes", ["suite"]),
                           ("forbidden", []), ("expected_tests", ["other.test"])):
            item = request()
            item[key] = value
            with self.assertRaises(ValueError):
                self.validate(item)

    def test_duplicate_roster_and_changed_reference(self):
        item = request()
        item["expected_tests"] *= 2
        with self.assertRaises(ValueError):
            self.validate(item)
        item = request()
        item["adoption"]["path"] = "../grant.json"
        with self.assertRaises(ValueError):
            self.validate(item)

    def test_independent_review_exact_source_and_adoption_joins(self):
        item = request()
        review = {"status": "ACCEPTED_SOURCE_LQ1", "authors": ["author"], "reviewer": "reviewer", "sources": item["sources"]}
        p.validate_chain(item, review, adoption(item))
        for field, value in (("source_review_sha256", "2"*64), ("launch_authorized", True),
                             ("created_utc", "2026-10-29T00:01:00Z")):
            record = adoption(item)
            record[field] = value
            with self.assertRaises(ValueError):
                p.validate_chain(item, review, record)
        review["reviewer"] = "author"
        with self.assertRaises(ValueError):
            p.validate_chain(item, review, adoption(item))

    def test_report_omissions_failures_and_false_authority(self):
        expected = request()["expected_tests"]
        record = {"schema": "cho51_q_test_report_v1", "operation_id": "operation", "tests": expected,
          "tests_run": len(expected), "failures": 0, "errors": 0, "skipped": 0, "expected_failures": 0,
          "unexpected_successes": 0, "successful": True, "report": "ok",
          "fixture_files": 0, "fixture_bytes": 0, "fixture_largest": 0,
          "probe_observation": None, "probe_assets": None,
          "api_mapping":{'path':p.PHASE+'/api-mapping_operation.json','bytes':1,'sha256':'a'*64},
          "api_mapping_native_identity":'a'*16+':'+'b'*32, **p.FALSES}
        record['native_diagnostic']={'path':p.PHASE+'/native-diagnostic_operation.json','bytes':1,'sha256':'c'*64}
        record['native_diagnostic_native_identity']='c'*16+':'+'d'*32
        record['sharing_controls']={k:True for k in ('cooperative_read_protected','ordinary_reader_strict','capability_authentication')}
        record['sharing_test_ids']=sorted('tools.local_validation.lq15.test_native_reader.HandoffSharingTests.'+name for name in (
            'test_cooperative_read_preserves_unrelated_writer_delete_and_rename_denial',
            'test_ordinary_readers_remain_incompatible_with_live_writer',
            'test_capability_rejects_path_role_hash_and_native_identity_mismatch'))
        record['sharing_separate']=False
        record['caller_artifact_capabilities']=[{'role':role,'path':'D:/fixture/'+name,'bytes':1,'sha256':'a'*64,
            'native_identity':'a'*16+':'+'b'*32,'read_share':3} for role,name in
            (('mapping','api-mapping_operation.json'),('diagnostic','native-diagnostic_operation.json'),('helper','native-helper_operation.dll'))]
        p.validate_report(record, expected, "operation")
        for key, value in (("tests_run", True), ("skipped", 1), ("errors", 1), ("tests", []),
                           ("launch_authorized", True), ("fixture_files", 241), ("successful", False),
                           ('sharing_test_ids',[]),('sharing_separate',True)):
            changed = copy.deepcopy(record)
            changed[key] = value
            with self.assertRaises(ValueError):
                p.validate_report(changed, expected, "operation")
        resolver=['tools.local_validation.lplan12.test_compiler.ResolverTests.test_fixture_%02d'%i for i in range(40)]
        resolver+=['tools.local_validation.lplan12.test_compiler.FrontierTests.test_fixture_%02d'%i for i in range(32)]
        resolver+=['tools.local_validation.lplan12.test_compiler.LosslessTests.test_fixture_%02d'%i for i in range(28)]
        secondary=copy.deepcopy(record)
        secondary.update(tests=resolver,tests_run=100,sharing_separate=True)
        p.validate_report(secondary,resolver,'operation')
        secondary['sharing_separate']=False
        with self.assertRaises(ValueError):p.validate_report(secondary,resolver,'operation')

    def test_verified_bytes_exact_content_size_types(self):
        raw = b"fixture"
        pin = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        self.assertIs(p.verify_bytes(raw, pin), raw)
        for other in (raw + b"x", bytearray(raw), b"changed"):
            with self.assertRaises(ValueError):
                p.verify_bytes(other, pin)

    def test_nonfinite_duplicate_and_unknown_json_refuse(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":1e999}', b'{"x":NaN}'):
            with self.assertRaises(ValueError):
                r.strict_loads(raw)










