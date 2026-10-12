# Windows continuation qualification, 12 October 2026

The source and migration tools are pushed to the private
[Thinking Interfaces repository](https://github.com/RAMZI0TO99/thinking-interfaces).
The full environment, historical restoration and all nine cache reconstruction
paths passed in a fresh Windows checkout. All 58 private Release assets matched
GitHub's server SHA256 values. A separate HTTPS clone downloaded every part from
the published Release and restored all 28,679 historical files with matching
per-file hashes. Start another device with [WINDOWS_SETUP.md](../../WINDOWS_SETUP.md).

| Check | Executed result |
| --- | --- |
| Fresh Windows checkout, including a folder with spaces | Exact canonical bytes restored; Git working tree clean |
| Python 3.12.14 x64 full environment | 123 exact hash-locked wheels installed; editable project installed |
| Dependency consistency and imports | `pip check` passed; all core and EEG libraries imported |
| Migration boundary tests | 22 passed in 20.546 seconds; Ruff and formatting checks passed |
| Public checkpoint downloads | Original PTH, converted safetensors and configuration matched pinned hashes; no model deserialization |
| Local archive restoration | All 28,679 historical files independently checked; long Windows paths restored |
| Data reconstruction smoke checks | Subject 1 in all nine cache families matched every NumPy member and the original whole-NPZ SHA256 |
| Public raw download checks | Both BCI subject-1 MATs, Cho subject-1 MAT and three MMIDB subject-1 EDFs matched pinned hashes |
| Remote repository clone | HTTPS GitHub clone with `core.autocrlf=true` normalized to the exact source and remained clean |
| Private Release restoration | All 58 parts downloaded from GitHub; all 28,679 files restored and independently verified; native Job cleanup passed |

The new [machine-readable qualification](windows_migration_qualification_20261012.json)
indexes copied admission, deadline, command and cleanup receipts under
[`evidence/windows-migration-20261012`](../../evidence/windows-migration-20261012).
These small receipts are committed so the migration checks remain reviewable
without depending on this machine's ignored `runs` directory. Each completed
guarded operation records native exit, Job cleanup and fresh Job-name absence.
Failed operations and floor refusals retain their separate failure status.

The 2,407,031,049-byte history archive is split into 58 verified parts for the
[private evidence Release](https://github.com/RAMZI0TO99/thinking-interfaces/releases/tag/windows-portable-20261012).
The committed per-file and per-part manifest binds every restored byte. It
preserves logs, results, attempt ledgers, quarantines, reference code, processed
sidecars and historical trained checkpoints. Disposable virtual environments and
tool caches are reinstalled. Public data and original public weights use their
verified upstream URLs; the 410 processed NPZs have array-member identities and
rebuild commands. A separate ZIP preserves the exact 725-file repository context
from before migration documentation was added.

Two native Windows stack-overflow failures were resolved within the migration
tools. Pip's large bytecode compilation pass failed on this host; `--no-compile`
then passed an entirely fresh full install. Bulk `os.rename` calls failed during
history publication; exclusive NTFS hard links then restored all 28,679 files
without overwriting destinations. BCI's HTTPS issuer needed the installed,
hash-locked certifi CA bundle in addition to Windows roots. Certificate and
hostname verification remain enabled. A PhysioNet connection timeout was retried
in a fresh bounded Job, retaining the already verified recording. Startup floor
refusals were preserved; later operations used fresh admission with the same
10/4 GiB RAM and 20 GiB disk floors.

This migration executed nine subject/profile reconstructions, not all 410 caches
or all 397 recordings. Older exact reconstruction receipts for 170 Profile A
caches and 52 Cho 60 Hz caches retain their dated scope. A fresh directory on this
host establishes installation and restoration behavior; another device still
needs its own admission and runtime checks. The setup commands create those
receipts. All archived absolute paths, schedules, Jobs and admissions remain
inert history.

The 432 canonical implementation files retain source SHA256
`3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529`.
The historical quality receipt remains 1,055 passes, 3 skips, 5 warnings and 1,125
subtests; it was not rerun for migration and does not certify these new tools or
another hardware runtime. Original case attempts remain two spent and zero
remaining. Gate A, seven owner decisions and the experiment freeze remain
unsigned; actual checkpoint training coverage and overlap remain unknown.
The separate LaBraM maintainer issue remains prepared and unsent.

The measured remote transfer could not fit the whole archive into one ten-minute
Job. The owned combined download was stopped, preserving 16 verified parts and
its failed/cleanup receipt. Setup now downloads or verifies each part in its own
fresh bounded Job, then restores from verified local parts in a separate Job.
This retains finite execution while allowing an automatic complete transfer.
