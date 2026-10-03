"""BCI manifest-bound LaBraM support episodes for all six methods; engineering only."""

from __future__ import annotations

import copy
import math
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch

from adaptation.labram_adapter import (
    AdapterEpisodeResult,
    LaBraMAdapterReport,
    adapt_labram_adapter_support,
    inject_labram_adapters,
)
from adaptation.labram_lora_support import (
    LoRAEpisodeResult,
    LoRAMask,
    adapt_labram_lora_support,
)
from adaptation.labram_prompt import (
    ClassPrototypePromptGenerator,
    PromptEpisodeResult,
    adapt_labram_prompt_support,
)
from adaptation.labram_tuning import (
    TuningEpisodeResult,
    TuningMask,
    TuningMethod,
    adapt_labram_tuning_support,
    configure_labram_tuning,
)
from core.config import config_digest, config_snapshot
from encoder.labram import LaBraMClassifier
from evaluation.labram_parity import state_digest
from evaluation.phase2_profile_binding import (
    BCIProfileAssets,
    BCIProfileBinding,
    BCIProfileEpisode,
    ChoProfileAssets,
    ChoProfileAssets60Hz,
    ChoProfileBinding,
    ChoProfileEpisode,
    MMIDBProfileAssets,
    dataset_cohort,
    load_bci_profile_b_episode,
    load_cho_profile_b_episode,
    load_mmidb_profile_b_episode,
)
from evaluation.phase2_protocol import TrialCatalog, source_selection
from evaluation.phase2_records import verify_envelope
from scripts.audit_phase2_protocol import inside, validate_protocol


@dataclass(frozen=True, slots=True)
class LaBraMTuningSettings:
    method: TuningMethod
    steps: int
    learning_rate: float
    partial_depth: int | None = None
    query_batch_size: int = 8

    def __post_init__(self) -> None:
        if (
            self.method not in ("linear", "partial", "full")
            or type(self.steps) is not int
            or self.steps < 1
            or type(self.learning_rate) not in (int, float)
            or not math.isfinite(self.learning_rate)
            or self.learning_rate <= 0
            or type(self.query_batch_size) is not int
            or self.query_batch_size < 1
        ):
            raise ValueError("explicit valid method, steps, learning rate and batch size required")
        if self.method == "partial":
            if type(self.partial_depth) is not int or self.partial_depth < 1:
                raise ValueError("partial tuning requires a positive integer depth")
        elif self.partial_depth is not None:
            raise ValueError("depth is only valid for partial tuning")

    @property
    def sha256(self) -> str:
        return config_digest(asdict(self))


@dataclass(frozen=True, slots=True)
class LaBraMLoRASettings:
    target_modules: tuple[str, ...]
    rank: int
    alpha: float
    seed: int
    train_head: bool
    steps: int
    learning_rate: float
    query_batch_size: int = 8

    def __post_init__(self) -> None:
        # Reuse the common scalar contract without changing the tuning settings API.
        LaBraMTuningSettings(
            "linear", self.steps, self.learning_rate, query_batch_size=self.query_batch_size
        )
        if (
            type(self.target_modules) is not tuple or not self.target_modules
            or any(
                type(n) is not str or re.fullmatch(r"backbone\.blocks\.\d+\.attn\.qkv", n) is None
                for n in self.target_modules
            )
            or len(set(self.target_modules)) != len(self.target_modules)
            or type(self.rank) is not int or self.rank < 1
            or type(self.alpha) not in (int, float)
            or not math.isfinite(self.alpha) or self.alpha <= 0
            or type(self.seed) is not int or not 0 <= self.seed < 2**63
            or type(self.train_head) is not bool
        ):
            raise ValueError(
                "explicit valid QKV targets, rank, alpha, seed and head policy required"
            )

    @property
    def sha256(self) -> str:
        return config_digest(asdict(self))


@dataclass(frozen=True, slots=True)
class LaBraMAdapterSettings:
    target_modules: tuple[str, ...]
    bottleneck_dim: int
    seed: int
    train_head: bool
    steps: int
    learning_rate: float
    query_batch_size: int = 8

    def __post_init__(self) -> None:
        LaBraMTuningSettings(
            "linear", self.steps, self.learning_rate, query_batch_size=self.query_batch_size
        )
        if (
            type(self.target_modules) is not tuple or not self.target_modules
            or any(
                type(n) is not str or re.fullmatch(r"backbone\.blocks\.\d+", n) is None
                for n in self.target_modules
            )
            or len(set(self.target_modules)) != len(self.target_modules)
            or type(self.bottleneck_dim) is not int or self.bottleneck_dim < 1
            or type(self.seed) is not int or not 0 <= self.seed < 2**63
            or type(self.train_head) is not bool
        ):
            raise ValueError("explicit valid adapter targets, width, seed and head policy required")

    @property
    def sha256(self) -> str:
        return config_digest(asdict(self))


