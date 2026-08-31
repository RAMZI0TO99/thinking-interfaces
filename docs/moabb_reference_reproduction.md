# MOABB EEGNet reference reproduction investigation

Status: reference identified and real-data integration smoke passed on 2026-08-31;
full matched evaluation is still outstanding and no pass tolerance is adopted.
This is separate from the frozen Phase I benchmark grid.

## Verified primary sources

- [Published table and metric definitions](https://moabb.neurotechx.com/docs/paper_results.html).
- [Benchmark paper, methods and motor-imagery preprocessing](https://arxiv.org/html/2404.15319v1).
- [Linked v1.1.2 pipeline configuration](https://github.com/NeuroTechX/moabb/blob/v1.1.2/pipelines/Keras_EEGNet_8_2.yml).
- [Model wrapper](https://github.com/NeuroTechX/moabb/blob/v1.1.2/moabb/pipelines/deep_learning.py),
  [epoch transformations](https://github.com/NeuroTechX/moabb/blob/v1.1.2/moabb/pipelines/features.py),
  [evaluation](https://github.com/NeuroTechX/moabb/blob/v1.1.2/moabb/evaluations/evaluations.py),
  [paradigm](https://github.com/NeuroTechX/moabb/blob/v1.1.2/moabb/paradigms/motor_imagery.py),
  [dependency declarations](https://github.com/NeuroTechX/moabb/blob/v1.1.2/pyproject.toml).

## Behavior verified from the linked implementation

The evaluator loops over subjects and sessions separately, applies shuffled
stratified five-fold splits, clones each pipeline per fold and averages fold
scores. LeftRightImagery scores ROC-AUC. The linked `benchmark.py` explicitly
sets evaluation random state 42; its deep-learning example also calls setup_seed(42).
That distinguishes the reference invocation from an arbitrary evaluator default.
The classifier's configured random state is independently fixed at 42.

The pipeline resamples Epochs to 128 Hz, converts to an array and standardizes each
epoch separately. Importantly, StandardScaler is applied to the channels-by-time
array without a transpose: its statistics are across channels for each time
sample, not across time for each channel. Its fit method learns no pooled
cross-trial statistics. Do not substitute a different standardization convention.

The YAML sets 300 epochs, batch size 64, sparse categorical cross-entropy, Adam at
0.001, classifier random state 42, and a 20% validation split. It configures
validation-loss early stopping and learning-rate reduction with patience 75 and
reduction factor 0.5. It does not explicitly enable best-weight restoration;
installed Keras 3.3.3 source confirms restore_best_weights=False, unlike the
current project's best-validation-checkpoint behavior. Its validation splitter
uses the final 20% of the supplied outer-training rows before training shuffle;
it is not a separately randomized/stratified inner validation split. The source
also confirms early-stopping min_delta 0 and the learning-rate callback's default
min_delta 1e-4, cooldown 0 and minimum learning rate 0.

The wrapper sets F1=8, D=2, temporal kernel 64, dropout 0.5 and a dense classifier
with max-norm 0.5 followed by softmax. Inspection of the called block confirms
channels-last convolutions, SAME temporal padding, depthwise max-norm 1, ELU,
pooling by 4 then 8, and a separable temporal kernel 16. The implementation must
be used directly, not approximated by the project's existing Braindecode model.

The paper confirms 8–32 Hz motor-imagery filtering. The linked paradigm uses
continuous-run IIR filtering on EEG channels, no baseline and no new common-average
reference. BNCI2014_001's epoch interval is [2, 6] seconds relative to its loader's
event times; task-relative tmin 0 is added to that interval's start. Epochs retain
their default inclusive endpoint, then the pipeline resamples to 128 Hz. Record
the actual resulting sample count rather than assuming that it equals Profile A's
512. The paper independently confirms the YAML's 300 epochs, batch 64, Adam 0.001
and patience 75. The reference's full-run filtering before random fold assignment
is part of its offline protocol, not proof of a causal online implementation.

## Environment and unresolved implementation details

The main Python 3.12 environment has no TensorFlow, Keras or SciKeras. The linked
reference declares NumPy 1.x and scikit-learn below 1.6, unlike the active project's
NumPy 2.x/newer stack. It also declares TensorFlow >=2.16, Keras >=3.2 and SciKeras
0.13. The public v1.1.2 reference resolves to commit
`507a4cccda9efbd5ef019aceeeeb3d298308ec43` (2025-03-05), whose package version is
1.2.0. It is later than the 2024 paper and is not evidence of the exact original
training environment. The tag-specific API lookup did not resolve; use the commit
identity, not an assumed immutable tag or package version alone.

`configs/moabb_reference_environment.toml` pins a separate compatibility environment
under `runs/moabb_reference/environment` and nine reviewed source-file hashes.
It uses TensorFlow 2.16.1, Keras 3.3.3, SciKeras 0.13, NumPy 1.26.4, MNE 1.7.1 and
scikit-learn 1.5.2. The first dry-run rejected Seaborn 0.13.2; the requirement was
corrected to 0.12.2 to satisfy MOABB's declared range, before any package install.
The successful dry-run report records the transitive dependencies and archive
hashes; installation uses those exact URLs and hashes with dependency re-resolution
disabled. The main environment is not downgraded or otherwise modified.

The lightweight checker runs as:

```powershell
.\runs\moabb_reference\environment\Scripts\python.exe -m scripts.check_moabb_reference_environment
```

It verifies the interpreter, pinned dependency versions, upstream archive URL and
source-file bytes without importing the ML stack. Its timestamped receipt separates
environment verification from training readiness and explicitly records that no
training or reproduction occurred. Training needs at least 10 GiB free memory and
10 GiB free disk; the existing benchmark retains priority. Successful installation
or a future short smoke test must not be presented as a reference reproduction.

The first installation check passed at 2026-08-31T10:28:26Z, including all nine
source hashes and resolved dependency versions; `pip check` found no broken
requirements. Receipt: `runs/moabb_reference/environment_check_20260831T102826074433Z.json`.
Installed files totaled 2,040,825,731 bytes (logical size). The sorted main-environment
package/version snapshot hash was unchanged before/after:
`4edf489d3e1916bbe0012b56cd845c085f5993cb47426466880b855cca645191`.
Only 7.20 GiB memory was free, so training readiness was false and no model was
imported or trained. Available disk was 26.88 GiB after installation.

The bounded smoke is now implemented and its refusal paths are tested:

```powershell
.\runs\moabb_reference\environment\Scripts\python.exe -m scripts.smoke_moabb_reference
```

Its committed settings select subject 1, session 0train, fold 0 of five, model
and split seeds 42, and only two epochs. It uses the verified upstream loader,
preprocessing and classifier directly. The only loader override redirects its
download resolver to the two existing local MAT files; unexpected filenames are
rejected and raw hashes are recorded. It retains optimization/validation/query
indices and query probabilities, verifies callback/class order, finite losses and
probabilities, and confirms the reference's spatial centering. Outputs and a
RunRecord are separate from the main benchmark. A low-memory check precedes ML
imports and an additional stop check runs before fit and at each epoch.

The first actual invocation at 10:34:42 UTC deferred at 6.95 GiB free memory, with
training_performed=false. Receipt:
`runs/moabb_reference/environment_check_20260831T103442143787Z.json`.
No numerical smoke result existed at that point; the later successful test is
documented below. A two-epoch integration score does not
count toward the reference's 300-epoch training protocol or any gate acceptance.

Next: complete and independently audit the prepared grid; the first declared
full-protocol fold has now passed its record checks. Four repeat seeds
are required by the day plan; the reference YAML fixes model seed 42, so explain
any repeated-seed extension explicitly. Preserve per-fold predictions, split
identities, preprocessing/source/configuration hashes and elapsed time. Report
the reference's aggregation separately from subject-level uncertainty.

No current run or historical result may be relabeled as this reproduction.

## Successful real-data smoke and protected benchmark resumption

After saving Cho tangent subject 38, the verified main queue was deliberately
paused. The first post-pause memory check was still below 10 GiB and deferred;
a fresh check then exceeded the unchanged limit and permitted the two-epoch test.
No memory threshold, benchmark setting or completed result was changed.

The real reference smoke completed on CPU at 2026-08-31T10:51:39Z:
`runs/moabb_reference/smoke/20260831T105139058810Z/result.json`, SHA-256
`680339220612ce4c17a8410831d924d16f314427aafe65af9996b8bd74240c5b`.
Its RunRecord hash is
`f586445559fe4619af38469b3604ab1eafb9e74bd7d39b662d407f3e02dc206c`.
Source commit: `4eee55848ff6cd6da3a03818bead543aa0125a53`, clean;
source fingerprint: `d2dbaacb152c827271ef53dd4ba58dc0081a78cd1a570fc230ff7d9c27bee218`.

Subject 1/session 0train contained 144 left/right epochs of 22 channels and 1,001
native samples. The reference resampled these to **513 samples**, preserving the
inclusive endpoint; do not truncate to the earlier pipeline's 512. The first fold
had 92 optimization, 23 validation and 29 query trials; query classes were 14/15.
All three index sets were disjoint and together covered the session. Fit time was
2.073 seconds for two epochs, including setup overhead, not a full-training time
estimate. Losses and query probabilities were finite. ROC-AUC was 0.6523809524;
this two-epoch integration score is not a Gate A reproduction or a comparison
against the published 300-epoch training protocol. Best-weight restoration was off.

An independent check recomputed ROC-AUC from saved probabilities, checked the
split partition and rehashed both MAT inputs. It agreed with the RunRecord and
result. The upstream warnings about epoch display, Keras input_shape and absent
optional PyTorch were retained; PyTorch was not installed into this Keras-only
environment. The successful run does not prove causal filtering or absence of
acquisition confounds.

All 1,870 pre-pause benchmark files remained unchanged; subject 38 added one new
record. All 1,871 files at the paused snapshot were rehashed successfully before
resumption. Snapshot: `750dd8b52f071a82b210dcdb9783371ce4864bcef0131d8a516633141ad846f8`.
The benchmark resumed at 10:52:23 UTC in
`runs/compute_logs/20260831T1052234984766Z.stdout.log` with a separate stderr log.
The queue reused previous controls and neural records and returned to the unfinished
Cho classical work. This deliberate bounded interruption is not a failed fit or
a restart triggered by an observation timeout.

## Prepared full evaluation grid

`configs/moabb_reference_evaluation.toml` declares all nine subjects, both sessions
and five within-session folds. Seed 42 is the published-configuration anchor
(90 fits). The earlier Gate A repeat seeds 11/23/37/53 remain a separate four-seed
extension (360 fits). Thus the prepared grid has 450 fits, not 450 independent
subjects and not 450 existing results. One declared fit has completed; the full
queue has not yet been launched. The CV split seed
remains 42 across model seeds, isolating training-seed variation.

The configuration preserves 300 epochs, batch 64, Adam 0.001, 20% validation,
dropout 0.5, patience 75, no best-weight restoration and upstream preprocessing.
The plan validator rejects an incomplete subject/session grid, altered protocol,
ambiguous identity types or an added pass tolerance. The descriptive aggregator
requires every unique configured fold, averages folds within sessions, reports
each seed separately and computes the four-repeat-seed interval over nine subject
means. Seed 42 is excluded from that four-seed interval. Sample and population SDs
across subject/session pairs are both labeled because the table's precise ddof
has not been established from the linked converter. The published SD is not used
as a tolerance.

These functions are tested with synthetic scores, not a reproduced EEGNet result.
Even a complete score table explicitly leaves underlying run integrity unverified
and scientific gate approval false; actual recorded predictions, identities and
provenance still need a separate audit before any completion claim.

## Resumable worker and record checks

The full worker is implemented and its first full-protocol fit passed record checks.
It shares the exact numerical training/preprocessing function with the successful
smoke. The refactor adds session labels, channel names, prediction timing and
early-stopping history metadata; it does not change numerical operations. The
two-epoch smoke wrapper remains bounded and separate. Its saved prerequisite
result is pinned by SHA-256 in the full-evaluation configuration.

```powershell
# Audit saved reference records without training (exit 2 means incomplete).
.\.venv\Scripts\python.exe -m scripts.run_moabb_reference --check-only
# Qualify the first declared full-protocol unit; no shortened training override.
.\runs\moabb_reference\environment\Scripts\python.exe -m scripts.run_moabb_reference --unit-index 0
# Resume all 450 declared fits, in isolated sequential child processes.
.\.venv\Scripts\python.exe -m scripts.run_moabb_reference
```

Each fit requires a fresh verified environment/resource receipt and committed,
clean source. It preserves raw-input hashes, all splits, predictions and history
in an atomic RunRecord envelope under a configuration-specific reference folder.
Existing results are checked before reuse and never silently replaced. Exclusive
per-unit locks prevent concurrent writers; stale locks require process-identity
review. Low startup resources defer before importing the training stack; the
per-epoch memory stop remains active. The main benchmark's configuration and
records are not changed by this runner.

The record checker reconstructs the five-fold split and final-20% validation
partition, independently computes pairwise ROC-AUC from saved probabilities,
and replays the configured patience-75 early-stopping rule from validation loss.
It verifies full-protocol epoch counts, provenance, raw-input identity and input
shapes. Missing/invalid/unexpected records or pending locks prevent completion.
These checks do not yet independently reconstruct epochs from raw recordings or
resolve the scientific acceptance decision; neither a smoke nor a complete
record table automatically approves Gate A.

## First full-protocol fit and independent input-audit implementation

At 2026-08-31T11:24Z the unchanged resource guard permitted model seed 42,
subject 1/session 0train/fold 0. It completed all 300 epochs (no early stopping)
in 71.352 fit seconds plus 0.162 prediction seconds. ROC-AUC was 0.9142857143
on 29 query trials. This is a single fold, not the published aggregate.
Record: `runs/moabb_reference/evaluation/75135218cfb8104fb74a879e2a73c2e2ac19c876bf551c71ff6526afe56b0a93/seed_42/subject_01/0train/fold_0.json`.
Source commit `8f100aee0c2e23441c7fa2965b832197830ae8d8`, clean; fingerprint
`d7e592dee19e210dd655703cb39377414862705d023311d84dc7e3cf8d080df4`.
The full-grid record audit found 1/450 valid fits, no invalid fits, and explicitly
reported incomplete. The other 449 fits still need execution.

The main queue was paused after Cho tangent subject 45 was saved. All 1,877
pre-pause records were retained, and all 1,878 paused files were independently
rehashed unchanged before resumption at 11:26:12 UTC. Paused snapshot:
`19b1c8aa7fc27be94aab16d787e486903ddc1d62d89a49d18bfbd0945cd76cf6`.
Resumed log: `runs/compute_logs/20260831T1126123805071Z.stdout.log`.

The independent input auditor is implemented and unit-tested; its real-data
execution remains to be qualified:

```powershell
.\runs\moabb_reference\environment\Scripts\python.exe -m scripts.audit_moabb_reference_inputs
```

It reads MAT event labels and one-based onsets directly, constructs the 22-EEG
raw runs without MOABB dataset/pipeline calls, and reconstructs continuous-run
IIR filtering, inclusive [2,6]-second epochs, query-fold resampling and per-epoch
spatial scaling. It compares exact transformed-array hashes and label/channel/
split identities for every saved fit against a shared subject/session proof.
It uses the same pinned MNE/sklearn numerical primitives, so it is independent
orchestration, not an independently implemented filter or scaler. It does not
train/import TensorFlow, uses one computational thread, checks the existing
4-GiB memory stop threshold before each run/fold, and keeps timestamped audit
reports outside the training-record folder. The 10-GiB training-start guard
remains unchanged. Partial coverage cannot produce a complete audit.
