# MOABB EEGNet reference reproduction investigation

Status: reference identified on 2026-08-31; no matched run completed and no pass
tolerance adopted. This is separate from the frozen Phase I benchmark grid.

## Verified primary sources

- [Published table and metric definitions](https://moabb.neurotechx.com/docs/paper_results.html).
- [Linked v1.1.2 pipeline configuration](https://github.com/NeuroTechX/moabb/blob/v1.1.2/pipelines/Keras_EEGNet_8_2.yml).
- [Model wrapper](https://github.com/NeuroTechX/moabb/blob/v1.1.2/moabb/pipelines/deep_learning.py),
  [epoch transformations](https://github.com/NeuroTechX/moabb/blob/v1.1.2/moabb/pipelines/features.py),
  [evaluation](https://github.com/NeuroTechX/moabb/blob/v1.1.2/moabb/evaluations/evaluations.py),
  [paradigm](https://github.com/NeuroTechX/moabb/blob/v1.1.2/moabb/paradigms/motor_imagery.py),
  [dependency declarations](https://github.com/NeuroTechX/moabb/blob/v1.1.2/pyproject.toml).

## Behavior verified from the linked implementation

The evaluator loops over subjects and sessions separately, applies shuffled
stratified five-fold splits, clones each pipeline per fold and averages fold
scores. LeftRightImagery scores ROC-AUC. Evaluation random state is distinct from
the classifier's configured random state; the published run's evaluation seed
still needs identification.

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
with max-norm 0.5 followed by softmax. The called EEGNet block still needs detailed
inspection. The single-pass motor-imagery paradigm defaults to 8–32 Hz, tmin 0,
dataset-defined tmax, no baseline and all EEG channels. These are library defaults,
not proof that the paper's benchmark invocation left them unchanged; inspect the
benchmark invocation before fixing a reproduction configuration.

## Environment and unresolved implementation details

The current Python 3.12 environment has no TensorFlow, Keras or SciKeras. The linked
tag declares NumPy 1.x and scikit-learn below 1.6, unlike the active project's
NumPy 2.x/newer stack. It also declares TensorFlow >=2.16, Keras >=3.2 and SciKeras
0.13. The file inside the tag labels itself version 1.2.0; resolve the actual
commit and archive hashes rather than treating an installed version string as
proof of source identity. No dependencies have been installed or downgraded.

Next: verify the original benchmark invocation and preprocessing, resolve exact
source identity, establish a compatible isolated environment, then run a bounded
fold smoke test before committing to the nine-subject/four-seed grid. Four seeds
are required by the day plan; the reference YAML fixes model seed 42, so explain
any repeated-seed extension explicitly. Preserve per-fold predictions, split
identities, preprocessing/source/configuration hashes and elapsed time. Report
the reference's aggregation separately from subject-level uncertainty.

No current run or historical result may be relabeled as this reproduction.