@dataclass(frozen=True, slots=True)
class AdapterMask:
    injection: LaBraMAdapterReport
    train_head: bool
    trainable_names: tuple[str, ...]
    trainable_parameters: int
    method: str = "adapter"
    support_normalization_policy: str = "all_modules_eval_source_affine_and_buffers_frozen"


@dataclass(frozen=True, slots=True)
class LaBraMPromptSettings:
    prompt_tokens: int
    hidden_dim: int
    seed: int
    train_head: bool
    steps: int
    learning_rate: float
    query_batch_size: int = 8

    def __post_init__(self) -> None:
        LaBraMTuningSettings(
            "linear", self.steps, self.learning_rate, query_batch_size=self.query_batch_size
        )
        if (
            type(self.prompt_tokens) is not int or self.prompt_tokens < 1
            or type(self.hidden_dim) is not int or self.hidden_dim < 1
            or type(self.seed) is not int or not 0 <= self.seed < 2**63
            or type(self.train_head) is not bool
        ):
            raise ValueError("explicit valid prompt dimensions, seed and head policy required")

    @property
    def sha256(self) -> str:
        return config_digest(asdict(self))


@dataclass(frozen=True, slots=True)
class PromptMask:
    prompt_tokens: int
    hidden_dim: int
    generator_parameters: int
    train_head: bool
    trainable_names: tuple[str, ...]
    trainable_parameters: int
    method: str = "support_prompt"
    placement: str = "after_cls_after_position_time_assembly_persist_all_blocks"
    conditioning: str = "class_means_of_frozen_unprompted_batch_one_support_features"
    support_normalization_policy: str = "all_modules_eval_source_affine_and_buffers_frozen"


type LaBraMManifestSettings = (
    LaBraMTuningSettings | LaBraMLoRASettings | LaBraMAdapterSettings | LaBraMPromptSettings
)


@dataclass(frozen=True, slots=True)
class LaBraMTuningPrediction:
    binding: BCIProfileBinding | ChoProfileBinding
    role: str
    selection_sha256: str
    source_state_sha256: str
    settings: LaBraMManifestSettings
    mask: TuningMask | LoRAMask | AdapterMask | PromptMask
    support_losses: tuple[float, ...]
    adapted_state_sha256: str
    logits: torch.Tensor
    targets: torch.Tensor
    engineering_only: bool = True
    source_training_history_verified: bool = False


