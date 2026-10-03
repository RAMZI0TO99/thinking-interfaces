"""Continue a source-trained LaBraM support-prompt generator under audited roles."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.nn.utils import parametrize

from adaptation.labram_adapter import LaBraMAdapterBlock
from adaptation.labram_manifest import (
    LaBraMPromptSettings,
    LaBraMTuningManifestRunner,
    LaBraMTuningSettings,
    PromptMask,
)
from adaptation.labram_prompt import (
    ClassPrototypePromptGenerator,
    PromptEpisodeResult,
    adapt_labram_prompt_support,
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
class PromptSourceSettings:
    prompt_tokens: int
    hidden_dim: int
    seed: int
    train_head: bool
    steps_per_subject: int
    support_shots_per_class: int
    query_shots_per_class: int
    learning_rate: float

    @property
    def batch_size(self) -> int:
        """Fixed four-class BCI episode size; class-balanced shots are explicit."""
        return 4 * (self.support_shots_per_class + self.query_shots_per_class)

    def __post_init__(self) -> None:
        LaBraMPromptSettings(
            self.prompt_tokens,
            self.hidden_dim,
            self.seed,
            self.train_head,
            self.steps_per_subject,
            self.learning_rate,
            4 * (self.support_shots_per_class + self.query_shots_per_class),
        )
        if (
            type(self.support_shots_per_class) is not int
            or self.support_shots_per_class < 1
            or type(self.query_shots_per_class) is not int
            or self.query_shots_per_class < 1
            or self.batch_size > 8
        ):
            raise ValueError(
                "explicit class-balanced episode shots within the eight-trial ceiling required"
            )


@dataclass(frozen=True, slots=True)
class PromptContinuationSettings:
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
class PromptSourceCandidate:
    name: str
    source: PromptSourceSettings
    support: PromptContinuationSettings

    def __post_init__(self) -> None:
        require_names((self.name,), "candidate name")
        if not isinstance(self.source, PromptSourceSettings) or not isinstance(
            self.support, PromptContinuationSettings
        ):
            raise ValueError(
                "explicit source prompt and learned-generator continuation settings required"
            )


class TrainedPromptSourceModel(nn.Module):
    """Own the plain frozen classifier and its separately trained generator.

    The classifier keeps the verified plain architecture; only the generator and
    an explicitly enabled head ever receive gradients. Its state dictionary pins
    both components together for digest and checkpoint identity.
    """

    def __init__(
        self, classifier: LaBraMClassifier, generator: ClassPrototypePromptGenerator
    ) -> None:
        super().__init__()
        if not isinstance(classifier, LaBraMClassifier) or not isinstance(
            generator, ClassPrototypePromptGenerator
        ):
            raise ValueError("a plain LaBraM classifier and prompt generator are required")
        if (
            generator.embedding_dim != int(classifier.backbone.embed_dim)
            or generator.classes != classifier.head.out_features
        ):
            raise ValueError("generator width and classes must match the classifier head")
        self.classifier = classifier
        self.generator = generator


def validate_trained_prompt(
    model: TrainedPromptSourceModel, settings: PromptSourceSettings
) -> None:
    """Pin generator structure and non-tensor activation semantics."""
    if not isinstance(model, TrainedPromptSourceModel) or not isinstance(
        settings, PromptSourceSettings
    ):
        raise ValueError("trained prompt container and explicit source prompt metadata required")
    classifier = model.classifier
    backbone = classifier.backbone
    if (
        not backbone.neural_tokenizer
        or backbone.fc_norm is not None
        or any(isinstance(m, LaBraMAdapterBlock) for m in classifier.modules())
        or any(parametrize.is_parametrized(m) for m in classifier.modules())
    ):
        raise ValueError("the plain verified neural-tokenizer CLS-head classifier is required")
    generator = model.generator
    network = generator.network
    dim = int(backbone.embed_dim)
    if (
        type(generator) is not ClassPrototypePromptGenerator
        or generator.embedding_dim != dim
        or generator.classes != classifier.head.out_features
        or generator.prompt_tokens != settings.prompt_tokens
        or type(network) is not nn.Sequential
        or len(network) != 3
        or type(network[0]) is not nn.Linear
        or network[0].in_features != generator.classes * dim
        or network[0].out_features != settings.hidden_dim
        or network[0].weight.shape != (settings.hidden_dim, generator.classes * dim)
        or network[0].bias is None
        or network[0].bias.shape != (settings.hidden_dim,)
        or type(network[1]) is not nn.GELU
        or network[1].approximate != "none"
        or type(network[2]) is not nn.Linear
        or network[2].in_features != settings.hidden_dim
        or network[2].out_features != settings.prompt_tokens * dim
        or network[2].weight.shape != (settings.prompt_tokens * dim, settings.hidden_dim)
        or network[2].bias is None
        or network[2].bias.shape != (settings.prompt_tokens * dim,)
        or set(dict(generator.named_parameters()))
        != {"network.0.weight", "network.0.bias", "network.2.weight", "network.2.bias"}
        or tuple(generator.named_buffers())
    ):
        raise ValueError(
            "trained generator dimensions, activation or parameter structure differs"
        )
    if any(p.device.type != "cpu" or p.dtype != torch.float32 for p in model.parameters()):
        raise ValueError("trained prompt components require CPU float32 parameters")
    if any(not torch.isfinite(v).all() for v in model.state_dict().values()):
        raise ValueError("nonfinite trained prompt state")


def configure_trained_prompt(
    model: TrainedPromptSourceModel, settings: PromptSourceSettings, *, train_head: bool
) -> PromptMask:
    validate_trained_prompt(model, settings)
    if type(train_head) is not bool:
        raise ValueError("explicit prompt head policy required")
    model.requires_grad_(False)
    model.generator.requires_grad_(True)
    model.classifier.head.requires_grad_(train_head)
    model.eval()
    for p in model.parameters():
        p.grad = None
    names = tuple(n for n, p in model.named_parameters() if p.requires_grad)
    return PromptMask(
        settings.prompt_tokens,
        settings.hidden_dim,
        sum(p.numel() for p in model.generator.parameters()),
        train_head,
        names,
        sum(p.numel() for p in model.parameters() if p.requires_grad),
    )


def initialize_source_prompt(
    plain: LaBraMClassifier, settings: PromptSourceSettings
) -> tuple[TrainedPromptSourceModel, PromptMask]:
    classifier = copy.deepcopy(plain)
    configure_labram_tuning(classifier, method="linear")  # Rejects hybrid backbones.
    classifier.requires_grad_(False)
    with torch.random.fork_rng(devices=[]):
        torch.random.set_rng_state(
            torch.Generator(device="cpu").manual_seed(settings.seed).get_state()
        )
        generator = ClassPrototypePromptGenerator(
            embedding_dim=int(classifier.backbone.embed_dim),
            classes=int(classifier.head.out_features),
            prompt_tokens=settings.prompt_tokens,
            hidden_dim=settings.hidden_dim,
        )
    model = TrainedPromptSourceModel(classifier, generator)
    return model, configure_trained_prompt(model, settings, train_head=settings.train_head)


def continue_trained_prompt_support(
    source: TrainedPromptSourceModel,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    source_settings: PromptSourceSettings,
    settings: PromptContinuationSettings,
) -> PromptEpisodeResult:
    """Continue learned generator weights from each subject's permitted support.

    The existing support loop deep-copies both components, rebuilds the class
    conditioning from the supplied support and creates fresh SGD. This wrapper
    never reinitializes the generator and verifies that only the declared
    generator/head parameters of the returned episode may change.
    """
    if not isinstance(settings, PromptContinuationSettings):
        raise ValueError("explicit learned-prompt continuation settings required")
    validate_trained_prompt(source, source_settings)
    if (
        inputs.ndim != 3
        or inputs.shape[1:] != (len(source.classifier.channel_names), 800)
        or not inputs.is_floating_point()
        or not torch.isfinite(inputs).all()
        or targets.dtype != torch.long
        or targets.shape != (len(inputs),)
        or set(targets.tolist()) != set(range(source.classifier.head.out_features))
    ):
        raise ValueError("finite Profile B support and all-class integer labels required")
    source_sha = state_digest(source)
    frozen = {
        n: v.clone()
        for n, v in source.classifier.state_dict().items()
        if not (settings.train_head and n.startswith("head."))
    }
    result = adapt_labram_prompt_support(
        source.classifier,
        source.generator,
        inputs,
        targets,
        steps=settings.steps,
        learning_rate=settings.learning_rate,
        train_head=settings.train_head,
    )
    expected = {f"generator.{n}" for n in source.generator.state_dict()}
    if settings.train_head:
        expected.update(("classifier.head.weight", "classifier.head.bias"))
    if set(result.trainable_names) != expected:
        raise ValueError("prompt support mask differs from declared continuation")
    if any(
        not torch.equal(result.model.classifier.state_dict()[n], v) for n, v in frozen.items()
    ):
        raise ValueError("continuation changed a frozen classifier parameter or buffer")
    if state_digest(source) != source_sha:
        raise ValueError("continuation changed the trained prompt source")
    return result


@dataclass(frozen=True, slots=True)
class TrainedPromptPrediction:
    binding: BCIProfileBinding | ChoProfileBinding
    role: str
    selection_sha256: str
    source_state_sha256: str
    source_settings_sha256: str
    settings: PromptContinuationSettings
    mask: PromptMask
    support_losses: tuple[float, ...]
    adapted_state_sha256: str
    logits: torch.Tensor
    targets: torch.Tensor
    component_policy: str = "continue_source_trained_prompt_generator_without_reinitialization"
    engineering_only: bool = True
    source_training_history_verified: bool = False


class TrainedPromptManifestRunner:
    """Audited fixed roles for a supplied trained prompt pair; prior history is unverified."""

    def __init__(
        self,
        root: Path,
        protocol_config: Mapping[str, Any],
        catalogs: tuple[TrialCatalog, ...],
        selection_record: Mapping[str, Any],
        source: TrainedPromptSourceModel,
        profile_assets: Mapping[str, BCIProfileAssets | ChoProfileAssets],
        *,
        source_settings: PromptSourceSettings,
        source_state_sha256: str,
        outer_target: str,
        validation_subject: str | None = None,
    ) -> None:
        require_digest(source_state_sha256, "source_state_sha256")
        validate_trained_prompt(source, source_settings)
        if state_digest(source) != source_state_sha256:
            raise ValueError("trained source differs from its pinned state")
        # The classifier is already plain; admission never touches the trained pair.
        LaBraMTuningManifestRunner(
            root,
            protocol_config,
            catalogs,
            selection_record,
            source.classifier,
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
        settings: PromptContinuationSettings,
    ) -> TrainedPromptPrediction:
        if not isinstance(settings, PromptContinuationSettings):
            raise ValueError("explicit learned-prompt continuation settings required")
        validate_trained_prompt(self._source, self._source_settings)
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
        adapted = continue_trained_prompt_support(
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
        validate_trained_prompt(self._source, self._source_settings)
        if (
            state_digest(adapted.model) != adapted_sha
            or state_digest(self._source) != self._source_sha
        ):
            raise ValueError("query inference changed trained or adapted state")
        if logits.shape != (
            len(episode.query_labels), self._source.classifier.head.out_features
        ) or not torch.isfinite(logits).all():
            raise ValueError("invalid trained-prompt query logits")
        mask = PromptMask(
            self._source_settings.prompt_tokens,
            self._source_settings.hidden_dim,
            sum(p.numel() for p in adapted.model.generator.parameters()),
            settings.train_head,
            adapted.trainable_names,
            adapted.trainable_parameters,
        )
        return TrainedPromptPrediction(
            episode.binding,
            role,
            self._selection.sha256,
            self._source_sha,
            config_digest(asdict(self._source_settings)),
            settings,
            mask,
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
        settings: PromptContinuationSettings,
    ) -> TrainedPromptPrediction:
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
        settings: PromptContinuationSettings,
    ) -> TrainedPromptPrediction:
        if self._validation is not None:
            raise ValueError("outer-target prediction is unavailable during inner validation")
        return self._predict(
            self._selection.target_subject, "outer_target", record, shots_per_class, settings
        )
