# Native final-case contract repair

V10 completed and published the accepted first engineering case, then its
native launcher rejected the child's recorder completion at a final check:
the launcher expected `measured_cases`; the recorder emits `measured`.
The original package, failed native receipt and accepted recorder evidence
remain historical evidence and must not be overwritten or rerun.

`Build-V11.ps1` reconstructs a fresh **historical baseline repair template**
from six exact hash-pinned V10 files. It changes only the completion field,
two stale memory-cap descriptions, and four deadline sites. Every replacement
must occur once; reversing the replacements must reproduce the original
bytes. The build preserves line endings, BOM state and all untouched bytes.
An existing output directory is an error, including after a partial build.
The script never deletes previous output or creates an execution release.

From the project root, run the native PowerShell checks:

```powershell
& ./docs/phase2/native_launcher_contract/Build-V11.ps1
& ./docs/phase2/native_launcher_contract/Test-FinalCaseContract.ps1
```

Both scripts accept `-ProjectRoot`. The builder accepts `-OutputDirectory`
for a fresh directory beneath `runs/coordination`; the validator accepts
`-PackageDirectory` and a fresh `-ReceiptPath` within that package.
Historical V10 artifacts and the accepted c003 child-result fixture are
local ignored evidence required to reproduce these checks. The tracked
scripts do not embed runtime inventories, raw data, weights or credentials.

The validator parses both complete launchers but executes only their actual
AST-extracted final rejection conditions. It reproduces V10's rejection of
the saved c003 child result, accepts that result with V11's condition, and
rejects synthetic missing/malformed completion and incorrect case identities.
It does not invoke either complete launcher, Python, Torch, a Job, training
or recorder publication. Its fresh receipt certifies only this predicate
regression, not runtime supervision, whole-launcher acceptance or a new case.

The template retains source fingerprint `62536382...` and the historical
runtime record deliberately as baseline evidence; neither certifies the live
source or environment. The deadline `2026-10-05T10:00:00Z` describes a bounded
repair-staging phase, not a compute lease, owner expiry or reusable execution
window. Expired historical releases must not be copied into the successor.
Future execution requires a settled live source, current quality/environment
evidence, a new audited prerequisite board, fresh coordination, a fresh scoped
release and fresh attempt paths. The fixed first-case wrapper still refuses
prior canonical case state and is not a next-case runner. Scientific Gate A
and the experiment freeze remain unsigned.

The 5 October staging directory preserves its initial generated draft under
`pre_format_draft001/`: the corrected cap descriptions initially exceeded
the project's 100-character line convention. Shorter equivalent descriptions
were rebuilt into fresh `settled_reproduction/`; its six artifacts and build
provenance are byte-identical to the settled files at the package root.
`draft_preservation_001.json` records that staging correction. Neither copy
has an execution release.

This tracked repair recipe sits under documentation because it reproduces
ignored historical operational evidence rather than changing the numerical
implementation. Operational hashes remain explicit in its build provenance.
The project source fingerprint enumerator currently excludes `docs/`; the
template must never be described as certification of unrelated source edits.
