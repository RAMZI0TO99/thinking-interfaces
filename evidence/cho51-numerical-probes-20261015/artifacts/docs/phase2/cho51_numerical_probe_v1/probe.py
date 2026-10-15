"""Full-shape random-initialization numerical fixtures for four Cho methods.

The native child owns resource admission and the output directory. All numerical
imports and execution stay inside run_probe so its caller installs its audit
before any numerical library is imported.
"""
from __future__ import annotations

import copy
import gc
import hashlib
import math
import os
from pathlib import Path

METHODS = ('eegnet', 'labram_linear', 'labram_lora', 'labram_full')
RATES = (0.001, 0.0005)
SUCCESS_CHECKS = (
    'finite_logits', 'finite_losses', 'finite_selected_gradients', 'finite_parameters',
    'updates_nonempty_within_mask', 'frozen_state_unchanged', 'source_unchanged',
    'rng_unchanged', 'no_storage_alias', 'query_state_unchanged', 'exact_replay',
    'state_roundtrip_exact', 'query_roundtrip_exact', 'fixture_inputs_unchanged',
)


def run_probe(output: Path, method: str, model_config: dict) -> dict:
    """Run two finite synthetic rates, each with source2/support1/replay1 steps.

    No adopted candidate, real recording, pretrained checkpoint, recorder,
    public source selector, complete5253-step fit or scientific claim is used.
    """
    if type(method) is not str or method not in METHODS or type(model_config) is not dict:
        raise ValueError('one exact fixture method and detached config dictionary required')
    if (not isinstance(output, Path) or not output.is_absolute()
            or output.resolve(strict=True) != output or not output.is_dir()):
        raise ValueError('existing direct owned output directory required')
    output_paths = tuple(output / f'rate_{index:02d}_fullstate.safetensors' for index in (1, 2))
    if any(path.exists() for path in output_paths):
        raise ValueError('fresh numerical fixture state paths required')
    if method != 'eegnet':
        expected_keys = {'n_outputs', 'n_chans', 'n_times', 'input_window_seconds', 'sfreq', 'chs_info', 'braindecode_version'}
        if (set(model_config) != expected_keys or model_config['n_outputs'] != 0
                or model_config['n_chans'] is not None or model_config['n_times'] != 3000
                or model_config['input_window_seconds'] is not None or model_config['sfreq'] is not None
                or model_config['braindecode_version'] != '1.3.2'
                or type(model_config['chs_info']) is not list or len(model_config['chs_info']) != 128
                or any(type(info) is not dict or set(info) != {'ch_name'}
                       or type(info['ch_name']) is not str for info in model_config['chs_info'])
                or len({info['ch_name'] for info in model_config['chs_info']}) != 128):
            raise ValueError('complete pinned128-channel3000-sample LaBraM metadata config required')

    import torch
    from braindecode.models import EEGNet, Labram
    from safetensors.torch import load, save
    from torch.optim.optimizer import register_optimizer_step_pre_hook
    from adaptation.labram_lora_trained import (
        LoRAContinuationSettings, LoRASourceSettings, continue_trained_lora_support,
        initialize_source_lora,
    )
    from adaptation.labram_tuning import adapt_labram_tuning_support, configure_labram_tuning
    from encoder.labram import LaBraMClassifier, configure_pretrained_sequence
    from evaluation.labram_parity import state_digest
    from evaluation.phase2_profile_binding import CHO_CHANNELS

    def need(condition, message):
        if not condition:
            raise ValueError(message)

    need(torch.get_num_threads() == 1 and torch.get_num_interop_threads() == 1,
         'native child must establish one-thread execution')
    need(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'native child must hide GPU access')
    need(len(CHO_CHANNELS) == 64, 'unchanged canonical Cho64-channel montage required')
    samples = 512 if method == 'eegnet' else 800
    generator = torch.Generator(device='cpu').manual_seed(11)
    source_x = torch.randn((2, 64, samples), generator=generator, dtype=torch.float32) * 0.1
    support_x = torch.randn((10, 64, samples), generator=generator, dtype=torch.float32) * 0.1
    query_x = torch.randn((2, 64, samples), generator=generator, dtype=torch.float32) * 0.1
    source_y = torch.tensor([0, 1], dtype=torch.long)
    support_y = torch.tensor([0] * 5 + [1] * 5, dtype=torch.long)
    source_settings = None

    def tensor_sha(value):
        return hashlib.sha256(value.detach().cpu().contiguous().numpy().tobytes()).hexdigest()

    def state_hashes(model):
        return {name: tensor_sha(value) for name, value in model.state_dict().items()}

    def fixture_hashes():
        return tuple(tensor_sha(value) for value in (source_x, source_y, support_x, support_y, query_x))

    fixture_before = fixture_hashes()

    def build():
        # Independent architecture construction preserves the caller's RNG.
        with torch.random.fork_rng(devices=[]):
            torch.random.set_rng_state(torch.Generator(device='cpu').manual_seed(11).get_state())
            if method == 'eegnet':
                model = EEGNet(n_chans=64, n_outputs=2, n_times=512, sfreq=128,
                               final_layer_with_constraint=True).cpu().float().eval()
                model.requires_grad_(True)
            else:
                config = copy.deepcopy(model_config)
                config.pop('braindecode_version')
                backbone = Labram(**config)
                need(len(backbone.blocks) == 12 and int(backbone.embed_dim) == 200,
                     'full12-block200-dimensional LaBraM backbone required')
                configure_pretrained_sequence(backbone, samples=800)
                plain = LaBraMClassifier(backbone, classes=2, channel_names=CHO_CHANNELS).cpu().float().eval()
                if method == 'labram_lora':
                    model, _ = initialize_source_lora(plain, source_settings)
                    target = model.get_submodule('backbone.blocks.11.attn.qkv')
                    adapter = target.parametrizations.weight[0]
                    need(torch.count_nonzero(adapter.lora_b).item() == 0
                         and torch.count_nonzero(adapter.lora_a).item() > 0,
                         'source LoRA must start with seeded nonzeroA and exact zeroB')
                    with torch.no_grad():
                        need(torch.equal(target.weight, target.parametrizations.weight.original)
                             and torch.equal(target.weight, plain.get_submodule('backbone.blocks.11.attn.qkv').weight),
                             'initial effective LoRA QKV must exactly equal the independently constructed base')
                    del target, adapter
                    del plain, backbone
                else:
                    model = plain
                    configure_labram_tuning(model, method='linear' if method == 'labram_linear' else 'full')
                model.eval()
        need(all(p.device.type == 'cpu' and p.dtype == torch.float32 for p in model.parameters()),
             'CPU float32 full model required')
        return model

    def selected_names(model):
        names = tuple(name for name, parameter in model.named_parameters() if parameter.requires_grad)
        need(bool(names), 'nonempty explicit trainable mask required')
        all_names = {name for name, _ in model.named_parameters()}
        if method == 'labram_linear':
            expected = {name for name in all_names if name.startswith('head.')}
        elif method == 'labram_lora':
            expected = {'head.weight', 'head.bias',
                        'backbone.blocks.11.attn.qkv.parametrizations.weight.0.lora_a',
                        'backbone.blocks.11.attn.qkv.parametrizations.weight.0.lora_b'}
        else:
            expected = all_names
        need(set(names) == expected, 'actual trainable names differ from full fixture policy')
        return names

    def check_state(model):
        need(all(torch.isfinite(value).all().item() for value in model.state_dict().values()), 'nonfinite model state')
        need(not any(module.training for module in model.modules()), 'all fixture modules must remain in eval mode')

    def changes(before, model, mask):
        after = state_hashes(model)
        need(set(before) == set(after), 'state inventory changed')
        changed = {name for name in before if before[name] != after[name]}
        need(bool(changed) and changed <= set(mask), 'nonempty updates must remain inside the expected mask')
        if method.startswith('labram'):
            need('head.weight' in changed, 'selected head did not update')
        if method == 'labram_lora':
            need({'backbone.blocks.11.attn.qkv.parametrizations.weight.0.lora_a',
                  'backbone.blocks.11.attn.qkv.parametrizations.weight.0.lora_b'} <= changed,
                 'both selected LoRA A andB must actually update')
        if method == 'labram_full':
            need({'backbone.blocks.11.attn.qkv.weight',
                  'backbone.patch_embed.temporal_conv.conv1.weight',
                  'backbone.position_embedding', 'backbone.norm.weight', 'head.weight'} <= changed,
                 'full patcher, position embedding, final norm, head and lastQKV must actually update')
        return changed

    def storage(model):
        return {value.untyped_storage().data_ptr() for value in model.state_dict().values() if value.numel()}

    def query(model, inputs):
        before = state_digest(model)
        with torch.inference_mode():
            logits = model(inputs).detach().clone()
        need(tuple(logits.shape) == (len(inputs), 2) and torch.isfinite(logits).all().item(), 'invalid finite two-class logits')
        need(state_digest(model) == before, 'query changed model state')
        return logits

    phase = {'name': None, 'rate': None, 'selected': 0}
    gradient_events = []

    def before_optimizer_step(optimizer, args, kwargs):
        need(type(optimizer) is torch.optim.SGD, 'only actual fresh SGD fixtures are permitted')
        parameters = [p for group in optimizer.param_groups for p in group['params']]
        need(len(parameters) == phase['selected'], 'optimizer differs from selected parameter inventory')
        need(all(p.requires_grad and p.grad is not None and torch.isfinite(p.grad).all().item()
                 for p in parameters), 'missing or nonfinite selected gradient')
        need(all(group['lr'] == phase['rate'] and group.get('momentum', 0) == 0
                 and group.get('weight_decay', 0) == 0 and not group.get('nesterov', False)
                 and not group.get('maximize', False) for group in optimizer.param_groups), 'fixture SGD policy drift')
        gradient_events.append(phase['name'])

    def source_sgd(model, rate):
        optimizer = torch.optim.SGD([p for p in model.parameters() if p.requires_grad], lr=rate)
        losses = []
        for _ in range(2):
            optimizer.zero_grad(set_to_none=True)
            logits = model(source_x)
            need(tuple(logits.shape) == (2, 2) and torch.isfinite(logits).all().item(), 'nonfinite source logits')
            loss = torch.nn.functional.cross_entropy(logits, source_y)
            need(torch.isfinite(loss).item(), 'nonfinite source loss')
            loss.backward()
            optimizer.step()
            check_state(model)
            losses.append(float(loss.detach()))
        optimizer.zero_grad(set_to_none=True)
        return tuple(losses)

    def support(model, rate):
        if method == 'labram_lora':
            adapted = continue_trained_lora_support(model, support_x, support_y, source_settings=source_settings,
                settings=LoRAContinuationSettings(True, 1, rate, query_batch_size=2))
            return adapted.model, tuple(adapted.losses)
        if method in ('labram_linear', 'labram_full'):
            adapted = adapt_labram_tuning_support(model, support_x, support_y,
                method='linear' if method == 'labram_linear' else 'full', steps=1, learning_rate=rate)
            return adapted.model, tuple(adapted.losses)
        # Fixture-owned EEGNet path follows canonical eval/fresh-SGD policy.
        # It does not call or qualify the public source selector/worker.
        adapted = copy.deepcopy(model).eval()
        optimizer = torch.optim.SGD([p for p in adapted.parameters() if p.requires_grad], lr=rate)
        optimizer.zero_grad(set_to_none=True)
        logits = adapted(support_x)
        need(tuple(logits.shape) == (10, 2) and torch.isfinite(logits).all().item(), 'nonfinite support logits')
        loss = torch.nn.functional.cross_entropy(logits, support_y)
        need(torch.isfinite(loss).item(), 'nonfinite support loss')
        loss.backward()
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        return adapted, (float(loss.detach()),)

    checks = []
    parameter_count = None
    hook = register_optimizer_step_pre_hook(before_optimizer_step)
    try:
        for index, rate in enumerate(RATES):
            source_settings = LoRASourceSettings(('backbone.blocks.11.attn.qkv',), 2, 4.0, 11, True, 2, 2, rate)
            source = build()
            mask = selected_names(source)
            count = sum(p.numel() for p in source.parameters())
            need(parameter_count in (None, count), 'independent construction changed parameter count')
            parameter_count = count
            initial = state_hashes(source)
            phase.update(name='source', rate=rate, selected=len(mask))
            event_start = len(gradient_events)
            source_losses = source_sgd(source, rate)
            changes(initial, source, mask)
            del initial
            if method == 'labram_lora':
                with torch.no_grad():
                    target = source.get_submodule('backbone.blocks.11.attn.qkv')
                    need(not torch.equal(target.weight, target.parametrizations.weight.original),
                         'source-trained LoRA effective QKV did not change from frozen base')
                    del target
            source_sha = state_digest(source)
            source_hashes = state_hashes(source)
            source_modes = tuple(module.training for module in source.modules())
            source_storage = storage(source)
            rng = torch.random.get_rng_state().clone()

            phase['name'] = 'support'
            adapted, losses = support(source, rate)
            need(selected_names(adapted) == mask, 'support parameter mask changed')
            check_state(adapted)
            changes(source_hashes, adapted, mask)
            if method == 'labram_lora':
                with torch.no_grad():
                    need(not torch.equal(adapted.get_submodule('backbone.blocks.11.attn.qkv').weight,
                                         source.get_submodule('backbone.blocks.11.attn.qkv').weight),
                         'continued LoRA effective QKV did not change from trained source')
            need(not source_storage & storage(adapted), 'support model aliases source storage')
            need(state_digest(source) == source_sha and tuple(module.training for module in source.modules()) == source_modes
                 and all(p.grad is None for p in source.parameters()), 'support changed immutable source')
            need(torch.equal(torch.random.get_rng_state(), rng), 'support changed global CPU RNG')
            need(len(losses) == 1 and all(math.isfinite(v) for v in losses), 'finite one-step support loss required')
            adapted_sha = state_digest(adapted)
            first_logits = query(adapted, query_x)
            query(adapted, support_x)
            blob = save({name: value.detach().cpu().contiguous() for name, value in adapted.state_dict().items()})
            need(0 < len(blob) <= 25 * 1024**2, 'bounded full-state safetensors fixture required')
            del adapted
            gc.collect()

            phase['name'] = 'replay'
            repeated, repeat_losses = support(source, rate)
            check_state(repeated)
            changes(source_hashes, repeated, mask)
            need(not source_storage & storage(repeated), 'replayed support model aliases source storage')
            need(repeat_losses == losses and state_digest(repeated) == adapted_sha, 'support state/loss replay differs')
            need(torch.equal(query(repeated, query_x), first_logits), 'support query replay differs')
            need(state_digest(source) == source_sha and tuple(module.training for module in source.modules()) == source_modes
                 and all(p.grad is None for p in source.parameters()), 'replay changed immutable source')
            need(torch.equal(torch.random.get_rng_state(), rng), 'replayed support changed global CPU RNG')
            del repeated
            gc.collect()

            # Rebuild the complete architecture independently. For LoRA the
            # parametrizations already exist before strict state loading.
            restored = build()
            need(not source_storage & storage(restored), 'restored architecture aliases source')
            decoded = load(blob)
            incompatible = restored.load_state_dict(decoded, strict=True)
            need(not incompatible.missing_keys and not incompatible.unexpected_keys, 'strict full-state restore differs')
            need(all(torch.equal(value, restored.state_dict()[name]) for name, value in decoded.items()),
                 'strictly restored state tensors differ from the encoded full state')
            del decoded
            check_state(restored)
            need(state_digest(restored) == adapted_sha, 'restored full-state digest differs')
            need(torch.equal(query(restored, query_x), first_logits), 'restored query logits differ')
            need(selected_names(restored) == mask, 'restored trainable mask differs')
            need(fixture_hashes() == fixture_before, 'numerical fixture inputs/labels changed')
            need(gradient_events[event_start:] == ['source', 'source', 'support', 'replay'], 'exact four SGD updates per rate required')
            path = output_paths[index]
            with path.open('xb') as stream:
                stream.write(blob)
                stream.flush()
                os.fsync(stream.fileno())
            check = {name: True for name in SUCCESS_CHECKS}
            check.update(rate=rate, source_gradient_updates=2, support_gradient_updates=2, actual_gradient_updates=4,
                source_losses=list(source_losses), support_loss=losses[0], replay_support_loss=repeat_losses[0],
                source_state_sha256=source_sha, adapted_state_sha256=adapted_sha,
                weights_file=str(path), weights_sha256=hashlib.sha256(blob).hexdigest(), weights_bytes=len(blob),
                selected_parameter_names=list(mask), changed_source_and_support_parameters_only_within_mask=True)
            if method == 'labram_lora':
                check.update(lora_initial_zero_b_effective_identity_verified=True,
                             lora_source_and_support_both_matrices_updated=True,
                             lora_source_and_support_effective_qkv_changed=True)
            checks.append(check)
            del source, restored, blob, source_hashes, first_logits
            gc.collect()
    finally:
        hook.remove()
    need(len(gradient_events) == 8 and len(checks) == 2, 'two complete numerical fixture rates required')
    return dict(
        schema='cho51_numerical_probe_v1', method=method, passed=True, rate_cases=2,
        actual_gradient_updates=8, source_gradient_updates=4, support_gradient_updates=4,
        source_examples=2, support_examples=10, query_examples=2, channels=64, samples=samples,
        model_blocks=0 if method == 'eegnet' else 12, parameter_count=parameter_count,
        random_initialization=True, full_architecture_shape=True, baseline_checkpoint_used=False,
        source_kernel_fixture_owned=True, fixture_rates_are_adopted_candidates=False,
        public_source_fit_verified=False, canonical_source_selector_integration_verified=False,
        source_cohort_or_selector_used=False, recorder_used=False, full_worker_verified=False,
        full_5253_gradient_selection_executed=False, scientific_admission=False,
        original_case_attempts_remaining=0, checks=checks,
    )
