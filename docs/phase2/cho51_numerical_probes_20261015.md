# Full-shape synthetic numerical probes, 15 October 2026

All four methods now have successful finite CPU numerical probes using the
unchanged [probe source](cho51_numerical_probe_v1/README.md). EEGNet, LaBraM
linear and LoRA passed in a 2/3 GiB process/Job envelope. Full tuning passed in
a separately reviewed 3/4 GiB successor after an unsuccessful run near its
original 2 GiB process cap. The original refusal and three passes remain intact.

The evidence comprises the [41-artifact initial packet](../../evidence/cho51-numerical-probes-20261015/README.md)
and [18-artifact full-tuning successor](../../evidence/cho51-numerical-full-successor-20261015/README.md).
These are random-initialized synthetic numerical fixtures. They do not establish
pretrained parity, complete selector/worker resources, fitted study publications,
the 1,020-case roster or scientific admission.

## Executed results

| Method / attempt | Native Job | Result | Native seconds | Peak process / Job bytes |
| --- | --- | --- | ---: | --- |
| EEGNet | `20261015T103532Z_4548f1bc1e` | Passed, 2/3 GiB caps | 17.061 | 1,315,024,896 / 1,345,032,192 |
| LaBraM linear | `20261015T103612Z_1182506cc9` | Passed, 2/3 GiB caps | 21.037 | 1,460,498,432 / 1,490,657,280 |
| LaBraM LoRA | `20261015T103653Z_c6def8678d` | Passed, 2/3 GiB caps | 22.257 | 1,496,981,504 / 1,526,943,744 |
| LaBraM full, initial | `20261015T103727Z_edf91030bf` | Refused; exit 4294967295, 2/3 GiB caps | 19.008 | 2,147,426,304 / 2,178,310,144 |
| LaBraM full, successor | `20261015T104219Z_ac3b37bb20` | Passed, 3/4 GiB caps | 25.455 | 2,364,608,512 / 2,394,779,648 |

The initial full run ended near its process limit. The exit code alone does not
uniquely identify the cause; the observation is consistent with cap pressure.
The successor changed only its versioned method scope, resource envelope and
metadata. It retained the exact architecture, inputs, rates and update schedule.
The source probe SHA remained
`782fd51846e41c093ac2a3c5d5db6c78ecd5148a310dd4a275fd488b773e0847`.
No smaller fixture was substituted and no historical result was rewritten.
The existing native guard permits configurable caps; its implementation and
canonical configuration were unchanged. These larger caps apply only to the
full synthetic successor, not to scientific execution or other launchers.

## Numerical workload and assertions

Every successful probe uses seeded CPU float32 arrays: source batch 2, support
batch 10 (five examples per class), and query batch 2. EEGNet uses the actual
64-channel, 512-sample constrained-classifier architecture. LaBraM uses the
pinned baseline architecture JSON, random initialization of its full 12-block,
200-dimensional backbone, canonical sequence cropping from 3,000 to 800 samples,
and the canonical 64-channel Cho montage/two-class classifier. No baseline
checkpoint weights are read. Actual parameter counts are 2,642 for EEGNet,
5,818,138 for linear/full LaBraM, and 5,819,738 for LoRA.

Two explicit engineering rates, 0.001 and 0.0005, each receive two source SGD
updates, one support SGD update and one fresh support replay. The child observes
exactly eight tensor backward calls and eight SGD steps per successful method.
Thus 32 updates are certified across the four successful fixtures. The aborted
initial full attempt has no complete child qualification, so its partial update
count is unknown and is not included in that number. The rates are fixture
settings, not adopted study candidate recipes.

Source SGD is fixture-owned. EEGNet also uses a fixture-owned support kernel
following the eval-mode, fresh momentum-free SGD policy; it does not qualify
canonical selector/anchor integration. LaBraM uses unchanged public tuning masks,
`adapt_labram_tuning_support`, and trained-LoRA initialization/continuation.
LoRA targets last-block QKV, rank 2, alpha 4 and a trainable head. It requires
initial zero B/nonzero A and effective-QKV identity with the base, followed by
actual A/B and effective-QKV changes in source and support work. Full tuning
requires actual patcher, position-embedding, final-normalization, head and
last-block QKV changes.

