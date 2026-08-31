# Cho2017 subject 43 — targeted plausibility review

Review date: 2026-08-31. All results remain exploratory while Gate A is unsigned.

## Finding

The frozen EEGNet benchmark reaches 98.42–99.47% balanced accuracy across five
seeds on the same 190 held-out trials. Shallow seed 11 reaches 98.42%. These
scores trigger the plan's plausibility review; they are not accepted as evidence
of an unusually effective BCI without further validation.

## Independent controls

The diagnostic selected the original earliest five target trials per class
before shuffling labels. It shuffled only the source-plus-support training labels,
preserving their counts. The original query signals, labels, and membership stayed
unchanged. Model settings match the frozen benchmark; only training labels differ.
Results are isolated under `runs/falsification/cho2017/subject_43/` and cannot enter
benchmark aggregation.

| Model | Seed 11 | Seed 23 | Seed 37 | Mean |
|---|---:|---:|---:|---:|
| EEGNet, shuffled training labels | 48.95% | 43.68% | 51.58% | 48.07% |
| Shallow, shuffled training labels | 48.42% | 49.47% | 57.37% | 51.75% |

The descriptive mean across all six fits is 49.91%, near the 50% two-class chance
level. These fits share the same query trials, so they are **not** six independent
subject samples and their predictions must not be pooled into an ordinary
independent-trial significance test. No post-hoc chance acceptance interval was
introduced. This control did not reproduce the near-perfect original scores.

SHA-256 comparisons found no exact target/source or query/training signal copies.
The processed channel inventory contains 64 EEG-named channels and no named
EMG/EOG/stim channels. Profile A selects the loader's EEG channel type before
filtering; the installed Cho loader marks the final four auxiliary channels EMG
and the event channel stim, excluding them from model input. Name checks alone
would not establish this.

Target median RMS is 115.61 µV for left and 112.75 µV for right; maxima are about
2.50 mV. These are descriptive values, not proof of artifact-free EEG. The frozen
5.896 mV dataset threshold is permissive for this subject; it was not tightened
after observing results.

## Ordering and filtering limitation

The installed MOABB `datasets/gigadb.py` loader separately demeans the left and
right arrays, concatenates all left trials, a 500-sample zero buffer, and all
right trials. Its own warning identifies noncontinuous-trial edge effects.
Accordingly, the saved target labels have one transition between 100 left and
100 right trials. This is loader order, **not demonstrated original acquisition
chronology**. The support selection is earliest within the available class order.

Neither trial index nor labels enter model input. Nevertheless, class-conditioned
assembly and zero-phase filtering across reconstructed boundaries can create
signal confounds that a training-label shuffle would remove too. Exact hashing
also does not test near-duplicates or overlapping original recording intervals.
The present diagnostics therefore cannot isolate motor-imagery physiology from
all acquisition or preprocessing cues.

## Disposition

Direct index overlap, exact copied signals, and persistent high decoding under
the tested label shuffles were not observed. The high original score remains
unexplained, with a documented loader/edge-effect risk. Keep the fold in the
precommitted exploratory table; do not remove it or tune preprocessing based on
its accuracy. No blanket leakage clearance or scientific gate approval is granted.
A new boundary-isolated/raw-chronology control would need a separately labelled
protocol, not silent replacement of this frozen benchmark.
