# Guarded whole-fold CPU/GPU comparison

19 September 2026, milestone 52. This closes the remaining device-choice question
from the owner's request to use GPU when better. Milestone 49 timed kernels;
this comparison times complete public source-validation folds under fixed
engineering settings. It changes no source, configuration, test or science policy.

## Predeclared measurement

Four public folds: full/CPU, full/GPU, LoRA/GPU, LoRA/CPU, in that order. Each has
50 source steps across Cho subjects 03-52 and one CPU support step on inner
validation subject 02. Outer target 01 is not fitted or predicted. Both methods
use the same safe pretrained template, seed 23, source batch two, rate 0.001,
one shot/class, FP32, two CPU threads, deterministic algorithms and TF32 off.
Catalogs/episodes and all input hashes are reconstructed. Initial model states,
settings, masks, sampling orders and data identities match across devices.

Timing covers the public fold, including audited source loading, gradients,
history hashes, resource checks, support adaptation and query evaluation. It
excludes imports, initial catalog reconstruction/template construction, post-fit
preservation audits and checkpoint serialization. The CPU probe adds the existing
live machine guard before every optimizer step; GPU uses its native source-step
machine/context/cooling checks. This compares these guarded workflows, including
their differing check overheads; it is not an isolated hardware benchmark.

Before compute, the operational rule was fixed at >=1.15x elapsed-time advantage
for a provisional preference; smaller differences remain inconclusive. Only
elapsed time is used for that choice. No accuracy-based setting or selection is
made. There is one observation per method/device, no across-subject/seed estimate.

| Method | CPU fold seconds | GPU fold seconds | CPU/GPU time | Provisional case preference |
| --- | ---: | ---: | ---: | --- |
| full | 138.68 | 78.03 | 1.777x | gpu |
| lora | 43.67 | 129.77 | 0.337x | cpu |

Adopted as an operational deviation: **full: gpu (CPU/GPU elapsed ratio 1.777x); lora: cpu (CPU/GPU elapsed ratio 0.337x)**. This preference is restricted
to the measured bounded workflow. It does not alter default device arguments,
scientific settings, linear-probe/EEGNet policy or the freeze draft. In particular,
the 1,893.4-hour neural CPU planning proxy is not divided by these ratios: it was
derived under other pilot settings, and complete search, checkpoint storage,
unseen candidates/subjects and execution overhead remain unbudgeted.

## Verification and recovery scope

All four public calls passed: **204 engineering gradient steps** (200 source,
four CPU validation-support), zero outer-target predictions, full selections or
scientific cells. The full selection still refused before fitting at its original
ceiling. Each worker had a 600-second cap and an 8 GiB GPU allocator cap; existing
machine/cooling guards remained unchanged. Completed timing cases are immutable
resume units. Per-step serialization is excluded equally for this short
calibration; an interrupted timing case would be retained as failure evidence
and require a separately admitted retry. The checkpoint feature and its actual
hard-exit/sensor-stop recovery remain verified at milestone 50.

All 45,040 prior run files retain their hashes.
The source fingerprint remains `6d01ec59d7323af0fd91f141d1484a419717062b43d7d52dc221d27ea9be19a2`.
The exact-source 571-test/935-subtest lint/types/tests bundle and 45/45 current
controls remain independently verified. They were reused without rerunning
unchanged tests or control fits; the new checks are the actual paired workflow
measurements, identity comparison and preservation audit.

There is no remaining identified bounded implementation task in the authorized
GPU/checkpoint/control scope. The next scientific step requires the owner's
freeze/EA decision and committed-config/workload prerequisites. Gate A sign-off,
MMIDB eligibility and commit/push remain reserved for the owner. The delegated
12-hour window does not waive those explicit reservations; generic continuation
does not authorize inventing another engineering milestone or bypassing a guard.
Final receipt: `runs/phase2/whole_fold_device_checks/20260919_step52/receipt.json`.
