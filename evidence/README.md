# Portable historical evidence

`portable-20261012-v2/manifest.json` lists 28,679 historical files, their original
sizes and SHA256 hashes, plus 58 independently hashed download parts. The parts
are private GitHub Release assets under `windows-portable-20261012`; they restore
2,965,454,392 bytes from a 2,407,031,049-byte streaming archive. Public raw data,
processed NPZ caches, original public weights, copied virtual environments and
disposable tool caches are excluded. Historical trained/adapter checkpoints are
retained because reproducing them would require new fits.

`repository-context.zip` preserves the exact working bytes of all 725 originally
tracked files at commit `c994101334864579a0082f3d242a5d54b0b0d0b2`, before migration
documentation changes. Its companion JSON records every byte hash, including
mixed line endings. This supports review of old context pins against old bytes.
It is a historical snapshot, not a second active checkout or launcher package.

The first long-range compression attempt reached its ten-minute deadline and
was stopped with its private Job confirmed absent. Its partial archive remains
locally quarantined. A fresh fast-streaming export completed in 148.438 seconds
without deserializing weights or fitting. Old evidence was not rewritten.

Use [WINDOWS_SETUP.md](../WINDOWS_SETUP.md) to restore this history. The downloader
uses the existing Git Credential Manager login for this private repository and
checks every part and the complete archive before checking each extracted file.
Tokens are kept in memory and stripped when requests redirect to a different host.
No credentials are stored in the repository or archive manifests.

Old receipts, attempt counters, quarantines, schedules and absolute paths retain
their dates and scopes. Bootstrap is not scientific admission. Original attempts
remain zero; Gate A, owner decisions and experiment freeze remain unsigned.
