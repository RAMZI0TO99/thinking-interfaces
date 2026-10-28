"""Fresh selected restoration and target adaptation inside one parent-owned lock."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from core.config import config_digest
from core.provenance import capture_source
from evaluation.phase2_records import envelope
from docs.phase2.cho51_provenance_numerical_worker_v2 import numerical_worker as Worker


class FactoryNumericalBackend:
    """Numerical implementation; observer and native admission remain external."""

    def __init__(self, *, route, source_fixture, method_config, protocol_config,
            input_audit, observer_snapshot, execution_scope):
        if (type(route) is not Worker.WorkerRoute.Cho51WorkerRoute or not isinstance(source_fixture, Path)
                or not all(callable(callback) for callback in (input_audit, observer_snapshot, execution_scope))):
            raise ValueError('actual adopted route and explicit native observation callbacks required')
        self.route = route
        self.source_fixture = source_fixture
        self.method_json = Worker.Factory.canonical(method_config)
        self.protocol_json = Worker.Factory.canonical(protocol_config)
        self.input_audit = input_audit
        self.observer_snapshot = observer_snapshot
        self.execution_scope = execution_scope
        self._used = False

    def __call__(self, request, request_path, request_sha256, assert_live_lock):
        from evaluation.phase2_runner import LockedCase
        if (self._used or type(request) is not Worker.NumericalWorkerRequest
                or request_path != request.workspace / 'request.json' or request_sha256 != request.sha256
                or type(getattr(assert_live_lock, '__self__', None)) is not LockedCase
                or getattr(assert_live_lock, '__func__', None) is not LockedCase._require_active):
            raise ValueError('once-only numerical backend and actual canonical live lock required')
        self._used = True
        assert_live_lock()
        session = assert_live_lock.__self__
        if session.plan != request.plan or session._recorder.output_root != request.historical_binding.recorder_root:
            raise ValueError('numerical backend capability belongs to another case/recorder')
        Worker._request_files(request)
        Worker.verify_executor_files(request)
        binding = Worker.build_current_binding(request)
        Worker.Lifecycle._write_json_once(request.workspace / 'backend-attempt.json',
            dict(schema='cho51_provenance_numerical_backend_attempt_v1', **binding,
                engineering_only=True, scientific_admission=False))
        marker_sha = Worker.Lifecycle._read(request.workspace / 'backend-attempt.json')[1][-1]
        before_observer = Worker.validate_observer(self.observer_snapshot(), zero=True)
        before_inputs = json.loads(Worker.Factory.canonical(self.input_audit()))
        historical = request.historical_binding
        current = dict(git_commit=historical.fixture_git_commit, source_sha256=historical.fixture_source_sha256,
            git_dirty=historical.fixture_git_dirty)
        Worker._exact(asdict(capture_source(self.source_fixture)), current, 'actual target-source fixture context')
        inputs = self.route.inputs_for(request.plan)
        protocol = json.loads(self.protocol_json)
        Worker._exact(inputs.protocol_config, protocol, 'backend route protocol')
        if config_digest(protocol) != request.factory_request.protocol_config_sha256:
            raise ValueError('backend protocol differs from factory request')
        method = json.loads(self.method_json)
        restore_witnesses = []

        def restore_adapter():
            assert_live_lock()
            if restore_witnesses:
                raise ValueError('exactly one provenance-aware restoration callback required')
            factory = Worker.Factory.ProvenanceRestoreFactory(request.factory_request,
                request.factory_request_path, request.factory_request.sha256, assert_live_lock)
            restored = factory.restore(method_config=method, protocol_config=protocol,
                catalogs=inputs.catalogs, selection_record=inputs.selection_record, assets=inputs.assets)
            witness = json.loads(Worker.Factory.canonical(restored.witness))
            witness['current_worker_binding'] = binding
            Worker.Lifecycle._write_json_once(request.workspace / 'restore-witness.json', witness)
            restore_witnesses.append(witness)
            assert_live_lock()
            return restored.adapter

        from docs.phase2.cho51_linear_target_route_v1.target_route import run_target_route
        Worker._exact(self.observer_snapshot(), before_observer, 'read-only target module import')
        with self.execution_scope(request, request_path, request_sha256, assert_live_lock):
            target = run_target_route(fixture_root=self.source_fixture, plan=request.plan,
                protocol_config=protocol, catalogs=inputs.catalogs, selection_record=inputs.selection_record,
                episode_record=inputs.episode_record, assets=inputs.assets, current_context=current,
                expected_current_context=current, historical_context=Worker.WorkerRoute.HISTORICAL_SOURCE,
                expected_source_state_sha256=request.factory_request.producer.model_state_sha256,
                restore_adapter=restore_adapter)
        assert_live_lock()
        if len(restore_witnesses) != 1:
            raise ValueError('fresh completed provenance-aware restoration required')
        observed = Worker.validate_observer(self.observer_snapshot())
        target['current_worker_binding'] = binding
        Worker.Lifecycle._write_json_once(request.workspace / 'target-witness.json', target)
        after_inputs = json.loads(Worker.Factory.canonical(self.input_audit()))
        Worker._exact(after_inputs, before_inputs, 'unchanged complete original input inventory')
        counts = dict(source_updates=0, restore_count=observed['factory_restore_returns'],
            support_updates=observed['numerical_calls']['sgd_step'],
            gradient_updates=observed['numerical_calls']['tensor_backward'],
            target_inference_calls=target['witnesses']['calls']['runner_prediction'],
            query_count=target['query_count'], model_constructions=observed['model_constructions'], measured_cells=0)
        Worker._counts(counts, Worker.EXPECTED_BUDGET, 'independent backend aggregate ledger')
        outputs = {filename: dict(sha256=Worker.Lifecycle._read(request.workspace / filename)[1][-1],
            bytes=(request.workspace / filename).stat().st_size)
            for filename in ('restore-witness.json', 'target-witness.json')}
        payload = dict(schema='cho51_provenance_numerical_execution_v1', **binding,
            backend_attempt_file_sha256=marker_sha, source_fixture=str(self.source_fixture),
            current_control_source=current, historical_source=Worker.WorkerRoute.HISTORICAL_SOURCE,
            current_executor_source=Worker.Factory._source(request.factory_request.executor.source_json),
            expected_numerical_budget=Worker.EXPECTED_BUDGET, current_counter_ledger=counts,
            independent_observer=observed, input_audit_before=before_inputs, input_audit_after=after_inputs,
            physical_outputs=outputs, restore_witness=restore_witnesses[0], target_route_witness=target,
            engineering_only=True, scientific_admission=False, measured_cells=0,
            native_closeout_status='pending_external_post_job')
        assert_live_lock()
        return Worker.Lifecycle._write_json_once(request.workspace / 'current-execution.json',
            envelope('engineering_smoke', payload))
