# Cho2017 cross-profile episode binding

17 September 2026, milestone 30. The audited Cho2017 Profile A episodes now
bind to the generated Profile B encoder inputs: `load_cho_profile_b_episode`
reconstructs the saved episode from the audited catalog, joins every original
A/B trial by session/run/index with equal labels, and returns owned float32
support/query arrays in the audited order. The primary E2 dataset's pilot cases
are one runner-generalization step away from execution.

## Contract and implementation

`evaluation/phase2_profile_binding.py` gained `CHO_CLASSES`,
`CHO_CHANNELS` (the canonical 64-electrode order), `ChoProfileBinding`,
`ChoProfileEpisode` and `load_cho_profile_b_episode`, mirroring the verified
BCI binding with three deliberate differences. First, Cho Profile A carries no
sidecar manifests: its identity is the audited catalog's artifact hash plus
the frozen threshold profile, both re-verified against the bytes on disk, and
the binding schema records that fact. Second, the guards pin the Cho2017
dataset, its two-class roster, the subject range 01..52 and the declared
artifact directory. Third, the internal artifact reader and manifest checker
are parameterized by montage and classes instead of the BCI constants; the BCI
paths pass their previous values explicitly and their tests pass unmodified.

Everything else follows the BCI contract unchanged: the saved episode envelope
must verify against the reconstructed nested partition; pinned Profile A,
Profile B, manifest, base-config and threshold hashes must match before and
after tensor loading; base Profile A/B preprocessing digests must equal the
supported input contract; the A/B trial-identity-to-label maps must be equal
bijections; and no subset override, scaling, normalization or fit is accepted.

## Verification

The focused suite passed **4 new tests / 7 subtests** (13 tests / 33 subtests
including the unchanged BCI binding regression): all four shot levels binding
support and the fixed query pool with correct shapes, labels, identities and
binding fields; exact repeat binding with unchanged inputs; wrong catalogs,
records and pinned hashes refusing before reading; and label, trial-identity
and manifest tampering refusing at the content layer with refreshed pins.

The real-data check bound the pilot's Cho development target `subject_01` at
all four shot levels from the saved audit records: 200 retained catalog trials,
finite (2*shots, 64, 800) float32 support arrays, and the fixed common query
pool of **160 trials at every shot level** — matching the pilot specification's
declared Cho2017 query count exactly. All 64 canonical channels map one-to-one
into LaBraM's electrode montage (maximum index 87), satisfying the encoder
precondition. Repeats were byte-exact and all input hashes were unchanged.

Full lint and strict types pass. The exact-source suite passes **546 tests /
914 subtests**, with the same four existing warnings; raw results are retained
in the receipt. Evidence directory:
`runs/phase2/cho_binding_checks/20260917_step30/`.
Current source fingerprint:
`a01d74b7c1c55ddb64cd0611b8c07ba8bf7f4e569450b56a4fcb369c0e2d1188`.
`evaluation/phase2_profile_binding.py` changed by the parameterization plus
the Cho section, and the Cho binding test file is new.

## Next work and unchanged limits

Next is generalizing the manifest runners and selector admissions beyond the
fixed nine-subject BCI cohort so the pilot executor can run Cho cases
end-to-end, then the remaining fifty Cho subjects once disk is freed. The
D01-D06 decisions, operator compute admission, the scientific freeze and the
RAM-deferred control refresh remain user-gated. P2 remains partial; no gate or
guard changed and no scientific experiment ran.
