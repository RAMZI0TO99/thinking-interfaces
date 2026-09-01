# Thinking Interfaces

Phase I builds a reproducible EEG-decoding harness and a working real-time demonstration. Research claims begin only in Phase II.

## Phase I lanes

| Lane | Directory | Responsibility |
|---|---|---|
| Lead | `core/`, `configs/` | Contracts, run records, configuration, metrics, CI, gates |
| Encoder | `encoder/` | LaBraM loading, electrode mapping, depth controls |
| Adaptation | `adaptation/` | Episodic protocol, LoRA, adapters, prompt generator |
| Data | `data/` | Dataset loaders, channel canonicalisation, preprocessing |
| Real-time | `realtime/` | LSL, causal buffering, gating, interface |
| Shared evaluation | `evaluation/` | Baselines, leakage tests, statistics, figures |

## Non-negotiable rules

- Every experimental parameter comes from a committed configuration file.
- Every result is associated with a `RunRecord` containing its configuration, seed, Git commit, dataset, fold, metrics, and timestamp.
- Raw data, processed data, credentials, weights, and run outputs are never committed.
- Source and target subjects must be disjoint in every cross-subject split.
- Support data may change a model; query data may only evaluate it.
- Phase I Gate A must pass before later results are treated as interpretable.

The local Git history begins at `bf78379b6ec67a6fef3db83d8e3c34f37b35299b`.
Runs made before versioning keep their original explicit unversioned identity;
they are not retroactively attributed to this commit. New benchmark runs capture
the current commit, a source/configuration fingerprint and dirty-state flag.
Reused deterministic fits keep the original fit's provenance. These source
changes were created by the assistant and have not been uploaded. Most snapshots
use `Codex <codex@localhost>`; commit `659949a` inherited Git's automatic local
identity. Commit metadata is not evidence of manual user review or gate approval.
The final plausibility audit retains 1,051 legacy unversioned records and 4,899
records with source fingerprints; it does not rewrite either group. A separate
45/45 current-source control bundle verifies the present training paths.

## Current status

All 170 public subjects are downloaded and structurally audited: BCI Competition
IV 2a (9), Cho2017 (52), and MMIDB (109). Profile A, Profile B, label-blind frozen
artifact thresholds, leakage controls, seven benchmark variants, safe LaBraM
loading, LoRA/adapters/prompts, LSL streaming, confidence gating, accumulated
evidence, CPU/GPU latency, and the held-out replay demonstrator are operational.
The final configuration-hash benchmark sweep is complete: 5,950/5,950 records
across 170 subjects, seven methods and five seeds independently pass the record
audit. Its snapshot is
`ff7076b53efd77569d35b6b4d9460be3505376dd174cd690e22c6dee3cfe461a`.
The 21-row primary table, diagnostic table and three snapshot-bound figures were
regenerated and visually checked. These remain exploratory results.

A native Windows demonstration now connects actual true-rate LSL replay to
causal windows, CPU EEGNet, confidence gating and an on-screen command grid.
The visible A09 rehearsal received all 6,144 samples and displayed all 12 windows;
training used the other eight subjects only. All decisions abstained, so this
verifies the integration, not useful decoding accuracy. See
`docs/realtime_system.md` for the one-command rehearsal and its limitations.

Run `scripts/verify_phase1_quality.py` with the project Python to record lint,
type checks and tests for the exact source snapshot. The final completion checker
also verifies report hashes, benchmark completeness and the native display receipt.

Gate A remains unsigned. MOABB does publish an EEGNet reference for this dataset;
the earlier statement that it was absent was incorrect. Its within-session
five-fold protocol and scoring differ from the existing cross-session attempts,
so those attempts do not establish reproduction. The separate protocol-matched
grid is now complete at 450/450 valid fits, and an independent raw-input audit
matched every fit. The seed-42 mean ROC-AUC is 75.66% versus the published 77.15%;
the four declared repeat seeds average 75.02%. No acceptance tolerance or approval
has been adopted, so this descriptive comparison does not sign Gate A.
The user explicitly authorized later Phase I work as exploratory; no downstream
result is represented as resolving Gate A. See `docs/gate_a_status.md` and
`docs/deviation_log.md`.

## Local setup

The project targets Python 3.12. A project-local `.venv` is used; no system-wide packages are required.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pip install -r requirements.lock
.\.venv\Scripts\python -m pytest
```

Install the heavier EEG and GPU dependencies only after the foundation tests pass.

## Subject 1 EEGNet baseline

The training session is split into training and validation subsets. The evaluation
session remains untouched until final scoring.

```powershell
.\.venv\Scripts\python -m pip install -r requirements-data.lock
.\.venv\Scripts\python -m pip install -r requirements-ml.lock
.\.venv\Scripts\python scripts\run_eegnet_baseline.py --smoke
.\.venv\Scripts\python scripts\run_eegnet_baseline.py
```
