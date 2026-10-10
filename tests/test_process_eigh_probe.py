from __future__ import annotations

import unittest
from concurrent.futures import Future
from unittest.mock import patch

import array_api_compat.numpy as facade
import numpy as np

from evaluation.process_eigh_probe import ProcessEighProbe, _initialize_worker


class ImmediatePool:
    """Single-threaded test double; never use threads for NumPy eigensolver tests."""

    def __init__(self, **kwargs):
        self.shutdown_called = False

    def submit(self, function, argument):
        future = Future()
        try:
            future.set_result(function(argument))
        except Exception as error:
            future.set_exception(error)
        return future

    def shutdown(self, **kwargs):
        self.shutdown_called = True


class ProcessEighProbeTests(unittest.TestCase):
    def setUp(self):
        # These unit tests replace the process pool. Declare its expected backend
        # metadata too, without changing the real NumPy pool's thread settings.
        backend = patch(
            "evaluation.process_eigh_probe.numpy_backend", return_value={"num_threads": 24},
        )
        backend.start()
        self.addCleanup(backend.stop)

    def candidate(self, **settings):
        return ProcessEighProbe(
            **{
                "workers": 2,
                "chunk_matrices": 64,
                "minimum_memory_gib": 4.0,
                **settings,
            }
        )

    def test_exact_ordered_outputs_bounded_pending_and_facade_restoration(self):
        matrices = np.broadcast_to(np.diag(np.arange(1, 65.0)), (129, 64, 64)).copy()
        matrices *= np.arange(1, 130)[:, None, None]
        original = matrices.copy()
        expected = np.linalg.eigh(matrices)
        original_facade = facade.linalg.eigh
        original_numpy = np.linalg.eigh
        with (
            patch("evaluation.process_eigh_probe.ProcessPoolExecutor", ImmediatePool),
            patch("evaluation.process_eigh_probe.available_memory_gib", return_value=16.0),
            self.candidate() as candidate,
        ):
            actual = facade.linalg.eigh(matrices)
            self.assertIs(np.linalg.eigh, original_numpy)
            self.assertEqual(candidate.stats["blocks"], 3)
            self.assertEqual(candidate.stats["maximum_pending_blocks"], 2)
            self.assertEqual(candidate.stats["parallel_calls"], 1)
            self.assertEqual(candidate.stats["minimum_observed_free_memory_gib"], 16.0)
        self.assertIs(facade.linalg.eigh, original_facade)
        np.testing.assert_array_equal(actual[0], expected[0])
        np.testing.assert_array_equal(actual[1], expected[1])
        np.testing.assert_array_equal(matrices, original)

    def test_small_single_precision_and_keyword_calls_fall_back(self):
        cases = (
            (np.eye(3), {}),
            (np.eye(64, dtype=np.float32)[None], {}),
            (np.eye(3), {"UPLO": "U"}),
        )
        with (
            patch("evaluation.process_eigh_probe.ProcessPoolExecutor", ImmediatePool),
            patch("evaluation.process_eigh_probe.available_memory_gib", return_value=16.0),
            self.candidate() as candidate,
        ):
            for values, keywords in cases:
                actual = candidate(values, **keywords)
                expected = np.linalg.eigh(values, **keywords)
                np.testing.assert_array_equal(actual[0], expected[0])
                np.testing.assert_array_equal(actual[1], expected[1])
            self.assertEqual(candidate.stats["parallel_calls"], 0)
            self.assertEqual(candidate.stats["fallback_calls"], 3)

    def test_memory_failure_restores_the_facade(self):
        original = facade.linalg.eigh
        with (
            patch("evaluation.process_eigh_probe.ProcessPoolExecutor", ImmediatePool),
            patch("evaluation.process_eigh_probe.available_memory_gib", side_effect=[16.0, 3.0]),
            self.assertRaisesRegex(RuntimeError, "memory guard"),
            self.candidate() as candidate,
        ):
            candidate(np.eye(3))
        self.assertIs(facade.linalg.eigh, original)

    def test_bad_worker_backend_is_rejected(self):
        with (
            patch("evaluation.process_eigh_probe.numpy_backend", return_value={"threads": 1}),
            self.assertRaisesRegex(RuntimeError, "differ"),
        ):
            _initialize_worker({"threads": 24}, 4.0)

    def test_parent_backend_thread_drift_is_rejected_before_pool_creation(self):
        original = facade.linalg.eigh
        for threads in (1, 2, 23, 25):
            with (
                self.subTest(threads=threads),
                patch(
                    "evaluation.process_eigh_probe.numpy_backend",
                    return_value={"num_threads": threads},
                ),
                patch("evaluation.process_eigh_probe.ProcessPoolExecutor") as pool,
                self.assertRaisesRegex(RuntimeError, "original 24-thread"),
            ):
                self.candidate().__enter__()
            pool.assert_not_called()
            self.assertIs(facade.linalg.eigh, original)

    def test_worker_failure_restores_facade_and_closes_pool(self):
        original = facade.linalg.eigh
        pool = ImmediatePool()
        with (
            patch("evaluation.process_eigh_probe.ProcessPoolExecutor", return_value=pool),
            patch("evaluation.process_eigh_probe.available_memory_gib", return_value=16.0),
            patch("evaluation.process_eigh_probe._eigh_block", side_effect=RuntimeError("worker")),
            self.assertRaisesRegex(RuntimeError, "worker"),
            self.candidate() as candidate,
        ):
            candidate(np.broadcast_to(np.eye(64), (128, 64, 64)).copy())
        self.assertIs(facade.linalg.eigh, original)
        self.assertTrue(pool.shutdown_called)

    def test_protocol_and_inactive_use_fail_closed(self):
        for settings in (
            {"workers": 1},
            {"workers": True},
            {"chunk_matrices": 128},
            {"minimum_memory_gib": 1.0},
        ):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                self.candidate(**settings)
        with self.assertRaisesRegex(RuntimeError, "not active"):
            self.candidate()(np.eye(3))


if __name__ == "__main__":
    unittest.main()
