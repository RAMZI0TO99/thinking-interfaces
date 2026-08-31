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
