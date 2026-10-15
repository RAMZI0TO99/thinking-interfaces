"""Staged selector with a typed canonical fit-roster check.

The accepted continuation's incomplete branch is preserved in its frozen file.
This separately versioned class checks the raw canonical tuple roster as a list
before the final evidence envelope performs its normal JSON conversion. Its
numerical final branch is qualified only by a successful fresh native final Job.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from fractions import Fraction
import json

from adaptation.labram_source import BCILaBraMSourceSelector, SelectedLaBraM
from core.config import canonical_config_json, config_digest
from evaluation.labram_parity import state_digest

from docs.phase2.cho51_linear_continuation_v1.contract import require_complete_folds


class StagedLinearSourceSelector(BCILaBraMSourceSelector):
    """Inherited public folds and an independently authenticated fresh final fit."""

    def admit_complete_scope(self) -> str:
        """Check the unchanged logical5,253-step contract without fitting."""
        if self.contract.get('method') != 'labram_linear' or self.contract.get('maximum_gradient_steps') != 5253:
            raise ValueError('the unchanged complete linear selector declaration is required')
        self._admit(5253)
        return config_digest(self.contract)

    def complete_final_fit(
        self, records, method_config, *, input_identity_sha256: str,
        template_state_sha256: str, initial_state_sha256: str,
        lineage_recipe_sha256: str, verify_origins: Callable,
    ) -> SelectedLaBraM:
        """Gate all102 raw folds and their native origins before a fresh fit.

        The required trusted capability authenticates immutable raw records and
        native execution receipts against independent caller pins. Detached
        snapshots and repeated validation prevent callback input substitution.
        Pure complete-roster metadata alone never grants fitting authority.
        """
        records_snapshot = json.loads(json.dumps(
            records, allow_nan=False, sort_keys=True, separators=(',', ':')))
        method_snapshot = json.loads(canonical_config_json(method_config))
        metadata = require_complete_folds(
            records_snapshot, method_snapshot, input_identity_sha256=input_identity_sha256,
            template_state_sha256=template_state_sha256,
            initial_state_sha256=initial_state_sha256,
            lineage_recipe_sha256=lineage_recipe_sha256)
        if not callable(verify_origins):
            raise ValueError('an independently verified complete origin-chain capability is required')
        if (metadata['contract_sha256'] != config_digest(self.contract)
                or self.contract.get('method') != 'labram_linear'
                or self.contract.get('maximum_gradient_steps') != 5253
                or state_digest(self._initial) != initial_state_sha256):
            raise ValueError('staged folds and the fresh selector initialization differ')
        preserved_sha256 = config_digest({
            'records': records_snapshot, 'method': method_snapshot, 'metadata': metadata})
        receipt = verify_origins(json.loads(json.dumps(
                                    records_snapshot, allow_nan=False, sort_keys=True, separators=(',', ':'))),
                                 json.loads(canonical_config_json(metadata)))
        if config_digest({'records': records_snapshot, 'method': method_snapshot,
                          'metadata': metadata}) != preserved_sha256:
            raise ValueError('staged inputs changed across independent origin verification')
        repeated = require_complete_folds(
            records_snapshot, method_snapshot, input_identity_sha256=input_identity_sha256,
            template_state_sha256=template_state_sha256,
            initial_state_sha256=initial_state_sha256,
            lineage_recipe_sha256=lineage_recipe_sha256)
        if config_digest(repeated) != config_digest(metadata):
            raise ValueError('complete fold metadata changed across origin verification')
        required = {
            'schema': 'cho51_linear_complete_native_origins_v1', 'passed': True,
            'complete_manifest_sha256': metadata['sha256'],
            'contract_sha256': metadata['contract_sha256'], 'raw_fold_count': 102,
            'all_native_receipts_verified': True,
            'record_sha256': metadata['record_sha256'],
        }
        if (not isinstance(receipt, Mapping) or set(receipt) != set(required)
                or config_digest(receipt) != config_digest(required)):
            raise ValueError('independent complete native origin-chain receipt differs')
        self._admit(5253)
        winner_name = metadata['winner_candidate']
        winner = next(candidate for candidate in self._candidates if candidate.name == winner_name)
        if state_digest(self._initial) != initial_state_sha256:
            raise ValueError('fresh final-fit initialization changed before fitting')
        model, fit = self._fit(winner, None)
        if (fit['initial_state_sha256'] != initial_state_sha256
                or fit['validation_subject'] is not None
                or list(fit['training_subjects']) != self.contract['selection']['source_subjects']
                or len(fit['steps']) != 51):
            raise ValueError('fresh all-51-source final fit differs from the staged declaration')
        by_pair = {
            (record['payload']['folds'][0]['candidate'],
             record['payload']['folds'][0]['validation_subject']): record['payload']['folds'][0]
            for record in records_snapshot
        }
        folds = [by_pair[(row['candidate'], row['validation_subject'])]
                 for row in metadata['full_roster']]
        scores = []
        for candidate in self._candidates:
            values = [Fraction(*fold['balanced_accuracy']) for fold in folds
                      if fold['candidate'] == candidate.name]
            score = sum(values, Fraction()) / 51
            scores.append({'candidate': candidate.name,
                           'mean_balanced_accuracy': [score.numerator, score.denominator]})
        evidence = self._evidence({
            'complete': True, 'folds': folds, 'selected_candidate': winner.name,
            'scores': scores, 'final_source_fit': fit,
            'outer_target_predictions_performed': False})
        return SelectedLaBraM(model, evidence)
