# Scientific run recorder: case manifests, claims and evaluation cells

17 September 2026, milestone 27. `evaluation.phase2_runner` provides the run/
history recording foundation the P3 pilot requires: deterministic pilot case
manifests, atomic case claims with a single linked retry, immutable failure
records, and no-clobber publication of signed `evaluation_cell` records with
exact-rational metric verification. The module executes no method, reads no
target signals and publishes no cell without a cited selection evidence digest.

## Contract and implementation

`environment_digest()` pins the local execution environment (interpreter, torch,
numpy, braindecode/scikit-learn/safetensors versions, device, threads,
determinism flag) as a digest. `method_configuration()` digests an explicit
method configuration and refuses any missing optimizer, steps, fit-scope or
preprocessing field — existing smoke settings are never implicit defaults, and
classical methods must declare their null values explicitly.

`CasePlan` fixes one planned pilot target case (dataset, target, method, shots,
model seed, repetition). Repetitions share the cell identity key but not claim
attempts. `pilot_case_plans()` enumerates the matrix deterministically in
dataset/method/shots/repetition order and rejects duplicate or empty rosters.

`CaseRecorder` owns the lifecycle under an admitted output root inside
`runs/phase2`:

- **Claims** are deterministic engineering envelopes; replaying identical bytes
  is a no-op, while a different worker or content conflicts atomically. A retry
  is admitted only after a recorded failure of the prior attempt, and at most
  one retry exists per case.
- **Failures** require an explicit error description and are immutable.
- **Cells** are `evaluation_cell` envelopes named by their `CellIdentity`
  digest. Metrics must declare `role = outer_target`, cite a 64-hex
  `selection_evidence_sha256` (the matched selection result the pilot spec
  demands), and carry a confusion matrix whose exact rational mean class recall
  equals the declared balanced accuracy with a matching positive query count.
  Losses and stage timings, when present, must be finite. Publishing a cell for
  an inner-validation role or with inconsistent metrics is refused.
- `measured_identities()` re-verifies every published cell's envelope on read,
  and `completion()` derives measured/claimed/failed/pending accounting purely
  from immutable records on disk.

## Verification

The focused suite passed **8 tests / 26 subtests**: environment and method-
configuration digest behavior; deterministic case ordering with unique ids and
shared identity keys across repetitions; the atomic claim lifecycle including
byte-identical replay, duplicate-worker conflict, unlinked-retry refusal and the
single linked retry; failure-description requirements; cell metric invariants
(wrong rationals, ragged/negative/empty confusion rows, mismatched counts,
inner roles, missing or short digests, nonfinite losses); byte tampering of a
published cell being caught on re-verification; completion accounting across
measured/claimed/failed/pending states; and output-root containment.

The real-identity check enumerated the pilot specification's matrix from the
saved audits and roster: nine adopted methods across the three datasets at one
and twenty shots plus the five Cho five-shot tranche methods, three repetitions,
model seed 23 — **177 deterministic cases**. Grounded directory checks show 54
measurable BCI main-matrix cases and 123 blocked Cho/MMIDB cases (no Profile B
inputs yet); the blocked reasons are recorded per dataset with target and
audited-episode counts. The claim lifecycle was exercised end-to-end on one
measurable case (claim, replay no-op, duplicate-worker conflict, unlinked-retry
refusal, linked retry, second-retry refusal), and completion accounting derived
**0 measured / 1 failed / 176 pending** from the immutable records. Zero
scientific cells were published and zero outer-target predictions were made.

Full lint and strict types pass. The exact-source suite passes **535 tests / 899
subtests**, with the same four existing warnings; raw results are retained in
the receipt. Evidence directory:
`runs/phase2/recorder_checks/20260917_step27/`.
Current source fingerprint:
`e85c32ae66ff358e1cb97ba255cf2431fe398d41f9d3e3863e4b72a1129068a9`.
The runner module and its tests are new; no pre-existing source/config/test
file changed this milestone.

## Next work and unchanged limits

The pilot executor (`scripts/phase2_pilot.py`), its measured stages and compute
admission remain unimplemented and unfrozen; this recorder is their
prerequisite, not their authorization. Cho2017/MMIDB Profile B preparation is
still required before those cases become measurable (disk headroom is currently
too tight to generate it). The scientific freeze, D01-D06 register decisions,
RAM-deferred control refresh and Gate A signing remain open. P2 is still
partial; no gate or guard changed and no scientific experiment ran.
