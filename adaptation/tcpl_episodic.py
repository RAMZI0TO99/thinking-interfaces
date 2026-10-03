"""Local TCPL source meta-loss/training and fixed-target inference primitives.

These tensor helpers do not authorize trial roles. Audited-manifest integration,
source validation, scheduling and the scientific training budget remain separate.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass

import torch
from torch.nn import functional as F

from encoder.tcpl import TCPLClassifier


@dataclass(frozen=True, slots=True)
class TCPLMetaLoss:
    total: torch.Tensor
    query_cross_entropy: torch.Tensor
    prompt_penalty: torch.Tensor
    logits: torch.Tensor
    prompts: torch.Tensor


def tcpl_meta_episode_loss(
    model: TCPLClassifier,
    support: torch.Tensor,
    queries: torch.Tensor,
    query_targets: torch.Tensor,
    *,
    prompt_l2_weight: float = 1e-4,
) -> TCPLMetaLoss:
    """Mean over episodes of (mean query CE + lambda * sum of squared prompts).

    Dense episodes have uniform shot/query counts; the penalty is counted once
    per episode, not once per query or averaged over prompt coordinates. This
    function preserves caller modes, gradients and parameter flags. Returned
    tensors retain the graph. Only source-training queries may be used here.
    """
    if not math.isfinite(prompt_l2_weight) or prompt_l2_weight < 0:
        raise ValueError("prompt_l2_weight must be finite and nonnegative")
    model._validate_queries(queries)
    if (
        support.ndim != 4
        or support.shape[0] != queries.shape[0]
        or support.device != queries.device
        or support.dtype != queries.dtype
    ):
        raise ValueError("support/query episode counts, devices and dtypes must match")
    if (
        query_targets.shape != queries.shape[:2]
        or query_targets.dtype != torch.long
        or query_targets.device != queries.device
        or (query_targets < 0).any()
        or (query_targets >= model.classes).any()
    ):
        raise ValueError("expected long [episodes, queries] targets within the class range")
    prompts = model.support_prompt(support)
    logits = model.forward_with_prompts(queries, prompts)
    per_query = F.cross_entropy(
        logits.reshape(-1, model.classes), query_targets.reshape(-1), reduction="none"
    ).reshape(query_targets.shape)
    query_ce = per_query.mean(dim=1).mean()
    penalty = prompts.square().sum(dim=(1, 2)).mean() * prompt_l2_weight
    total = query_ce + penalty
    if not torch.isfinite(total):
        raise ValueError("nonfinite TCPL meta-loss")
    return TCPLMetaLoss(total, query_ce, penalty, logits, prompts)


@dataclass(frozen=True, slots=True)
class TCPLMetaStep:
    total: float
    query_cross_entropy: float
    prompt_penalty: float


class TCPLSourceTrainer:
    """Own a fresh trainable source clone and one persistent Adam optimizer.

    Each step is one dense meta-batch; all parameter groups train jointly.
    Learning rate/weight decay/lambda defaults follow the reference inventory;
    Adam betas=(0.9,0.999), eps=1e-8 and no AMSGrad are local choices. There is no
    scheduler, stopping rule or scientific episode budget here. A new trainer
    resets optimizer/model state from its supplied template. Target inference
    must use TCPLTargetSession, which has no optimizer or label input.
    """

    def __init__(
        self,
        source_template: TCPLClassifier,
        *,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
        prompt_l2_weight: float = 1e-4,
    ) -> None:
        if not math.isfinite(learning_rate) or learning_rate <= 0:
            raise ValueError("learning_rate must be finite and positive")
        if not math.isfinite(weight_decay) or weight_decay < 0:
            raise ValueError("weight_decay must be finite and nonnegative")
        if not math.isfinite(prompt_l2_weight) or prompt_l2_weight < 0:
            raise ValueError("prompt_l2_weight must be finite and nonnegative")
        self.model = copy.deepcopy(source_template).requires_grad_(True).train()
        self.model.zero_grad(set_to_none=True)
        self.prompt_l2_weight = prompt_l2_weight
        self._optimizer = torch.optim.Adam(
            self.model.parameters(), lr=learning_rate, weight_decay=weight_decay,
            betas=(0.9, 0.999), eps=1e-8, amsgrad=False,
        )

    def step(
        self, support: torch.Tensor, queries: torch.Tensor, query_targets: torch.Tensor
    ) -> TCPLMetaStep:
        """Update owned source parameters; do not accumulate caller input gradients.

        Reject nonfinite loss/gradients before optimizer.step and clear owned
        gradients on success or failure. Failed calls may consume dropout RNG;
        no transactional rollback of arbitrary optimizer failures is promised.
        """
        self.model.train()
        self._optimizer.zero_grad(set_to_none=True)
        try:
            loss = tcpl_meta_episode_loss(
                self.model, support.detach(), queries.detach(), query_targets.detach(),
                prompt_l2_weight=self.prompt_l2_weight,
            )
            loss.total.backward()  # type: ignore[no-untyped-call]  # Torch lacks this annotation.
            if any(
                p.grad is None or not torch.isfinite(p.grad).all()
                for p in self.model.parameters()
            ):
                raise ValueError("missing or nonfinite TCPL source gradient")
            metrics = TCPLMetaStep(
                float(loss.total.detach()), float(loss.query_cross_entropy.detach()),
                float(loss.prompt_penalty.detach()),
            )
            self._optimizer.step()
            return metrics
        finally:
            self._optimizer.zero_grad(set_to_none=True)


class TCPLTargetSession:
    """Snapshot a source model and support prompts before seeing any queries.

    No target labels, optimizer, fitting or source-mode mutation. Support is
    copied for conditioning and then discarded. Model weights and prompts are
    independent of subsequent caller mutations. New subjects require new sessions.
    Private internals must not be mutated by callers; this is an API boundary,
    not a security boundary. Inputs are already preprocessed by the future runner.
    """

    def __init__(self, source_model: TCPLClassifier, support: torch.Tensor) -> None:
        self._model = copy.deepcopy(source_model).eval().requires_grad_(False)
        self._model.zero_grad(set_to_none=True)
        with torch.inference_mode():
            self._prompts: torch.Tensor = self._model.support_prompt(
                support.detach().clone()
            ).clone()
        if not torch.isfinite(self._prompts).all():
            raise ValueError("nonfinite TCPL target prompts")

    @property
    def prompts(self) -> torch.Tensor:
        """Return an independent diagnostic copy, never the session's cache."""
        return self._prompts.clone()

    def predict(
        self, queries: torch.Tensor, *, query_batch_size: int | None = None
    ) -> torch.Tensor:
        """Return [episodes, queries, classes] logits without fitting or gradients."""
        self._model._validate_queries(queries)
        if query_batch_size is not None and (
            type(query_batch_size) is not int or query_batch_size < 1
        ):
            raise ValueError("query_batch_size must be a positive integer or None")
        batch_size = queries.shape[1] if query_batch_size is None else query_batch_size
        with torch.inference_mode():
            parts = [
                self._model.forward_with_prompts(
                    queries[:, start:start + batch_size], self._prompts
                )
                for start in range(0, queries.shape[1], batch_size)
            ]
            logits = torch.cat(parts, dim=1)
            if not torch.isfinite(logits).all():
                raise ValueError("nonfinite TCPL target logits")
        return logits.clone()
