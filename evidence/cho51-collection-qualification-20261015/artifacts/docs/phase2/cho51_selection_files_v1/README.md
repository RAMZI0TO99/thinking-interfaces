# Adopted 51-target selection-file verifier, version 1

Prepared 15 October 2026. **Source preparation only; no passing behavioral or
native receipt exists for these files.** No project tests or numerical code were
imported or executed while preparing this successor.

`selection_files.py` provides `verify_cho51_recorded_selection_files`. It accepts
an actual adopted `Cho51WorkerRoute`, an existing typed recorder, exactly 1,020
independent case pins, independent source and unchanged four-method digests,
the direct absolute project root, and the independent
`selection_ceiling_config_sha256`. The public entrypoint rederives the adopted
scope and every case identity before reading selection bytes. Subjects 02–52
are targets; all 52 available catalogs/assets and subject 01 as source remain.
Incomplete, duplicate, excluded, legacy-52-target or altered-scope pins fail.

The policy loader requires a direct, bounded, singly linked file at
`configs/phase2/selection_ceiling.toml`, externally pinned raw SHA-256 bytes,
and exactly one TOML key, integer `maximum_gradient_steps = 5253`. It refuses
booleans, floating values, zero, a changed ceiling, additional keys and missing,
oversized or aliased files. Each selection contract must retain an integer
gradient ceiling between 1 and 5,253; passing this static bound does not prove
the complete fold ledger or actual gradient-step count. The ceiling's bytes
and filesystem identity are rechecked across selection verification and in
the returned witness's `verify_stable()` method.

The old `evaluation/phase2_cho_selection_file_bridge.py` remains untouched.
Its 256 guard is preserved. This successor copies only `_static_contract`,
`_case_claims` and their byte loop because the legacy claim helper closes over
its fixed static checker. The new checker explicitly receives the pinned
ceiling. No legacy module globals/functions are patched, no contract is
rewritten to 256, and candidate templates/digests are independently derived.
Unchanged canonical-file, relative-path, logical-envelope, selected-store
factored read, claim dataclass and physical witness helpers are reused.

`Cho51SelectionFileWitness` exposes `claims`, `physical`, `ceiling` and
`owner_decision_sha256`; `verify_stable()` checks both policy and selection
physical files. `scientific_result_admitted` is always false. The API reads
small persisted selection/cell records and policy/owner/route metadata only.
It does not reconstruct real inputs, read arrays/weights, extract scores,
create a recorder, fit a model, run a worker or start an original attempt.

`test_selection_files.py` prepares 43 synthetic cases: policy/alias/reread tests, per-method
canonical and factored binding checks, repinned invalid gradient/candidate/path
claims, unchanged contracts across the old 256 boundary, changed physical evidence,
complete 1,020-cell synthetic collection,
and bad scope/source/method/roster rejection before selection reads. The fixture
constructs fabricated all-52 metadata and cells while using the existing exact
adoption evidence and candidate-template bytes as independent inputs. It writes
no weights or arrays. Empty synthetic folds on canonical fixtures deliberately
show that static file claims are not complete selection-evidence admission.
The factored fixture supplies fabricated complete structural folds solely for
the codec; they are not executed folds or scientific evidence.

Root must independently review these sources and obtain fresh finite native
admission before executing tests: current coordination/pause monitoring, fresh
source/runtime pins and attempt directory, one native thread/hidden GPUs,
RAM 10/4 GiB and disk 20 GiB floors, and explicit wall/process/Job caps. No old
lease, launcher, passing receipt, watcher or expired scheduling window admits
execution. Real recorder/selection composition, complete public selector-evidence
verification, selected publication and supervised tensor witnesses remain
separate gates. Checkpoint-cohort review, full worker resource qualification,
final owner freeze and scientific budget remain pending; original retries stay
zero. This directory grants no scientific execution or publication authority.
