# Roster completion: remaining real Cho folds

17 September 2026, milestone 34. The two remaining roster method families ran
real Cho folds on the full fifty-two-subject cohort: LaBraM full tuning (the
last primary-tranche method) and the local TCPL reconstruction (the
separate-architecture member, Profile A only). Every method family in the
adopted roster has now executed bounded real Cho engineering folds with zero
outer-target reads. One TCPL admission fix landed: the selector now accepts
the Cho Profile A convention of catalog-hash identity without sidecar
manifests, refusing a nonempty inventory instead.

## Folds

Both folds used the pilot specification's named subjects (outer target
`subject_01`, inner validation `subject_02`), fifty permitted source subjects
at one step each, and predicted all 159 fixed common queries of the inner
subject:

- **LaBraM full tuning**: the safe pretrained checkpoint with all backbone
  parameters plus head trainable (5,818,138 parameters in the recorded mask),
  fifty source steps, exact trial/state histories.
- **TCPL**: a fresh seeded local reconstruction (64-channel, two-class),
  fifty class-balanced episodic Adam steps over the same permitted sources
  through the audited manifest runner.

Both scored exactly 1/2 — chance under one-step engineering fits, carrying no
performance meaning. Complete selections remain unexecuted under the 256-step
engineering ceiling; they are separately charged scientific work awaiting
admission. The first execution of this check was invalidated by the concurrent
TCPL selector fix changing the source identity mid-milestone; its artifacts
are preserved under `superseded_tcpl_fix/` and the check re-ran against the
fixed source. A full-suite run in that window also crashed with a transient
Windows stack overflow at 23% progress (identical source had passed forty
minutes earlier); the clean re-run below is the evidence of record.

## Verification

Full lint and strict types pass. The exact-source suite passes **553 tests /
914 subtests** (the TCPL admission change is behavior-preserving for the BCI
suites; focused suites re-passed), with the same four existing warnings; raw
results are retained in the receipt. Evidence directory:
`runs/phase2/roster_cho_checks/20260917_step34/`.
Current source fingerprint:
`504724f716024594a4a5ed22a7dcb2d9178e5cb83c530141acbdcac3fe3d9264`.
Changed pre-existing files: `adaptation/tcpl_source.py` (the Cho manifest
policy); no new source files this milestone.

## Next work and unchanged limits

The bounded engineering roster is now fully exercised on real data: nine
method families across BCI (nine-subject) and Cho2017 (fifty-two-subject)
cohorts, all through cohort-generic runners with audited identities,
immutable evidence and zero outer-target predictions. The remaining bounded
dataset gap is MMIDB Profile B (low scientific priority). Everything else is
user-gated: the D01-D06 decisions, operator compute admission, the scientific
freeze and the RAM-deferred control refresh before any commit. P2 remains
partial; no gate or guard changed and no scientific experiment ran.
