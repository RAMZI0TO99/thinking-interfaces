# Project cache cleanup - milestone 48

19 September 2026. The owner requested a project space audit and removal of
junk. Removed **13,523 regenerable cache files,
314.09 MiB (329,345,439 logical bytes)**: source-backed
Python bytecode in the main venv and project modules, mypy/ruff caches and
Matplotlib font indexes. No package source, binary or dependency metadata was
removed. Python may recreate bytecode on future ordinary runs.

The fresh required quality run passed: **564 passed, 4 warnings, 925 subtests passed in 1284.44s (0:21:24)**; lint and strict types
also passed. Bytecode writing was disabled only in the quality process's
environment. Normal mypy/ruff cache contents recreated by verification were
removed afterward (48,606,493 bytes); this is temporary
regeneration, not extra pre-existing space recovered.

The audit preserved datasets, processed artifacts, all checkpoints, the main
venv packages, the separate MOABB compatibility environment, Git/uncommitted
work, reference assets and every historical receipt/log. SHA-256 checks match
all 77,109 readable pre-existing retained files. The quality-status
pointer advanced normally; its prior bytes are saved. Source fingerprint stays
`1e79dfc779b0cf616243c3e33f2f8a0893397bf41e02ebdf36b0e29e7bdf05f9` and Git stays at `e378dfd` with 85 status
entries. No scientific fit, control refresh, commit or push was launched.

Windows denies traversal of 28 directories,
including `.pytest_cache`, five old `tmp` test directories and historical
test-temp directories beneath `runs`. Their contents/sizes are unknown and
they were left untouched; no ACL/ownership changes were made. Full directory
usage figures are therefore lower bounds. Unknown DesktopCentral logs were
also retained. `.cache` is not uniformly disposable: it contains the local
LaBraM checkpoint and pinned research references.

Final free-space snapshot: **33.28 GiB**, above the unchanged
20 GiB floor. Free space fluctuated independently of the listed deletion
during this session; logical bytes removed and volume free-space change are
separate measures. Cleanup does not admit E2 or resolve owner decisions.

The first deletion attempt failed during prevalidation on PowerShell 5.1's
`Split-Path` parameter combination; zero files were removed by that attempt.
The corrected helper retained containment, SHA-256, exclusive-open and worker
checks. Both scripts and logs remain visible. Only exact files were deleted;
no recursive deletion or Git cleanup command was used.

Evidence: `runs/phase2/cleanup_checks/20260919_step48/` contains the baseline,
candidate inventory, retained-file hashes, deletion receipts, fresh quality,
preservation result and final receipts. No resource guard or scientific
contract changed. The larger remaining allocations are research inputs and
required environments, not established junk.
