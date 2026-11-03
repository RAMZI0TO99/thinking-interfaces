# Windows setup and verified restoration

Updated 2 November 2026, Asia/Riyadh. Read [the current handoff](HANDOFF.md)
and [project execution policy](docs/PROJECT_EXECUTION_POLICY.md) before setup.
Root owns this project's admission and scheduling. No outside chat response,
shared lease or external pause-file setup is required by the active workflow.

The commands below describe the verified migration tooling; this documentation
update does not run them or qualify another runtime. Check the actual tool
contract and current local resource envelope before execution. If a frozen
launcher requires a retired scheduling contract, use a reviewed successor;
do not manufacture historical decisions or edit accepted receipts.

The [local validation contract](docs/phase2/cho51_p3_local_validation_contract_20261029.md)
has independent design acceptance. It binds 117 candidate cases, 34 successor
controls and 26 qualification scenarios to separate qualification, preparation,
loader/collection, validation and closeout stages. The two retired shared-window
controls are explicitly replaced by local-window controls.

The [P2 dependency map and file-only caller](docs/phase2/cho51_p3_dependency_preparation_20261029.md) have accepted Q10 qualification (198 methods, eight UTC controls, two native fault controls and three sharing checks) and accepted P10 physical preparation: 20,406 files, 888 native images and 4,843 dependency edges. The 105.32-second run completed full final input verification and owned cleanup. Earlier failures and unknown cleanup remain frozen; physical preparation does not qualify loader/ABI behavior.

The [native-memory bootstrap and refreshed preparation](docs/phase2/cho51_p3_native_memory_bootstrap_20261031.md) are implemented and source-reviewed. Fresh native-bootstrap Q2 accepted 368 methods and all required controls, including two actual P-bootstrap cases. Separately admitted P2 returned successfully in 116.96 seconds, reporting 21,115 files, 893 native images and 4,847 dependency edges, full final verification and owned cleanup. P physical preparation is independently accepted for this operation.

The [CM3 supplied-event parser and evidence join](docs/phase2/cho51_p3_cm3_implementation_20261102.md) are independently accepted for source only with no findings. The eight-file package checks exact CM2 event bytes, canonical supplied tables and full raw collection/event/table joins. Current source is 796 identities/34 modules with 280 proposed selections; 32 new methods remain unexecuted. The historical parser target stays 764/248. Twenty-three design scenarios have source examples and nine real-boundary/capture obligations remain unimplemented; none is qualified. No execution or admission occurred; dispatch remains refused and P stays disabled.

The [CM3 design](docs/phase2/cho51_p3_cm3_evidence_design_20261102.md), [CM2 implementation](docs/phase2/cho51_p3_cm2_implementation_20261102.md), CM1 and HB1 remain frozen. Full historical CM2 collection precedes distinct 732/30 and 700/28 projections; current-roster collection/event production is not implemented. Future normal mapping is conditionally 1,096 records / 561,152 bytes; the earlier 1,000- and 860-record bounds retain their original scopes. Raw bytes cannot prove hidden cleanup/suite closure/final refusal, actual trace/subcase completeness or native custody. Next is source-only design/review of explicit lifecycle/final-refusal evidence and current-roster collection/event integration. Actual runtime remains held pending all original failure/capture/native/allocation/lifecycle and timing/memory gates.

The [bounded resolver](docs/phase2/cho51_p3_bounded_resolver_20261031.md) and [supplied-data codec](docs/phase2/cho51_p3_lossless_codec_implementation_20261101.md) retain their accepted scoped evidence. The [fixed probe](docs/phase2/cho51_p3_probe_implementation_20261101.md) remains source-reviewed but fresh Q is NOT ACCEPTED: six consumed attempts, latest32 method and three sharing passes followed by a later control deadline and incomplete final verification. Latest owned cleanup is established;8bf386d1 final caller,6f9c898c final caller/outer/bootstrap and131bc595 outer/bootstrap custody remain UNKNOWN. Historical [QD a1f12701](docs/phase2/cho51_p3_qd_execution_20261102.md) retains59/42 timing records,37.7609334s prefix,45.4523028s external return, final verification and owned closure, but overall INCOMPLETE_REFUSED for17/16 closeout accounting. No repair, retry or second QD is inferred. [SC1](docs/phase2/cho51_p3_sc1_implementation_20261102.md) and the [HB1 design](docs/phase2/cho51_p3_host_binding_design_20261102.md) remain frozen source/design predecessors;54 SC1 and10 QD methods,24 HB/40 SC/36 diagnostic scenarios remain unqualified. Complete-Q timing/output feasibility is NOT_ESTABLISHED.

Full Q probe32/100/384 and every control remain held; all guards remain. No original-package-path custody, continuation or debt discharge is established. All18,793 resolver rows,13,406 inventory occurrences,724 queues,1,782 frontiers,1,786 binding loads and3,972 effects remain open. Complete continuation is INFEASIBLE_UNDER_CURRENT_GUARDS: at least31,002 rows against24,000; conditional node/raw-byte findings retain scope. G2 is INCOMPLETE_REFUSED; candidate117/V34 and science remain unexecuted. Old failures stay consumed; documentation does not refresh P custody or census.

