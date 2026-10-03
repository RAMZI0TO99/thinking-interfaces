from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch
from safetensors.torch import load

from adaptation.tcpl_manifest import TCPLManifestRunner
from core.config import canonical_config_json, config_digest, load_toml
from core.provenance import SourceProvenance
from encoder.tcpl import TCPLClassifier
from evaluation.phase2_protocol import nested_episode, source_selection
from evaluation.phase2_records import envelope
from evaluation.tcpl_publication import _write_checkpoint, publish_tcpl_engineering_prediction
from scripts.audit_phase2_protocol import file_digest, read_catalog


class TCPLPublicationTests(unittest.TestCase):
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
        (self.root / 'configs/phase2').mkdir(parents=True)
        self.method_path = self.root / 'configs/phase2/tcpl_local_contract.toml'
        self.method_path.write_bytes(Path('configs/phase2/tcpl_local_contract.toml').read_bytes())
        threshold = self.root / 'configs/benchmark.toml'
        threshold.write_text('[datasets.toy]\nartifact_threshold_volts = 1.0\n')
        config = load_toml('configs/phase2/protocol.toml')
        config['datasets'] = {'toy': {'artifact_directory': 'data/toy',
                                     'classes': ['left', 'right'], 'expected_subjects': 3}}
        preprocessing = config_digest({
            'profile_identity': config['preparation']['profile_identity'],
            'threshold_config_sha256': file_digest(threshold), 'dataset': 'toy', 'threshold': 1.0,
        })
        catalogs = []
        for index in range(3):
            path = self.root / 'data/toy' / f'subject_0{index}.npz'
            np.savez(path, signals=np.full((48, 2, 17), 0.02, dtype=np.float32),
                     labels=['left', 'right'] * 24, sessions=['s'] * 48, runs=['r'] * 48,
                     trial_indices=np.arange(48), channel_names=['C3', 'C4'])
            catalog, _ = read_catalog(path, dataset='toy', classes=('left', 'right'),
                                      threshold=1.0, preprocessing_sha256=preprocessing)
            catalogs.append(catalog)
        selection = source_selection(catalogs, target='subject_02')
        self.runner = TCPLManifestRunner(
            self.root, config, tuple(catalogs), envelope('source_selection', asdict(selection)),
            TCPLClassifier(2, 2), outer_target='subject_02', channel_names=('C3', 'C4'),
        )
        manifest = nested_episode(catalogs[-1], shots=(1, 5, 10, 20),
                                  protocol_sha256=config_digest(config))
        self.episode_record = envelope('episode_manifest', manifest.payload())
        # Temporary fixtures have no Git repository; production refuses this absence.
        self.provenance = SourceProvenance('a' * 40, 'b' * 64, True)
        self.source_mock = patch('evaluation.tcpl_publication.capture_source',
                                 return_value=self.provenance)
        self.capture = self.source_mock.start()
        self.output = self.root / 'runs/phase2/tcpl_engineering_predictions'

    def tearDown(self):
        self.source_mock.stop()
        self.temp.cleanup()
        torch.random.set_rng_state(self.rng)

    def publish(self, **kwargs):
        return publish_tcpl_engineering_prediction(
            self.runner, self.episode_record, shots_per_class=1, **kwargs
        )

    def test_checkpoint_restoration_identity_and_engineering_record(self):
        result = self.publish(reported_model_seed=23)
        self.assertFalse(result.resumed)
        record = json.loads(result.record_path.read_text())
        self.assertEqual(record['kind'], 'engineering_smoke')
        payload = record['payload']
        self.assertFalse(payload['scientific_evaluation'])
        self.assertFalse(payload['checkpoint_training_history_verified'])
        self.assertFalse(payload['model_seed_verified'])
        self.assertEqual(payload['identity']['reported_model_seed'], 23)
        self.assertEqual(config_digest(payload['identity']), result.run_sha256)
        self.assertEqual(hashlib.sha256(result.checkpoint_path.read_bytes()).hexdigest(),
                         result.checkpoint_sha256)
        self.assertEqual(payload['identity']['environment_sha256'],
                         config_digest(payload['environment']))
        self.assertEqual(payload['identity']['method_config_sha256'], file_digest(self.method_path))
        restored = TCPLClassifier(2, 2).eval()
        restored.load_state_dict(load(result.checkpoint_path.read_bytes()), strict=True)
        for name, value in restored.state_dict().items():
            torch.testing.assert_close(value, self.runner._trainer.model.state_dict()[name],
                                       rtol=0, atol=0)
        expected = self.runner.predict_target(self.episode_record, shots_per_class=1)
        torch.testing.assert_close(torch.tensor(payload['logits']), expected.logits, rtol=0, atol=0)
        self.assertEqual(payload['query_trial_ids'], list(expected.query_trial_ids))
        self.assertEqual(payload['targets'], expected.targets.tolist())

    def test_verified_resume_preserves_bytes_mtime_model_modes_gradients_and_rng(self):
        model = self.runner._trainer.model
        model.head.weight.grad = torch.ones_like(model.head.weight)
        state = copy.deepcopy(model.state_dict())
        modes = {n: m.training for n, m in model.named_modules()}
        rng = torch.random.get_rng_state()
        first = self.publish()
        paths = (first.record_path, first.checkpoint_path)
        saved = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in paths}
        second = self.publish()
        self.assertTrue(second.resumed)
        self.assertEqual(first.run_sha256, second.run_sha256)
        self.assertEqual(saved, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in paths})
        for n, v in model.state_dict().items():
            torch.testing.assert_close(v, state[n], rtol=0, atol=0)
        self.assertEqual(modes, {n: m.training for n, m in model.named_modules()})
        torch.testing.assert_close(model.head.weight.grad, torch.ones_like(model.head.weight))
        torch.testing.assert_close(torch.random.get_rng_state(), rng, rtol=0, atol=0)
        self.assertFalse(self.runner._trainer._optimizer.state)

    def test_changed_checkpoint_or_run_context_produces_distinct_identity(self):
        first = self.publish()
        first_bytes = first.record_path.read_bytes()
        seed = self.publish(reported_model_seed=71)
        self.assertNotEqual(seed.run_sha256, first.run_sha256)
        self.assertEqual(seed.checkpoint_sha256, first.checkpoint_sha256)
        with torch.no_grad():
            self.runner._trainer.model.head.bias.add_(1)
        changed = self.publish()
        self.assertNotEqual(changed.run_sha256, first.run_sha256)
        self.assertNotEqual(changed.checkpoint_sha256, first.checkpoint_sha256)
        self.assertEqual(first.record_path.read_bytes(), first_bytes)

    def test_rehashed_prediction_label_and_scope_tampering_is_preserved_and_rejected(self):
        first = self.publish()
        original = first.record_path.read_bytes()
        for field in ('logits', 'targets', 'scientific_evaluation'):
            with self.subTest(field=field):
                payload = json.loads(original)['payload']
                if field == 'logits':
                    payload[field][0][0] += 1
                elif field == 'targets':
                    payload[field][0] = 1 - payload[field][0]
                else:
                    payload[field] = True
                tainted = envelope('engineering_smoke', payload)
                bad = (canonical_config_json(tainted) + '\n').encode()
                first.record_path.write_bytes(bad)
                with self.assertRaises(FileExistsError):
                    self.publish()
                self.assertEqual(first.record_path.read_bytes(), bad)
                first.record_path.write_bytes(original)

    def test_checkpoint_tampering_is_not_overwritten(self):
        first = self.publish()
        record = first.record_path.read_bytes()
        damaged = first.checkpoint_path.read_bytes() + b'changed'
        first.checkpoint_path.write_bytes(damaged)
        with self.assertRaisesRegex(FileExistsError, 'checkpoint'):
            self.publish()
        self.assertEqual(first.record_path.read_bytes(), record)
        self.assertEqual(first.checkpoint_path.read_bytes(), damaged)

    def test_interrupted_checkpoint_or_record_publication_has_no_completed_record(self):
        with (
            patch('evaluation.tcpl_publication.os.link', side_effect=OSError('interrupted')),
            self.assertRaises(OSError),
        ):
            self.publish()
        self.assertFalse(list(self.output.rglob('*.json')))
        self.assertFalse(list(self.output.rglob('*.safetensors')))
        self.assertFalse(list(self.output.rglob('.tcpl-*')))
        with (
            patch('evaluation.tcpl_publication.write_once', side_effect=OSError('interrupted')),
            self.assertRaises(OSError),
        ):
            self.publish()
        self.assertFalse(list(self.output.rglob('*.json')))
        self.assertEqual(len(list(self.output.rglob('*.safetensors'))), 1)
        result = self.publish()
        self.assertTrue(result.record_path.is_file())
        self.assertFalse(result.resumed)

    def test_unverified_git_and_context_drift_fail_before_writing(self):
        self.capture.return_value = SourceProvenance('unversioned-workspace', 'b' * 64, None)
        with self.assertRaisesRegex(ValueError, 'real Git'):
            self.publish()
        self.capture.side_effect = [
            self.provenance, replace(self.provenance, source_sha256='c' * 64)
        ]
        with self.assertRaisesRegex(ValueError, 'context changed'):
            self.publish()
        self.assertFalse(list(self.output.rglob('*.json')))
        self.assertFalse(list(self.output.rglob('*.safetensors')))

    def test_invalid_scope_inputs_and_nonfinite_checkpoint_are_rejected(self):
        for kwargs in ({'query_batch_size': True}, {'reported_model_seed': -1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.publish(**kwargs)
        self.runner._validation_subject = 'subject_00'
        with self.assertRaisesRegex(ValueError, 'outer-target'):
            self.publish()
        self.runner._validation_subject = None
        with torch.no_grad():
            self.runner._trainer.model.head.bias.fill_(float('inf'))
        with self.assertRaisesRegex(ValueError, 'nonfinite tensors'):
            self.publish()
        self.assertFalse(list(self.output.rglob('*.json')))

    def test_checkpoint_atomic_publication_and_path_boundary(self):
        path = self.output / 'checkpoints/example.safetensors'
        content = b'complete test bytes'
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda _: _write_checkpoint(path, content, self.output), range(8)))
        self.assertEqual(path.read_bytes(), content)
        self.assertFalse(list(self.output.rglob('.tcpl-*')))
        with self.assertRaises(ValueError):
            _write_checkpoint(self.output / '..' / 'escape', content, self.output)
