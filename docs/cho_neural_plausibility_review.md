# Cho neural-grid plausibility review — preliminary, not clearance

Reviewed on 2026-08-31 while the classical/MMIDB grid was still incomplete.
This is not the final `runs/plausibility_review.json` and cannot satisfy the
complete-grid review requirement. The reviewed evidence packet contains 1,355
records, including all 1,040 Cho neural records and 315 four-class BCI records.

Record snapshot: `d94e5e286688a471ac01b54b76b02f61ac8e667157222d047cb46e9109335f3b`.
Benchmark configuration: `434fc4d25a5071a094268ab410c47f79bd92823aacd8e9d06e9f684609aab258`.
Audited input snapshot: `a5b83711ed36a33f541349824face53cb74ec7fa1755d240d5a25e40873b550d`.

## Cases inspected

All five seed results and both class recalls were inspected for each of the
53 subject/method cases triggered by any seed exceeding 78% balanced accuracy.
These are 265 evaluations of repeatedly reused query trials, not 265 independent
subjects or trial sets. No method-level mean exceeded that trigger in this packet.

| Method | Cases | Subject numbers |
|---|---:|---|
| Deep | 10 | 03, 04, 09, 14, 22, 25, 36, 41, 43, 48 |
| EA + EEGNet | 17 | 03, 04, 10, 11, 12, 14, 15, 18, 21, 22, 23, 25, 41, 43, 44, 46, 48 |
| EEGNet | 13 | 03, 04, 09, 10, 14, 15, 22, 23, 24, 25, 41, 43, 48 |
| Shallow | 13 | 03, 04, 05, 10, 14, 23, 26, 31, 36, 41, 43, 44, 48 |

The independently audited packet found no record/input count mismatches.
Most listed queries have 190 trials, 95 per class. Subject 15 has 189 after a
frozen rejection; subjects 09 and 46 have 230, 115 per class. These differences
are retained rather than equalized after observing results.

## Interpretation and disposition

- Subject 43 is consistently extreme across all four neural methods: approximately
  97.37–99.47% across these 20 runs, with high recall for both hands. This is not
  an ordinary majority-class accuracy artifact. The six separate shuffled-label
  controls for EEGNet/Shallow are at chance, and no exact signal copies were found.
  Those controls do not validate Deep/EA models independently or remove the known
  acquisition-order and offline-filter boundary concerns.
- Subjects 03, 04, 14, 41 and 48 also trigger across all four methods. Cross-model
  agreement is not independent confirmation of motor-imagery physiology because
  every model uses the same recordings and preprocessing. In particular, subject
  41's EA + EEGNet results are 96.84–98.95% and remain an unresolved high-score case.
- Several triggers occur only in a minority of seeds. Deep subject 48, for example,
  ranges from 61.58% to 83.68%, with strongly uneven class recall in weaker runs.
  No best-seed score is substituted for the predeclared seed average, and a weaker
  mean is not used to dismiss the original high-seed flag.
- Balanced accuracy averages the two recalls. The high triggered runs therefore
  cannot be explained solely by predicting the majority class. This arithmetic
  observation is not proof that labels, chronology or preprocessing are leakage-free.

All 53 cases stay in the frozen exploratory table with unresolved scientific
dispositions. No subject is removed, threshold changed, seed selected, or H2
planning variance recomputed after this review. The complete-cohort exact-copy
audit and `docs/cho_subject43_review.md` provide the existing input/control checks
and their limitations. Classical Cho and all MMIDB results must still be reviewed
when complete. The separate two-class BCI support-fine-tuning baseline is outside
this packet, and four-class BCI is not judged using this two-class 78% trigger.