The [accepted v8 inventory](docs/phase2/cho51_p3_inventory_observation_20261029.md)
remains a 742-file current-byte observation with 19 passing tests. The 117
candidate tests and 34 successor controls remain unexecuted. Bootstrap004 stays
consumed, diagnostics005 held, custody UNRESOLVED and006 unadmitted. Scientific
cells remain 0/1020. The new scoped policy replacement takes effect only through
implementation-specific adoption; the full-restart claim remains unchanged.

The latest observation used a freshly pinned retained Python3.12.14 base with
732 declared files. The old `.venv` points to an unavailable earlier base.
Recheck your actual runtime; setup on another device does not inherit these
observations. See the [inventory record](docs/phase2/cho51_p3_inventory_observation_20261029.md).

## Restore a Windows environment

Use **Windows x64**, Git (including Git Credential Manager) and **x64 Python 3.12**.
This repository and its evidence Release are private: sign in to the GitHub
account that can clone it. The same cached Git login downloads the evidence;
no token needs to be put in a file or environment variable.
Use PowerShell from a normal user account.
Choose a short clone path on an NTFS drive with enough disk space; no matching username or drive
letter is required. Setup runs one native thread, hides worker windows, contains
each operation in a Windows Job and records fresh receipts. The migration tooling's default
limits require 10 GiB available RAM at admission, 4 GiB during execution and
20 GiB free disk. A phase-specific contracts allowance does not silently alter
this separate setup envelope. Restoring every raw recording and processed cache needs about
20 GiB of data space in addition to the environment, history and disk floor.

```powershell
git clone https://github.com/RAMZI0TO99/thinking-interfaces.git
Set-Location thinking-interfaces
powershell -NoProfile -ExecutionPolicy Bypass -File tools/migration/bootstrap.ps1 -DownloadWeights
```

If Python 3.12 is not registered with the Windows launcher, append
`-Python 'C:\path\to\python.exe'`. Bootstrap installs the pinned full environment,
installs the project, checks dependency consistency, normalizes only independently
verified source line endings, and restores historical evidence. It refuses to
overwrite changed source, data or historical files. `-CoreOnly` installs the
core analysis/development dependencies; use the default for EEG/LaBraM work.
`-RestoreData` also downloads all recordings and rebuilds all caches. Add it
to the first bootstrap command for complete data restoration. The hash-locked
full environment contains 123 exact wheels; the core profile contains 26.
The original root lockfiles keep their historical bytes.
`-SkipInstall` restores history on an already configured clone. `-SkipHistory`
is useful for source-only inspection. `-DownloadWeights` fetches the pinned
original and converted public checkpoints without deserializing them.

Setup operations are finite (at most ten minutes each). Each of the 58 history
parts has its own bounded download/verification Job, followed by a separate
local restoration Job. Completed matching parts are reused automatically.
A slow network can hit a deadline;
the failure is recorded and the owned process tree is stopped. Rerun bootstrap
to create a fresh setup attempt; pip preserves completed installations. No setup
retry changes the separate original model-case attempt ledger.

For interactive work after bootstrap:

```powershell
. ./tools/migration/activate.ps1
python -I -B tools/migration/doctor.py
```

Activation routes Hugging Face into this clone and enables offline model loading.
The weights command pins the cache's `main` reference to revision
`0563b6c626e7b40d9a36653b763715db94d945d7`. The original LaBraM checkpoint is
bound to official commit `c431221e6cfd23dbfa9950e0180682fb322b0548`.
Do not update these model identities to a moving branch to make a check pass.

Restore public data and rebuild caches, with downloads checked before processing:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/migration/rebuild.ps1 -Dataset all
```

For a smaller first step, use `-Dataset mmidb -Subjects 1` (or `cho2017` or
`bci_iv_2a`). `-Profile profile_a` selects one cache family. Each subject/profile
uses a new bounded Job. Existing matching caches are verified and skipped;
conflicting caches are preserved. Rebuilds happen in a private staging tree,
then matching NPZ arrays are published without overwriting existing files.
Historical sidecars retain their original bytes; new build receipts live under
`runs/migration/`. This command preprocesses data and does not fit a model.

The raw-asset manifest covers 397 recordings: 327 MMIDB EDFs, 18 BCI IV 2a MATs
and 52 Cho2017 MATs. The cache manifest covers 410 NPZs across nine dataset/profile
families. Whole ZIP hashes may vary with timestamps/compression, so cache checks
compare the member names, sizes and SHA256 of every uncompressed `.npy` member.
These file checks establish content identity, not scientific independence.

Verify complete local restoration when all downloads/rebuilds are present:

```powershell
python -I -B tools/migration/doctor.py --verify-history --verify-assets --verify-caches
```

Full implementation validation on the new device is a separate fresh operation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/migration/quality.ps1
```

This creates an unused attempt directory and a separate bounded Job (70 minutes,
6 GiB per process/7.5 GiB aggregate, 10/4 GiB RAM and 20 GiB disk floors).
Read the current project execution policy and establish local admission first.
This historical source pin is valid only while the canonical files are unchanged. After intentional implementation edits, calculate the new
source identity and validate that source; never normalize away semantic edits.

No credentials, user profiles, virtual environments, raw recordings, processed
signals or original public weights are committed. Do not add `.env` files or
change the global Git configuration. The compact history is dated inert evidence;
secrets and disposable dependency/tool caches are excluded from its export.

The previous full setup/status document is preserved in
[the documentation archive](docs/history/project_focus_20261028/README.md).
Historical scheduling instructions do not override the current project policy.
