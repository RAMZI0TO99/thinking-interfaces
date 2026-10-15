"""Staged detached restoration of one immutable accepted historical publication.

Only call verify_publication inside a newly admitted detached native Job. Its
source request, claim, source result, and published artifacts retain their
original immutable bindings. The caller independently confines detached_output
to its fresh staged output outside the historical run workspace and fixture.
The frozen result schema retains the historical request and source provenance.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from docs.phase2.cho51_complete_eegnet_v2.selection import (
    MAXIMUM_WEIGHTS_BYTES, SOURCE_UPDATES, SUPPORT_UPDATES, TOTAL_UPDATES,
    _context, _history_summary, _method_config, _need, _object, _plain,
    _publication_pins, _request_sha256, _rng_snapshot, _rng_unchanged, _write,
)


def verify_publication(request, source_result, *, expected_source_result_file_sha256,
                       set_protected_inputs, detached_output):
    """Read-only detached reconstruction from the parent's external source-result pin.

The source child never calls this function. The caller carries the exact file
SHA from the accepted fresh source Job into this independently guarded process.
No optimizer, fitting call, target inference, or publication occurs here.
    """
    import torch
    from core.config import config_digest
    from core.provenance import capture_source
    from evaluation.labram_parity import state_digest
    from evaluation.phase2_cho_method_template import derive_cho_method_template
    from evaluation.phase2_cho_selected_manifest_bridge import verify_cho_selected_manifest_files
    from evaluation.phase2_cho_source_restore import (
        prepare_cho_source_restore, restore_cho_selected_source, verify_cho_selected_source_state,
    )
    from evaluation.phase2_pilot import AnchorAdapter
    from evaluation.phase2_protocol import require_digest
    from evaluation.phase2_selected_source_store import SelectedSourceStore

    rng = _rng_snapshot()
    require_digest(expected_source_result_file_sha256, 'external source-result file pin')
    plan, method_config, method_pin, fixture, initial_inputs, initial_source = _context(request)
    output = Path(detached_output)
    _need(output.is_dir() and output.resolve(strict=True) == output
          and not (output / 'detached-result.json').exists(), 'fresh detached output required')
    source_result_path = Path(request['selection_output']) / 'source-result.json'
    observed_result, source_pin = _object(source_result_path)
    _need(source_pin['file_sha256'] == expected_source_result_file_sha256
          and type(source_result) is dict and observed_result == source_result,
          'source result differs from the independently supplied physical file pin')
    _need(source_result.get('schema') == 'cho51_complete_eegnet_source_result_v1'
          and source_result.get('passed') is True
          and source_result.get('request_sha256') == _request_sha256(request)
          and source_result.get('case') == asdict(plan) and source_result.get('case_id') == plan.case_id
          and source_result.get('claim_file_sha256') == request['claim_file_sha256']
          and source_result.get('pins_sha256') == request['independent_pins_sha256']
          and source_result.get('execution_source_sha256') == request['execution_source_sha256']
          and source_result.get('method_config_sha256') == request['method_config_sha256']
          and source_result.get('method_config_file_sha256') == request['method_config_file_sha256']
          and source_result.get('fixture_source') == asdict(initial_source)
          and source_result.get('fixture_identity_sha256') == request['fixture_identity_sha256']
          and source_result.get('fixture_identity_file_sha256') == request['fixture_identity_file_sha256'],
          'actual source result request, adopted method or fixture context differs')
    _need(source_result.get('complete') is True and source_result.get('full_selector_verified') is True
          and source_result.get('public_selection_verifier_passed') is True
          and source_result.get('publication_performed') is True
          and source_result.get('actual_gradient_updates') == TOTAL_UPDATES
          and source_result.get('source_updates') == SOURCE_UPDATES
          and source_result.get('support_updates') == SUPPORT_UPDATES
          and source_result.get('fold_count') == 102 and source_result.get('final_source_subjects') == 51
          and source_result.get('engineering_only') is True
          and source_result.get('scientific_admission') is False
          and source_result.get('original_case_attempts_remaining') == 0
          and source_result.get('measured_cells') == 0
          and source_result.get('target_prediction_performed') is False,
          'source result must describe exactly one complete synthetic engineering selector')
    publication = source_result['publication']
    for key in ('manifest_sha256', 'evidence_sha256', 'model_state_sha256', 'weights_sha256'):
        require_digest(publication[key], f'source publication {key}')
    _need(publication['manifest_path'] == str(fixture.root / 'runs/phase2/selected_sources/manifests'
                / f"{publication['manifest_sha256']}.json")
          and publication['evidence_path'] == str(fixture.root / 'runs/phase2/selected_sources/evidence'
                / f"{publication['evidence_sha256']}.json")
          and publication['weights_path'] == str(fixture.root / 'runs/phase2/selected_sources/weights'
                / f"{publication['weights_sha256']}.safetensors")
          and publication['resumed'] is False and publication['weights_format'] == 'full_v1'
          and publication['evidence_format'] == 'canonical_json_v1'
          and publication['evidence_sha256'] == source_result['selection_evidence_sha256']
          and publication['model_state_sha256'] == source_result['model_state_sha256']
          and publication['selected_candidate'] == source_result['selected_candidate'],
          'source publication must use its direct canonical content-addressed paths')
    evidence_path = fixture.root / 'runs/phase2/selection_evidence' / f"{publication['evidence_sha256']}.json"
    _need(str(evidence_path) == source_result['selection_evidence_path'],
          'original selector evidence path differs from its logical pin')
    protected = False
    try:
        set_protected_inputs(fixture.protected_outer_paths, True)
        protected = True
        record, _ = _object(evidence_path)
        summary, expected_trace = _history_summary(record)
        _need(record['sha256'] == publication['evidence_sha256']
              and record['payload']['contract_sha256'] == source_result['selection_contract_sha256']
              and derive_cho_method_template(plan, record['payload']['contract'], {}) == method_config
              and summary['fitted_state_sha256'] == publication['model_state_sha256']
              and summary['selected_candidate'] == publication['selected_candidate'],
              'detached actual complete evidence differs from independent source publication pins')
        for key, value in summary.items():
            _need(source_result.get(key) == value, 'source summary differs from detached complete-history reconstruction')
        trace_path = Path(request['selection_output']) / 'optimizer-observations.json'
        trace, trace_pin = _object(trace_path)
        _need(source_result['optimizer_trace_path'] == str(trace_path)
              and trace_pin['file_sha256'] == source_result['optimizer_trace_file_sha256']
              and trace_pin['size_bytes'] == source_result['optimizer_trace_file_bytes']
              and trace.get('schema') == 'cho51_complete_eegnet_optimizer_observations_v1'
              and trace.get('actual_gradient_updates') == TOTAL_UPDATES
              and len(trace['events']) == TOTAL_UPDATES,
              'real source optimizer observation transcript differs from its external pin')
        for number, (event, phase) in enumerate(zip(trace['events'], expected_trace, strict=True), 1):
            _need(event['update'] == number and event['phase'] == list(phase)
                  and event['selected_parameters'] == 2642
                  and event['finite_selected_gradients'] is True
                  and event['finite_selected_parameters'] is True
                  and event['selected_state_sha256_before'] != event['selected_state_sha256_after'],
                  'detached source update observations differ from actual complete histories')
        prepared = prepare_cho_source_restore(
            root=fixture.root, plan=plan, method_config=method_config,
            expected_method_config_sha256=request['method_config_sha256'],
            selected_candidate=publication['selected_candidate'])
        _need(prepared.model_config_path is None and prepared.baseline_weights_path is None
              and config_digest(prepared.model_recipe) == source_result['model_recipe_sha256'],
              'independently derived EEGNet recipe must require no external baseline')
        witness = verify_cho_selected_manifest_files(
            fixture.root, Path(publication['manifest_path']),
            manifest_sha256=publication['manifest_sha256'], evidence_sha256=publication['evidence_sha256'],
            selection_contract_sha256=source_result['selection_contract_sha256'],
            selected_candidate=publication['selected_candidate'],
            protocol_config_sha256=config_digest(fixture.protocol), expected_source=initial_source,
            model_recipe_sha256=source_result['model_recipe_sha256'],
            model_state_sha256=publication['model_state_sha256'])
        actual_files = _publication_pins(publication, evidence_path)
        _need(actual_files == source_result['publication_files'],
              'source publication physical bytes or identities changed before detached restoration')
        _need(type(actual_files['weights']['size_bytes']) is int
              and 0 < actual_files['weights']['size_bytes'] <= MAXIMUM_WEIGHTS_BYTES,
              'independently pinned EEGNet full-state file must fit the fixed one-MiB bound')
        restore_limits = []

        class BoundedEEGNetStore(SelectedSourceStore):
            """Inject only the EEGNet byte ceiling into unchanged public restoration."""

            def restore(self, manifest_sha256, model, *, expected_evidence_sha256,
                        protocol_config, model_recipe,
                        maximum_weights_bytes=MAXIMUM_WEIGHTS_BYTES):
                _need(type(maximum_weights_bytes) is int
                      and 0 < maximum_weights_bytes <= MAXIMUM_WEIGHTS_BYTES,
                      'EEGNet restore requires a positive integer byte limit no greater than one MiB')
                restore_limits.append(maximum_weights_bytes)
                return super().restore(
                    manifest_sha256, model,
                    expected_evidence_sha256=expected_evidence_sha256,
                    protocol_config=protocol_config, model_recipe=model_recipe,
                    maximum_weights_bytes=maximum_weights_bytes)

        store = BoundedEEGNetStore(fixture.root)
        # The actual public tensor checker retains its unmodified six/four GiB
        # host-RAM checks and independently reconstructs the seeded full model.
        tensor_witness = verify_cho_selected_source_state(
            root=fixture.root, plan=plan, method_config=method_config,
            expected_method_config_sha256=request['method_config_sha256'],
            selected_candidate=publication['selected_candidate'],
            manifest_sha256=publication['manifest_sha256'], evidence_sha256=publication['evidence_sha256'],
            protocol_config=fixture.protocol,
            expected_model_recipe_sha256=source_result['model_recipe_sha256'],
            expected_model_state_sha256=publication['model_state_sha256'], store=store)
        restored = restore_cho_selected_source(
            root=fixture.root, plan=plan, method_config=method_config,
            expected_method_config_sha256=request['method_config_sha256'],
            selected_candidate=publication['selected_candidate'],
            manifest_sha256=publication['manifest_sha256'], evidence_sha256=publication['evidence_sha256'],
            protocol_config=fixture.protocol, catalogs=fixture.catalogs,
            selection_record=fixture.selection_record, assets={}, store=store)
        _need(restore_limits == [MAXIMUM_WEIGHTS_BYTES, MAXIMUM_WEIGHTS_BYTES],
              'both actual public restore paths must delegate with the fixed one-MiB EEGNet limit')
        model = restored.restored.model
        _need(type(restored.adapter) is AnchorAdapter and restored.adapter.method == 'eegnet'
              and restored.adapter._model is model
              and restored.selection.selected_candidate == publication['selected_candidate']
              and restored.selection.evidence_sha256 == publication['evidence_sha256']
              and restored.restored.evidence_record == record
              and restored.model_recipe == prepared.model_recipe
              and state_digest(model) == publication['model_state_sha256']
              and sum(parameter.numel() for parameter in model.parameters()) == 2642
              and all(parameter.grad is None for parameter in model.parameters()),
              'actual detached public restore must release the exact fitted full-source adapter')
        manifest, _ = _object(Path(publication['manifest_path']))
        schema = manifest['payload']['tensor_schema']
        expected_state = model.state_dict()
        _need(set(schema) == set(expected_state) and all(
            list(value.shape) == schema[name]['shape'] and str(value.dtype) == schema[name]['dtype']
            and torch.isfinite(value).all().item() for name, value in expected_state.items()),
            'every publicly restored tensor must match the complete pinned finite schema')
        _need(asdict(tensor_witness) == {
            'manifest_sha256': publication['manifest_sha256'],
            'evidence_sha256': publication['evidence_sha256'],
            'selected_candidate': publication['selected_candidate'],
            'model_recipe_sha256': source_result['model_recipe_sha256'],
            'model_state_sha256': publication['model_state_sha256'],
            'weights_sha256': publication['weights_sha256']},
            'actual public independent tensor witness differs from external source pins')
        witness.verify_stable()
        _need(_publication_pins(restored.restored.publication, evidence_path) == actual_files,
              'publication changed during detached tensor reconstruction')
        # Both public paths decode full_v1 only inside their trusted restore
        # stacks, verify every tensor's schema/finite bytes, strictly load the
        # complete state and compare its full byte digest with the external pin.
        # No second decoder is called outside those public gates.
        tensor_count = len(expected_state)
        restored_publication = _plain(asdict(restored.restored.publication))
    finally:
        if protected:
            set_protected_inputs(fixture.protected_outer_paths, False)

    _need(fixture.verify_inputs() == initial_inputs and capture_source(fixture.root) == initial_source
          and _method_config(request)[1] == method_pin and _rng_unchanged(rng),
          'detached verification changed physical inputs, source context, method pins or global RNG')
    _need(_object(source_result_path)[1] == source_pin and _object(trace_path)[1] == trace_pin,
          'external source-result or optimizer transcript changed during detached verification')
    witness.verify_stable()
    result = {
        'schema': 'cho51_complete_eegnet_detached_result_v1', 'passed': True,
        'request_sha256': _request_sha256(request), 'case': asdict(plan), 'case_id': plan.case_id,
        'claim_file_sha256': request['claim_file_sha256'],
        'pins_sha256': request['independent_pins_sha256'],
        'execution_source_sha256': request['execution_source_sha256'],
        'fixture_root': str(fixture.root), 'fixture_source': asdict(initial_source),
        'fixture_identity_sha256': initial_inputs['sha256'],
        'fixture_identity_file_sha256': fixture.identity_file_sha256,
        'method_config_sha256': request['method_config_sha256'],
        'method_config_file_sha256': request['method_config_file_sha256'],
        'source_result_path': str(source_result_path),
        'source_result_file_sha256': expected_source_result_file_sha256,
        'source_result_identity': source_pin['identity'],
        'selected_candidate': publication['selected_candidate'],
        'selection_evidence_sha256': publication['evidence_sha256'],
        'selection_contract_sha256': source_result['selection_contract_sha256'],
        'model_state_sha256': publication['model_state_sha256'],
        'model_recipe_sha256': source_result['model_recipe_sha256'],
        'publication': publication, 'publication_files': actual_files,
        'restored_publication': restored_publication,
        'publication_witness': _plain(asdict(witness)), 'tensor_witness': asdict(tensor_witness),
        'tensor_count': tensor_count, 'all_tensors_equal': True,
        'full_state_digest_matches': True,
        'tensor_equality_boundary': 'two_public_full_state_restores_and_external_full_state_digest',
        'bounded_store': {
            'schema': 'cho51_eegnet_full_state_bound_v1',
            'base_class': 'evaluation.phase2_selected_source_store.SelectedSourceStore',
            'maximum_weights_bytes': MAXIMUM_WEIGHTS_BYTES,
            'actual_weights_bytes': actual_files['weights']['size_bytes'],
            'restore_limits_bytes': restore_limits,
            'generic_restore_default_bytes': 4 * 1024**3,
            'generic_restore_default_avoided': True,
            'canonical_restore_delegated': True,
            'public_factory_store_injection': True,
        },
        'initial_lineage_reconstructed': True, 'public_restore_adapter_released': True,
        'public_selection_verifier_passed': True, 'full_selector_verified': True,
        'verified_source_gradient_updates': TOTAL_UPDATES,
        'verified_source_updates': SOURCE_UPDATES, 'verified_support_updates': SUPPORT_UPDATES,
        'verified_fold_count': 102, 'verified_final_source_subjects': 51,
        'actual_gradient_updates': 0, 'detached_tensor_verified': True,
        'all_physical_inputs_rehashed_unchanged': True, 'fixture_source_context_unchanged': True,
        'torch_numpy_python_rng_unchanged': True,
        'full_worker_verified': False, 'target_prediction_performed': False,
        'publication_performed': False, 'recorder_used': False, 'measured_cells': 0,
        'synthetic': True, 'actual_study_data_loaded': False, 'pretrained_weights_loaded': False,
        'engineering_only': True, 'scientific_admission': False,
        'original_case_attempts_remaining': 0,
    }
    _write(output / 'detached-result.json', result)
    return result