class LaBraMTuningManifestRunner:
    """Owned source snapshot and fixed outer/optional inner subject permissions.

    Catalogs, inventory hashes and source template are trusted constructor inputs.
    Reconstruct the selection envelope before cloning the model. Predictions bind
    the selected subject's actual A/B files and complete audited episode before
    support-only SGD. The source snapshot never receives an optimizer update.

    This class does not train a source model or authenticate its past subjects,
    choose candidates, publish scientific cells, or fit target alignment. Its
    training_subjects property declares the permitted source cohort for future
    fitting, not evidence that the supplied weights were trained on that cohort.
    """

    def __init__(
        self,
        root: Path,
        protocol_config: Mapping[str, Any],
        catalogs: tuple[TrialCatalog, ...],
        selection_record: Mapping[str, Any],
        source_template: LaBraMClassifier,
        profile_assets: Mapping[str, BCIProfileAssets | ChoProfileAssets],
        *,
        outer_target: str,
        validation_subject: str | None = None,
    ) -> None:
        self._root = root.resolve()
        config: dict[str, Any] = config_snapshot(protocol_config)
        self._config = config
        validate_protocol(config)
        selection = source_selection(catalogs, target=outer_target)
        if not verify_envelope(
            selection_record, kind="source_selection", expected_payload=asdict(selection)
        ):
            raise ValueError("selection differs from the reconstructed catalog cohort")
        dataset, channels, classes, subjects = dataset_cohort(config, catalogs)
        settings: dict[str, Any] = config["datasets"][dataset]
        if (
            selection.dataset != dataset
            or catalogs[0].classes != classes
            or tuple(settings["classes"]) != classes
            or set(profile_assets) != subjects
            or any(
                not isinstance(v, (BCIProfileAssets, ChoProfileAssets, MMIDBProfileAssets))
                for v in profile_assets.values()
            )
        ):
            raise ValueError(
                f"complete {dataset} catalogs and the matching asset inventory are required"
            )
        if any(
            (isinstance(v, BCIProfileAssets)) != (dataset == "bci_iv_2a")
            for v in profile_assets.values()
        ):
            raise ValueError("asset inventory type must match the dataset's sidecar convention")
        cho_60hz = False
        if dataset == "cho2017":
            if any(not isinstance(v, ChoProfileAssets) for v in profile_assets.values()):
                raise ValueError("Cho asset inventory must contain only Cho assets")
            versions = {isinstance(v, ChoProfileAssets60Hz) for v in profile_assets.values()}
            if len(versions) != 1:
                raise ValueError("Cho asset inventory mixes 50 Hz and 60 Hz variants")
            cho_60hz = True in versions
        for profile in ("a", "b"):
            relative = f"data/processed/{dataset}/profile_{profile}"
            if profile == "b" and cho_60hz:
                relative = "data/processed/cho2017/profile_b_60hz_v1"
            directory = inside(self._root, relative)
            if {p.stem for p in directory.glob("subject_*.npz")} != subjects:
                raise ValueError("profile directory differs from declared cohort")
        if validation_subject is not None and validation_subject not in selection.source_subjects:
            raise ValueError("inner validation must be a source subject, never the outer target")
        if (
            not isinstance(source_template, LaBraMClassifier)
            or source_template.channel_names != channels
            or source_template.head.out_features != len(classes)
        ):
            raise ValueError(
                f"source classifier must use the declared {dataset} montage and head"
            )
        owned = copy.deepcopy(source_template)
        configure_labram_tuning(owned, method="linear")  # Validate plain installed architecture.
        segment = owned.backbone.patch_embed[0]
        if segment.n_times != 800 or segment.patch_size != 200:
            raise ValueError("source backbone must accept 800 samples in 200-sample patches")
        if any(p.device.type != "cpu" or p.dtype != torch.float32 for p in owned.parameters()):
            raise ValueError("this bounded runner requires CPU float32 parameters")
        if any(not torch.isfinite(v).all() for v in owned.state_dict().values()):
            raise ValueError("source state contains nonfinite values")
        owned.eval()
        for parameter in owned.parameters():
            parameter.grad = None
        self._source = owned
        self._source_sha = state_digest(owned)
        self._catalogs = {c.subject: c for c in catalogs}
        self._assets = dict(profile_assets)
        self._selection = selection
        self._classes = len(classes)
        self._validation_subject = validation_subject
        self._training_subjects = tuple(
            s for s in selection.source_subjects if s != validation_subject
        )

    @property
    def training_subjects(self) -> tuple[str, ...]:
        return self._training_subjects

    def _predict(
        self,
        subject: str,
        role: str,
        record: Mapping[str, Any],
        shots: int,
        settings: LaBraMManifestSettings,
    ) -> LaBraMTuningPrediction:
        if not isinstance(settings, (
            LaBraMTuningSettings, LaBraMLoRASettings, LaBraMAdapterSettings, LaBraMPromptSettings
        )):
            raise ValueError("explicit LaBraM tuning, LoRA, adapter or prompt settings required")
        if isinstance(settings, LaBraMTuningSettings) and (
            settings.partial_depth is not None and settings.partial_depth > len(
                self._source.backbone.blocks
            )
        ):
            raise ValueError("partial depth exceeds the source backbone")
        if isinstance(settings, LaBraMLoRASettings):
            for name in settings.target_modules:
                try:
                    module = self._source.get_submodule(name)
                except AttributeError as error:
                    raise ValueError(f"missing QKV target: {name}") from error
                if (
                    not isinstance(module, torch.nn.Linear)
                    or settings.rank > min(module.weight.shape)
                ):
                    raise ValueError("LoRA rank exceeds source QKV dimensions")
        if isinstance(settings, LaBraMAdapterSettings):
            for name in settings.target_modules:
                try:
                    block = self._source.get_submodule(name)
                except AttributeError as error:
                    raise ValueError(f"missing adapter target: {name}") from error
                norm = block.get_submodule("norm1")
                if (
                    not isinstance(norm, torch.nn.LayerNorm)
                    or settings.bottleneck_dim >= norm.normalized_shape[0]
                ):
                    raise ValueError("adapter width must be smaller than source block dimension")
        if isinstance(settings, LaBraMPromptSettings) and (
            not self._source.backbone.neural_tokenizer or self._source.backbone.fc_norm is not None
        ):
            raise ValueError("prompts require the verified neural-tokenizer CLS-head encoder")
        if state_digest(self._source) != self._source_sha:
            raise ValueError("owned source state changed")
        assets = self._assets[subject]
        episode: BCIProfileEpisode | ChoProfileEpisode
        if isinstance(assets, BCIProfileAssets):
            episode = load_bci_profile_b_episode(
                self._root, self._config, self._catalogs[subject], record,
                shots_per_class=shots, **asdict(assets),
            )
        elif isinstance(assets, ChoProfileAssets):
            episode = load_cho_profile_b_episode(
                self._root, self._config, self._catalogs[subject], record,
                shots_per_class=shots, **asdict(assets),
            )
        else:
            episode = load_mmidb_profile_b_episode(
                self._root, self._config, self._catalogs[subject], record,
                shots_per_class=shots, **asdict(assets),
            )
        adapted: (
            TuningEpisodeResult | LoRAEpisodeResult | AdapterEpisodeResult | PromptEpisodeResult
        )
        mask: TuningMask | LoRAMask | AdapterMask | PromptMask
        if isinstance(settings, LaBraMPromptSettings):
            with torch.random.fork_rng(devices=[]):
                torch.random.set_rng_state(
                    torch.Generator(device="cpu").manual_seed(settings.seed).get_state()
                )
                generator = ClassPrototypePromptGenerator(
                    embedding_dim=int(self._source.backbone.embed_dim), classes=self._classes,
                    prompt_tokens=settings.prompt_tokens, hidden_dim=settings.hidden_dim,
                )
            adapted = adapt_labram_prompt_support(
                self._source, generator,
                torch.from_numpy(episode.support_signals),
                torch.from_numpy(episode.support_labels),
                steps=settings.steps, learning_rate=settings.learning_rate,
                train_head=settings.train_head,
            )
            mask = PromptMask(
                settings.prompt_tokens, settings.hidden_dim,
                sum(p.numel() for p in adapted.model.generator.parameters()),
                settings.train_head, adapted.trainable_names, adapted.trainable_parameters,
            )
        elif isinstance(settings, LaBraMAdapterSettings):
            template = copy.deepcopy(self._source)
            # Seed new adapter tensors without changing the caller's CPU or CUDA RNG.
            with torch.random.fork_rng(devices=[]):
                torch.random.set_rng_state(
                    torch.Generator(device="cpu").manual_seed(settings.seed).get_state()
                )
                injection = inject_labram_adapters(
                    template, target_modules=settings.target_modules,
                    bottleneck_dim=settings.bottleneck_dim,
                )
            adapted = adapt_labram_adapter_support(
                template,
                torch.from_numpy(episode.support_signals),
                torch.from_numpy(episode.support_labels),
                steps=settings.steps, learning_rate=settings.learning_rate,
                train_head=settings.train_head,
            )
            mask = AdapterMask(
                injection, settings.train_head, adapted.trainable_names,
                adapted.trainable_parameters,
            )
            del template
        elif isinstance(settings, LaBraMLoRASettings):
            adapted = adapt_labram_lora_support(
                self._source,
                torch.from_numpy(episode.support_signals),
                torch.from_numpy(episode.support_labels),
                target_modules=settings.target_modules,
                rank=settings.rank, alpha=settings.alpha, seed=settings.seed,
                train_head=settings.train_head,
                steps=settings.steps, learning_rate=settings.learning_rate,
            )
            mask = adapted.mask
        else:
            adapted = adapt_labram_tuning_support(
                self._source,
                torch.from_numpy(episode.support_signals),
                torch.from_numpy(episode.support_labels),
                method=settings.method,
                partial_depth=settings.partial_depth,
                steps=settings.steps,
                learning_rate=settings.learning_rate,
            )
            mask = adapted.mask
        adapted_sha = state_digest(adapted.model)
        queries = torch.from_numpy(episode.query_signals)
        with torch.inference_mode():
            logits = torch.cat([
                adapted.model(queries[start:start + settings.query_batch_size])
                for start in range(0, len(queries), settings.query_batch_size)
            ]).clone()
        if (
            logits.shape != (len(episode.binding.query_trial_ids), self._classes)
            or not torch.isfinite(logits).all()
        ):
            raise ValueError("invalid query logits")
        if (
            state_digest(adapted.model) != adapted_sha
            or state_digest(self._source) != self._source_sha
        ):
            raise ValueError("query inference changed model state")
        return LaBraMTuningPrediction(
            episode.binding,
            role,
            self._selection.sha256,
            self._source_sha,
            settings,
            mask,
            adapted.losses,
            adapted_sha,
            logits,
            torch.from_numpy(episode.query_labels).clone(),
        )

    def predict_target(
        self,
        episode_record: Mapping[str, Any],
        *,
        shots_per_class: int,
        settings: LaBraMManifestSettings,
    ) -> LaBraMTuningPrediction:
        if self._validation_subject is not None:
            raise ValueError("outer-target prediction is unavailable during inner validation")
        return self._predict(
            self._selection.target_subject,
            "outer_target",
            episode_record,
            shots_per_class,
            settings,
        )

    def predict_validation(
        self,
        episode_record: Mapping[str, Any],
        *,
        shots_per_class: int,
        settings: LaBraMManifestSettings,
    ) -> LaBraMTuningPrediction:
        if self._validation_subject is None:
            raise ValueError("this runner has no inner-validation subject")
        return self._predict(
            self._validation_subject, "inner_validation", episode_record, shots_per_class, settings
        )
