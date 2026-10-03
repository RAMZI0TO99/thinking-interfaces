"""Bounded BCI LaBraM plain/LoRA/adapter source fitting and source-only LOSO."""

from __future__ import annotations

import copy
import platform
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from fractions import Fraction
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from torch import nn

from adaptation.labram_adapter_trained import (
    AdapterSourceCandidate,
    TrainedAdapterManifestRunner,
    TrainedAdapterPrediction,
    initialize_source_adapter,
    validate_trained_adapter,
)
from adaptation.labram_lora_support import LoRAMask
from adaptation.labram_lora_trained import (
    LoRASourceCandidate,
    TrainedLoRAManifestRunner,
    TrainedLoRAPrediction,
    initialize_source_lora,
    validate_trained_lora,
)
from adaptation.labram_manifest import (
    AdapterMask,
    LaBraMTuningManifestRunner,
    LaBraMTuningPrediction,
    LaBraMTuningSettings,
)
from adaptation.labram_prompt import prompted_labram_logits
from adaptation.labram_prompt_trained import (
    PromptSourceCandidate,
    TrainedPromptManifestRunner,
    TrainedPromptPrediction,
    TrainedPromptSourceModel,
    initialize_source_prompt,
    validate_trained_prompt,
)
from adaptation.labram_tuning import TuningMask, TuningMethod, configure_labram_tuning
from adaptation.source_checkpoint import SourceFitCheckpoint, source_execution_guard
from adaptation.source_selection import SelectionEvidence
from core.config import canonical_config_json, config_digest, config_snapshot
from core.provenance import capture_source, source_fingerprint
from encoder.labram import LaBraMClassifier
from evaluation.labram_parity import state_digest
from evaluation.phase2_cho_b_input_snapshot import _ChoBInputSnapshot
from evaluation.phase2_profile_binding import (
    BCIProfileAssets,
    BCIProfileEpisode,
    ChoProfileAssets,
    ChoProfileAssets60Hz,
    ChoProfileEpisode,
    load_bci_profile_b_episode,
    load_cho_profile_b_episode,
)
from evaluation.phase2_protocol import (
    TrialCatalog,
    nested_episode,
    require_digest,
    require_names,
    selection_gradient_ceiling,
    source_selection,
)
from evaluation.phase2_records import envelope
from scripts.audit_phase2_protocol import validate_protocol


@dataclass(frozen=True, slots=True)
class LaBraMSourceSettings:
    method: TuningMethod
    steps_per_subject: int
    batch_size: int
    learning_rate: float
    partial_depth: int | None = None

    def __post_init__(self) -> None:
        LaBraMTuningSettings(
            self.method,
            self.steps_per_subject,
            self.learning_rate,
            partial_depth=self.partial_depth,
            query_batch_size=self.batch_size,
        )


@dataclass(frozen=True, slots=True)
class LaBraMSourceCandidate:
    name: str
    source: LaBraMSourceSettings
    support: LaBraMTuningSettings

    def __post_init__(self) -> None:
        require_names((self.name,), "candidate name")
        if not isinstance(self.source, LaBraMSourceSettings) or not isinstance(
            self.support, LaBraMTuningSettings
        ):
            raise ValueError("explicit plain LaBraM source and support settings required")


type SourceCandidate = (
    LaBraMSourceCandidate | LoRASourceCandidate | AdapterSourceCandidate | PromptSourceCandidate
)


def _support_method(candidate: SourceCandidate) -> str:
    if isinstance(candidate, AdapterSourceCandidate):
        return "adapter"
    if isinstance(candidate, PromptSourceCandidate):
        return "support_prompt"
    return "lora" if isinstance(candidate, LoRASourceCandidate) else candidate.support.method


@dataclass(frozen=True, slots=True)
class SelectedLaBraM:
    source: LaBraMClassifier | TrainedPromptSourceModel
    evidence: SelectionEvidence


def _runtime(device: str = "cpu") -> dict[str, Any]:
    runtime: dict[str, Any] = {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "numpy": np.__version__,
        "braindecode": version("braindecode"),
        "device": device,
        "dtype": "float32",
        "torch_threads": torch.get_num_threads(),
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
    }
    if device == "cuda:0":
        runtime.update(
            cuda=torch.version.cuda,
            cudnn=cast(Callable[[], int | None], torch.backends.cudnn.version)(),
            gpu_name=torch.cuda.get_device_name(0),
            gpu_capability=list(torch.cuda.get_device_capability(0)),
            matmul_tf32=torch.backends.cuda.matmul.allow_tf32,
            cudnn_tf32=torch.backends.cudnn.allow_tf32,
            cudnn_benchmark=torch.backends.cudnn.benchmark,
            cudnn_deterministic=torch.backends.cudnn.deterministic,
        )
    return runtime


