# Cho classical-method review — partial grid, not scientific clearance

Reviewed 2026-08-31 after FBCSP and tangent-space logistic regression each
completed all 52 subjects. EA + tangent LR and the wider three-dataset grid
remain unfinished. This is not the final `runs/plausibility_review.json`.

## Evidence and coverage

Each reviewed method has 260 records: 52 actual fits at seed 11 and 208 explicitly
marked deterministic copies for seeds 23/37/53/71. The copies preserve the source
fit's numerical provenance and have zero new fit/prediction time; they are not
independent training repetitions. Both methods retain all 52 subjects.

Current full-record snapshot:
`c93da073ae17e2c69952c1c4b35d333dce2f9ce381f1b9f49e5adce0db3c8d6d`.
The 520-record FBCSP/tangent subset fingerprint is
`a532f1f1969af377d56469e2a3a25e6d694c61c79daa389b31f807a63be5968b`
(canonical configuration digest of the relative-file/SHA-256 mapping).
Benchmark configuration:
`434fc4d25a5071a094268ab410c47f79bd92823aacd8e9d06e9f684609aab258`.

The independently rebuilt packet cross-checked 2,093 records with no input-count
mismatches and retained the verified complete-cohort artifact snapshot. Its
preserved copy is `runs/plausibility_packet_cho_classical_20260831T1201.json`,
SHA-256 `ba8943b77530c3bea35571bed5518e302a06cf350ec77b601bb7608cad6f4f2a`.
It explicitly reports benchmark completion and final local review as false.

## Every flagged case in these two completed methods

All seven cases have 190 query trials, exactly 95 per hand, and ten support
trials. The table reports the ungated balanced accuracy and each class's recall.
These seven fitted prediction sets appear in 35 seed-labelled records; they are
not 35 independent tests. The trigger is any seed above the fixed 78% ceiling.

| Method | Subject | Balanced accuracy | Left recall | Right recall |
|---|---:|---:|---:|---:|
| FBCSP | 03 | 78.4211% | 57.8947% | 98.9474% |
| FBCSP | 41 | 81.5789% | 89.4737% | 73.6842% |
| FBCSP | 43 | 94.7368% | 90.5263% | 98.9474% |
| Tangent LR | 03 | 85.2632% | 80.0000% | 90.5263% |
| Tangent LR | 14 | 80.5263% | 91.5789% | 69.4737% |
| Tangent LR | 41 | 79.4737% | 77.8947% | 81.0526% |
| Tangent LR | 43 | 87.8947% | 77.8947% | 97.8947% |

Across all 52 subjects, FBCSP mean balanced accuracy is 58.8322% with subject SD
10.1391 percentage points; tangent LR is 60.9559% with subject SD 9.4603 points.
These SDs describe subjects, not the deterministic seed copies. Neither method
mean exceeds the trigger; that does not dismiss its individual high-score cases.

## Disposition and limits

- All seven flags remain unresolved in the exploratory benchmark. No subject,
  trial, seed or threshold is removed or changed after seeing these scores.
- Their balanced query classes rule out a simple majority-class explanation.
  FBCSP subject 03 is notably asymmetric in recall, while subject 43 scores
  highly on both hands. Neither observation proves acquisition independence.
- Subjects 03, 14, 41 and 43 also appear in the neural-method review. Agreement
  between classifiers does not independently validate physiology: all consume
  the same recordings and frozen preprocessing.
- The Cho loader's separate class arrays, demeaning, artificial concatenation
  boundary and unproven chronological reconstruction still require caution.
  The full-cohort exact-copy audit found no exact reused signals; it does not
  exclude near-copy, acquisition-block or offline-filter confounds.
- The three-seed subject-43 shuffled-label controls cover EEGNet and Shallow,
  not these FBCSP/tangent fits. Their near-chance results are not transferred as
  blanket classical-method clearance.
- FBCSP's 100% selective accuracy on subjects 41 and 43 covers only 19/190 and
  43/190 query trials respectively. It does not replace the ungated score.
  Subject 43's ECE is 0.3063, so high accuracy also does not imply calibrated
  probability estimates.

The final review must include EA + tangent LR and all later MMIDB flags, bind
the complete record/input snapshot, and keep scientific sign-off separate from
completion of the local review. Existing input/control detail is in
`docs/cho_subject43_review.md`, `docs/cho_neural_plausibility_review.md` and
`docs/corpus_duplicate_review.md`.

## Supplemental EA + tangent review: two early flags, incomplete method

The 2,115-record audit snapshot
`e20bad0b555b8d02cdb099fef01fa38c74d62dee8bf1ed73814cae69ba297901`
contained 22/52 actual Cho EA + tangent fits and two flagged cases, both at seed
11. Later subjects and the deterministic seed copies remain outside this review.
This section does not claim a complete EA-method review or a final review packet.

| Subject | Balanced accuracy | Left correct/query | Right correct/query | Confidence-gated correct/accepted |
|---|---:|---:|---:|---:|
| 03 | 84.2105% | 75/95 | 85/95 | 140/160 |
| 14 | 83.6842% | 71/95 | 88/95 | 135/153 |

Both records retain 200 original trials, zero rejected trials, ten support trials
and 190 balanced query trials, agreeing with the existing corpus summaries. Their
ECE values are 0.0378367794 and 0.0366613382 respectively; this is descriptive
calibration on these query sets, not independent generalization evidence.

The exact seed-11 record hashes under
`runs/benchmark/cho2017/ea_tangent_lr/seed_11/` are:

- `subject_03.json`:
  `fb3b61177f324e21a1c4d30f57cd9bfb606e62a058db5b1616cb0acd0658cd1e`.
- `subject_14.json`:
  `a69b6f4d0031db4815b81b280ba52f5e29f9c4feece6e82acb7d40dc9afa4c4d`.

Inspection of `evaluation/benchmark.py` and `evaluation/alignment.py` confirms
that the held-out subject's whitener is fitted from support trials only. Cached
alignment is computed independently per subject; this fold takes only other
subjects' rows from that cache. Target support is separately aligned, and target
query uses the support-fitted whitener without fitting on query data. These two
code files are unchanged between the two recorded historical commits and the
reviewed HEAD `573f62a61f00f4eef2c94598e62cc5a1bac09ed0`.

The existing synthetic regression compares cached and fold-local alignment
accuracy/confusion, and the domain tests check separate source alignment. This
static path review is not a newly executed real-data leakage control, a proof
about all preprocessing, or a claim that the shared query sets are independent.

Both flags remain unresolved and retained. Subjects 03 and 14 were already high
in other methods; reusing the same recordings does not provide independent
physiological confirmation. Balanced class counts do not remove Cho's unresolved
class-block chronology, artificial boundary and offline-filter concerns. No
EA-specific shuffled-label result is available, and the neural controls are not
transferred as clearance. The final review must add every later EA and MMIDB flag.
