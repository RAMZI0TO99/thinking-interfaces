"""Continue source-trained LaBraM post-block adapters under audited roles."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.nn.utils import parametrize

from adaptation.adapter import BottleneckAdapter
from adaptation.labram_adapter import (
    LaBraMAdapterBlock,
    LaBraMAdapterReport,
    adapt_labram_adapter_support,
    inject_labram_adapters,
)
from adaptation.labram_manifest import (
    AdapterMask,
    LaBraMAdapterSettings,
    LaBraMTuningManifestRunner,
    LaBraMTuningSettings,
)
from adaptation.labram_tuning import configure_labram_tuning
from core.config import config_digest, config_snapshot
from encoder.labram import LaBraMClassifier
from evaluation.labram_parity import state_digest
from evaluation.phase2_profile_binding import (
    BCIProfileAssets,
    BCIProfileBinding,
    BCIProfileEpisode,
    ChoProfileAssets,
    ChoProfileBinding,
    ChoProfileEpisode,
    load_bci_profile_b_episode,
    load_cho_profile_b_episode,
)
from evaluation.phase2_protocol import TrialCatalog, require_digest, require_names, source_selection


@dataclass(frozen=True, slots=True)
class AdapterSourceSettings:
    target_modules: tuple[str, ...]
    bottleneck_dim: int
    seed: int
    train_head: bool
    steps_per_subject: int
    batch_size: int
    learning_rate: float

    def __post_init__(self) -> None:
        LaBraMAdapterSettings(
            self.target_modules,
            self.bottleneck_dim,
            self.seed,
            self.train_head,
            self.steps_per_subject,
            self.learning_rate,
            self.batch_size,
        )


@dataclass(frozen=True, slots=True)
class AdapterContinuationSettings:
    train_head: bool
    steps: int
    learning_rate: float
    query_batch_size: int = 8

    def __post_init__(self) -> None:
        LaBraMTuningSettings(
            "linear", self.steps, self.learning_rate, query_batch_size=self.query_batch_size
        )
        if type(self.train_head) is not bool:
            raise ValueError("explicit continuation head policy required")


@dataclass(frozen=True, slots=True)
class AdapterSourceCandidate:
    name: str
    source: AdapterSourceSettings
    support: AdapterContinuationSettings

    def __post_init__(self) -> None:
        require_names((self.name,), "candidate name")
        if not isinstance(self.source, AdapterSourceSettings) or not isinstance(
            self.support, AdapterContinuationSettings
        ):
            raise ValueError(
                "explicit source adapter and learned-weight continuation settings required"
            )


@dataclass(frozen=True, slots=True)
class TrainedAdapterEpisodeResult:
    model: LaBraMClassifier
    mask: AdapterMask
    losses: tuple[float, ...]


def _plain_snapshot(model: LaBraMClassifier, settings: AdapterSourceSettings) -> LaBraMClassifier:
    """Unwrap only an owned architecture-admission copy, never the prediction model."""
    plain = copy.deepcopy(model)
    for name in settings.target_modules:
        wrapper = plain.get_submodule(name)
        assert isinstance(wrapper, LaBraMAdapterBlock)
        parent, child = name.rsplit(".", 1)
        setattr(plain.get_submodule(parent), child, wrapper.block)
    configure_labram_tuning(plain, method="linear")
    return plain


def validate_trained_adapter(model: LaBraMClassifier, settings: AdapterSourceSettings) -> None:
    """Pin post-block structure and non-tensor activation/dropout semantics."""
    from braindecode.models.labram import _WindowsAttentionBlock  # type: ignore[import-untyped]

    if not isinstance(model, LaBraMClassifier) or not isinstance(settings, AdapterSourceSettings):
        raise ValueError("LaBraM classifier and explicit source adapter metadata required")
    actual = {n for n, m in model.named_modules() if isinstance(m, LaBraMAdapterBlock)}
    if actual != set(settings.target_modules) or any(
        parametrize.is_parametrized(m) for m in model.modules()
    ):
        raise ValueError(
            "installed adapter target inventory differs or contains hybrid parametrizations"
        )
    for name in settings.target_modules:
        wrapper = model.get_submodule(name)
        if type(wrapper) is not LaBraMAdapterBlock or not isinstance(
            wrapper.block, _WindowsAttentionBlock
        ):
            raise ValueError("exact post-block adapter wrapper and installed source block required")
        adapter = wrapper.adapter
        dim = int(wrapper.block.norm1.normalized_shape[0])
        width = settings.bottleneck_dim
        if (
            type(adapter) is not BottleneckAdapter
            or not 0 < width < dim
            or set(dict(adapter.named_children())) != {"down", "activation", "dropout", "up"}
            or type(adapter.down) is not nn.Linear
            or type(adapter.up) is not nn.Linear
            or adapter.down.in_features != dim
            or adapter.down.out_features != width
            or adapter.up.in_features != width
            or adapter.up.out_features != dim
            or adapter.down.weight.shape != (width, dim)
            or adapter.up.weight.shape != (dim, width)
            or adapter.down.bias is None
            or adapter.down.bias.shape != (width,)
            or adapter.up.bias is None
            or adapter.up.bias.shape != (dim,)
            or type(adapter.activation) is not nn.GELU
            or adapter.activation.approximate != "none"
            or type(adapter.dropout) is not nn.Dropout
            or adapter.dropout.p != 0
            or adapter.dropout.inplace is not False
            or set(dict(adapter.named_parameters()))
            != {"down.weight", "down.bias", "up.weight", "up.bias"}
            or tuple(adapter.named_buffers())
        ):
            raise ValueError(
                "trained adapter dimensions, activation, dropout or parameter structure differs"
            )
    if any(p.device.type != "cpu" or p.dtype != torch.float32 for p in model.parameters()):
        raise ValueError("trained adapters require CPU float32 parameters")
    if any(not torch.isfinite(v).all() for v in model.state_dict().values()):
        raise ValueError("nonfinite trained adapter state")


def configure_trained_adapter(
    model: LaBraMClassifier, settings: AdapterSourceSettings, *, train_head: bool
) -> AdapterMask:
    validate_trained_adapter(model, settings)
    if type(train_head) is not bool:
        raise ValueError("explicit adapter head policy required")
    model.requires_grad_(False)
    count = 0
    for target in settings.target_modules:
        adapter = model.get_submodule(target + ".adapter")
        adapter.requires_grad_(True)
        count += sum(p.numel() for p in adapter.parameters())
    model.head.requires_grad_(train_head)
    model.eval()
    for p in model.parameters():
        p.grad = None
    names = tuple(n for n, p in model.named_parameters() if p.requires_grad)
    return AdapterMask(
        LaBraMAdapterReport(settings.target_modules, settings.bottleneck_dim, count),
        train_head,
        names,
        sum(p.numel() for p in model.parameters() if p.requires_grad),
    )


def initialize_source_adapter(
    plain: LaBraMClassifier, settings: AdapterSourceSettings
) -> tuple[LaBraMClassifier, AdapterMask]:
    model = copy.deepcopy(plain)
    configure_labram_tuning(model, method="linear")
    model.requires_grad_(False)
    with torch.random.fork_rng(devices=[]):
        torch.random.set_rng_state(
            torch.Generator(device="cpu").manual_seed(settings.seed).get_state()
        )
        inject_labram_adapters(
            model, target_modules=settings.target_modules, bottleneck_dim=settings.bottleneck_dim
        )
    return model, configure_trained_adapter(model, settings, train_head=settings.train_head)


def continue_trained_adapter_support(
    source: LaBraMClassifier,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    source_settings: AdapterSourceSettings,
    settings: AdapterContinuationSettings,
) -> TrainedAdapterEpisodeResult:
    """Continue learned adapters using the existing support loop and fresh SGD."""
    if not isinstance(settings, AdapterContinuationSettings):
        raise ValueError("explicit learned-adapter continuation settings required")
    validate_trained_adapter(source, source_settings)
    _plain_snapshot(source, source_settings)
    if (
        inputs.ndim != 3
        or inputs.shape[1:] != (len(source.channel_names), 800)
        or not inputs.is_floating_point()
        or not torch.isfinite(inputs).all()
        or targets.dtype != torch.long
        or targets.shape != (len(inputs),)
        or set(targets.tolist()) != set(range(source.head.out_features))
    ):
        raise ValueError("finite Profile B support and all-class integer labels required")
    owned = copy.deepcopy(source)
    mask = configure_trained_adapter(owned, source_settings, train_head=settings.train_head)
    frozen = {n: v.clone() for n, v in owned.state_dict().items() if n not in mask.trainable_names}
    result = adapt_labram_adapter_support(
        owned,
        inputs,
        targets,
        steps=settings.steps,
        learning_rate=settings.learning_rate,
        train_head=settings.train_head,
    )
    assert isinstance(result.model, LaBraMClassifier)
    validate_trained_adapter(result.model, source_settings)
    if result.trainable_names != mask.trainable_names:
        raise ValueError("adapter support mask differs from declared continuation")
    if any(not torch.equal(v, result.model.state_dict()[n]) for n, v in frozen.items()):
        raise ValueError("continuation changed a frozen parameter or buffer")
    return TrainedAdapterEpisodeResult(result.model, mask, result.losses)


@dataclass(frozen=True, slots=True)
class TrainedAdapterPrediction:
    binding: BCIProfileBinding | ChoProfileBinding
    role: str
    selection_sha256: str
    source_state_sha256: str
    source_settings_sha256: str
    settings: AdapterContinuationSettings
    mask: AdapterMask
    support_losses: tuple[float, ...]
    adapted_state_sha256: str
    logits: torch.Tensor
    targets: torch.Tensor
    component_policy: str = "continue_source_trained_adapter_without_reinitialization"
    engineering_only: bool = True
    source_training_history_verified: bool = False


class TrainedAdapterManifestRunner:
    """Audited fixed roles for a supplied trained Adapter snapshot; prior history is unverified."""

    def __init__(
        self,
        root: Path,
        protocol_config: Mapping[str, Any],
        catalogs: tuple[TrialCatalog, ...],
        selection_record: Mapping[str, Any],
        source: LaBraMClassifier,
        profile_assets: Mapping[str, BCIProfileAssets | ChoProfileAssets],
        *,
        source_settings: AdapterSourceSettings,
        source_state_sha256: str,
        outer_target: str,
        validation_subject: str | None = None,
    ) -> None:
        require_digest(source_state_sha256, "source_state_sha256")
        validate_trained_adapter(source, source_settings)
        if state_digest(source) != source_state_sha256:
            raise ValueError("trained source differs from its pinned state")
        # The plain copy is only for cohort/architecture admission, never for prediction.
        LaBraMTuningManifestRunner(
            root,
            protocol_config,
            catalogs,
            selection_record,
            _plain_snapshot(source, source_settings),
            profile_assets,
            outer_target=outer_target,
            validation_subject=validation_subject,
        )
        self._root = root.resolve()
        self._config: dict[str, Any] = config_snapshot(protocol_config)
        self._catalogs = {c.subject: c for c in catalogs}
        self._assets = dict(profile_assets)
        self._selection = source_selection(catalogs, target=outer_target)
        self._validation = validation_subject
        self._source = copy.deepcopy(source).eval()
        for parameter in self._source.parameters():
            parameter.grad = None
        self._source_sha = source_state_sha256
        self._source_settings = source_settings

    @property
    def training_subjects(self) -> tuple[str, ...]:
        return tuple(s for s in self._selection.source_subjects if s != self._validation)

    def _predict(
        self,
        subject: str,
        role: str,
        record: Mapping[str, Any],
        shots: int,
        settings: AdapterContinuationSettings,
    ) -> TrainedAdapterPrediction:
        if not isinstance(settings, AdapterContinuationSettings):
            raise ValueError("explicit learned-Adapter continuation settings required")
        validate_trained_adapter(self._source, self._source_settings)
        if state_digest(self._source) != self._source_sha:
            raise ValueError("owned trained source changed")
        assets = self._assets[subject]
        episode: BCIProfileEpisode | ChoProfileEpisode
        if isinstance(assets, BCIProfileAssets):
            episode = load_bci_profile_b_episode(
                self._root, self._config, self._catalogs[subject], record,
                shots_per_class=shots, **asdict(assets),
            )
        else:
            episode = load_cho_profile_b_episode(
                self._root, self._config, self._catalogs[subject], record,
                shots_per_class=shots, **asdict(assets),
            )
        adapted = continue_trained_adapter_support(
            self._source,
            torch.from_numpy(episode.support_signals),
            torch.from_numpy(episode.support_labels),
            source_settings=self._source_settings,
            settings=settings,
        )
        adapted_sha = state_digest(adapted.model)
        queries = torch.from_numpy(episode.query_signals)
        with torch.inference_mode():
            logits = torch.cat(
                [
                    adapted.model(queries[i : i + settings.query_batch_size])
                    for i in range(0, len(queries), settings.query_batch_size)
                ]
            ).clone()
        validate_trained_adapter(adapted.model, self._source_settings)
        validate_trained_adapter(self._source, self._source_settings)
        if (
            state_digest(adapted.model) != adapted_sha
            or state_digest(self._source) != self._source_sha
        ):
            raise ValueError("query inference changed trained or adapted state")
        if logits.shape != (
            len(episode.query_labels), self._source.head.out_features
        ) or not torch.isfinite(logits).all():
            raise ValueError("invalid trained-Adapter query logits")
        return TrainedAdapterPrediction(
            episode.binding,
            role,
            self._selection.sha256,
            self._source_sha,
            config_digest(asdict(self._source_settings)),
            settings,
            adapted.mask,
            adapted.losses,
            adapted_sha,
            logits,
            torch.from_numpy(episode.query_labels).clone(),
        )

    def predict_validation(
        self,
        record: Mapping[str, Any],
        *,
        shots_per_class: int,
        settings: AdapterContinuationSettings,
    ) -> TrainedAdapterPrediction:
        if self._validation is None:
            raise ValueError("runner has no inner-validation subject")
        return self._predict(
            self._validation, "inner_validation", record, shots_per_class, settings
        )

    def predict_target(
        self,
        record: Mapping[str, Any],
        *,
        shots_per_class: int,
        settings: AdapterContinuationSettings,
    ) -> TrainedAdapterPrediction:
        if self._validation is not None:
            raise ValueError("outer-target prediction is unavailable during inner validation")
        return self._predict(
            self._selection.target_subject, "outer_target", record, shots_per_class, settings
        )
