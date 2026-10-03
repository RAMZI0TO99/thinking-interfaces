from __future__ import annotations

import copy
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

from adaptation.tcpl_episodic import TCPLMetaStep
from adaptation.tcpl_manifest import TCPLManifestRunner
from core.config import config_digest, load_toml
from encoder.tcpl import TCPLClassifier
from evaluation.phase2_protocol import nested_episode, source_selection
from evaluation.phase2_records import envelope
from scripts.audit_phase2_protocol import file_digest, read_catalog


class TCPLManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.threads = torch.get_num_threads()
        torch.set_num_threads(2)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.threads)

    def setUp(self):
        self.rng = torch.random.get_rng_state()
        torch.manual_seed(23)
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd() / 'tmp')
        self.root = Path(self.temp.name)
        (self.root / 'data/toy').mkdir(parents=True)
        (self.root / 'configs').mkdir()
        self.threshold_path = self.root / 'configs/benchmark.toml'
        self.threshold_path.write_text('[datasets.toy]\nartifact_threshold_volts = 1.0\n')
        self.config = load_toml('configs/phase2/protocol.toml')
        self.config['datasets'] = {'toy': {'artifact_directory': 'data/toy',
                                         'classes': ['left', 'right'], 'expected_subjects': 4}}
        self.preprocessing = config_digest({
            'profile_identity': self.config['preparation']['profile_identity'],
            'threshold_config_sha256': file_digest(self.threshold_path),
            'dataset': 'toy', 'threshold': 1.0,
        })
        self.catalogs = []
        self.arrays = {}
        for subject in ('subject_00', 'subject_01', 'subject_02', 'subject_03'):
            signals = np.arange(48 * 2 * 17, dtype=np.float32).reshape(48, 2, 17) / 10000
            signals[0] = 2.0  # Rejected trial: retained and artifact indices now differ.
            path = self.root / 'data/toy' / (subject + '.npz')
            np.savez(path, signals=signals, labels=['left', 'right'] * 24,
                     sessions=['s'] * 48, runs=['r'] * 48, trial_indices=np.arange(48),
                     channel_names=['C3', 'C4'])
            catalog, _ = read_catalog(path, dataset='toy', classes=('left', 'right'),
                                      threshold=1.0, preprocessing_sha256=self.preprocessing)
            self.catalogs.append(catalog)
            self.arrays[subject] = signals
        self.catalogs = tuple(self.catalogs)
        self.selection = source_selection(self.catalogs, target='subject_03')
        self.record = envelope('source_selection', asdict(self.selection))
        self.model = TCPLClassifier(2, 2)

    def tearDown(self):
        self.temp.cleanup()
        torch.random.set_rng_state(self.rng)

    def runner(self, **kwargs):
        return TCPLManifestRunner(
            self.root, self.config, self.catalogs, self.record, self.model,
            outer_target='subject_03', channel_names=('C3', 'C4'), **kwargs,
        )

    def episode(self, subject):
        catalog = next(c for c in self.catalogs if c.subject == subject)
        manifest = nested_episode(catalog, shots=(1, 5, 10, 20),
                                  protocol_sha256=config_digest(self.config))
        return manifest, envelope('episode_manifest', manifest.payload())

    def test_bound_tensors_use_retained_indices_and_declared_label_order(self):
        runner = self.runner()
        manifest, record = self.episode('subject_00')
        partition = manifest.partition(5)
        with patch.object(runner._trainer, 'step', return_value=TCPLMetaStep(1, 0.9, 0.1)) as step:
            result = runner.source_step('subject_00', record, shots_per_class=5)
        support, query, labels = step.call_args.args
        raw = self.arrays['subject_00']
        torch.testing.assert_close(support[0], torch.from_numpy(
            raw[np.asarray(partition.support_indices) + 1]), rtol=0, atol=0)
        torch.testing.assert_close(query[0], torch.from_numpy(
            raw[np.asarray(partition.query_indices) + 1]), rtol=0, atol=0)
        self.assertEqual(labels[0].tolist(), [manifest.catalog.classes.index(
            manifest.catalog.labels[i]) for i in partition.query_indices])
        self.assertEqual(result.query_trial_ids, tuple(manifest.catalog.trial_ids[i]
                                                      for i in partition.query_indices))
        self.assertFalse(set(result.query_trial_ids) & set(result.support_trial_ids))

    def test_source_update_and_fixed_target_prediction_use_real_helpers(self):
        runner = self.runner()
        source_state = copy.deepcopy(self.model.state_dict())
        before = copy.deepcopy(runner._trainer.model.state_dict())
        _, record = self.episode('subject_00')
        result = runner.source_step('subject_00', record, shots_per_class=1)
        self.assertTrue(np.isfinite(result.loss.total))
        self.assertTrue(any(not torch.equal(v, before[n])
                            for n, v in runner._trainer.model.state_dict().items()))
        trained = copy.deepcopy(runner._trainer.model.state_dict())
        manifest, record = self.episode('subject_03')
        first = runner.predict_target(record, shots_per_class=1, query_batch_size=2)
        second = runner.predict_target(record, shots_per_class=20, query_batch_size=3)
        self.assertEqual(first.query_trial_ids, second.query_trial_ids)
        self.assertEqual(first.logits.shape, (7, 2))
        self.assertEqual(first.episode_sha256, manifest.sha256)
        self.assertEqual(first.role, 'outer_target')
        for n, v in self.model.state_dict().items():
            torch.testing.assert_close(v, source_state[n], rtol=0, atol=0)
        for n, v in runner._trainer.model.state_dict().items():
            torch.testing.assert_close(v, trained[n], rtol=0, atol=0)

    def test_outer_and_inner_held_out_subjects_rejected_before_execution(self):
        runner = self.runner(validation_subject='subject_01')
        self.assertEqual(runner.training_subjects, ('subject_00', 'subject_02'))
        with patch.object(runner._trainer, 'step') as step, patch(
            'adaptation.tcpl_manifest.TCPLTargetSession'
        ) as target:
            for subject in ('subject_01', 'subject_03', 'unknown'):
                with self.subTest(subject=subject), self.assertRaises(ValueError):
                    runner.source_step(subject, {}, shots_per_class=1)
            with self.assertRaises(ValueError):
                runner.predict_target({}, shots_per_class=1)
            step.assert_not_called()
            target.assert_not_called()
        _, validation = self.episode('subject_01')
        self.assertEqual(runner.predict_validation(validation, shots_per_class=1).role,
                         'inner_validation')
        with self.assertRaises(ValueError):
            self.runner().predict_validation(validation, shots_per_class=1)
        with self.assertRaises(ValueError):
            self.runner(validation_subject='subject_03')

    def test_rehashed_selection_tampering_fails_before_trainer_creation(self):
        changed = copy.deepcopy(self.record['payload'])
        changed['source_subjects'].append('subject_03')
        with patch('adaptation.tcpl_manifest.TCPLSourceTrainer') as trainer:
            with self.assertRaisesRegex(ValueError, 'selection record'):
                TCPLManifestRunner(self.root, self.config, self.catalogs,
                                   envelope('source_selection', changed), self.model,
                                   outer_target='subject_03', channel_names=('C3', 'C4'))
            trainer.assert_not_called()

    def test_rehashed_partition_and_wrong_subject_records_fail_before_step(self):
        runner = self.runner()
        _, record = self.episode('subject_00')
        payload = copy.deepcopy(record['payload'])
        payload['partitions'][0]['support_indices'][0] = 40
        altered = envelope('episode_manifest', payload)
        _, other = self.episode('subject_01')
        with patch.object(runner._trainer, 'step') as step:
            for candidate in (altered, other):
                with self.subTest(record=candidate['sha256']), self.assertRaises(ValueError):
                    runner.source_step('subject_00', candidate, shots_per_class=1)
            step.assert_not_called()

    def test_artifact_and_threshold_edits_fail_before_execution(self):
        runner = self.runner()
        _, record = self.episode('subject_00')
        path = self.root / 'data/toy/subject_00.npz'
        original = path.read_bytes()
        with patch.object(runner._trainer, 'step') as step:
            path.write_bytes(original + b'changed')
            with self.assertRaisesRegex(ValueError, 'artifact bytes'):
                runner.source_step('subject_00', record, shots_per_class=1)
            path.write_bytes(original)
            self.threshold_path.write_text('[datasets.toy]\nartifact_threshold_volts = 2.0\n')
            with self.assertRaisesRegex(ValueError, 'threshold configuration changed'):
                runner.source_step('subject_00', record, shots_per_class=1)
            step.assert_not_called()

    def test_final_artifact_hash_is_checked_before_step(self):
        runner = self.runner()
        _, record = self.episode('subject_00')
        calls = 0

        def digest(path):
            nonlocal calls
            if path.suffix == '.npz':
                calls += 1
                if calls == 2:
                    return '0' * 64
            return file_digest(path)

        with patch('adaptation.tcpl_manifest.file_digest', side_effect=digest), patch.object(
            runner._trainer, 'step'
        ) as step:
            with self.assertRaisesRegex(ValueError, 'changed while binding'):
                runner.source_step('subject_00', record, shots_per_class=1)
            step.assert_not_called()

    def test_catalog_label_forgery_and_channel_order_are_detected(self):
        original = self.catalogs[0]
        changed = replace(original, labels=original.labels[1::-1] + original.labels[2:])
        catalogs = (changed,) + self.catalogs[1:]
        selection = source_selection(catalogs, target='subject_03')
        runner = TCPLManifestRunner(
            self.root, self.config, catalogs, envelope('source_selection', asdict(selection)),
            self.model, outer_target='subject_03', channel_names=('C3', 'C4'),
        )
        manifest = nested_episode(changed, shots=(1, 5, 10, 20),
                                  protocol_sha256=config_digest(self.config))
        with patch.object(runner._trainer, 'step') as step:
            with self.assertRaisesRegex(ValueError, 'identities/labels/montage'):
                runner.source_step('subject_00', envelope('episode_manifest', manifest.payload()),
                                   shots_per_class=1)
            step.assert_not_called()
        runner = TCPLManifestRunner(self.root, self.config, self.catalogs, self.record, self.model,
                                    outer_target='subject_03', channel_names=('C4', 'C3'))
        _, record = self.episode('subject_00')
        with self.assertRaisesRegex(ValueError, 'identities/labels/montage'):
            runner.source_step('subject_00', record, shots_per_class=1)

    def test_protocol_and_complete_cohort_are_bound(self):
        changed = copy.deepcopy(self.config)
        changed['datasets']['toy']['expected_subjects'] = 3
        with self.assertRaisesRegex(ValueError, 'cohort/count/classes'):
            TCPLManifestRunner(self.root, changed, self.catalogs, self.record, self.model,
                               outer_target='subject_03', channel_names=('C3', 'C4'))
        changed = copy.deepcopy(self.config)
        changed['protocol']['model_seeds'] = [99]
        runner = TCPLManifestRunner(self.root, changed, self.catalogs, self.record, self.model,
                                    outer_target='subject_03', channel_names=('C3', 'C4'))
        _, record = self.episode('subject_00')
        with self.assertRaisesRegex(ValueError, 'episode record'):
            runner.source_step('subject_00', record, shots_per_class=1)
        with self.assertRaises(ValueError):
            self.runner().source_step('subject_00', record, shots_per_class=2)
