"""Continue learned LaBraM QKV LoRA under audited source/target roles; engineering only."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.nn.utils import parametrize

from adaptation.labram_lora import LowRankWeight, inject_labram_qkv_lora
from adaptation.labram_lora_support import LoRAEpisodeResult, LoRAMask
from adaptation.labram_manifest import (
    LaBraMLoRASettings,
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
class LoRASourceSettings:
    target_modules: tuple[str, ...]
    rank: int
    alpha: float
    seed: int
    train_head: bool
    steps_per_subject: int
    batch_size: int
    learning_rate: float

    def __post_init__(self) -> None:
        LaBraMLoRASettings(
            self.target_modules,
            self.rank,
            self.alpha,
            self.seed,
            self.train_head,
            self.steps_per_subject,
            self.learning_rate,
            self.batch_size,
        )


@dataclass(frozen=True, slots=True)
class LoRAContinuationSettings:
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
class LoRASourceCandidate:
    name: str
    source: LoRASourceSettings
    support: LoRAContinuationSettings

    def __post_init__(self) -> None:
        require_names((self.name,), "candidate name")
        if not isinstance(self.source, LoRASourceSettings) or not isinstance(
            self.support, LoRAContinuationSettings
        ):
            raise ValueError(
                "explicit source LoRA and learned-weight continuation settings required"
            )


def _plain_snapshot(model: LaBraMClassifier, settings: LoRASourceSettings) -> LaBraMClassifier:
    """Replace QKV modules in an owned copy for architecture admission only.

    Removing a parametrization from a deepcopy can delete a property on the shared
    dynamic class in installed Torch. Replacements leave the trained model intact.
    """
    plain = copy.deepcopy(model)
    for name in settings.target_modules:
        module = plain.get_submodule(name)
        assert isinstance(module, nn.Linear)
        replacement = nn.Linear(module.in_features, module.out_features, bias=False, device="meta")
        replacement.weight = nn.Parameter(
            module.get_parameter("parametrizations.weight.original").detach().clone(),
            requires_grad=False,
        )
        parent, child = name.rsplit(".", 1)
        setattr(plain.get_submodule(parent), child, replacement)
    configure_labram_tuning(plain, method="linear")
    return plain


def validate_trained_lora(model: LaBraMClassifier, settings: LoRASourceSettings) -> None:
    """Validate non-tensor scaling too: a tensor-state digest alone cannot pin LoRA."""
    if not isinstance(model, LaBraMClassifier) or not isinstance(settings, LoRASourceSettings):
        raise ValueError("LaBraM classifier and explicit source LoRA metadata required")
    actual = {n for n, m in model.named_modules() if parametrize.is_parametrized(m)}
    if actual != set(settings.target_modules):
        raise ValueError("installed LoRA target inventory differs from source metadata")
    for name in settings.target_modules:
        module = model.get_submodule(name)
        if not isinstance(module, nn.Linear) or module.bias is not None:
            raise ValueError("trained LoRA must occupy bias-free QKV Linear weights")
        if set(module.parametrizations) != {"weight"} or len(module.parametrizations.weight) != 1:
            raise ValueError("exactly one effective-weight LoRA parametrization required")
        adapter = module.parametrizations.weight[0]
        if (
            type(adapter) is not LowRankWeight
            or adapter.lora_a.shape != (settings.rank, module.in_features)
            or adapter.lora_b.shape != (module.out_features, settings.rank)
            or adapter.scaling != settings.alpha / settings.rank
            or set(dict(adapter.named_parameters())) != {"lora_a", "lora_b"}
            or tuple(adapter.named_buffers())
        ):
            raise ValueError("trained LoRA rank, scaling or parameter structure differs")
    if any(p.device.type != "cpu" or p.dtype != torch.float32 for p in model.parameters()):
        raise ValueError("trained LoRA requires CPU float32 parameters")
    if any(not torch.isfinite(v).all() for v in model.state_dict().values()):
        raise ValueError("nonfinite trained LoRA state")


def configure_trained_lora(
    model: LaBraMClassifier, settings: LoRASourceSettings, *, train_head: bool
) -> LoRAMask:
    validate_trained_lora(model, settings)
    if type(train_head) is not bool:
        raise ValueError("explicit LoRA head policy required")
    model.requires_grad_(False)
    names = {
        f"{target}.parametrizations.weight.0.{part}"
        for target in settings.target_modules
        for part in ("lora_a", "lora_b")
    }
    adapter_count = 0
    for name, parameter in model.named_parameters():
        parameter.grad = None
        if name in names:
            parameter.requires_grad_(True)
            adapter_count += parameter.numel()
    model.head.requires_grad_(train_head)
    model.eval()
    selected = tuple(n for n, p in model.named_parameters() if p.requires_grad)
    return LoRAMask(
        settings.target_modules,
        settings.rank,
        settings.alpha,
        train_head,
        selected,
        sum(p.numel() for p in model.parameters() if p.requires_grad),
        adapter_count,
    )


def initialize_source_lora(
    plain: LaBraMClassifier, settings: LoRASourceSettings
) -> tuple[LaBraMClassifier, LoRAMask]:
    model = copy.deepcopy(plain)
    configure_labram_tuning(model, method="linear")
    model.requires_grad_(False)
    with torch.random.fork_rng(devices=[]):
        torch.random.set_rng_state(
            torch.Generator(device="cpu").manual_seed(settings.seed).get_state()
        )
        inject_labram_qkv_lora(
            model, target_modules=settings.target_modules, rank=settings.rank, alpha=settings.alpha
        )
    return model, configure_trained_lora(model, settings, train_head=settings.train_head)


def continue_trained_lora_support(
    source: LaBraMClassifier,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    source_settings: LoRASourceSettings,
    settings: LoRAContinuationSettings,
) -> LoRAEpisodeResult:
    """Fresh optimizer and owned snapshot, preserving learned A/B tensors and the head."""
    if not isinstance(settings, LoRAContinuationSettings):
        raise ValueError("explicit learned-LoRA continuation settings required")
    validate_trained_lora(source, source_settings)
    _plain_snapshot(source, source_settings)  # Reject hybrid/non-LaBraM architecture.
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
    model = copy.deepcopy(source)
    mask = configure_trained_lora(model, source_settings, train_head=settings.train_head)
    frozen = {n: v.clone() for n, v in model.state_dict().items() if n not in mask.trainable_names}
    selected = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.SGD(selected, lr=settings.learning_rate)
    criterion = nn.CrossEntropyLoss()
    x = inputs.detach().to(device="cpu", dtype=torch.float32).clone()
    y = targets.detach().to(device="cpu").clone()
    losses = []
    for _ in range(settings.steps):
        optimizer.zero_grad(set_to_none=True)
        loss = criterion(model(x), y)
        if not torch.isfinite(loss):
            raise ValueError("nonfinite continuation loss")
        loss.backward()
        if any(p.grad is None or not torch.isfinite(p.grad).all() for p in selected):
            raise ValueError("missing or nonfinite continuation gradient")
        optimizer.step()
        losses.append(float(loss.detach()))
        validate_trained_lora(model, source_settings)
    optimizer.zero_grad(set_to_none=True)
    if any(not torch.equal(v, model.state_dict()[n]) for n, v in frozen.items()):
        raise ValueError("continuation changed a frozen parameter or buffer")
    return LoRAEpisodeResult(model, mask, tuple(losses))


@dataclass(frozen=True, slots=True)
class TrainedLoRAPrediction:
    binding: BCIProfileBinding | ChoProfileBinding
    role: str
    selection_sha256: str
    source_state_sha256: str
    source_settings_sha256: str
    settings: LoRAContinuationSettings
    mask: LoRAMask
    support_losses: tuple[float, ...]
    adapted_state_sha256: str
    logits: torch.Tensor
    targets: torch.Tensor
    component_policy: str = "continue_source_trained_lora_without_reinitialization"
    engineering_only: bool = True
    source_training_history_verified: bool = False


class TrainedLoRAManifestRunner:
    """Audited fixed roles for a supplied trained LoRA snapshot; prior history is unverified."""

    def __init__(
        self,
        root: Path,
        protocol_config: Mapping[str, Any],
        catalogs: tuple[TrialCatalog, ...],
        selection_record: Mapping[str, Any],
        source: LaBraMClassifier,
        profile_assets: Mapping[str, BCIProfileAssets | ChoProfileAssets],
        *,
        source_settings: LoRASourceSettings,
        source_state_sha256: str,
        outer_target: str,
        validation_subject: str | None = None,
    ) -> None:
        require_digest(source_state_sha256, "source_state_sha256")
        validate_trained_lora(source, source_settings)
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
        settings: LoRAContinuationSettings,
    ) -> TrainedLoRAPrediction:
        if not isinstance(settings, LoRAContinuationSettings):
            raise ValueError("explicit learned-LoRA continuation settings required")
        validate_trained_lora(self._source, self._source_settings)
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
        adapted = continue_trained_lora_support(
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
        validate_trained_lora(adapted.model, self._source_settings)
        validate_trained_lora(self._source, self._source_settings)
        if (
            state_digest(adapted.model) != adapted_sha
            or state_digest(self._source) != self._source_sha
        ):
            raise ValueError("query inference changed trained or adapted state")
        if logits.shape != (
            len(episode.query_labels), self._source.head.out_features
        ) or not torch.isfinite(logits).all():
            raise ValueError("invalid trained-LoRA query logits")
        return TrainedLoRAPrediction(
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
        self, record: Mapping[str, Any], *, shots_per_class: int, settings: LoRAContinuationSettings
    ) -> TrainedLoRAPrediction:
        if self._validation is None:
            raise ValueError("runner has no inner-validation subject")
        return self._predict(
            self._validation, "inner_validation", record, shots_per_class, settings
        )

    def predict_target(
        self, record: Mapping[str, Any], *, shots_per_class: int, settings: LoRAContinuationSettings
    ) -> TrainedLoRAPrediction:
        if self._validation is not None:
            raise ValueError("outer-target prediction is unavailable during inner validation")
        return self._predict(
            self._selection.target_subject, "outer_target", record, shots_per_class, settings
        )
