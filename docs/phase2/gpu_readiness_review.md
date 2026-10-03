# GPU readiness and CPU-hours clarification - milestone 49

19 September 2026. The owner renewed delegated operational judgment and explicitly
allowed GPU use if useful, asking whether 1,893 CPU hours means actual hours.
This authorizes the bounded engineering probe below. It does not resolve the
standing owner-only freeze/EA, MMIDB, Gate A or commit/push decisions.

## What the hours mean

The corrected draft's 1,893.4 hours is a projected sum of elapsed CPU execution
stage times on one worker, including a 1.25 allowance: about 78.9 days if run
sequentially at those observed rates. It is not the sum of time on individual
CPU cores and is not one model's training duration. Pilot scripts measured
`time.perf_counter()`, not process CPU time. The four neural methods have
52 targets x 5 seeds x 4 methods = 1,040 selections; each has 102 inner
candidate/fold evaluations plus final fitting and target evaluation. That
repetition produces the large estimate. The additional EA proxy is 3,328.0
hours. Neither number is a measured full sweep, a verified upper bound or a
completion promise; costs missing from the draft remain missing.

## Bounded CPU/GPU measurement

The RTX 4080 Laptop GPU passed live machine admission. The probe used one
fixed audited **Cho subject_02 source-support batch**, no subject_01 target
queries, the verified safe LaBraM weights, seed 11, float32, SGD and the two
proposed learning rates. LaBraM uses two trials at 64 x 800; EEGNet uses four
at 64 x 512, scaled exactly as its CPU source path. CPU uses two threads;
TF32, mixed precision and cuDNN benchmarking are disabled. Every case gets
an independent model and fresh optimizer; models stay in evaluation mode.

Four methods x two rates x two devices x (one warm-up + five measured steps)
= **96 actual engineering gradient steps**, 48 on each device. These are
primitive timing checks, not complete source fits, selection or accuracy
results. Measured medians exclude initialization, device transfer, resource
checks and state validation. CUDA synchronizes around every timed step.

| Method | Learning rate | CPU ms/step | GPU ms/step | CPU/GPU ratio |
| --- | --- | --- | --- | --- |
| labram_linear | 0.001 | 44.77 | 26.54 | 1.69x |
| labram_linear | 0.002 | 43.14 | 27.08 | 1.59x |
| labram_lora | 0.001 | 50.12 | 30.70 | 1.63x |
| labram_lora | 0.002 | 48.52 | 30.69 | 1.58x |
| labram_full | 0.001 | 161.04 | 47.12 | 3.42x |
| labram_full | 0.002 | 163.38 | 88.40 | 1.85x |
| eegnet | 0.001 | 9.98 | 11.52 | 0.87x |
| eegnet | 0.002 | 10.47 | 11.54 | 0.91x |

A ratio below 1 means CPU was faster. There are only five observations per
case, one subject and one seed, and CPU preceded GPU. Full-tuning timing
varies substantially between these two runs; this does not establish a
learning-rate effect or a stable whole-workload speedup.

Initial CPU/GPU logits passed a separately declared float32 sanity check
(atol/rtol 1e-4); maximum observed absolute difference was 2.2530556e-05.
Selected parameters changed, gradients/parameters stayed finite, and frozen
state plus original templates were unchanged. This is not full optimization
trajectory parity and does not replace historical reference tolerances.
All audited input/checkpoint hashes and the project source fingerprint match.
Peak observed Torch allocated memory was 216.67 MiB; maximum temperature
recorded after GPU cases was 57 C. These exclude other applications' GPU
memory and are not continuous peak-temperature measurements.

The unchanged live disk/GPU/RAM checks passed before every step. Existing
80 C pause / 76 C resume cooling was used; this probe additionally required
an available sensor and 1 GiB free GPU headroom, capped its own allocator at
8 GiB, and stopped at 96 steps / 600 seconds. Measured loop elapsed time was
49.41 seconds (imports are outside that timer). No other
project worker was observed in the pre-launch check. No selector admission
method was bypassed or private fitting helper invoked.

## Adopted operational decisions and remaining work

- Prefer a GPU-capable LaBraM engineering path based on this bounded gain;
  retain CPU for EEGNet at the tested batch size. These choices are provisional
  until full source/support/query timing is available, not a scientific freeze.
- Retain current scientific batch sizes and proposed rates during comparison;
  no accuracy-dependent or convergence claim is made.
- Do not divide the 1,893.4-hour proxy by the step-speedup. Source iteration,
  repeated artifact loading/verification, state hashing, target adaptation,
  query evaluation and persistence were not timed end to end. One observed
  Profile B load alone took 0.566 s;
  one Profile A load took 0.280 s.
  These single observations do not establish the full overhead distribution.
- The installed neural selectors/adapters explicitly assume CPU execution;
  no production GPU integration was performed here. GPU support requires
  device-aware tensors, model/optimizer state, RNG/runtime provenance and
  appropriate state-isolation checks before an end-to-end admitted probe.
  The unchanged 256-step ceiling still rejects complete Cho selection.
- EA's existing classical implementation has no verified GPU path here. EA
  inclusion remains an owner decision; it is not silently removed or approved.

No production/config/test file changed. The exact-source full quality bundle
from milestone 48 still verifies: **564 tests / 925 subtests, lint and strict
types passed**. It was not rerun for this evidence-only primitive probe; the
new GPU checks above were actually executed and recorded separately.
No scientific cells, complete selections, target-query evaluations, control
refresh, commit or push occurred. The scientific draft remains byte-identical
and unratified. Gate A remains unsigned; all Phase II evidence is exploratory.

Evidence: `runs/phase2/gpu_readiness_checks/20260919_step49/`, including the
pre-run admission, exact executable probe, per-case timing arrays, input hashes,
resource snapshots, quality-bundle copy and final receipts.