def _batch(
    episode: BCIProfileEpisode | ChoProfileEpisode, trial_ids: tuple[str, ...]
) -> tuple[torch.Tensor, torch.Tensor]:
    # At maximum shots the two audited partitions cover every retained source trial.
    rows = {
        name: (signals[i], labels[i])
        for names, signals, labels in (
            (episode.binding.support_trial_ids, episode.support_signals, episode.support_labels),
            (episode.binding.query_trial_ids, episode.query_signals, episode.query_labels),
        )
        for i, name in enumerate(names)
    }
    return (
        torch.from_numpy(np.stack([rows[name][0] for name in trial_ids])),
        torch.tensor([int(rows[name][1]) for name in trial_ids], dtype=torch.long),
    )


class BCILaBraMSourceSelector:
    """Fixed BCI roster, plain/LoRA/adapter/prompt masks and exact source-only selection.

    The caller supplies a pinned plain template. Its earlier training is unverified.
    The owned head is reset once with the explicit seed; every fit clones that same
    initialized state. Source SGD sees sampled permitted-source trials only. It uses
    declared linear/partial/full masks or learned component continuation, fixed
    eval-mode normalization, no momentum, no decay and no early stopping.
    Per-subject permutations share an isolated CPU sampling generator; batches wrap
    without reshuffling and record exact IDs.

    Candidates must evaluate the same support method. LoRA candidates initialize
    seeded effective-QKV weights per fit and retain learned weights in validation.
    Adapter candidates similarly preserve learned post-block adapters in validation.
    Prompt candidates fit a seeded generator over class-balanced support/query
    episodes and preserve its learned weights through validation, rebuilding the
    conditioning from each held-out subject's permitted support. This does not
    select between research methods or publish scientific cells.
    Hard ceilings: 256 total source/support gradient steps per invocation; source
    and query batches <= 8. Heavy compute/resource admission remains separate.
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
        template_state_sha256: str,
        candidates: tuple[SourceCandidate, ...],
        seed: int,
        shots_per_class: int,
        maximum_gradient_steps: int,
        source_device: str = "cpu",
        checkpoint_directory: Path | None = None,
        operator_compute_admitted: bool = False,
    ) -> None:
        require_digest(template_state_sha256, "template_state_sha256")
        if (
            not isinstance(candidates, tuple)
            or not candidates
            or any(
                not isinstance(
                    c,
                    (
                        LaBraMSourceCandidate,
                        LoRASourceCandidate,
                        AdapterSourceCandidate,
                        PromptSourceCandidate,
                    ),
                )
                for c in candidates
            )
        ):
            raise ValueError("explicit immutable LaBraM candidate roster required")
        require_names(tuple(c.name for c in candidates), "candidate names")
        hashes = [
            config_digest({"source": asdict(c.source), "support": asdict(c.support)})
            for c in candidates
        ]
        if len(set(hashes)) != len(hashes):
            raise ValueError("duplicate candidate settings")
        if len({_support_method(c) for c in candidates}) != 1:
            raise ValueError("selection candidates must evaluate one fixed support method")
        if type(seed) is not int or not 0 <= seed < 2**63:
            raise ValueError("explicit nonnegative 63-bit seed required")
        if type(maximum_gradient_steps) is not int or not 1 <= maximum_gradient_steps <= (
            selection_gradient_ceiling(root)
        ):
            raise ValueError("engineering gradient-step ceiling must be between 1 and 256")
        if any(c.source.batch_size > 8 or c.support.query_batch_size > 8 for c in candidates):
            raise ValueError("engineering source/query batch ceiling is eight trials")
        if source_device not in ("cpu", "cuda:0"):
            raise ValueError("source device must be cpu or cuda:0")
        extended = source_device != "cpu" or checkpoint_directory is not None
        if extended:
            if operator_compute_admitted is not True:
                raise ValueError("GPU/checkpoint execution needs explicit operator admission")
            if any(not isinstance(c, (LaBraMSourceCandidate, LoRASourceCandidate))
                   for c in candidates):
                raise ValueError("GPU/checkpoint source execution supports plain tuning and LoRA")
            if source_device == "cuda:0" and not torch.cuda.is_available():
                raise ValueError("CUDA source execution is unavailable")
            if checkpoint_directory is not None:
                allowed = root.resolve() / "runs" / "phase2"
                path = checkpoint_directory.resolve()
                if path == allowed or not path.is_relative_to(allowed):
                    raise ValueError("checkpoints require a dedicated directory inside runs/phase2")
        config: dict[str, Any] = config_snapshot(protocol_config)
        shots = validate_protocol(config)
        if type(shots_per_class) is not int or shots_per_class not in shots:
            raise ValueError("shots must belong to the audited protocol")
        # Validate the actual existing runner contract before any source fit.
        LaBraMTuningManifestRunner(
            root,
            config,
            catalogs,
            selection_record,
            source_template,
            profile_assets,
            outer_target=outer_target,
        )
        if state_digest(source_template) != template_state_sha256:
            raise ValueError("template differs from its pinned state")
        initial = copy.deepcopy(source_template).eval()
        for candidate in candidates:
            if isinstance(candidate, AdapterSourceCandidate):
                initialize_source_adapter(initial, candidate.source)
            elif isinstance(candidate, LoRASourceCandidate):
                initialize_source_lora(initial, candidate.source)  # Validate before fitting.
            elif isinstance(candidate, PromptSourceCandidate):
                initialize_source_prompt(initial, candidate.source)  # Validate before fitting.
            else:
                for settings in (candidate.source, candidate.support):
                    configure_labram_tuning(
                        initial,
                        method=settings.method,
                        partial_depth=settings.partial_depth,
                    )
            if any(len(c.trial_ids) < candidate.source.batch_size for c in catalogs):
                raise ValueError("source batch exceeds a retained subject's trial count")
        with torch.random.fork_rng(devices=[]):
            torch.random.set_rng_state(torch.Generator(device="cpu").manual_seed(seed).get_state())
            initial.head.reset_parameters()
        for parameter in initial.parameters():
            parameter.grad = None
        self._initial = initial
        self._initial_sha = state_digest(initial)
        self._root = root.resolve()
        self._config = config
        self._catalogs = {c.subject: c for c in catalogs}
        self._assets = dict(profile_assets)
        self._selection = source_selection(catalogs, target=outer_target)
        self._selection_record = config_snapshot(selection_record)
        self._episodes = {
            c.subject: nested_episode(c, shots=shots, protocol_sha256=config_digest(config))
            for c in catalogs
        }
        self._maximum_shots = shots[-1]
        self._cho_b_inputs = (
            _ChoBInputSnapshot(
                self._root, config,
                tuple(self._catalogs[s] for s in self._selection.source_subjects),
                {
                    s: cast(ChoProfileAssets60Hz, self._assets[s])
                    for s in self._selection.source_subjects
                },
            )
            if self._selection.dataset == "cho2017"
            and all(isinstance(c, (LaBraMSourceCandidate, LoRASourceCandidate)) for c in candidates)
            and all(isinstance(a, ChoProfileAssets60Hz) for a in self._assets.values())
            else None
        )
        self._shots = shots_per_class
        self._seed = seed
        self._candidates = candidates
        self._maximum = maximum_gradient_steps
        self._source_device = source_device
        self._checkpoint_directory = checkpoint_directory
        self._extended_execution = extended
        self._contract: dict[str, Any] = {
            "method": "labram_" + _support_method(candidates[0]),
            "dataset": self._selection.dataset,
            "selection": asdict(self._selection),
            "protocol_sha256": config_digest(config),
            "profile_assets": {n: asdict(a) for n, a in self._assets.items()},
            "candidates": [asdict(c) for c in candidates],
            "head_and_sampling_seed": seed,
            "shots_per_class": shots_per_class,
            "maximum_gradient_steps": maximum_gradient_steps,
            "template_state_sha256": template_state_sha256,
            "initial_state_sha256": self._initial_sha,
            "prior_template_training_verified": False,
            "initialization": "pinned_supplied_backbone_and_fresh_seeded_linear_head",
            "source_policy": "all_non_target_subjects; inner_validation_also_excluded",
            "source_trial_pool": "all_profile_a_retained_trials_joined_to_profile_b",
            "extra_input_scale": 1.0,
            "sampling_rate_hz": 200,
            "samples_per_trial": 800,
            "stored_unit_volts": 0.0001,
            "score": "mean_subject_balanced_accuracy_exact_rational",
            "tie_break": "first_in_declared_candidate_order",
            "early_stopping": False,
            "source": asdict(capture_source(self._root)),
            "runtime": _runtime(source_device),
            "engineering_only": True,
            "scientific_evaluation": False,
        }
        if extended:
            self._contract["source_execution"] = {
                "source_device": source_device,
                "support_query_device": "cpu",
                "checkpoint_policy": (
                    "immutable_every_gradient_step_all_generations_retained"
                    if checkpoint_directory is not None else "disabled"
                ),
                "optimizer_resume": "stateless_sgd_only",
            }

    @property
    def contract(self) -> dict[str, Any]:
        return config_snapshot(self._contract)

    def _check_context(self) -> None:
        if state_digest(self._initial) != self._initial_sha:
            raise ValueError("owned initialization state changed")
        if _runtime(self._source_device) != self._contract["runtime"]:
            raise ValueError("execution runtime differs from the pinned contract")
        if source_fingerprint(self._root) != self._contract["source"]["source_sha256"]:
            raise ValueError("source/config identity changed")

    def _admit(self, steps: int) -> None:
        self._check_context()
        if steps > self._maximum:
            raise ValueError("requested work exceeds the declared gradient-step ceiling")

    def _fit(
        self, candidate: SourceCandidate, validation_subject: str | None
    ) -> tuple[LaBraMClassifier | TrainedPromptSourceModel, dict[str, Any]]:
        try:
            return self._fit_impl(candidate, validation_subject)
        except BaseException:
            self._clear_cho_b_inputs()
            raise

    def _fit_impl(
        self, candidate: SourceCandidate, validation_subject: str | None
    ) -> tuple[LaBraMClassifier | TrainedPromptSourceModel, dict[str, Any]]:
        if isinstance(candidate, PromptSourceCandidate):
            return self._fit_prompt(candidate, validation_subject)
        if not self._extended_execution:
            return self._fit_sgd(candidate, validation_subject, None)
        cuda = self._source_device == "cuda:0"
        source_execution_guard(self._root, cuda=cuda)
        with torch.random.fork_rng(devices=[0] if cuda else []):
            if self._checkpoint_directory is None:
                return self._fit_sgd(candidate, validation_subject, None)
            checkpoint = SourceFitCheckpoint(
                self._root, self._checkpoint_directory, self.contract,
                {"candidate_sha256": config_digest(asdict(candidate)),
                 "validation_subject": validation_subject},
            )
            with checkpoint.session():
                return self._fit_sgd(candidate, validation_subject, checkpoint)

    def _fit_sgd(
        self, candidate: LaBraMSourceCandidate | LoRASourceCandidate | AdapterSourceCandidate,
        validation_subject: str | None, checkpoint: SourceFitCheckpoint | None,
    ) -> tuple[LaBraMClassifier, dict[str, Any]]:
        subjects = tuple(s for s in self._selection.source_subjects if s != validation_subject)
        settings = candidate.source
        mask: TuningMask | LoRAMask | AdapterMask
        if isinstance(candidate, AdapterSourceCandidate):
            model, mask = initialize_source_adapter(self._initial, candidate.source)
        elif isinstance(candidate, LoRASourceCandidate):
            model, mask = initialize_source_lora(self._initial, candidate.source)
        else:
            model = copy.deepcopy(self._initial).eval()
            mask = configure_labram_tuning(
                model,
                method=candidate.source.method,
                partial_depth=candidate.source.partial_depth,
            )
        initial_sha = state_digest(model)
        frozen = {
            n: v.clone() for n, v in model.state_dict().items() if n not in mask.trainable_names
        }
        model.to(self._source_device)
        selected = [p for p in model.parameters() if p.requires_grad]
        optimizer = torch.optim.SGD(selected, lr=settings.learning_rate)
        criterion = nn.CrossEntropyLoss()
        generator = torch.Generator(device="cpu").manual_seed(self._seed)
        history: list[dict[str, Any]] = []
        identities: dict[str, Any] = {}
        resumed_identities: dict[str, Any] = {}
        sampling_state: torch.Tensor | None = None
        cuda = self._source_device == "cuda:0"
        if checkpoint is not None:
            history, resumed_identities, sampling_state = checkpoint.restore(
                model, optimizer, cuda=cuda,
            )
        resumed_steps = len(history)
        if resumed_steps > len(subjects) * settings.steps_per_subject:
            raise ValueError("checkpoint exceeds the declared fit budget")
        if any(not torch.equal(model.state_dict()[n].cpu(), v) for n, v in frozen.items()):
            raise ValueError("checkpoint changed frozen source state")
        cursor = 0
        for subject in subjects:
            catalog = self._catalogs[subject]
            fit_assets = self._assets[subject]
            episode: BCIProfileEpisode | ChoProfileEpisode
            if isinstance(fit_assets, BCIProfileAssets):
                episode = load_bci_profile_b_episode(
                    self._root,
                    self._config,
                    catalog,
                    envelope("episode_manifest", self._episodes[subject].payload()),
                    shots_per_class=self._maximum_shots,
                    **asdict(fit_assets),
                )
            elif self._cho_b_inputs is not None and isinstance(fit_assets, ChoProfileAssets60Hz):
                episode = self._cho_b_inputs.load(
                    self._config, catalog,
                    envelope("episode_manifest", self._episodes[subject].payload()),
                    shots_per_class=self._maximum_shots, profile_assets=fit_assets,
                )
            else:
                episode = load_cho_profile_b_episode(
                    self._root,
                    self._config,
                    catalog,
                    envelope("episode_manifest", self._episodes[subject].payload()),
                    shots_per_class=self._maximum_shots,
                    **asdict(fit_assets),
                )
            ids = episode.binding.support_trial_ids + episode.binding.query_trial_ids
            if len(ids) != len(catalog.trial_ids) or set(ids) != set(catalog.trial_ids):
                raise ValueError("maximum-pool binding must cover every retained source trial")
            identities[subject] = {
                "catalog_sha256": catalog.sha256,
                "binding": asdict(episode.binding),
            }
            if subject in resumed_identities and (
                config_digest(identities[subject]) != config_digest(resumed_identities[subject])
            ):
                raise ValueError("checkpoint source input identity differs")
            permutation = torch.randperm(len(catalog.trial_ids), generator=generator).tolist()
            for step in range(settings.steps_per_subject):
                positions = range(step * settings.batch_size, (step + 1) * settings.batch_size)
                trial_ids = tuple(
                    catalog.trial_ids[permutation[i % len(permutation)]] for i in positions
                )
                cursor += 1
                if cursor <= resumed_steps:
                    previous = history[cursor - 1]
                    if (previous["step"] != cursor or previous["subject"] != subject
                            or previous["subject_step"] != step + 1
                            or tuple(previous["trial_ids"]) != trial_ids):
                        raise ValueError("checkpoint progress differs from the declared iterator")
                    if cursor == resumed_steps and (
                        sampling_state is None
                        or not torch.equal(sampling_state, generator.get_state())
                    ):
                        raise ValueError("checkpoint sampling RNG differs from the iterator")
                    continue
                if self._extended_execution:
                    self._check_context()
                    source_execution_guard(self._root, cuda=cuda)
                inputs, targets = _batch(episode, trial_ids)
                inputs, targets = inputs.to(self._source_device), targets.to(self._source_device)
                optimizer.zero_grad(set_to_none=True)
                loss = criterion(model(inputs), targets)
                if not torch.isfinite(loss):
                    raise ValueError("nonfinite source loss")
                loss.backward()
                if any(p.grad is None or not torch.isfinite(p.grad).all() for p in selected):
                    raise ValueError("missing or nonfinite selected source gradient")
                optimizer.step()
                if any(not torch.isfinite(p).all() for p in selected):
                    raise ValueError("nonfinite source parameters")
                history.append(
                    {
                        "step": len(history) + 1,
                        "subject": subject,
                        "trial_ids": trial_ids,
                        "subject_step": step + 1,
                        "iterator_wraps": ((step + 1) * settings.batch_size - 1)
                        // len(permutation),
                        "loss": float(loss.detach()),
                        "state_sha256_after": state_digest(model),
                    }
                )
                if checkpoint is not None:
                    checkpoint.publish(model, optimizer, history, identities,
                                       generator.get_state(), cuda=cuda)
            del episode
        optimizer.zero_grad(set_to_none=True)
        model.cpu()
        if any(not torch.equal(model.state_dict()[n], v) for n, v in frozen.items()):
            raise ValueError("source fitting changed a frozen parameter or buffer")
        if state_digest(self._initial) != self._initial_sha:
            raise ValueError("source fitting changed the owned initialization")
        if isinstance(candidate, LoRASourceCandidate):
            validate_trained_lora(model, candidate.source)
        if isinstance(candidate, AdapterSourceCandidate):
            validate_trained_adapter(model, candidate.source)
        return model, {
            "candidate": candidate.name,
            "candidate_sha256": config_digest(asdict(candidate)),
            "validation_subject": validation_subject,
            "training_subjects": subjects,
            "input_identities": identities,
            "head_and_sampling_seed": self._seed,
            "settings": asdict(settings),
            "mask": asdict(mask),
            "optimizer": {"name": "SGD", "momentum": 0, "weight_decay": 0, "fresh": True},
            "normalization_and_dropout": "all_modules_eval_affine_follows_mask",
            "initial_state_sha256": initial_sha,
            "fitted_state_sha256": state_digest(model),
            "steps": history,
            "history_scope": "complete_for_this_bounded_fit_only",
            "engineering_only": True,
        }

    def _fit_prompt(
        self, candidate: PromptSourceCandidate, validation_subject: str | None
    ) -> tuple[TrainedPromptSourceModel, dict[str, Any]]:
        """Class-balanced episodic source fits that preserve the learned generator.

        Each step draws distinct class-stratified support/query trials from one
        subject's retained pool, conditions the generator on batch-one frozen
        unprompted support features and takes cross entropy only on that step's
        query trials. Support features are memoized per subject because the
        frozen backbone makes them identical for every later episode use.
        """
        settings = candidate.source
        classes = int(self._initial.head.out_features)
        take = settings.support_shots_per_class + settings.query_shots_per_class
        subjects = tuple(s for s in self._selection.source_subjects if s != validation_subject)
        model, mask = initialize_source_prompt(self._initial, settings)
        initial_sha = state_digest(model)
        selected = [p for p in model.parameters() if p.requires_grad]
        optimizer = torch.optim.SGD(selected, lr=settings.learning_rate)
        criterion = nn.CrossEntropyLoss()
        generator = torch.Generator(device="cpu").manual_seed(self._seed)
        history: list[dict[str, Any]] = []
        identities: dict[str, Any] = {}
        frozen = {
            n: v.clone() for n, v in model.state_dict().items() if n not in mask.trainable_names
        }
        for subject in subjects:
            catalog = self._catalogs[subject]
            fit_assets = self._assets[subject]
            episode: BCIProfileEpisode | ChoProfileEpisode
            if isinstance(fit_assets, BCIProfileAssets):
                episode = load_bci_profile_b_episode(
                    self._root,
                    self._config,
                    catalog,
                    envelope("episode_manifest", self._episodes[subject].payload()),
                    shots_per_class=self._maximum_shots,
                    **asdict(fit_assets),
                )
            else:
                episode = load_cho_profile_b_episode(
                    self._root,
                    self._config,
                    catalog,
                    envelope("episode_manifest", self._episodes[subject].payload()),
                    shots_per_class=self._maximum_shots,
                    **asdict(fit_assets),
                )
            ids = episode.binding.support_trial_ids + episode.binding.query_trial_ids
            if len(ids) != len(catalog.trial_ids) or set(ids) != set(catalog.trial_ids):
                raise ValueError("maximum-pool binding must cover every retained source trial")
            rows = {
                name: (signals[i], labels[i])
                for names, signals, labels in (
                    (
                        episode.binding.support_trial_ids,
                        episode.support_signals,
                        episode.support_labels,
                    ),
                    (
                        episode.binding.query_trial_ids,
                        episode.query_signals,
                        episode.query_labels,
                    ),
                )
                for i, name in enumerate(names)
            }
            by_class = {
                c: [name for name in catalog.trial_ids if int(rows[name][1]) == c]
                for c in range(classes)
            }
            if any(len(members) < take for members in by_class.values()):
                raise ValueError("class-balanced episodes need enough retained trials per class")
            identities[subject] = {
                "catalog_sha256": catalog.sha256,
                "binding": asdict(episode.binding),
            }
            permutation = {
                c: torch.randperm(len(by_class[c]), generator=generator).tolist()
                for c in range(classes)
            }
            features: dict[str, torch.Tensor] = {}
            for step in range(settings.steps_per_subject):
                support_ids: list[str] = []
                query_ids: list[str] = []
                for c in range(classes):
                    members = [
                        by_class[c][permutation[c][(step * take + i) % len(permutation[c])]]
                        for i in range(take)
                    ]
                    support_ids.extend(members[: settings.support_shots_per_class])
                    query_ids.extend(members[settings.support_shots_per_class :])
                stacked = []
                for name in support_ids:
                    if name not in features:
                        with torch.no_grad():
                            features[name] = model.classifier.backbone(
                                torch.from_numpy(rows[name][0]).unsqueeze(0),
                                ch_names=list(model.classifier.channel_names),
                                return_features=True,
                            )["cls_token"][0].detach().clone()
                    stacked.append(features[name])
                support_labels = torch.tensor(
                    [int(rows[name][1]) for name in support_ids], dtype=torch.long
                )
                inputs = torch.from_numpy(np.stack([rows[name][0] for name in query_ids]))
                targets = torch.tensor(
                    [int(rows[name][1]) for name in query_ids], dtype=torch.long
                )
                optimizer.zero_grad(set_to_none=True)
                prompts = model.generator(torch.stack(stacked), support_labels)
                loss = criterion(
                    prompted_labram_logits(model.classifier, inputs, prompts), targets
                )
                if not torch.isfinite(loss):
                    raise ValueError("nonfinite source loss")
                loss.backward()
                if any(p.grad is None or not torch.isfinite(p.grad).all() for p in selected):
                    raise ValueError("missing or nonfinite selected source gradient")
                optimizer.step()
                if any(not torch.isfinite(p).all() for p in selected):
                    raise ValueError("nonfinite source parameters")
                history.append(
                    {
                        "step": len(history) + 1,
                        "subject": subject,
                        "trial_ids": tuple(support_ids + query_ids),
                        "support_trial_ids": tuple(support_ids),
                        "query_trial_ids": tuple(query_ids),
                        "subject_step": step + 1,
                        "iterator_wraps": max(
                            ((step + 1) * take - 1) // len(by_class[c]) for c in range(classes)
                        ),
                        "loss": float(loss.detach()),
                        "state_sha256_after": state_digest(model),
                    }
                )
            del episode
        optimizer.zero_grad(set_to_none=True)
        if any(not torch.equal(model.state_dict()[n], v) for n, v in frozen.items()):
            raise ValueError("source fitting changed a frozen parameter or buffer")
        if state_digest(self._initial) != self._initial_sha:
            raise ValueError("source fitting changed the owned initialization")
        validate_trained_prompt(model, settings)
        return model, {
            "candidate": candidate.name,
            "candidate_sha256": config_digest(asdict(candidate)),
            "validation_subject": validation_subject,
            "training_subjects": subjects,
            "input_identities": identities,
            "head_and_sampling_seed": self._seed,
            "settings": asdict(settings),
            "mask": asdict(mask),
            "optimizer": {"name": "SGD", "momentum": 0, "weight_decay": 0, "fresh": True},
            "normalization_and_dropout": "all_modules_eval_affine_follows_mask",
            "initial_state_sha256": initial_sha,
            "fitted_state_sha256": state_digest(model),
            "steps": history,
            "history_scope": "complete_for_this_bounded_fit_only",
            "engineering_only": True,
        }

    def _fold(self, candidate: SourceCandidate, subject: str) -> dict[str, Any]:
        model, fit = self._fit(candidate, subject)
        prediction: (
            LaBraMTuningPrediction
            | TrainedLoRAPrediction
            | TrainedAdapterPrediction
            | TrainedPromptPrediction
        )
        if isinstance(candidate, AdapterSourceCandidate):
            assert isinstance(model, LaBraMClassifier)
            adapter_runner = TrainedAdapterManifestRunner(
                self._root, self._config, tuple(self._catalogs.values()), self._selection_record,
                model, self._assets, source_settings=candidate.source,
                source_state_sha256=fit["fitted_state_sha256"],
                outer_target=self._selection.target_subject, validation_subject=subject,
            )
            prediction = adapter_runner.predict_validation(
                envelope("episode_manifest", self._episodes[subject].payload()),
                shots_per_class=self._shots, settings=candidate.support,
            )
        elif isinstance(candidate, PromptSourceCandidate):
            assert isinstance(model, TrainedPromptSourceModel)
            prompt_runner = TrainedPromptManifestRunner(
                self._root, self._config, tuple(self._catalogs.values()), self._selection_record,
                model, self._assets, source_settings=candidate.source,
                source_state_sha256=fit["fitted_state_sha256"],
                outer_target=self._selection.target_subject, validation_subject=subject,
            )
            prediction = prompt_runner.predict_validation(
                envelope("episode_manifest", self._episodes[subject].payload()),
                shots_per_class=self._shots, settings=candidate.support,
            )
        elif isinstance(candidate, LoRASourceCandidate):
            assert isinstance(model, LaBraMClassifier)
            trained_runner = TrainedLoRAManifestRunner(
                self._root, self._config, tuple(self._catalogs.values()), self._selection_record,
                model, self._assets, source_settings=candidate.source,
                source_state_sha256=fit["fitted_state_sha256"],
                outer_target=self._selection.target_subject, validation_subject=subject,
            )
            prediction = trained_runner.predict_validation(
                envelope("episode_manifest", self._episodes[subject].payload()),
                shots_per_class=self._shots, settings=candidate.support,
            )
        else:
            assert isinstance(model, LaBraMClassifier)
            runner = LaBraMTuningManifestRunner(
                self._root,
                self._config,
                tuple(self._catalogs.values()),
                self._selection_record,
                model,
                self._assets,
                outer_target=self._selection.target_subject,
                validation_subject=subject,
            )
            prediction = runner.predict_validation(
                envelope("episode_manifest", self._episodes[subject].payload()),
                shots_per_class=self._shots,
                settings=candidate.support,
            )
        if prediction.source_state_sha256 != fit["fitted_state_sha256"]:
            raise ValueError("validation source state differs from its fit history")
        classes = prediction.logits.shape[1]
        confusion = np.zeros((classes, classes), dtype=np.int64)
        np.add.at(confusion, (prediction.targets.numpy(), prediction.logits.argmax(1).numpy()), 1)
        score = (
            sum(
                (
                    Fraction(int(confusion[i, i]), int(confusion[i].sum()))
                    for i in range(classes)
                ),
                start=Fraction(),
            )
            / classes
        )
        return {
            "candidate": candidate.name,
            "validation_subject": subject,
            "source_fit": fit,
            "binding": asdict(prediction.binding),
            "support_mask": asdict(prediction.mask),
            "support_losses": prediction.support_losses,
            "adapted_state_sha256": prediction.adapted_state_sha256,
            "confusion_matrix": confusion.tolist(),
            "balanced_accuracy": [score.numerator, score.denominator],
            **({
                "component_policy": prediction.component_policy,
                "support_source_state_sha256": prediction.source_state_sha256,
                "source_settings_sha256": prediction.source_settings_sha256,
            } if isinstance(
                prediction,
                (TrainedLoRAPrediction, TrainedAdapterPrediction, TrainedPromptPrediction),
            ) else {}),
        }

    def _evidence(self, payload: Mapping[str, Any]) -> SelectionEvidence:
        try:
            if self._cho_b_inputs is not None:
                self._cho_b_inputs.verify(self._config)
            return self._verified_evidence(payload)
        finally:
            self._clear_cho_b_inputs()

    def _clear_cho_b_inputs(self) -> None:
        if self._cho_b_inputs is not None:
            self._cho_b_inputs.clear()

    def _verified_evidence(self, payload: Mapping[str, Any]) -> SelectionEvidence:
        self._check_context()
        return SelectionEvidence(
            canonical_config_json(
                envelope(
                    "engineering_smoke",
                    {
                        "purpose": "bounded_labram_source_selection",
                        "contract": self.contract,
                        "contract_sha256": config_digest(self._contract),
                        **payload,
                    },
                )
            )
        )

    def run_fold(self, *, candidate_name: str, validation_subject: str) -> SelectionEvidence:
        try:
            return self._run_fold(
                candidate_name=candidate_name, validation_subject=validation_subject,
            )
        finally:
            self._clear_cho_b_inputs()

    def _run_fold(self, *, candidate_name: str, validation_subject: str) -> SelectionEvidence:
        candidate = next((c for c in self._candidates if c.name == candidate_name), None)
        if candidate is None:
            raise ValueError("candidate is outside the fixed roster")
        if validation_subject not in self._selection.source_subjects:
            raise ValueError("validation must be a source subject, never the outer target")
        sources = len(self._selection.source_subjects)
        self._admit(
            (sources - 1) * candidate.source.steps_per_subject + candidate.support.steps
        )
        fold = self._fold(candidate, validation_subject)
        return self._evidence({"complete": False, "folds": [fold], "selected_candidate": None})

    def run_selection(self) -> SelectedLaBraM:
        """All source-subject folds, then a fresh all-source fit of the winner.

        Optional checkpoints resume source SGD only, after full admission. Support
        and query evaluation restart from that fit. No external scores, outer-target
        prediction or scientific publication; verify the returned mutable model on reuse.
        """
        try:
            return self._run_selection()
        finally:
            self._clear_cho_b_inputs()

    def _run_selection(self) -> SelectedLaBraM:
        sources = len(self._selection.source_subjects)
        self._admit(
            sum(
                sources * ((sources - 1) * c.source.steps_per_subject + c.support.steps)
                for c in self._candidates
            )
            + sources * max(c.source.steps_per_subject for c in self._candidates)
        )
        folds = [
            self._fold(c, fold.validation_subject)
            for c in self._candidates
            for fold in self._selection.inner_folds
        ]
        scores = [
            sum(
                (Fraction(*f["balanced_accuracy"]) for f in folds if f["candidate"] == c.name),
                start=Fraction(),
            )
            / len(self._selection.inner_folds)
            for c in self._candidates
        ]
        winner = self._candidates[max(range(len(scores)), key=lambda i: scores[i])]
        model, fit = self._fit(winner, None)
        return SelectedLaBraM(
            model,
            self._evidence(
                {
                    "complete": True,
                    "folds": folds,
                    "selected_candidate": winner.name,
                    "scores": [
                        {
                            "candidate": c.name,
                            "mean_balanced_accuracy": [s.numerator, s.denominator],
                        }
                        for c, s in zip(self._candidates, scores, strict=True)
                    ],
                    "final_source_fit": fit,
                    "outer_target_predictions_performed": False,
                }
            ),
        )
