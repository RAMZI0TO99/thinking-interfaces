# MMIDB EEGNet plausibility review — preliminary, not clearance

Reviewed on 2026-08-31 after seeds 11 and 23 completed for all 109 subjects.
The remaining three EEGNet seeds and six other methods are incomplete. This is
not the final complete-grid review and cannot satisfy that requirement.

The inspected packet contains 1,848 records, with snapshot
`642142cc88fa1807eaacfbd7dd117d9a7e9d85d32b5c4098f24c11d627d3253e`.
Benchmark configuration:
`434fc4d25a5071a094268ab410c47f79bd92823aacd8e9d06e9f684609aab258`.
Audited input snapshot:
`a5b83711ed36a33f541349824face53cb74ec7fa1755d240d5a25e40873b550d`.
No input/record count mismatches were found. Repeated seeds share query trials;
they are not independent repetitions of data collection.

## Cases inspected

Both saved seeds, both class recalls and both query-class counts were inspected
for all 33 subject/method cases triggered by any score above 78% balanced accuracy.
All are EEGNet cases. The flagged cases have 35 query trials each, with class
counts between 16 and 19, and no frozen artifact rejections for these subjects.

| Triggering seeds | Subject numbers |
|---|---|
| Both 11 and 23 | 002, 007, 029, 034, 043, 048, 062, 065, 071, 072, 085 |
| Seed 11 only | 001, 019, 022, 031, 040, 042, 049, 052, 054, 055, 056, 064, 070, 075, 086, 090, 093 |
| Seed 23 only | 015, 044, 046, 060, 108 |

Subject 085 scores 100% in both seeds; subject 007 scores 97.22%/94.44%, and
subject 072 scores 94.44% in both. These high runs have strong recall for both
classes, so majority-class prediction alone cannot explain their balanced accuracy.
This arithmetic observation is not evidence of physiological or leakage clearance.
Identical confusion counts across seeds do not establish identical model weights.

Large seed variation also remains visible: subject 049 falls from 83.33% to
60.29%, and subject 042 from 80.56% to 58.33%. Lower seed means do not cancel an
original high-score flag. No best seed is selected and no subject is removed.

## Targeted review of subject 085

The original processed artifact contains 45 trials, 64 channels and 512 samples
per trial. There are 23 left-fist and 22 right-fist trials. Earliest balanced
support uses ten trials; the unchanged query contains 18 left and 17 right.
Both original runs classify all 35 correctly. These are two fits on the same
query set, not 70 independent held-out trials.

The three local EDF files for runs 04, 08 and 12 were inspected directly. Each
has 64 channels reported as EEG, 160 Hz sampling, 123 seconds duration and 15
motor cues. T1/T2 counts are 8/7, 8/7 and 7/8. Motor onsets range from 4.1 to
118.9 seconds with a minimum separation of approximately 8.2 seconds. Thus the
configured one-second baseline plus four-second epoch intervals do not overlap
between consecutive motor cues in these files. This does not establish that
offline filter influence, run effects or physiological artifacts are absent.
The processed run order is 04, 08, 12 with 15 trials each and 32 label transitions;
unlike the known Cho loader issue, this artifact is not one left block followed
by one right block. Correct ordering alone is not a leakage test.

The targeted signal audit found no exact source/target or training/query copies,
no repeated target signal hashes, and no EOG/EMG/stimulus-like channel names.
Median class RMS is approximately 9.175/9.323 microvolts, and maximum absolute
amplitude is 113.239/121.055 microvolts for left/right. Names and descriptive
amplitudes do not prove clean EEG or rule out muscle/eye/acquisition confounds.

### Fixed-episode shuffled-label controls

Three separate EEGNet controls used the unchanged training configuration and
seeds 11, 23 and 37. The original episode was selected before shuffling labels
of the 4,867 source trials plus ten support trials. The 35 query trials and their
labels were untouched. Controls write outside the benchmark tree.

| Shuffle seed | Balanced accuracy | Correct left / 18 | Correct right / 17 |
|---|---:|---:|---:|
| 11 | 37.4183% | 5 | 8 |
| 23 | 53.5948% | 14 | 5 |
| 37 | 48.2026% | 11 | 6 |

Mean balanced accuracy is 46.4052%. Independently reconstructing support/query
selection and label permutations reproduced the saved index/label hashes and
changed-label counts (2,444, 2,414, 2,394). Direct confusion arithmetic from the
saved query predictions reproduced all three balanced accuracies and kappas.
Class counts were preserved and the training/query indices were disjoint.
This supports a loss of predictive performance after training-label shuffling;
it is not an equivalence test proving chance performance or a blanket leakage
clearance. There are three fitted controls on one 35-trial query set, not 105
independent query trials. No other subject or method is cleared by these controls.

The main queue was paused after Cho tangent subject 16 was atomically saved.
All 1,849 benchmark records retained snapshot
`f43a972d916da85dc470506e2843480bc074897a7288cfb7ac004c07b0ec67a7`
through the controls and independent verification; then the queue was resumed.
The controls ran from clean source commit
`2c58b75ee7f955b8f41d5aa691f95385d3d0330f` with no production setting changes.
Operational logs: `runs/compute_logs/20260831T0901052861338Z.mmidb-085-controls.*.log`.

## Evidence hashes and disposition

Paths below are relative to the project root; all digests are SHA-256.

| Artifact | Digest |
|---|---|
| `data/processed/mmidb/profile_a/subject_085.npz` | `9fe1d5266e3b55d8d869d84c4bc1a1afe0c68ee6f5d0d362db7f569f22b3513b` |
| `runs/benchmark/mmidb/eegnet/seed_11/subject_085.json` | `ac19c5fecd11ea49737f45663cac4eee0668e2ba078fd4ad06d52aaf2030e59c` |
| `runs/benchmark/mmidb/eegnet/seed_23/subject_085.json` | `4b15e2d6d9d7fca6ab6fc83a6dcdf05b84d8740741f135b26c3b9cd94ef172a0` |
| `runs/falsification/mmidb/subject_085/signal_audit.json` | `ab1d758ed30eb19cb077fe39d157b4cd2df016079e6d544931efb94e6b353412` |
| `runs/falsification/mmidb/subject_085/eegnet_shuffled_seed_11.json` | `3a6729d4826e4084ac236493ab78149e6e74d0a084204ce96be32e7c1f36ba95` |
| `runs/falsification/mmidb/subject_085/eegnet_shuffled_seed_23.json` | `b035db7699a245906dd1cd6b816c54dbbf7a724cf43cb447f328215b56691cb1` |
| `runs/falsification/mmidb/subject_085/eegnet_shuffled_seed_37.json` | `27311ca0263c46739ef3dd60ce3de5a63e57258f1e4719de27414ffd98fe28ee` |

All 33 cases remain unresolved and retained in the frozen exploratory results.
The final review must cover all five seeds and all seven methods when complete.
Scientific Gate A is still unsigned. Neither these controls nor the complete-
cohort exact-copy audit authorizes scientific sign-off or post-result tuning.
