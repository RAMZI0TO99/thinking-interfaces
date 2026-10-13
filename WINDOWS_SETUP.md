# Windows setup and verified restoration

The current [all52 episode binding](docs/phase2/cho51_episode_binding_qualification_20261013.md)
and [read-only51 interface](docs/phase2/cho51_execution_interfaces_qualification_20261013.md)
packets/candidates are tracked in Git. They preserve52 available subjects and51
evaluation targets. Their exact input hashes apply to the audited current device;
another device needs fresh restored-byte/runtime/source review and admission.
Saved recipes, absolute paths and native receipts are inert. These checks do not
certify authenticated recorder/tensor/numerical sweep execution or scientific
cohort/freeze. The restoration procedure below remains required.

Use **Windows x64**, Git (including Git Credential Manager) and **x64 Python 3.12**.
This repository and its evidence Release are private: sign in to the GitHub
account that can clone it. The same cached Git login downloads the evidence;
no token needs to be put in a file or environment variable.
Use PowerShell from a normal user account.
Choose a short clone path on an NTFS drive with enough disk space; no matching username or drive
letter is required. Setup runs one native thread, hides worker windows, contains
each operation in a Windows Job and records fresh receipts. The current machine
policy requires 10 GiB available RAM at admission, 4 GiB during execution and
20 GiB free disk. Restoring every raw recording and processed cache needs about
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
Read coordination first. This historical source pin is valid only while the canonical
files are unchanged. After intentional implementation edits, calculate the new
source identity and validate that source; never normalize away semantic edits.

The shared Pro2 machine pause path is deliberately not hardcoded into portable
commands. On a machine that still runs that peer, set
`$env:PRO3_PEER_PAUSE_FILE` to its current pause-request file before setup.
Only a genuine current pause/compute lease applies; archived schedules have
expired. On a different machine, establish coordination for that machine.

No credentials, user profiles, virtual environments, raw recordings, processed
signals or original public weights are committed. Do not add `.env` files or
change the global Git configuration. The compact history is dated inert evidence;
secrets and disposable dependency/tool caches are excluded from its export.
