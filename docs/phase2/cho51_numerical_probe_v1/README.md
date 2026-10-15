# Full-shape synthetic numerical probe candidate

`run_probe(output, method, model_config)` prepares one method's bounded
engineering execution for a separate native child. All numerical imports occur
inside that function after the child installs its audit. Authoring and AST
inspection do not execute the probe.

The four methods are EEGNet, LaBraM linear, LaBraM LoRA and LaBraM full. EEGNet
uses the actual 64-channel, 512-sample, 128 Hz architecture with the constrained
final layer. LaBraM is constructed from the independently pinned cached
128-channel/3000-sample metadata configuration, retains all twelve blocks, crops
the temporal sequence to 800 samples, and uses the canonical 64 Cho channel
names plus a two-class head. Parameters are randomly initialized with seed 11;
the pretrained checkpoint is never loaded. The model and montage are not
shrunk for this probe.

Each method uses two explicit fixture rates, 0.001 and 0.0005. Each rate starts
from an independently constructed random model, performs two fresh no-momentum
SGD source-fixture updates on two synthetic examples, then adapts on ten
synthetic support examples (five per class) for one update. A second adaptation
from the same source must reproduce the exact loss, state and two-example
query logits. This is four updates per rate, eight per method, including replay.
Signals are CPU float32 random values scaled by 0.1.

LaBraM linear/full use the unchanged `configure_labram_tuning` and
`adapt_labram_tuning_support`. LoRA installs rank-two, alpha-four QKV LoRA at
`backbone.blocks.11.attn.qkv`, trains the existing head, and calls unchanged
`continue_trained_lora_support` without reinitializing its trained adapters.
EEGNet source/support SGD is fixture-owned and follows the eval-mode,
fresh-optimizer policy. It does not qualify canonical source-selector integration.

An official removable optimizer pre-step hook verifies every selected gradient
before canonical helpers clear gradients. The probe also checks finite logits,
losses and parameters; nonempty changes inside the exact mask; unchanged frozen
parameters/buffers; immutable source state/modes/gradients and CPU RNG around
support; disjoint storage; unchanged inputs and query state; and exact replay.
LoRA must begin with zero B and exact effective-weight agreement with its base,
then both A and B must change during source and support updates, with changed
effective QKV weights. Full tuning must change the temporal patcher, position
embedding, final norm, classifier head and last-block QKV in both phases.
Each adapted full state is encoded in memory as safetensors, strictly loaded
into a separately reconstructed architecture (with LoRA installed first), and
checked by full state digest plus exact query logits. Two owned full-state files
are written exclusively, at most 25 MiB each. The first adaptation is released
before replay or restoration to bound retained model copies.

These numerical fixtures do not use recordings, source cohorts, adopted
candidates, pretrained weights, public source fitting, the complete 5,253-step
selection, a recorder, or the full study worker. No scientific result or new
original-case attempt is admitted. Actual execution, resource admission and
qualification must be established by the separate native child's fresh proof;
the presence of this source does not establish that execution succeeded.