Substantive checks cover finite logits/losses/selected gradients/parameters,
nonempty changes within the exact mask, unchanged frozen tensors and buffers,
immutable source/modes/gradients/RNG, disjoint storage, unmodified inputs and
state after query inference, and exact repeated support loss/state/logits.
Each adapted state is encoded as full safetensors, then strictly loaded into
an independently rebuilt architecture with LoRA installed before loading when
needed. Every tensor, canonical state digest and query logit must match exactly.
The first adaptation is released before replay/restoration; retained snapshots
are hashes. No full selector, cohort artifact loader or recorder is constructed.

Each rate saves an owned full-state file: 12,664 bytes for EEGNet, 23,294,624 for
linear/full LaBraM and 23,301,304 for LoRA. The eight successful files total
139,806,432 bytes. Hashes and sizes are retained in child qualifications; weight
blobs are excluded from Git/evidence packets. This full-state exercise does not
qualify sparse selected-weight formats, which the canonical verifier still
does not support.

## Source, resource and cleanup proof

Every attempt used a fresh 300-second native Job, two startup samples meeting
10 GiB RAM/20 GiB disk, active 4 GiB RAM/20 GiB disk, actual Torch/inter-op 1/1,
hidden GPUs and all four genuine pause paths through 15 October. Initial successful
startup RAM samples ranged from 17,065,668,608 to 17,383,337,984 bytes. Full
successor samples were 17,491,046,400 and 17,491,927,040 bytes. No peer release,
peer count or host quiet is inferred. Source030 remains expired.

Successful child scopes took 12.953 / 16.828 / 18.093 / 21.359 seconds for EEGNet,
linear, LoRA and full respectively, including library setup and child checks.
Each successful Job blocked one exact optional IPv6 import probe, had zero
unexpected audit denials, and observed/rechecked 4,673 loaded-module files after
imports. These observed hashes are distinct from independent preparation pins.
Subprocesses, real study arrays/checkpoints, pretrained loaders, unowned writes,
recorders and numerical calls outside the pinned probe were blocked. Cache paths
were routed into owned output; the exact pinned 260-byte MNE anatomical template
was the sole external `.fif` resource exception.

Initial preparation pinned 556 source/context files and five runtime files;
successor preparation pinned 563 source/context files and the identical five
runtime files, refusing any drift in all 556 predecessor pins. Their pin-file
SHAs are respectively
`963c24bbcc2afc12b9daaea601eaefef3194bbc8f807575f1e95668e2183ccda` and
`0a1041b639dd3ef26e14d4c6d5fc00b0fde9fe41f821be9ca7f684608628f2e5`.
All 432 canonical files and file set remain exact at
`3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529`.
Historical 1,040-case/256-step guards and all earlier qualified candidates remain
unchanged. All five created Jobs closed empty with closed handles, no cleanup
or peak-sampling errors, and fresh name-absence checks at closeout. Workers and
reviewers completed and were stopped.

## Resume boundary

Next integrate the measured per-method envelope into a separately versioned
whole-worker/resource rehearsal, including fresh recorder/ledger composition
and complete selector accounting. These eight-update fixtures cannot bound
the 5,253-step selectors, complete target inference, checkpoint/runtime lineage,
full sweep wall time, storage peaks or scientific workload. The canonical
source execution guard and its GPU/machine admission checks were not called or
weakened; these synthetic CPU Jobs are not proof that those gates pass.

Checkpoint-cohort overlap, final owner freeze and scientific budget remain
pending. Gate A retains only its exact retrospective acceptance. The available
source pool remains 52 and adopted evaluation targets remain subjects02–52,
four methods/five seeds and 1,020 unchanged case IDs. Original subject01
remaining attempts stay zero. No study fitting, actual recording/target
prediction, original case, watcher, schedule, renewed Source030, new 30-hour
window, commit, push or PR occurred.
