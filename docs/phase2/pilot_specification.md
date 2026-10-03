# Phase II representative pilot specification

> Status clarification - 9 September 2026: this remains the unexecuted 8 September
> draft. Its disk-failure statement records that earlier snapshot; disk headroom
> was subsequently restored. The RAM-dependent control refresh remains deferred,
> and P2/source-selection plus scientific-runner requirements remain unfinished.
> See the [current status](README.md). No pilot limits or admission criteria changed.

Draft 1, 8 September 2026. Implements the P3 measurement requirements of the
existing v2 plan. **Specified, not executed; compute admission is false.**
The [JSON draft](pilot_specification.json) is a planning artifact, not an executable
training configuration or the frozen scientific experiment matrix.

## Case selection and coverage

Choose the lexicographically first eligible subject in each audited dataset as
the development target and the first different eligible subject as a representative
inner-validation fold. This rule uses existing identities and eligibility only;
no prediction score was read to select these cases. These subjects remain in the
declared scientific cohort: pilot query outputs may measure computation only and
must not supply hyperparameter selection or early stopping.

| Dataset | Development target | Representative inner fold | Current Profile A shape per trial | Common queries |
| --- | --- | --- | --- | --- |
| BCI IV 2a | subject_01 | subject_02 | 22 × 512, four classes | 496 |
| Cho2017 | subject_01 | subject_02 | 64 × 512, two classes | 160 |
| MMIDB | subject_001 | subject_002 | 64 × 512, two classes | 5 |

BCI provides the smaller montage; Cho supplies the larger montage and primary
dataset; MMIDB exercises a small common query pool and its distinct source-cohort
eligibility issue. The source-training fold excludes both named held-out subjects:
7 BCI, 50 Cho or 107 MMIDB source subjects. The final source fit excludes only the
outer target. One measured inner fold is a cost sample, not completed LOSO selection.

The matrix contains **59 target cases per repetition**:

- All nine adopted method IDs × three datasets × one/twenty shots = 54 cases.
- Cho five-shot linear, LoRA, full tuning, EEGNet and EA-tangent = five cases.

Use model seed 23 for this timing pilot; the scientific seeds remain
11/23/37/53/71. Fixed support is not resampled. All query trials remain outside
the maximum twenty-shot pool. Run three measured repetitions after warm-up:
177 target-case measurements, plus separately charged source/selection work.
Runtime repetitions are not new experimental seeds or independent subjects.

Before running a case, pin its real input profile, shape, units, class/montage,
method and source-fit dependencies. LaBraM's intended four-second Profile B input
is 800 samples at 200 Hz; current Profile A tensors must not be relabeled as that
input. Preparation and cross-profile joins must pass first. TCPL cases carry
`local_reconstruction` status; they cannot stand in for verified author reproduction.
All-shot integration checks, including ten shots, remain a P2 requirement even
though this cost pilot emphasizes the one/twenty-shot extremes.

## Measurements and bounded execution

The future `scripts/phase2_pilot.py` must consume a validated manifest and explicit
method candidate configuration; missing optimizer, stopping, fit-scope or
preprocessing fields cause refusal. Existing smoke values are not implicit defaults.

| Stage | Required measurement and boundary |
| --- | --- |
| Read/prepare | File/hash validation, decompression, preprocessing and tensor transfer times separately; input/output bytes and cache hit status. |
| Source fit | Permitted source IDs, candidate/seed identity, initialization time, optimizer, batch size, actual trials/steps, loss finite checks, peak RAM/VRAM and checkpoint bytes. |
| Inner validation | Held-out source support construction, adaptation/conditioning and all common-query inference; include model reload and candidate-selection overhead. |
| Target support | Fresh source/optimizer state where relevant, transform-fit scope, steps, support count and peak resources. TCPL conditions without target parameter updates; prompt batch-one support encoding is charged explicitly. |
| Target query | Whole common-query set, synchronized wall time and throughput at the declared batch size; separate batch-one timing. No target accuracy is used for pilot decisions. |
| Persist/audit | Safetensors/record write and verified-resume time, actual disk growth, failed attempts, control-refresh cost and audit time. |

