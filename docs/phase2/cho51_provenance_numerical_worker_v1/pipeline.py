"""Reusable engineering parent entry point over the adopted complete route."""
from __future__ import annotations

from docs.phase2.cho51_provenance_numerical_worker_v1 import numerical_worker as Worker


def run_parent_pipeline(recorder, plan, *, context, route, workspace, origin_contract_path,
        origin_contract_file_sha256, factory_template, backend, verifier=Worker.verify_current_execution):
    """Compose one exact engineering episode; scientific measured execution is pending."""
    Worker.WorkerRoute._only_plan(plan)
    Worker.WorkerRoute._route_contract(route, plan, context)
    return Worker.run_worker_case(recorder, plan, context=context, route=route, workspace=workspace,
        origin_contract_path=origin_contract_path, origin_contract_file_sha256=origin_contract_file_sha256,
        factory_template=factory_template, backend=backend, verifier=verifier)


def recover_parent_pipeline(recorder, *, context, route, request_path, expected_request_sha256,
        expected_attestation_sha256, verifier=Worker.verify_current_execution):
    """Recover an existing outer intent using only externally pinned physical evidence."""
    return Worker.recover_worker_case(recorder, context=context, route=route, request_path=request_path,
        expected_request_sha256=expected_request_sha256,
        expected_attestation_sha256=expected_attestation_sha256, verifier=verifier)
