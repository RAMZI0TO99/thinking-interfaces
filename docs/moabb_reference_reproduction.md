# MOABB EEGNet reference reproduction investigation

Status: reference identified on 2026-08-31; no matched run completed and no pass
tolerance adopted. This is separate from the frozen Phase I benchmark grid.

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
the installed callback default must be checked rather than assuming the current
project's best-validation-checkpoint behavior.

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

Next: implement and run a resource-guarded bounded fold smoke test before committing
to the nine-subject/four-seed grid. Four seeds
are required by the day plan; the reference YAML fixes model seed 42, so explain
any repeated-seed extension explicitly. Preserve per-fold predictions, split
identities, preprocessing/source/configuration hashes and elapsed time. Report
the reference's aggregation separately from subject-level uncertainty.

No current run or historical result may be relabeled as this reproduction.
