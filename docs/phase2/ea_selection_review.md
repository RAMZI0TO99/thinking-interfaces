# EA-tangent bounded candidate selection

16 September 2026, milestone 25. The bounded selection roster now covers the
classical EA-tangent anchor: `adaptation.ea_selection` fixes a candidate roster
of EA recipe settings, runs every candidate through all eight source-only inner
folds, ranks exact rational subject-averaged balanced accuracy and declares one
winner. This closes the remaining selection gap among the matched anchors; the
TCPL source-fit path remains next.

## Contract and implementation

EA-tangent is classical and stateless across predictions: every audited anchor
call refits per-source Euclidean alignment, OAS covariances, the Riemannian
tangent map and a balanced logistic regression over that fold's permitted
sources plus the held-out subject's selected support. There is no seed, no
optimizer state, no trained artifact to persist, so selection declares winning
settings rather than weights, and no final refit exists to perform.

`BCIEATangentSelector` accepts a fixed tuple of `EATangentCandidate` entries
(name plus `EATangentAnchorSettings`: regularization, C, max iterations, query
batch size). Constructor admission reuses the anchor runner's complete
nine-subject cohort, Profile A manifest and selection-envelope checks. Duplicate
settings are rejected; every fold re-verifies the audited episode envelope, and
artifact bytes are re-hashed before and after tensor binding by the existing
anchor path.

Each fold constructs a fresh inner-validation anchor runner, predicts the held-out
subject's fixed common queries with the candidate's recipe, and scores the exact
rational mean of per-class recalls from a confusion matrix over those queries.
Selection averages the eight folds with equal weight; exact rational ties choose
the first declared candidate. A failed fold returns no winner, and a single
diagnostic fold remains explicitly incomplete.

The engineering ceiling counts classical fits, not gradient steps: one per
anchor call, bounded by `maximum_classical_fits` (1-256) per invocation. There
is no early stopping, no external score import, no partial resume, and no
outer-target prediction; the outer target's artifact is never read during
selection or validation.

## Verification

The focused suite passed **6 tests / 10 subtests**: fold roles and recipe
contents with exact repeat; complete two-candidate selection under an unreadable
outer-target artifact with recomputed means, declared-order tie-breaks and
failure containment; immutable write-once evidence; roster, settings, shots,
ceiling and role rejections before any execution; and source-corruption
fail-closed behavior.

The real-data check declared two candidates before selection: regularization
1e-6, maximum 1,000 iterations, query batches of eight, and C values 1.0 and
2.0. Selection completed **16 inner folds** with 7,924 common-query predictions
while the outer target's Profile A artifact was unreadable, the first fold
repeated exactly, and the winner was declared as settings only. Including the
repeat, work totaled **17 classical source-plus-support fits**, with **zero
outer-target predictions**. Caller source identity and all original input and
audit hashes were preserved.

One process incident is recorded transparently: the first execution of the real
check completed its fits but was correctly rejected by the selector's
source-identity guard because TCPL selection edits were applied to source files
while that run was in flight; it emitted no evidence. The same run's
outer-target-unreadable discriminator also left the subject_01 Profile A
artifact as its placeholder because its restore was not exception-safe. The
source was restored byte-for-byte to this milestone's recorded baseline
(verified against `before.json`), and the artifact was regenerated from the
untouched raw sources through the unchanged Phase I pipeline, verified
byte-identical to the pinned catalog hash before replacement. The check re-ran
against the fixed source with an exception-safe restore. Both invalidated logs
are preserved beside the evidence.

Full lint and strict types pass. The exact-source suite passes **519 tests / 859
subtests**, with the same four existing warnings; raw results are retained in
the receipt. Evidence directory:
`runs/phase2/ea_selection_checks/20260916_step25/`.
Current source fingerprint:
`4770763f81a568a159a9499d637c7f0e54194f478128f7b3ef7c5b0e25dc284d`.
The EA selection module and its tests are new. One pre-existing engineering
file changed with cause: the regression suite outgrew the quality runner's
600-second hung-command timeout (575 s at milestone 24 plus the new tests), so
`scripts/verify_phase1_quality.py` raised it to 1800 seconds without weakening
any check; the timed-out run is preserved. See the deviation log entry of the
same date. Milestone evidence was re-run against the resulting source identity.

## Next work and unchanged limits

Next is the TCPL source-fit selection path over the audited Profile A runner,
completing method coverage of the bounded selection roster. Broader dataset
coverage (Cho2017/MMIDB), the scientific run/history recorder and the measured
P3 pilot remain open. P2 is still partial. The RAM-dependent control refresh
stays deferred; no guard, method configuration, scientific comparison or gate
changed, and no full scientific experiment ran.
