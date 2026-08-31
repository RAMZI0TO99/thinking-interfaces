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
Reused deterministic fits keep the original fit's provenance. Local snapshots
use the assistant identity `Codex <codex@localhost>` and have not been uploaded.

## Current status

All 170 public subjects are downloaded and structurally audited: BCI Competition
IV 2a (9), Cho2017 (52), and MMIDB (109). Profile A, Profile B, label-blind frozen
artifact thresholds, leakage controls, seven benchmark variants, safe LaBraM
loading, LoRA/adapters/prompts, LSL streaming, confidence gating, accumulated
evidence, CPU/GPU latency, and the held-out replay demonstrator are operational.
The final configuration-hash benchmark sweep is resumable and writes one atomic
record per fold and seed.

Gate A remains unsigned because the named MOABB EEGNet reference does not exist in
MOABB's published table and the available four-class comparator was not reproduced.
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
