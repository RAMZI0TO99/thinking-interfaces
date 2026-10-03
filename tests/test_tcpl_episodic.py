from __future__ import annotations

import copy
import math
import unittest

import torch

from adaptation.tcpl_episodic import (
    TCPLSourceTrainer,
    TCPLTargetSession,
    tcpl_meta_episode_loss,
)
from encoder.tcpl import TCPLClassifier


class TCPLEpisodicTests(unittest.TestCase):
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
        self.source = TCPLClassifier(3, 2).double().eval()
        self.support = torch.randn(2, 4, 3, 17, dtype=torch.float64)
        self.queries = torch.randn(2, 3, 3, 19, dtype=torch.float64)
        self.targets = torch.tensor([[0, 1, 0], [1, 1, 0]])

    def tearDown(self):
        torch.random.set_rng_state(self.rng)

    def assert_state_equal(self, model, state):
        self.assertEqual(set(model.state_dict()), set(state))
        for name, value in model.state_dict().items():
            torch.testing.assert_close(value, state[name], rtol=0, atol=0)

    def test_loss_matches_episode_formula_and_counts_penalty_once(self):
        weight = 0.003
        result = tcpl_meta_episode_loss(
            self.source, self.support, self.queries, self.targets, prompt_l2_weight=weight
        )
        # Independent scalar formula, deliberately not cross_entropy/reduction=mean.
        ce, penalty = [], []
        for e in range(2):
            terms = []
            for q in range(3):
                row = result.logits[e, q].detach()
                terms.append(float(torch.logsumexp(row, dim=0) - row[self.targets[e, q]]))
            ce.append(sum(terms) / 3)
            penalty.append(weight * sum(float(v) ** 2 for v in result.prompts[e].detach().ravel()))
        self.assertAlmostEqual(float(result.query_cross_entropy.detach()), sum(ce) / 2, places=12)
        self.assertAlmostEqual(float(result.prompt_penalty.detach()), sum(penalty) / 2, places=12)
        self.assertAlmostEqual(
            float(result.total.detach()), (sum(ce) + sum(penalty)) / 2, places=12
        )
        repeated = tcpl_meta_episode_loss(
            self.source, self.support, self.queries.repeat(1, 2, 1, 1),
            self.targets.repeat(1, 2), prompt_l2_weight=weight,
        )
        torch.testing.assert_close(repeated.total, result.total, rtol=1e-12, atol=1e-12)
        self.assertGreater(float(result.prompt_penalty.detach()), 0)
        # Incorrect coordinate-mean or per-query penalty gives a different objective.
        self.assertNotAlmostEqual(float(result.total.detach()), sum(ce) / 2 + sum(penalty), 8)
        self.assertNotAlmostEqual(
            float(result.total.detach()), sum(ce) / 2 + sum(penalty) / (2 * 640), 8
        )

    def test_loss_preserves_modes_and_weights_and_query_gradients_reach_support(self):
        state = copy.deepcopy(self.source.state_dict())
        self.source.transformer[0].train()
        modes = {n: m.training for n, m in self.source.named_modules()}
        self.support.requires_grad_()
        result = tcpl_meta_episode_loss(
            self.source, self.support, self.queries, self.targets, prompt_l2_weight=0
        )
        result.prompts.retain_grad()
        result.total.backward()
        self.assertEqual(float(result.prompt_penalty.detach()), 0)
        self.assertGreater(result.prompts.grad.abs().sum().item(), 0)
        self.assertGreater(self.support.grad.abs().sum().item(), 0)
        self.assert_state_equal(self.source, state)
        self.assertEqual(modes, {n: m.training for n, m in self.source.named_modules()})

    def test_trainer_owns_clone_optimizer_and_persistent_moments(self):
        self.source.head.bias.requires_grad_(False)
        self.source.head.weight.grad = torch.ones_like(self.source.head.weight)
        state = copy.deepcopy(self.source.state_dict())
        flags = {n: p.requires_grad for n, p in self.source.named_parameters()}
        trainer = TCPLSourceTrainer(self.source)
        owned = {id(p) for p in trainer.model.parameters()}
        optimized = [p for group in trainer._optimizer.param_groups for p in group['params']]
        self.assertEqual(len(optimized), len(owned))
        self.assertEqual({id(p) for p in optimized}, owned)
        self.assertTrue(owned.isdisjoint({id(p) for p in self.source.parameters()}))
        for name, p in trainer.model.named_parameters():
            self.assertNotEqual(p.data_ptr(), dict(self.source.named_parameters())[name].data_ptr())
        self.support.requires_grad_()
        self.queries.requires_grad_()
        metrics = trainer.step(self.support, self.queries, self.targets)
        self.assertTrue(math.isfinite(metrics.total))
        self.assertAlmostEqual(metrics.total, metrics.query_cross_entropy + metrics.prompt_penalty)
        trainer.step(self.support, self.queries, self.targets)
        self.assertTrue(all(float(s['step']) == 2 for s in trainer._optimizer.state.values()))
        self.assertEqual(len(trainer._optimizer.state), len(owned))
        for prefix in ('tcn', 'support_prompt.encoder', 'support_prompt.generator',
                       'transformer.0', 'transformer.1', 'transformer.2', 'transformer.3', 'head'):
            self.assertTrue(any(
                not torch.equal(v, state[n]) for n, v in trainer.model.state_dict().items()
                if n.startswith(prefix + '.')
            ), prefix)
        self.assertTrue(all(p.grad is None and p.requires_grad for p in trainer.model.parameters()))
        self.assertTrue(all(m.training for m in trainer.model.modules()))
        self.assertIsNone(self.support.grad)
        self.assertIsNone(self.queries.grad)
        self.assert_state_equal(self.source, state)
        self.assertFalse(self.source.training)
        self.assertEqual(flags, {n: p.requires_grad for n, p in self.source.named_parameters()})
        torch.testing.assert_close(self.source.head.weight.grad,
                                   torch.ones_like(self.source.head.weight), rtol=0, atol=0)

    def test_fresh_trainers_reset_and_match_with_same_dropout_rng(self):
        first, second = TCPLSourceTrainer(self.source), TCPLSourceTrainer(self.source)
        self.assertIsNot(first._optimizer, second._optimizer)
        torch.manual_seed(71)
        a = first.step(self.support, self.queries, self.targets)
        self.assertFalse(second._optimizer.state)
        torch.manual_seed(71)
        b = second.step(self.support, self.queries, self.targets)
        self.assertEqual(a, b)
        self.assert_state_equal(first.model, second.model.state_dict())
        third = TCPLSourceTrainer(self.source)
        self.assertFalse(third._optimizer.state)
        self.assert_state_equal(third.model, self.source.state_dict())

    def test_nonfinite_loss_or_gradient_is_rejected_before_optimizer_update(self):
        trainer = TCPLSourceTrainer(self.source)
        state = copy.deepcopy(trainer.model.state_dict())
        for kind in ('loss', 'gradient'):
            with self.subTest(kind=kind):
                hook = None
                queries = self.queries
                if kind == 'loss':
                    with torch.no_grad():
                        trainer.model.head.bias.fill_(float('inf'))
                    expected = copy.deepcopy(trainer.model.state_dict())
                else:
                    expected = state
                    hook = trainer.model.head.weight.register_hook(
                        lambda grad: torch.full_like(grad, float('inf'))
                    )
                try:
                    with self.assertRaisesRegex(ValueError, 'nonfinite'):
                        trainer.step(self.support, queries, self.targets)
                finally:
                    if hook is not None:
                        hook.remove()
                self.assertFalse(trainer._optimizer.state)
                self.assert_state_equal(trainer.model, expected)
                self.assertTrue(all(p.grad is None for p in trainer.model.parameters()))
                trainer.model.load_state_dict(state)

    def test_target_session_snapshots_source_support_and_prompt_cache(self):
        self.source.train()
        self.source.head.weight.grad = torch.ones_like(self.source.head.weight)
        source_state = copy.deepcopy(self.source.state_dict())
        support_state = self.support.clone()
        session = TCPLTargetSession(self.source, self.support)
        self.assertFalse(any(m.training for m in session._model.modules()))
        self.assertTrue(all(p.grad is None and not p.requires_grad
                            for p in session._model.parameters()))
        expected = session.predict(self.queries)
        session_state = copy.deepcopy(session._model.state_dict())
        cache = session.prompts
        self.assertFalse(expected.requires_grad)
        self.assert_state_equal(self.source, source_state)
        self.assertTrue(self.source.training)
        torch.testing.assert_close(self.source.head.weight.grad,
                                   torch.ones_like(self.source.head.weight), rtol=0, atol=0)
        torch.testing.assert_close(self.support, support_state, rtol=0, atol=0)
        with torch.no_grad():
            self.source.head.bias.add_(50)
            self.support.mul_(100)
            diagnostic = session.prompts
            diagnostic.zero_()
            expected_copy = expected.clone()
            expected.zero_()
        torch.testing.assert_close(session.prompts, cache, rtol=0, atol=0)
        torch.testing.assert_close(session.predict(self.queries), expected_copy, rtol=0, atol=0)
        self.assert_state_equal(session._model, session_state)

    def test_target_query_batches_order_and_independent_sessions(self):
        for dtype, rtol, atol in ((torch.float32, 1e-5, 1e-6), (torch.float64, 1e-12, 1e-12)):
            with self.subTest(dtype=dtype):
                source = copy.deepcopy(self.source).to(dtype=dtype)
                support, queries = self.support.to(dtype), self.queries.to(dtype)
                session = TCPLTargetSession(source, support)
                state = copy.deepcopy(session._model.state_dict())
                query_copy = queries.clone()
                expected = session.predict(queries)
                for size in (1, 2, 10):
                    torch.testing.assert_close(session.predict(queries, query_batch_size=size),
                                               expected, rtol=rtol, atol=atol)
                altered = queries.clone()
                altered[0, 1:] *= 50
                changed = session.predict(altered)
                torch.testing.assert_close(changed[0, 0], expected[0, 0], rtol=0, atol=0)
                torch.testing.assert_close(changed[1], expected[1], rtol=0, atol=0)
                torch.testing.assert_close(session.predict(queries.flip(1)), expected.flip(1),
                                           rtol=rtol, atol=atol)
                TCPLTargetSession(source, support * 20).predict(queries)
                repeated = TCPLTargetSession(source, support)
                torch.testing.assert_close(repeated.predict(queries), expected, rtol=0, atol=0)
                self.assert_state_equal(session._model, state)
                torch.testing.assert_close(queries, query_copy, rtol=0, atol=0)

    def test_invalid_loss_options_targets_and_optimizer_settings(self):
        for targets in (self.targets.float(), self.targets[:, :1], self.targets - 2,
                        self.targets + 2):
            with self.subTest(targets=targets.shape), self.assertRaises(ValueError):
                tcpl_meta_episode_loss(self.source, self.support, self.queries, targets)
        for value in (-1, float('nan'), float('inf')):
            with self.subTest(weight=value), self.assertRaises(ValueError):
                tcpl_meta_episode_loss(self.source, self.support, self.queries, self.targets,
                                       prompt_l2_weight=value)
        for options in ({'learning_rate': 0}, {'learning_rate': float('inf')},
                        {'weight_decay': -1}, {'prompt_l2_weight': float('nan')}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                TCPLSourceTrainer(self.source, **options)
        with self.assertRaises(ValueError):
            tcpl_meta_episode_loss(self.source, self.support[:1], self.queries, self.targets)

    def test_invalid_target_inputs_fail_without_changing_session(self):
        session = TCPLTargetSession(self.source, self.support)
        state = copy.deepcopy(session._model.state_dict())
        for size in (0, -1, True, 1.5):
            with self.subTest(size=size), self.assertRaises(ValueError):
                session.predict(self.queries, query_batch_size=size)
        for queries in (self.queries[:1], self.queries * float('nan'), self.queries[:, :0]):
            with self.subTest(shape=queries.shape), self.assertRaises(ValueError):
                session.predict(queries)
        with self.assertRaises(ValueError):
            TCPLTargetSession(self.source, self.support[:, :0])
        with self.assertRaises(TypeError):
            session.predict(self.queries, self.targets)
        self.assert_state_equal(session._model, state)

    def test_nonfinite_target_outputs_are_not_returned(self):
        with torch.no_grad():
            self.source.support_prompt.generator[-1].bias.fill_(float('inf'))
        with self.assertRaisesRegex(ValueError, 'nonfinite TCPL target prompts'):
            TCPLTargetSession(self.source, self.support)
        with torch.no_grad():
            self.source.support_prompt.generator[-1].bias.zero_()
            self.source.head.bias.fill_(float('inf'))
        session = TCPLTargetSession(self.source, self.support)
        with self.assertRaisesRegex(ValueError, 'nonfinite TCPL target logits'):
            session.predict(self.queries)
