# Local contract and commit checks

The local contract v1 receipt is `configs/contract_freeze.toml`, recorded on
2026-08-31 at 03:45:40 UTC. It hashes UTF-8 text with CRLF normalized to LF,
so Windows line endings do not create false changes. The checked files define
Epoch, Split, Episode, Decoder, Stream and RunRecord. Any future interface change
needs an explicit versioned amendment and deviation-log entry, not a silent hash
replacement. Earlier runs retain their original provenance.

This repository uses `.githooks` through its local `core.hooksPath` setting.
The pre-commit and pre-merge-commit hooks invoke the local environment, reject
unstaged/untracked source changes, run lint, type checking and tests, then verify
the three Phase I leakage controls. The source fingerprint includes hook files.
No external job, upload, model training or global Git setting is involved.

The negative controls are checked from their historical run records and frozen
control settings. They are not rerun on every commit. Their narrow scope and
remaining acquisition/filtering limitations remain explicit in the scientific
review. A boolean summary without supporting records fails.

Local hooks can be bypassed, and Git does not call pre-merge-commit for a
fast-forward update. Therefore these checks are local guardrails, not proof of
required remote CI. Remote branch protection and the team merge rehearsal remain
external closure items. On another checkout, the hook setting must be installed
explicitly; it is not automatically transferred by Git.

## Targeted control configuration

The separate high-score controls now take only a configuration-file selector:

```powershell
.\.venv\Scripts\python.exe scripts/audit_subject_falsification.py --config configs/subject_control_cho43.toml
.\.venv\Scripts\python.exe scripts/audit_subject_falsification.py --config configs/subject_control_mmidb85.toml
```

Dataset, subject, methods and seeds are declared in those files; training and
episode settings remain in the frozen benchmark configuration. Unknown fields,
noncanonical subjects, duplicate methods/seeds and invalid seed types are rejected.
The default Cho configuration keeps the existing compute queue compatible.

Existing controls retain their historical bytes and provenance. Resume checks
also verify the method and shuffle seed inside each record, not just its filename.
A changed existing signal audit is rejected and preserved, not overwritten.
New control records include the selected control configuration, its hash and
source provenance; these fields are not retroactively inserted into old records.
These targeted controls remain separate from the three historical merge checks.
