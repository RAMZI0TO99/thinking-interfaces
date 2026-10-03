"""Class-conditioned support prompts on the actual LaBraM token/attention path."""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from typing import cast

import torch
from torch import nn

from adaptation.labram_tuning import configure_labram_tuning
from encoder.labram import LaBraMClassifier, electrode_embedding_indices


class ClassPrototypePromptGenerator(nn.Module):
    """Pool features within each class, concatenate in label order, then generate.

    Unlike independently averaging features and label embeddings, class means
    retain the signal/label association when balanced support labels are swapped.
    This is the local same-backbone prompt method, not the TCPL architecture.
    """

    def __init__(self, *, embedding_dim: int, classes: int, prompt_tokens: int, hidden_dim: int):
        super().__init__()
        if (
            any(
                type(n) is not int or n < 1
                for n in (embedding_dim, classes, prompt_tokens, hidden_dim)
            )
            or classes < 2
        ):
            raise ValueError("positive integer dimensions and at least two classes are required")
        self.embedding_dim = embedding_dim
        self.classes = classes
        self.prompt_tokens = prompt_tokens
        self.network = nn.Sequential(
            nn.Linear(classes * embedding_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, prompt_tokens * embedding_dim),
        )

    def forward(self, features: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        if (
            features.ndim != 2
            or features.shape[0] < 1
            or features.shape[1] != self.embedding_dim
            or not features.is_floating_point()
            or labels.shape != (features.shape[0],)
            or labels.dtype != torch.long
            or labels.device != features.device
            or not torch.isfinite(features).all()
            or set(labels.tolist()) != set(range(self.classes))
        ):
            raise ValueError(
                "finite support features and integer labels covering all classes required"
            )
        prototypes = torch.stack(
            [features[labels == label].mean(0) for label in range(self.classes)]
        )
        prompts = self.network(prototypes.flatten().unsqueeze(0))
        return cast(torch.Tensor, prompts.reshape(1, self.prompt_tokens, self.embedding_dim))


def prompted_labram_logits(
    classifier: LaBraMClassifier, inputs: torch.Tensor, prompts: torch.Tensor
) -> torch.Tensor:
    """Insert tokens once after position/time assembly, preserving CLS at index 0.

    Tokens persist through every original block. They do not consume electrode
    or temporal embedding slots. An EMPTY prefix reproduces the normal forward;
    a zero-valued nonempty prefix is not an identity because attention includes it.
    This path supports the verified neural-tokenizer, CLS-head configuration only.
    """
    backbone = classifier.backbone
    if (
        not backbone.neural_tokenizer
        or backbone.fc_norm is not None
        or any(module.training for module in classifier.modules())
    ):
        raise ValueError("the verified CLS encoder must remain entirely in evaluation mode")
    weight = next(classifier.parameters())
    if (
        inputs.ndim != 3
        or any(size < 1 for size in inputs.shape)
        or inputs.shape[1] != len(classifier.channel_names)
        or inputs.shape[2] != backbone.patch_embed[0].n_times
        or inputs.dtype != weight.dtype
        or inputs.device != weight.device
        or not torch.isfinite(inputs).all()
        or prompts.ndim != 3
        or prompts.shape[0] not in (1, inputs.shape[0])
        or prompts.shape[2] != backbone.embed_dim
        or prompts.dtype != weight.dtype
        or prompts.device != weight.device
        or not torch.isfinite(prompts).all()
    ):
        raise ValueError("finite EEG inputs and compatible prompt tensors are required")
    batch = inputs.shape[0]
    patches = backbone.patch_embed(inputs)
    tokens = torch.cat((backbone.cls_token.expand(batch, -1, -1), patches), dim=1)
    indices = [0, *electrode_embedding_indices(classifier.channel_names)]
    if backbone.position_embedding is not None:
        tokens += backbone._adj_position_embedding(
            pos_embed_used=backbone.position_embedding[:, indices], batch_size=batch
        )
    tokens[:, 1:] += backbone._adj_temporal_embedding(
        num_ch=inputs.shape[1], batch_size=batch, dim_embed=backbone.embed_dim
    )
    tokens = backbone.pos_drop(tokens)
    tokens = torch.cat((tokens[:, :1], prompts.expand(batch, -1, -1), tokens[:, 1:]), dim=1)
    for block in backbone.blocks:
        tokens = block(tokens)
    tokens = backbone.norm(tokens)
    return cast(torch.Tensor, classifier.head(tokens[:, 0]))


class SupportPromptedLaBraM(nn.Module):
    """One isolated episode, with copied support-only frozen encoder features."""

    def __init__(
        self,
        source: LaBraMClassifier,
        generator: ClassPrototypePromptGenerator,
        support_inputs: torch.Tensor,
        support_labels: torch.Tensor,
    ) -> None:
        super().__init__()
        self.classifier = copy.deepcopy(source)
        configure_labram_tuning(self.classifier, method="linear")  # rejects hybrid backbones
        self.classifier.eval().requires_grad_(False)
        if (
            generator.embedding_dim != self.classifier.backbone.embed_dim
            or generator.classes != self.classifier.head.out_features
        ):
            raise ValueError("generator width and classes must match the source encoder/head")
        if (
            support_inputs.ndim != 3
            or any(size < 1 for size in support_inputs.shape)
            or support_inputs.shape[1] != len(self.classifier.channel_names)
            or support_inputs.shape[2] != self.classifier.backbone.patch_embed[0].n_times
            or not support_inputs.is_floating_point()
            or not torch.isfinite(support_inputs).all()
            or support_labels.shape != (support_inputs.shape[0],)
            or support_labels.dtype != torch.long
            or set(support_labels.tolist()) != set(range(generator.classes))
        ):
            raise ValueError(
                "finite named-channel support and valid labels for every class required"
            )
        weight = next(self.classifier.parameters())
        self.generator = copy.deepcopy(generator).to(device=weight.device, dtype=weight.dtype)
        inputs = support_inputs.detach().to(device=weight.device, dtype=weight.dtype).clone()
        labels = support_labels.detach().to(device=weight.device).clone()
        # Fixed batch-one extraction keeps each cached trial independent of its
        # support batch position/backend batching. Class pooling still has the
        # ordinary floating-point reduction tolerance for multiple shots/class.
        with torch.no_grad():
            features = torch.cat(
                [
                    self.classifier.backbone(
                        trial.unsqueeze(0),
                        ch_names=list(self.classifier.channel_names),
                        return_features=True,
                    )["cls_token"]
                    for trial in inputs
                ]
            )
        self.register_buffer("support_features", features.detach().clone())
        self.register_buffer("support_labels", labels)
        self.eval()

    def generated_prompts(self) -> torch.Tensor:
        return cast(torch.Tensor, self.generator(self.support_features, self.support_labels))

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return prompted_labram_logits(self.classifier, inputs, self.generated_prompts())


@dataclass(frozen=True, slots=True)
class PromptEpisodeResult:
    model: SupportPromptedLaBraM
    losses: tuple[float, ...]
    trainable_names: tuple[str, ...]
    trainable_parameters: int


def adapt_labram_prompt_support(
    source: LaBraMClassifier,
    generator: ClassPrototypePromptGenerator,
    support_inputs: torch.Tensor,
    support_labels: torch.Tensor,
    *,
    steps: int,
    learning_rate: float,
    train_head: bool,
) -> PromptEpisodeResult:
    """Fresh support context/model/SGD; train generator and explicitly optional head.

    Support features use the unprompted frozen source encoder once. No query data
    enters generation or optimization. The returned episode is eval-only until
    the caller deliberately changes its mode. Reuse the immutable source AND
    generator templates to reset; manifest and source-fit enforcement belongs
    to the future experiment runner. These optimizer choices are engineering.
    """
    if (
        type(steps) is not int
        or steps < 1
        or not math.isfinite(learning_rate)
        or learning_rate <= 0
        or type(train_head) is not bool
    ):
        raise ValueError("positive finite optimizer settings and explicit head policy required")
    model = SupportPromptedLaBraM(source, generator, support_inputs, support_labels)
    model.requires_grad_(False)
    model.generator.requires_grad_(True)
    model.classifier.head.requires_grad_(train_head)
    for p in model.parameters():
        p.grad = None
    names = tuple(n for n, p in model.named_parameters() if p.requires_grad)
    selected = [p for p in model.parameters() if p.requires_grad]
    weight = next(model.parameters())
    inputs = support_inputs.detach().to(device=weight.device, dtype=weight.dtype).clone()
    labels = support_labels.detach().to(device=weight.device).clone()
    optimizer = torch.optim.SGD(selected, lr=learning_rate)
    criterion = nn.CrossEntropyLoss()
    losses = []
    for _ in range(steps):
        optimizer.zero_grad(set_to_none=True)
        loss = criterion(model(inputs), labels)
        if not torch.isfinite(loss):
            raise ValueError("nonfinite support loss")
        loss.backward()
        if any(p.grad is None or not torch.isfinite(p.grad).all() for p in selected):
            raise ValueError("missing or nonfinite selected support gradient")
        optimizer.step()
        if any(not torch.isfinite(p).all() for p in selected):
            raise ValueError("nonfinite adapted parameter")
        losses.append(float(loss.detach()))
    optimizer.zero_grad(set_to_none=True)
    return PromptEpisodeResult(model, tuple(losses), names, sum(p.numel() for p in selected))