For neural source-cost probes, use two warm-up steps followed by three blocks of
twenty measured steps, capped at 100 total steps per probe. Record iterator wrap,
batch shape and actual unique trials. This is a throughput probe, not a converged
source fit. Target timings using these weights must say so. When epoch overhead,
checkpointing or variable-length work invalidates a per-step estimate, require a
separately admitted longer probe; do not claim the 62-step probe predicts accuracy
or the cost of an unspecified stopping rule. Classical fits use their full declared
pilot fold and the same timeout reporting rather than invented gradient steps.

Reset to the same starting state for measured repetitions. Record one cold load
and warm-cache repeats separately. Synchronize CUDA before and after timed GPU
sections, retain allocated/reserved VRAM peaks, and sample host RSS/available RAM
at 100 ms intervals. Record the sampling interval and possible missed brief peaks.
Measure wall-clock and active compute time separately from cooling waits. Report
all repetitions, their median and maximum, never just the fastest result.

## Admission, interruption and retry

These are draft operational caps to encode and validate before execution:

- One worker; at least 20 GiB free disk and 8,192 MiB GPU capacity, retaining the
  existing `configs/base.toml` thresholds. Require at least 4 GiB free host RAM
  throughout; choose a batch size only after a memory probe and record it.
- Apply `configs/runtime_limits.toml`: pause at 80°C, resume at/below 76°C. Charge
  cooling time separately and obey existing bounded waits.
- Maximum 10 minutes active work per probe and two hours active work for the first
  pilot session. Hitting either cap records an incomplete case/session, never a
  successful measurement. This ceiling is not a claim that 59 cases will fit.
- Stop safely before the next unit when disk/RAM guards fail. Preserve completed
  evidence and failures. No automatic file deletion, cohort reduction or weaker
  numerical criterion is an admissible recovery.
- At most one retry per failed case, using identical scientific identity and
  a new attempt ID linked to the failure. Identity changes create a different
  case. Atomically claim work so duplicate workers cannot claim the same case.

Current admission fails on disk. The general pilot and scientific claim/audit
implementation are also missing. Even adequate disk space alone would not make
this specification runnable. A matched scientific source fit and selection result
are required before publishing a scientific cell; provisional pilot weights
produce engineering measurement records only.

## Work estimate and freeze decision

Using current audited eligibility, the provisional scientific grid is:

| Scope | Arithmetic | Target evaluation cells |
| --- | --- | --- |
| Primary Cho five-shot tranche: linear, LoRA, full, two anchors | 52 × 5 methods × 5 seeds | 1,300 |
| All seven systems, all datasets/shots/seeds | 168 × 7 × 4 × 5 | 23,520 |
| Two anchors across the same grid | 168 × 2 × 4 × 5 | 6,720 |
| Combined expanded grid | 168 × 9 × 4 × 5 | 30,240 |

The original research plan's 23,800 seven-system cells used nominal 170 subjects.
The updated count reflects the two audited MMIDB target exclusions; the original
plan is preserved. These are planning counts, not admitted jobs or completed fits.
Do not count target cells as independent source fits. Deduplicate only compatible
source dependencies with identical cohort, candidate, seed, preprocessing and
checkpoint history. Deterministic anchors still need declared seed-cell handling;
never silently drop expected records because predictions happen to match.

Compute the forecast from the explicit dependency graph:

`active = sum(unique source-fit costs) + sum(inner-search costs) + sum(target
support/query costs) + preparation + persistence/audit + control refresh`.

Use maximum observed stage cost at the matching shape/batch as the initial
conservative estimator and multiply active work by **1.25** for a declared retry
allowance; then add observed cooling/wait overhead separately. Count failed work
already performed, and do not charge a shared source fit twice. Report checkpoint
and intermediate-data retention peaks in addition to final output size. If required
training steps, candidate counts or eligible source episodes are unresolved,
the relevant total stays unknown; a fabricated hours-to-completion value is invalid.

Before P3 exit, freeze candidate counts, selection/stopping rules, method and
preprocessing choices, seeds, primary/secondary families, failure policy, resource
envelope and expected scientific cell/dependency manifest. Admit only work that
fits the measured envelope. Accuracy cannot decide expansion. Pilot caps and
timing results do not modify the frozen H2 margin or supply scientific sign-off.
