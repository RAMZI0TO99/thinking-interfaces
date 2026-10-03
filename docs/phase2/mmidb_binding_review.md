# MMIDB cross-profile binding

19 September 2026, milestone 36. The third dataset's audited episodes now
bind to its Profile B encoder inputs: `load_mmidb_profile_b_episode` mirrors
the Cho contract with MMIDB's own montage (T9/T10), catalog-hash identity, the
recorded upsample-before-filter policy in the binding schema, and hard refusal
of the two audited-ineligible subjects. One testability fix landed in the
pilot executor: the host-RAM guard read is now injectable like disk and GPU so
live memory pressure cannot flip the fail-closed logic during test suites —
real admission checks still read live values.

## Contract and implementation

`evaluation/phase2_profile_binding.py` gained `MMIDB_CLASSES`,
`MMIDB_CHANNELS` (the canonical sixty-four-electrode order with T9/T10),
`MMIDBProfileAssets` (two pinned digests; no Profile A sidecars), the
`MMIDBProfileBinding`/`MMIDBProfileEpisode` records and
`load_mmidb_profile_b_episode`. The dataset tables now include mmidb, so the
cohort-generic runners admit the full roster on any declared dataset. The
binding enforces everything the Cho contract does — episode-envelope
verification, pinned hashes before and after loading, preprocessing digests,
A/B identity bijections with equal labels — plus the MMIDB-specific rules:
subjects 079 and 100 (no audited episodes) refuse construction outright, and
the binding schema records both the sidecar-free identity convention and the
Profile B resample policy.

`evaluation/phase2_pilot.py`'s `machine_snapshot`/`compute_admission` gained
an optional `free_host_ram_gib` injection parameter mirroring the existing
disk and GPU injections. The change is a testability gap fix only: a full
suite had flipped ten pilot-executor tests to failure because hours of heavy
runs pushed live free RAM below the 4 GiB floor mid-suite. The tests now
inject a comfortable value; every real admission check (the milestone-28
readiness check and any future pilot call) still reads live machine state.

## Verification

The focused suite passed **5 new tests / 7 subtests** (11 tests / 15 subtests
with the Cho and BCI binding regressions): all four shot levels binding
support and the fixed query pool with correct shapes and schema fields; exact
repeat binding with unchanged inputs; wrong pins and records refusing before
reading; label and manifest tampering refusing at the content layer; and the
ineligible subjects refusing construction.

The real-data check bound the pilot's MMIDB development target `subject_001`
and inner fold `subject_002` at all four shot levels from the saved audit
records: 45 retained trials each, finite (2*shots, 64, 800) float32 support
arrays, fixed common query pools (5 queries each — the documented small MMIDB
pools), byte-exact repeats, all input hashes unchanged, and both ineligible
subjects refusing. All 64 MMIDB channels map one-to-one into LaBraM's
electrode montage (maximum index 87).

Full lint and strict types pass. The exact-source suite passes **558 tests /
921 subtests**, with the same four existing warnings; raw results are retained
in the receipt. Evidence directory:
`runs/phase2/mmidb_binding_checks/20260919_step36/`.
Current source fingerprint:
`74feed107b258b533b5fce964d1562462fc4aa26172a3d144b77ab3ec3c80ae9`.
Changed pre-existing files: `evaluation/phase2_profile_binding.py`,
`evaluation/phase2_pilot.py`, `tests/test_phase2_pilot.py` (the RAM
injection); new: `tests/test_mmidb_binding.py`.

## Next work and unchanged limits

Every dataset now has generation, audit and binding end to end; the bounded
engineering surface is complete in full. The measured pilot is entirely
user-gated: the D01-D06 decisions, operator compute admission, the scientific
freeze and the RAM-deferred control refresh before any commit. P2 remains
partial; no gate or guard changed and no scientific experiment ran.
