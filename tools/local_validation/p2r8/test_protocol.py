"""Pure in-memory P admission/chain qualification cases; no operational records."""

from copy import deepcopy
import unittest

from . import protocol as p
from . import api_mapping as am
from ..v1.records import Refusal

ROOT = "D:/fixture-project"
ORIGIN = "2026-10-29T10:00:00Z"


def _pin(digest="a"):
    return {"bytes": 13, "sha256": digest * 64}


def fixtures():
    """Synthetic data stay in memory and confer no real project authority."""
    def ref(path, digest):
        return {"path": path, **_pin(digest)}

    sources = {name: _pin() for name in p.REQUIRED}
    request = {"schema": "cho51_p_admission_v1", "stage": "P",
        "operation_id": "12345678-1234-4234-8234-123456789abc", "created_utc": ORIGIN,
        "expires_utc": "2026-10-29T10:05:00Z", "root": ROOT,
        "python": ROOT + "/runtime/python.exe",
        "runtime": {"root": ROOT + "/runtime", "files": {ROOT + "/runtime/python.exe": _pin()},
            "recipe": "python.exe+root-dll+Lib-py-without-site-packages-or-pycache+DLLs-pyd-dll",
            "platform_trust": "reviewed-local-Windows-and-PowerShell-host-no-loaded-code-attestation"},
        "caller_runtime": {"path": ROOT + "/caller/pwsh.exe", "version": "7.5.0", **_pin()},
        "sources": sources, "review": ref(p.PHASE + "/source-review.json", "b"),
        "adoption": ref(p.PHASE + "/contract-adoption.json", "c"),
        "qualification": ref(p.Q_PHASE + "/root-qualification.json", "d"),
        "native_helper": ref(p.Q_PHASE + "/native-helper_12345678-1234-4234-8234-123456789abc.dll", "e"),
        "map_index": ref(p.PHASE + "/pin-index.json", "f"),
        "coverage_review": ref(p.PHASE + "/coverage-review.json", "1"),
        "extra_paths": [ROOT + "/observer/input.json"], "limits": deepcopy(p.LIMITS),
        "api_mapping":ref(p.Q_PHASE+'/api-mapping_12345678-1234-4234-8234-123456789abc.json','6'),
        "forbidden": list(p.FORBIDDEN), "scientific_admission": False}
    review = {"schema": "cho51_p2_source_review_v1", "status": "ACCEPTED_SOURCE_P2",
        "sources": deepcopy(sources), "reviewer": "independent_fixture_reviewer",
        "authors": ["fixture_author"], "created_utc": ORIGIN, "findings": [],
        "checks": ["in-memory fixture only"], "limitations": ["no operational authority"]}
    adoption = {"schema": "cho51_p_contract_adoption_v1", "author": "project_root",
        "status": "ADOPTED_P_ONLY", "created_utc": ORIGIN,
        "contract_sha256": sources[p.CONTRACT]["sha256"],
        "source_review_sha256": request["review"]["sha256"],
        "design_review_sha256": sources[p.DESIGN_REVIEW]["sha256"],
        "supplement_sha256": sources[p.SUPPLEMENT]["sha256"],
        "qualification_sha256": request["qualification"]["sha256"],
        "coverage_review_sha256": request["coverage_review"]["sha256"],
        "api_mapping_sha256":request['api_mapping']['sha256'], **p.FALSES}
    qualification = {"schema": "cho51_p2q_root_qualification_v1",
        "status": "QUALIFIED_P2_Q_TESTED_SCOPE", "author": "project_root", "created_utc": ORIGIN,
        "operation_id": request["operation_id"], "source_review": ref(p.Q_PHASE + "/source-review.json", "3"),
        "actual_review": ref(p.Q_PHASE + "/actual-review.json", "2"),
        "native_helper": deepcopy(request["native_helper"]), "test_count": p.EXPECTED_Q_TESTS,
        "timestamp_controls": 8, "native_fault_controls": 2,
        "native_builder_controls": {**{key: True for key in p.BUILDER_TRUE_KEYS},
                                     "helper_identity": "a" * 16 + ":" + "b" * 32},
        "api_mapping":deepcopy(request['api_mapping']),
        "api_mapping_native_identity":'c'*16+':'+'d'*32, **p.FALSES}
    coverage = {"schema": "cho51_p2_coverage_review_v1",
        "status": "ACCEPTED_PROPOSED_P2_PHYSICAL_COVERAGE",
        "reviewer": "independent_fixture_reviewer", "authors": ["fixture_author"],
        "created_utc": ORIGIN, "findings": [], "checks": ["in-memory fixture only"],
        "limitations": ["no operational authority"],
        "pin_index": deepcopy(request["map_index"]),
        "recipe_sha256": sources["tools/local_validation/p2r8/dependency_recipe.json"]["sha256"],
        "launch_authorized": False, "scientific_admission": False}
    q_source = {**deepcopy(review), "schema": "cho51_p2q_source_review_v1",
                "status": "ACCEPTED_SOURCE_P2Q", "reviewer": "q_source_fixture_reviewer"}
    q_actual = {**deepcopy(review), "schema": "cho51_p2q_actual_review_v1",
        "status": "ACCEPTED_P2Q_TESTED_SCOPE", "reviewer": "q_actual_fixture_reviewer",
        "operation_id": qualification["operation_id"],
        "source_review_sha256": qualification["source_review"]["sha256"],
        "tests_run": p.EXPECTED_Q_TESTS, "timestamp_controls_passed": 8,
        "native_fault_controls_passed": 2, "actual_tool_exit_code": 0,
        "new_operation_owned_lifecycle_closed": True,
        "native_helper": deepcopy(qualification["native_helper"]),
        "native_builder_controls": deepcopy(qualification["native_builder_controls"])}
    q_actual['api_mapping']=deepcopy(request['api_mapping'])
    q_actual['api_mapping_native_identity']=qualification['api_mapping_native_identity']
    plan={'schema':'cho51_p8_resident_reference_plan_v1','exact_query_names':[
        'api-ms-win-core-fixture-'+str(i).zfill(2)+'.dll' for i in range(14)],
        'os_version':'10.0.26200','files':[{'path':'C:/Windows/System32/'+name,'bytes':13,
            'sha256':'a'*64,'file_version':'fixture'} for name in
            ('apisetschema.dll','kernelbase.dll','kernel32.dll','ntdll.dll','cabinet.dll','fontsub.dll','mswsock.dll')],
        'negative_query':'api-ms-win-codex-absent-l999-999-999.dll',
        'baseline_modules':am.BASELINES.copy(),'target_host_loading_authorized':False}
    diagnostic_ref=ref(p.Q_PHASE+'/native-diagnostic_'+qualification['operation_id']+'.json','7')
    diagnostic_id='e'*16+':'+'f'*32
    request['native_diagnostic']=deepcopy(diagnostic_ref)
    adoption['native_diagnostic_sha256']=diagnostic_ref['sha256']
    qualification['native_diagnostic']=deepcopy(diagnostic_ref)
    qualification['native_diagnostic_native_identity']=diagnostic_id
    q_actual['native_diagnostic']=deepcopy(diagnostic_ref)
    q_actual['native_diagnostic_native_identity']=diagnostic_id
    handles=['0000000000010000','0000000000020000','0000000000030000']
    def reference(index,role,requested,handle,path='',acquired=True,error=0):
        return {'index':index,'role':role,'requested':requested,'handle':handle,'module_path':path,
            'acquired':acquired,'released':acquired,'acquire_error':error,'release_error':0,'module_length':len(path)}
    references=[reference(i,'baseline',path.replace('/','\\'),handles[i],path) for i,path in enumerate(am.BASELINES)]
    rows=[]
    for i,name in enumerate(plan['exact_query_names']):
        path=am.BASELINES[i%3];handle=handles[i%3]
        references.append(reference(i+3,'contract',name,handle,path))
        rows.append({'name':name,'host':path.rsplit('/',1)[1],'module_path':path,'baseline_handle':handle,
            'lookup_success':True,'reference_index':i+3,'module_length':len(path)})
    references.append(reference(17,'negative',plan['negative_query'],'0000000000000000',acquired=False,error=126))
    observation={'success':True,'exception_type':None,'exception_message':None,'references':references,'rows':rows,
        'controls':{key:True for key in am.CONTROLS},'acquired_count':17,'released_count':17,
        'all_owned_references_released':True,'flags':0,'buffer_wchars':260,'small_buffer_return':1,'small_buffer_error':122}
    mapping={'schema':'cho51_q8_api_mapping_v1','operation_id':qualification['operation_id'],
        'plan_sha256':sources[am.PLAN]['sha256'],'native_helper':deepcopy(qualification['native_helper']),
        'artifact_native_identity':qualification['api_mapping_native_identity'],'os_version':plan['os_version'],
        'platform_files':deepcopy(plan['files']),'observation':observation,'native_diagnostic':diagnostic_ref,
        'native_diagnostic_native_identity':diagnostic_id,'target_modules_loaded':False,'loader_qualified':False,'scientific_admission':False}
    return request, review, adoption, qualification, coverage, q_source, q_actual, mapping, plan


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        (self.request, self.review, self.adoption, self.qualification, self.coverage,
         self.q_source, self.q_actual, self.mapping, self.plan) = fixtures()

    def validate(self, origin=ORIGIN):
        return p.validate(self.request, ROOT, origin)

    def chain(self):
        return p.validate_chain(self.request, self.review, self.adoption,
                                self.qualification, self.coverage, self.q_source, self.q_actual, self.mapping, self.plan)

    def test_exact_300_second_origin_window_and_defensive_copy(self):
        result = self.validate()
        result["extra_paths"].append(ROOT + "/other.json")
        self.assertEqual(len(self.request["extra_paths"]), 1)
        self.chain()

    def test_299_second_window_refused(self):
        self.request["expires_utc"] = "2026-10-29T10:04:59Z"
        with self.assertRaises(Refusal):
            self.validate()

    def test_original_origin_cannot_restart_clock(self):
        with self.assertRaises(Refusal):
            self.validate("2026-10-29T10:00:01Z")

    def test_sources_exact_set_and_pin_shape(self):
        original = deepcopy(self.request)
        for change in ("missing", "extra", "digest", "bool_bytes"):
            with self.subTest(change=change):
                self.request = deepcopy(original)
                if change == "missing":
                    self.request["sources"].pop(p.REQUIRED[0])
                elif change == "extra":
                    self.request["sources"]["arbitrary.json"] = _pin()
                elif change == "digest":
                    self.request["sources"][p.REQUIRED[0]]["sha256"] = "A" * 64
                else:
                    self.request["sources"][p.REQUIRED[0]]["bytes"] = True
                with self.assertRaises(Refusal):
                    self.validate()

    def test_limits_and_forbidden_effects_exact(self):
        original = deepcopy(self.request)
        for field, value in (("work_seconds", 241), ("threads", True), ("gpu_visible", 0)):
            with self.subTest(field=field):
                self.request = deepcopy(original)
                self.request["limits"][field] = value
                with self.assertRaises(Refusal):
                    self.validate()
        self.request = deepcopy(original)
        self.request["forbidden"].remove("git")
        with self.assertRaises(Refusal):
            self.validate()

    def test_phase_utc_and_false_authority(self):
        original = deepcopy(self.request)
        for field, value in (("stage", "L"), ("created_utc", "2026-10-29T10:00:00+03:00"),
                             ("scientific_admission", 0)):
            with self.subTest(field=field):
                self.request = deepcopy(original)
                self.request[field] = value
                with self.assertRaises(Refusal):
                    self.validate()

    def test_extra_paths_closed_type_spelling_and_duplicates(self):
        for value in (ROOT + "/input.json", [True], [ROOT + "/../input.json"],
                      [ROOT + "/a.json", ROOT + "/a.json"]):
            with self.subTest(value=value):
                self.request["extra_paths"] = value
                with self.assertRaises(Refusal):
                    self.validate()

    def test_exact_reference_namespace_and_qualified_binary(self):
        original = deepcopy(self.request)
        for field, path in (("review", p.Q_PHASE + "/source-review.json"),
                            ("native_helper", p.Q_PHASE + "/native-helper_fixture.exe")):
            with self.subTest(field=field):
                self.request = deepcopy(original)
                self.request[field]["path"] = path
                with self.assertRaises(Refusal):
                    self.validate()

    def test_independent_source_review_and_exact_sources(self):
        original = deepcopy(self.review)
        for change in ("self_review", "different_source", "unaccepted"):
            with self.subTest(change=change):
                self.review = deepcopy(original)
                if change == "self_review":
                    self.review["authors"].append(self.review["reviewer"])
                elif change == "different_source":
                    self.review["sources"][p.REQUIRED[0]] = _pin("2")
                else:
                    self.review["status"] = "PENDING"
                with self.assertRaises(Refusal):
                    self.chain()

    def test_adoption_all_pin_joins(self):
        original = deepcopy(self.adoption)
        for field in ("contract_sha256", "source_review_sha256", "design_review_sha256",
                      "supplement_sha256", "qualification_sha256", "coverage_review_sha256"):
            with self.subTest(field=field):
                self.adoption = deepcopy(original)
                self.adoption[field] = "9" * 64
                with self.assertRaises(Refusal):
                    self.chain()

    def test_adoption_authority_flags_exact_false(self):
        original = deepcopy(self.adoption)
        for field in p.FALSES:
            with self.subTest(field=field):
                self.adoption = deepcopy(original)
                self.adoption[field] = 0
                with self.assertRaises(Refusal):
                    self.chain()

    def test_adoption_order_and_closed_record(self):
        self.adoption["created_utc"] = "2026-10-29T10:00:01Z"
        with self.assertRaises(Refusal):
            self.chain()
        self.adoption["created_utc"] = ORIGIN
        self.adoption["unreviewed_extension"] = True
        with self.assertRaises(Refusal):
            self.chain()

    def test_qualified_binary_identity_exact(self):
        original = deepcopy(self.qualification)
        for field, value in (("path", p.Q_PHASE + "/native-helper_other.dll"),
                             ("bytes", 14), ("sha256", "7" * 64)):
            with self.subTest(field=field):
                self.qualification = deepcopy(original)
                self.qualification["native_helper"][field] = value
                with self.assertRaises(Refusal):
                    self.chain()

    def test_coverage_index_and_recipe_binding(self):
        original = deepcopy(self.coverage)
        for change in ("map_path", "map_digest", "recipe_digest"):
            with self.subTest(change=change):
                self.coverage = deepcopy(original)
                if change == "map_path":
                    self.coverage["pin_index"]["path"] = p.PHASE + "/other-index.json"
                elif change == "map_digest":
                    self.coverage["pin_index"]["sha256"] = "7" * 64
                else:
                    self.coverage["recipe_sha256"] = "7" * 64
                with self.assertRaises(Refusal):
                    self.chain()

    def test_coverage_acceptance_cannot_grant_execution(self):
        original = deepcopy(self.coverage)
        for field, value in (("status", "PENDING"), ("launch_authorized", True),
                             ("scientific_admission", 0)):
            with self.subTest(field=field):
                self.coverage = deepcopy(original)
                self.coverage[field] = value
                with self.assertRaises(Refusal):
                    self.chain()

    def test_runtime_and_extra_windows_case_aliases(self):
        original = deepcopy(self.request)
        for change in ("runtime", "extras"):
            with self.subTest(change=change):
                self.request = deepcopy(original)
                if change == "runtime":
                    self.request["runtime"]["files"][ROOT + "/runtime/PYTHON.exe"] = _pin()
                else:
                    self.request["extra_paths"] = [ROOT + "/A.json", ROOT + "/a.json"]
                with self.assertRaises(Refusal):
                    self.validate()

    def test_chain_string_authors_and_extra_fields(self):
        original = (deepcopy(self.review), deepcopy(self.qualification), deepcopy(self.coverage))
        for target, change in (("review", "authors"), ("coverage", "authors"),
                               ("review", "extra"), ("qualification", "extra"), ("coverage", "extra")):
            with self.subTest(target=target, change=change):
                self.review, self.qualification, self.coverage = deepcopy(original)
                record = getattr(self, target)
                record["authors" if change == "authors" else "unreviewed_extension"] = (
                    "fixture_author" if change == "authors" else True)
                with self.assertRaises(Refusal):
                    self.chain()

    def test_q_exact_counts_lifecycle_and_native_controls(self):
        original = deepcopy((self.qualification, self.q_actual))
        changes = (("qualification", "test_count", 1), ("qualification", "timestamp_controls", True),
            ("q_actual", "tests_run", 1), ("q_actual", "actual_tool_exit_code", False),
            ("q_actual", "new_operation_owned_lifecycle_closed", 1),
            ("q_actual", "native_fault_controls_passed", True))
        for target, field, value in changes:
            with self.subTest(target=target, field=field):
                self.qualification, self.q_actual = deepcopy(original)
                getattr(self, target)[field] = value
                with self.assertRaises(Refusal):
                    self.chain()
        self.qualification, self.q_actual = deepcopy(original)
        self.q_actual["native_builder_controls"]["loaded_same_pe_bytes"] = 1
        with self.assertRaises(Refusal):
            self.chain()

    def test_q_review_refs_source_coverage_and_hash_joins(self):
        original = deepcopy((self.qualification, self.q_source, self.q_actual))
        for change in ("source_ref", "actual_ref", "source_hash", "missing_p_source", "changed_p_source"):
            with self.subTest(change=change):
                self.qualification, self.q_source, self.q_actual = deepcopy(original)
                if change in ("source_ref", "actual_ref"):
                    field = "source_review" if change == "source_ref" else "actual_review"
                    self.qualification[field]["path"] = p.Q_PHASE + "/other-review.json"
                elif change == "source_hash":
                    self.q_actual["source_review_sha256"] = "9" * 64
                elif change == "missing_p_source":
                    self.q_source["sources"].pop(p.REQUIRED[0])
                else:
                    self.q_source["sources"][p.REQUIRED[0]] = _pin("9")
                with self.assertRaises(Refusal):
                    self.chain()
        self.qualification, self.q_source, self.q_actual = deepcopy(original)
        initial=deepcopy(self.mapping)
        for change in ('short_roster','bad_length','failed_hresult','unclosed_module','bad_os_pin','control_false','mapping_join'):
            with self.subTest(mapping_change=change):
                self.mapping=deepcopy(initial)
                if change=='short_roster':self.mapping['observation']['rows'].pop()
                elif change=='bad_length':self.mapping['observation']['rows'][0]['module_length']=True
                elif change=='failed_hresult':self.mapping['observation']['rows'][0]['lookup_success']=False
                elif change=='unclosed_module':self.mapping['observation']['references'][0]['released']=False
                elif change=='bad_os_pin':self.mapping['platform_files'][0]['sha256']='9'*64
                elif change=='control_false':self.mapping['observation']['controls']['invalid_length_refused']=False
                else:self.mapping['artifact_native_identity']='e'*16+':'+'f'*32
                with self.assertRaises(Refusal):self.chain()
        self.mapping=deepcopy(initial)
        for change in ('bad_flags','foreign_handle','lost_repeated_reference','missing_release','wrong_diagnostic'):
            with self.subTest(resident_change=change):
                self.mapping=deepcopy(initial)
                if change=='bad_flags':self.mapping['observation']['flags']=2
                elif change=='foreign_handle':self.mapping['observation']['rows'][0]['baseline_handle']='0000000000090000'
                elif change=='lost_repeated_reference':self.mapping['observation']['references'].pop(4)
                elif change=='missing_release':self.mapping['observation']['references'][4]['released']=False
                else:self.mapping['native_diagnostic']['sha256']='9'*64
                with self.assertRaises(Refusal):self.chain()
        # Failure diagnostics preserve the observed release state and original
        # exception, but cannot be accepted as a mapping even when balanced.
        failed=deepcopy(initial['observation'])
        failed['success']=False;failed['exception_type']='System.IO.IOException';failed['exception_message']='exact lookup unavailable'
        self.assertEqual(am.validate_observation(failed,self.plan,False),{})
        with self.assertRaises(Refusal):am.validate_observation(failed,self.plan,True)

    def test_q_operation_time_and_independent_actual_review(self):
        original = deepcopy((self.qualification, self.q_source, self.q_actual))
        for change in ("operation", "actual_operation", "qual_time", "actual_time", "same_reviewer", "string_authors"):
            with self.subTest(change=change):
                self.qualification, self.q_source, self.q_actual = deepcopy(original)
                if change == "operation":
                    self.qualification["operation_id"] = "22345678-1234-4234-8234-123456789abc"
                elif change == "actual_operation":
                    self.q_actual["operation_id"] = "22345678-1234-4234-8234-123456789abc"
                elif change == "qual_time":
                    self.qualification["created_utc"] = "2026-10-29T10:00:01Z"
                elif change == "actual_time":
                    self.q_actual["created_utc"] = "2026-10-29T10:00:01Z"
                elif change == "same_reviewer":
                    self.q_actual["reviewer"] = self.q_source["reviewer"]
                else:
                    self.q_source["authors"] = "fixture_author"
                with self.assertRaises(Refusal):
                    self.chain()







