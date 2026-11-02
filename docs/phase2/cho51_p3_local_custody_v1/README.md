# P3 local custody contracts v1

Engineering-only design sources, 28 October 2026. See the
[design](../cho51_p3_local_custody_design_20261028.md) and
[current execution policy](../../PROJECT_EXECUTION_POLICY.md).

- `boundary-evidence.schema.json`: bounded packet references and source/runtime
  identity for a future locally admitted boundary observation.
- `disposition.schema.json`: historical failure retained separately from an
  independently reviewed current execution-domain decision.
- `local-admission.schema.json`: a separate one-operation Root admission for
  a new successor, conditional on actual qualified boundary evidence.
- `acceptance-cases.json`: required implementation scenarios; none has executed.

JSON Schema draft2020-12 is a structural contract. Semantic cross-file hashes,
source authorship, temporal ordering, authoritative provider coverage, actual
tool provenance, process ownership and once-only admission require the reviewed
implementation and independent actual-evidence review. Schemas cannot supply
those proofs. No executable launcher, collector or validator is included here.

No operational example with `accepted=true` or invented actual boot/host data is
created. Source review of these files does not activate diagnostics005, release
bootstrap004, or execute the117 pending candidate tests and34 controls.
