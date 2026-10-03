# MMIDB Profile B preparation

17 September 2026, milestone 35. The third and final audited dataset now has
encoder-ready Profile B inputs: all 109 MMIDB subjects were generated from the
pinned local PhysioNet EDF runs (892 MB; 21 GiB remained free) and audited
against the untouched Profile A artifacts. Two engineering findings are
recorded: the mixed native sampling rates required a documented
upsample-before-filter policy, and the A/B join-key conventions required the
Profile A session/run naming. Cross-profile binding remains future work; the
small MMIDB query pools limit its scientific priority.

## Generation and policy

`data/profile_b.py` gained `preprocess_profile_b_mmidb_subject`: the three
left/right-fist motor runs load from the local EEGBCI cache, cues that cannot
supply a complete post-cue epoch are dropped (the Profile A completeness rule
with a zero baseline), T1/T2 annotations are renamed to the canonical
`left_fist`/`right_fist` classes, channel names are canonicalized (the MMIDB
montage uses T9/T10 where Cho uses P9/P10), sessions and runs adopt Profile
A's exact conventions (`"0"` and the EDF run numbers) so the A/B join by
session/run/index is exact, and every run is upsampled to the 200 Hz target
rate BEFORE filtering.

The upsampling policy exists because subjects 88 onward are native 128 Hz —
below the Profile B bandpass Nyquist of 75 Hz — so the filter-first order of
the BCI/Cho pipelines cannot run. Upsampling adds no information above the
native Nyquist; the order difference from the other datasets is the recorded
MMIDB policy, and the first generation attempt's failure on subject 88 is
preserved in the generation logs. Two intermediate generation bugs (a
run-grouping collapse that silently kept only the last run per subject, and
mismatched session/run naming) were found by the audit's join-key checks and
fixed before the final regeneration; nothing was finalized on the buggy
bytes.

## Audit

The preparation audit verified for all 109 subjects against the saved mmidb
audit records and untouched Profile A artifacts: exact per-trial label,
session, run and index correspondence with Profile A; identical canonical
64-channel montages; finite float32 signals shaped (trials, 64, 800) at
200 Hz with four 200-sample patches; manifests matching the actual shapes;
and Profile A artifact hashes unchanged from the pinned catalogs. Subjects
079 and 100 — the two audited-ineligible subjects with no episode records —
are recorded as such: their generated artifacts remain usable as source
subjects under the declared cohort policy. The cohort totals 4,917 trials in
four distinct counts (36/42/45/57), with a fixed-pool query ceiling of 556
across eligible subjects.

## Verification

Full lint and strict types pass. The exact-source suite passes **553 tests /
914 subtests** (the focused Profile B suite re-passed), with the same four
existing warnings; raw results are retained in the receipt. Evidence
directory: `runs/phase2/mmidb_cohort_checks/20260917_step35/`.
Current source fingerprint:
`704d838597fdb01842ea9fdcf3be7aae709216155dad8be3cd57bdcd06bfdbb4`.
`data/profile_b.py` changed by the new MMIDB function and
`scripts/preprocess_profile_b_mmidb.py` is new; no test changes were needed.

## Next work and unchanged limits

All three audited datasets now have complete, audited Profile B cohorts. The
MMIDB cross-profile binding (adding its montage tables and loader) is the
remaining bounded engineering step if MMIDB cases are ever wanted; the tiny
query pools (median five queries) keep it low priority. The measured pilot
waits on the user-gated D01-D06 decisions, operator compute admission, the
scientific freeze and the RAM-deferred control refresh. P2 remains partial;
no gate or guard changed and no scientific experiment ran.
