# Windows setup and verified restoration

Updated 31 October 2026, Asia/Riyadh. Read [the current handoff](HANDOFF.md)
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

The [L observer and collection implementation](docs/phase2/cho51_p3_loader_implementation_20261031.md) is source-reviewed; its Q2 accepted 356 methods and scoped native controls. Its reviewed 20,798-file P2 proposal did not become accepted physical preparation: the earlier startup failure and UNPROVEN caller/guard/journal closure remain preserved.

The [startup diagnostic](docs/phase2/cho51_p3_startup_diagnostic_implementation_20261031.md) is implemented and independently accepted. Fresh SQ3 passed 124 methods, eight UTC controls, two native faults, eight syntax checks and eight real controller cases. Separately admitted D2 recorded the counter-constructor start marker but no completion marker before the five-second boundary; final verification and owned cleanup passed. This does not establish the earlier P failure's cause or cleanup.

Next is a reviewed P caller successor using the qualified native memory sensor, followed by applicable fresh Q qualification, refreshed P coverage and separately admitted physical preparation. The finite L plan and full 40-scenario qualification remain incomplete. L collection, the 117 candidate tests and 34 successor controls remain unexecuted; no unchanged P2 retry or automatic P grant follows.

The [accepted v8 inventory](docs/phase2/cho51_p3_inventory_observation_20261029.md)
remains a 742-file current-byte observation with 19 passing tests. The 117
candidate tests and 34 successor controls remain unexecuted. Bootstrap004 stays
consumed, diagnostics005 held, custody UNRESOLVED and006 unadmitted. Scientific
cells remain0/1020. The new scoped policy replacement takes effect only through
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
