# Complete-cohort exact-copy review

Date: 2026-08-31. Scope: the unchanged, frozen Profile A benchmark inputs.

The audit examined all 170 public subjects and 20,599 retained trials. It found
**zero byte-exact duplicate groups**, including zero source/query copies across
subjects and zero target support/query copies. The frozen thresholds excluded
the same 22 trials as the original artifact audit; nothing was removed or retuned
because of these checks. This audit counts each processed trial once, not five
times for the five model seeds.

The code reads one subject artifact at a time. It independently applies the
configured amplitude threshold, reconstructs the frozen earliest-balanced
episode, and hashes retained float32 signal values after sorting channels by
name. The signature includes channel names, sample count and sampling rate but
not labels or subject identity, so copying a trial under another label or
subject cannot hide it. Original file indices, session, run and trial metadata
remain available for investigating any detected copy. Both two-digit BCI/Cho
and three-digit MMIDB subject identifiers are verified without renaming them.

Every input file is hashed before and after reading, and the saved snapshot is
checked against the current files before final completion. Missing subjects,
changed artifacts, invalid channel arrays, and support/query copies are tested
failure cases. Source/target checks are dataset-qualified: copying between two
datasets is reported separately because datasets are evaluated separately here.

Evidence: `runs/corpus_duplicate_audit.json`. The artifact snapshot SHA-256 is
`a5b83711ed36a33f541349824face53cb74ec7fa1755d240d5a25e40873b550d`.

## Limits

These are byte-exact checks, not physiological validation or blanket leakage
clearance. They do not detect near-duplicates, shared acquisition artifacts,
unrecorded temporal overlap, class-conditioned loader behavior, or LaBraM
pretraining overlap. The Cho2017 boundary/chronology concern and high-score flags
remain unresolved. See `cho_subject43_review.md`. No scientific gate is signed
by this audit.
