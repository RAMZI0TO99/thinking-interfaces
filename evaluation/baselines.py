"""Phase I baseline decoders behind one fit/predict_proba interface."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray
from scipy.signal import butter, sosfiltfilt  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]

from core.config import config_digest
from data.array_cache import verified_float32_cache
from data.runtime import configure_scientific_runtime
from evaluation.csp_rank_certificate import FullRankCertificate, full_rank_certificate

configure_scientific_runtime()

import torch  # noqa: E402
from braindecode.models import (  # type: ignore[import-untyped]  # noqa: E402
    Deep4Net,
    EEGNet,
    ShallowFBCSPNet,
)
from mne import use_log_level  # type: ignore[import-untyped]  # noqa: E402
from mne.decoding import CSP  # type: ignore[import-untyped]  # noqa: E402
from pyriemann.estimation import Covariances  # type: ignore[import-untyped]  # noqa: E402
from pyriemann.tangentspace import TangentSpace  # type: ignore[import-untyped]  # noqa: E402
from torch import nn  # noqa: E402

FloatArray = NDArray[np.float32]
IntArray = NDArray[np.int64]


def _csp_input(
    band: NDArray[np.floating],
    indices: NDArray[np.integer] | None,
    *,
    chunk_trials: int = 32,
) -> NDArray[np.float64]:
    """Select directly into MNE's float64 input without a full float32 copy.

    MNE CSP already requires C-contiguous, writable float64 epochs. Casting
    float32 values this way is exact and does not change CSP or its rank rule.
    Only the indexed temporary is bounded; MNE's own fit still needs memory.
    """
    if band.ndim != 3 or chunk_trials < 1:
        raise ValueError("CSP input must be 3D with a positive selection chunk size")
    if indices is None:
        values = np.ascontiguousarray(band, dtype=np.float64)
        return values if values.flags.writeable else values.copy()
    if indices.ndim != 1:
        raise ValueError("CSP selection indices must be one-dimensional")
    selected = np.empty((len(indices), *band.shape[1:]), dtype=np.float64)
    for start in range(0, len(indices), chunk_trials):
        stop = min(start + chunk_trials, len(indices))
        selected[start:stop] = band[indices[start:stop]]
    return selected


class TangentSpaceLogistic:
    def __init__(self, *, c: float = 1.0, max_iterations: int = 1000) -> None:
        self.covariances = Covariances(estimator="oas")
        self.tangent = TangentSpace(metric="riemann")
        self.classifier = LogisticRegression(C=c, max_iter=max_iterations, class_weight="balanced")

    def fit(self, epochs: NDArray[np.floating], labels: NDArray[Any]) -> TangentSpaceLogistic:
        covariances = self.covariances.fit_transform(np.asarray(epochs))
        features = self.tangent.fit_transform(covariances)
        self.classifier.fit(features, labels)
        return self

    def predict_proba(self, epochs: NDArray[np.floating]) -> FloatArray:
        covariances = self.covariances.transform(np.asarray(epochs))
        features = self.tangent.transform(covariances)
        return np.asarray(self.classifier.predict_proba(features), dtype=np.float32)


class FilterBankCSP:
    def __init__(
        self,
        *,
        sampling_rate_hz: float,
        bands_hz: tuple[tuple[float, float], ...] = (
            (8.0, 12.0),
            (12.0, 16.0),
            (16.0, 20.0),
            (20.0, 24.0),
            (24.0, 28.0),
            (28.0, 32.0),
        ),
        components_per_band: int = 2,
        certify_rank: bool = False,
    ) -> None:
        if sampling_rate_hz <= 0 or components_per_band < 1:
            raise ValueError("sampling rate and component count must be positive")
        if any(not 0 < low < high < sampling_rate_hz / 2 for low, high in bands_hz):
            raise ValueError("filter bands must sit below the Nyquist frequency")
        self.sampling_rate_hz = sampling_rate_hz
        self.bands_hz = bands_hz
        self.components_per_band = components_per_band
        self.certify_rank = certify_rank
        self.rank_certificates: list[FullRankCertificate] = []
        self._filters = tuple(
            butter(4, (low, high), btype="bandpass", fs=sampling_rate_hz, output="sos")
            for low, high in bands_hz
        )
        self._csps: list[Any] = []
        self._classifier = LogisticRegression(max_iter=1000, class_weight="balanced")

    def _filtered(self, epochs: NDArray[np.floating], index: int) -> NDArray[np.float64]:
        return np.asarray(sosfiltfilt(self._filters[index], epochs, axis=-1), dtype=np.float64)

    def filtered_bands(self, epochs: NDArray[np.floating]) -> tuple[FloatArray, ...]:
        """Filter a complete dataset once for reuse across LOSO folds."""

        values = np.asarray(epochs)
        if values.ndim != 3:
            raise ValueError("epochs must have shape (trials, channels, samples)")
        return tuple(
            np.asarray(self._filtered(values, index), dtype=np.float32)
            for index in range(len(self.bands_hz))
        )

    def filtered_bands_memmap(
        self,
        epochs: NDArray[np.floating],
        directory: Path,
        *,
        chunk_trials: int = 256,
    ) -> tuple[FloatArray, ...]:
        """Build/reuse atomic, input-keyed and content-verified filter-bank caches."""

        values = np.asarray(epochs)
        if values.ndim != 3 or chunk_trials < 1:
            raise ValueError("epochs or chunk_trials are invalid")
        directory.mkdir(parents=True, exist_ok=True)
        input_sha256 = hashlib.sha256(
            memoryview(np.ascontiguousarray(values)).cast("B")
        ).hexdigest()
        outputs: list[FloatArray] = []
        for band_index in range(len(self.bands_hz)):
            path = directory / f"band_{band_index:02d}.npy"
            key = config_digest(
                {
                    "input_sha256": input_sha256,
                    "input_dtype": str(values.dtype),
                    "shape": list(values.shape),
                    "filter_sos": self._filters[band_index].tolist(),
                    "operation": "scipy.sosfiltfilt(axis=-1), float32 output",
                    "scipy_version": version("scipy"),
                    "numpy_version": np.__version__,
                }
            )

            def fill(target: np.memmap[Any, Any], index: int = band_index) -> None:
                for start in range(0, values.shape[0], chunk_trials):
                    stop = min(start + chunk_trials, values.shape[0])
                    target[start:stop] = np.asarray(
                        self._filtered(values[start:stop], index),
                        dtype=np.float32,
                    )

            outputs.append(verified_float32_cache(path, shape=values.shape, key=key, fill=fill))
        return tuple(outputs)

    def fit_prefiltered(
        self,
        bands: tuple[NDArray[np.floating], ...],
        labels: NDArray[Any],
        *,
        indices: NDArray[np.integer] | None = None,
    ) -> FilterBankCSP:
        if len(bands) != len(self.bands_hz) or any(band.ndim != 3 for band in bands):
            raise ValueError("prefiltered bands do not match the configured filter bank")
        if indices is None and any(band.shape[0] != len(labels) for band in bands):
            raise ValueError("prefiltered bands and labels have different trial counts")
        if indices is not None and len(indices) != len(labels):
            raise ValueError("prefilter indices and labels have different trial counts")
        features: list[NDArray[np.float64]] = []
        self._csps = []
        self.rank_certificates = []
        for band in bands:
            selected = _csp_input(band, indices)
            rank = None
            # The shortcut was reviewed against this pinned MNE implementation.
            if self.certify_rank and version("mne") == "1.12.1":
                certificate = full_rank_certificate(selected)
                self.rank_certificates.append(certificate)
                rank = certificate.mne_rank
            csp = CSP(
                n_components=self.components_per_band,
                reg="oas",
                log=True,
                cov_est="concat",
                norm_trace=False,
                component_order="mutual_info",
                rank=rank,
            )
            with use_log_level("ERROR"):
                features.append(np.asarray(csp.fit_transform(selected, labels)))
            self._csps.append(csp)
            del selected
        self._classifier.fit(np.concatenate(features, axis=1), labels)
        return self

    def fit(self, epochs: NDArray[np.floating], labels: NDArray[Any]) -> FilterBankCSP:
        return self.fit_prefiltered(self.filtered_bands(epochs), labels)

    def predict_proba_prefiltered(
        self,
        bands: tuple[NDArray[np.floating], ...],
        *,
        indices: NDArray[np.integer] | None = None,
    ) -> FloatArray:
        if len(self._csps) != len(self.bands_hz) or len(bands) != len(self.bands_hz):
            raise RuntimeError("FilterBankCSP must be fitted before prediction")
        with use_log_level("ERROR"):
            features = [
                np.asarray(csp.transform(_csp_input(band, indices)))
                for csp, band in zip(self._csps, bands, strict=True)
            ]
        return np.asarray(
            self._classifier.predict_proba(np.concatenate(features, axis=1)),
            dtype=np.float32,
        )

    def predict_proba(self, epochs: NDArray[np.floating]) -> FloatArray:
        return self.predict_proba_prefiltered(self.filtered_bands(epochs))


@dataclass(frozen=True, slots=True)
class TorchTrainingConfig:
    epochs: int = 20
    batch_size: int = 32
    learning_rate: float = 1e-3
    weight_decay: float = 0.0
    input_scale: float = 1.0
    device: str | None = None


class BraindecodeClassifier:
    """Small deterministic trainer for EEGNet, ShallowFBCSPNet, or Deep4Net."""

    def __init__(
        self,
        model_name: str,
        *,
        channels: int,
        classes: int,
        samples: int,
        sampling_rate_hz: float,
        seed: int,
        training: TorchTrainingConfig,
    ) -> None:
        if model_name not in {"eegnet", "shallow", "deep"}:
            raise ValueError(f"unknown braindecode model: {model_name}")
        self.model_name = model_name
        self.channels = channels
        self.classes = classes
        self.samples = samples
        self.sampling_rate_hz = sampling_rate_hz
        self.seed = seed
        self.training = training
        self.model: nn.Module | None = None

    def _make_model(self) -> nn.Module:
        arguments = {
            "n_chans": self.channels,
            "n_outputs": self.classes,
            "n_times": self.samples,
            "sfreq": self.sampling_rate_hz,
        }
        factories = {"eegnet": EEGNet, "shallow": ShallowFBCSPNet, "deep": Deep4Net}
        return cast(nn.Module, factories[self.model_name](**arguments))

    def fit(self, epochs: NDArray[np.floating], labels: NDArray[Any]) -> BraindecodeClassifier:
        values = np.ascontiguousarray(epochs, dtype=np.float32)
        targets = np.asarray(labels, dtype=np.int64)
        if values.shape != (targets.size, self.channels, self.samples):
            raise ValueError("training arrays do not match configured model dimensions")
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)
        device = torch.device(
            self.training.device
            if self.training.device is not None
            else ("cuda" if torch.cuda.is_available() else "cpu")
        )
        model = self._make_model().to(device)
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=self.training.learning_rate,
            weight_decay=self.training.weight_decay,
        )
        criterion = nn.CrossEntropyLoss()
        generator = torch.Generator().manual_seed(self.seed)
        input_tensor = torch.from_numpy(values)
        target_tensor = torch.from_numpy(targets)
        if device.type == "cuda":
            available = int(torch.cuda.mem_get_info(device)[0])
            required = values.nbytes + targets.nbytes
            if required <= available // 4:
                input_tensor = input_tensor.to(device)
                target_tensor = target_tensor.to(device)
        dataset = torch.utils.data.TensorDataset(
            input_tensor,
            target_tensor,
        )
        loader = torch.utils.data.DataLoader(
            dataset,
            batch_size=self.training.batch_size,
            shuffle=True,
            generator=generator,
            num_workers=0,
            pin_memory=device.type == "cuda" and input_tensor.device.type == "cpu",
        )
        model.train()
        for _ in range(self.training.epochs):
            for batch, target in loader:
                optimizer.zero_grad(set_to_none=True)
                device_batch = batch.to(device, non_blocking=True).mul(self.training.input_scale)
                logits = cast(torch.Tensor, model(device_batch))
                loss = criterion(logits, target.to(device, non_blocking=True))
                loss.backward()
                optimizer.step()
        self.model = model
        return self

    def predict_proba(self, epochs: NDArray[np.floating]) -> FloatArray:
        if self.model is None:
            raise RuntimeError("classifier must be fitted before prediction")
        device = next(self.model.parameters()).device
        values = np.ascontiguousarray(epochs, dtype=np.float32)
        self.model.eval()
        with torch.inference_mode():
            inputs = torch.from_numpy(values).to(device).mul(self.training.input_scale)
            logits = cast(torch.Tensor, self.model(inputs))
            probabilities = torch.softmax(logits, dim=1).cpu().numpy()
        return np.asarray(probabilities, dtype=np.float32)


BASELINE_METHODS = (
    "eegnet",
    "shallow",
    "deep",
    "fbcsp",
    "tangent_lr",
    "ea_eegnet",
    "ea_tangent_lr",
)
