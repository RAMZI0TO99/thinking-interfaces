# BCI/Cho reconstruction readiness: prepared, not executed

11 October 2026 UTC. The BCI candidate is committed and compiled without
scientific target imports. Its metadata preparation binds nine subjects,
18 local MAT files, nine existing caches and5,184 epochs. Cache/raw sizes,
mtimes and link counts agree with the prior inventory/checksum map. Large
inputs were not opened or freshly hashed in this metadata step; BCI publisher
checksums remain unverified. No real reconstruction has been admitted.

The two-stage [candidate](bci_cache_lineage_candidate/README.md) first measures
the actual local MAT converter and annotation/preprocessing runtime on an
owned synthetic four-class fixture. The proposed second stage reconstructs
all nine caches. Installed MOABB `_convert_mi` receives its unchanged BNCI
loader arguments; `SetRawAnnotations` applies interval[2,6], shifting native
trial starts by500 samples at250Hz. Frozen `preprocess_run` and the existing
Profile A collection schema preserve22 EEG channel names, four class labels,
sessions0train/1test, run indices0..5 and per-run trial indices. The probe's
four loader/units/cue/provenance checks are **not executed**.

The native launch refused before creating the attempt directory because
available RAM was below the10GiB startup floor. No Job/scientific worker,
temporary-awake request or probe attempt was created/consumed. A fresh
GlobalMemoryStatusEx observation at00:57:40UTC measured8.29121399GiB available,
confirming the same issue as WMI. No floor was reduced and no unrelated
process was stopped. The proposed10/4/20GiB floors, process4/Job5GiB caps,
CPU/Torch/native1 and120/150s probe versus300/330s real scopes remain.

While launch was guarded, the separate Cho loader route was traced and a
prototype compiled with no scientific imports. Metadata preparation covers
52 subjects/10,520 epochs. The prototype inherits the exact installed Cho
converter and overrides only local path resolution, then applies the default
annotation transformer and frozen unified Profile A. The converter demeans
each class and stacks classes with a500-sample zero buffer; that project
class-block order is not authenticated acquisition chronology. The prototype
has **no compute admission** and neither its synthetic nor real path ran.

Evidence is retained in
`runs/coordination/bci_cache_reconstruction_20261011_v1` (protocol, immutable
candidate/plan, metadata bindings and resource observation) and
`runs/coordination/cho_cache_reconstruction_preparation_20261011_v1`
(quarantined prototype and static input/source pins). The source fingerprint
remains3114ec43/432 with quality pointer4eb4d556; older suite receipts do not
certify these new candidate paths. After this documentation commit, a future
probe needs fresh matching execution-Git/admission bindings as well as the
unchanged resource floors and coordination. It must not reuse an expired
or mismatching admission, or overwrite these immutable preparations.

The earlier [all109 MMIDB result](mmidb_full_cache_reconstruction_20261010.md)
remains complete:4,917 epochs reproduce exactly, with26 owned Job names last
verified absent. Pro2 reports no pause/compute admission; its Source-only
scheduling does not confer quiet/resource/scientific acceptance. Gate A,
seven owner decisions/freeze and checkpoint cohort/overlap remain unsigned
or unverified. The request is unsent; both original LaBraM attempts remain
spent, zero remaining. No checkpoint, model, recorder or original case ran.
