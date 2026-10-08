"""Bounded operational experiment for pinned eval-mode, frozen CPU backbones.

Only detached cls-token features are retained. The live head always executes,
so head gradients/updates stay unchanged. All trainable backbones, hooks,
autocast, inference mode and nonstandard input layouts bypass the experiment.
Use only within an explicitly active source-selection scope, then deactivate
and clear before returning a selected model for any target use.
"""
from collections import OrderedDict
from types import MethodType
from weakref import WeakKeyDictionary
import hashlib

import torch
from encoder.labram import LaBraMClassifier
from evaluation.labram_parity import state_digest

class FrozenFeatureCache:
    def __init__(self, namespace, *, maximum_bytes=32 * 1024**2):
        if not isinstance(namespace, str) or not namespace:
            raise ValueError("feature cache requires an explicit recipe namespace")
        if type(maximum_bytes) is not int or not 0 <= maximum_bytes <= 32 * 1024**2:
            raise ValueError("feature cache must stay within32MiB")
        self.namespace = namespace
        self.maximum_bytes = maximum_bytes
        self.retained_bytes = 0
        self.active = False
        self._entries = OrderedDict()
        self._models = WeakKeyDictionary()
        self.statistics = {"hits": 0, "misses": 0, "bypasses": 0, "evictions": 0, "state_hashes": 0}

    def clear(self):
        self._entries.clear()
        self._models.clear()
        self.retained_bytes = 0

    @staticmethod
    def _eligible(model, inputs):
        if type(inputs) is not torch.Tensor or inputs.device.type != "cpu" or inputs.dtype != torch.float32 or inputs.requires_grad or not inputs.is_contiguous():
            return False
        if torch.is_autocast_enabled("cpu") or torch.is_inference_mode_enabled():
            return False
        hooks = torch.nn.modules.module
        if any(getattr(hooks, name) for name in ("_global_forward_hooks", "_global_forward_pre_hooks", "_global_backward_hooks", "_global_backward_pre_hooks")):
            return False
        for module in model.backbone.modules():
            if module.training or module._forward_hooks or module._forward_pre_hooks or module._backward_hooks or module._backward_pre_hooks:
                return False
        tensors = tuple(model.backbone.parameters()) + tuple(model.backbone.buffers())
        return all(not value.requires_grad and value.device.type == "cpu" and value.dtype in (torch.float32, torch.int64, torch.int32, torch.bool) for value in tensors)

    def _backbone_namespace(self, backbone):
        # Normal PyTorch in-place parameter/buffer updates increment _version.
        # Namespace is scoped to a pinned recipe; arbitrary .data mutation is
        # unsupported and requires the original final frozen-state validation.
        metadata = tuple((name, id(value), value._version, tuple(value.shape), value.dtype, value.device) for name, value in tuple(backbone.named_parameters()) + tuple(backbone.named_buffers()))
        # Keep function references in the entry key so a replacement cannot
        # reuse an old function's released id. Include child forwards as well
        # as the top-level backbone; deep copies share the same class methods.
        forwards = tuple((name, type(module), getattr(module.forward, "__func__", module.forward)) for name, module in backbone.named_modules())
        metadata = (metadata, forwards)
        previous = self._models.get(backbone)
        if previous is None or previous[0] != metadata:
            fingerprint = (state_digest(backbone), forwards)
            self._models[backbone] = (metadata, fingerprint)
            self.statistics["state_hashes"] += 1
            return fingerprint
        return previous[1]

    def _forward(self, model, inputs, original):
        if not self.active or self.maximum_bytes == 0 or not self._eligible(model, inputs):
            self.statistics["bypasses"] += 1
            return original(model, inputs)
        backbone_sha = self._backbone_namespace(model.backbone)
        input_sha = hashlib.sha256(inputs.detach().numpy().tobytes(order="C")).hexdigest()
        key = (self.namespace, backbone_sha, tuple(model.channel_names), tuple(inputs.shape), inputs.dtype, input_sha, torch.get_num_threads(), torch.are_deterministic_algorithms_enabled(), torch.get_float32_matmul_precision(), torch.backends.mkldnn.enabled)
        features = self._entries.get(key)
        if features is None:
            self.statistics["misses"] += 1
            features = model.backbone(inputs, ch_names=list(model.channel_names), return_features=True)["cls_token"]
            size = features.numel() * features.element_size()
            if size <= self.maximum_bytes:
                features = features.detach().clone()
                while self.retained_bytes + size > self.maximum_bytes:
                    _, evicted = self._entries.popitem(last=False)
                    self.retained_bytes -= evicted.numel() * evicted.element_size()
                    self.statistics["evictions"] += 1
                self._entries[key] = features
                self.retained_bytes += size
        else:
            self.statistics["hits"] += 1
            self._entries.move_to_end(key)
        # The private cached tensor never escapes or becomes an autograd owner.
        return model.head(features.clone())

    def install(self, model):
        if not isinstance(model, LaBraMClassifier) or "forward" in model.__dict__:
            raise ValueError("feature experiment requires an unwrapped LaBraMClassifier")
        original = type(model).forward
        owner = self
        def forward(current, inputs):
            return owner._forward(current, inputs, original)
        model.forward = MethodType(forward, model)

    @staticmethod
    def remove(model):
        if "forward" in model.__dict__:
            del model.forward
