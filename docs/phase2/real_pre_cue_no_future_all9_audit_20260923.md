# Real BCI IV 2a no-future pre-cue signal audit

**Status:** preliminary signal audit of the proposed, unratified
`pre_cue_no_future_v1` path. Gate A remains unsigned. This audit does not
produce control model metrics or admit scientific cells.

The [revised write-once receipt](../../runs/phase2/gate_a_diagnostics/20260923_no_future_all9_posthash/real_pre_cue_no_future_all9_posthash.json)
is the current all-nine engineering evidence. It supersedes the
[first receipt](../../runs/phase2/gate_a_diagnostics/20260923_no_future_all9/real_pre_cue_no_future_all9.json)
for raw-input stability because the revised audit rehashes every raw file
after cue processing and refuses a changed input before publication. The
first receipt remains preserved as historical evidence.

## Reproduction and scope

The revised write-once run used this wrapper from the project root with the
pinned local environment:

```powershell
.venv\Scripts\python.exe runs/phase2/gate_a_diagnostics/20260923_no_future_all9_posthash/run_posthash_audit.py
```

The wrapper's output namespace is now occupied, so another invocation would
refuse publication. The module's original `--write-receipt` path is likewise
occupied by the historical first receipt.

The [audit script](../../scripts/audit_real_pre_cue_no_future_all9.py) requires
all 18 BCI IV 2a `.mat` files to be cached locally before it starts. It
streams SHA-256 checks over each file, verifies both subject 01 hashes against
`configs/bci_iv_2a.toml`, records the other 16 raw hashes, checks the project
20 GiB free-disk floor and an additional 4 GiB available-RAM floor, and
rechecks resources after every run. It rehashes all 18 raw files after
processing and refuses publication if their roster, size or SHA-256 differs
from the initial scan. It reads the relevant preprocessing, loader,
record-writer, config and dependency-lock bytes before and after processing
and refuses a receipt if any changed. It records the active
MNE, MOABB, NumPy and SciPy versions. Processing runs sequentially at one
MNE worker.

For each annotated cue, the script compares the current
`preprocess_pre_cue_run` output with the proposed `preprocess_no_future_run`
output. It requires equal labels, cue counts, 22-channel order, finite
`float32` windows, and `(22, 128)` shape. The receipt records maximum absolute
and RMS differences in microvolts for every cue and every cue-channel pair,
with aggregate values for each channel and subject. For the first run in each
training and evaluation session, it changes the cue sample and every later
raw sample, then requires the proposed first-cue window to remain exactly
equal. The completed audit includes 18 such real-run future-input checks.

The old/new difference combines the effects of excluding future input and
filtering/resampling at a new right boundary. It is a signal comparison, not
an estimate of classifier performance or an isolated measure of future
leakage. The earlier [same-length future-input diagnostic](real_pre_cue_future_sensitivity_20260923.md)
isolates a different question on one run.

The only new output was the [revised write-once engineering receipt](../../runs/phase2/gate_a_diagnostics/20260923_no_future_all9_posthash/real_pre_cue_no_future_all9_posthash.json).
Historical pre-cue artifacts and the separate proposed output namespace are
untouched.

## Results

The guarded pass completed on all **9 subjects, 108 runs and 5,184 cues**.
Every subject supplied 576 cues, with 1,296 cues for each of the four
classes. Old and proposed windows had the same labels, canonical channel
order and `(22, 128)` shape. Every measured window was finite `float32`.

| Subject | Median cue maximum difference (uV) | Largest cue maximum difference (uV) | Median cue RMS difference (uV) |
| --- | ---: | ---: | ---: |
| 01 | 5.219 | 14.547 | 0.652 |
| 02 | 4.162 | 18.708 | 0.522 |
| 03 | 5.987 | 21.100 | 0.738 |
| 04 | 4.524 | 21.738 | 0.613 |
| 05 | 4.308 | 10.835 | 0.525 |
| 06 | 6.910 | 35.703 | 0.869 |
| 07 | 5.305 | 13.177 | 0.723 |
| 08 | 7.859 | 24.504 | 0.987 |
| 09 | 10.947 | 38.153 | 1.311 |

Across all cues, the median of each cue's maximum absolute difference was
**5.758 uV** (95th percentile **13.250 uV**, largest **38.153 uV**). The
median cue RMS difference was **0.731 uV** (95th percentile **1.830 uV**).
The receipt gives each cue's maximum and RMS difference, both measures for
all 22 channels within that cue, and subject/channel aggregates. The largest
observed sample difference was on subject 09, test run 4, cue 10, channel
`C4`; this is a signal discrepancy, without a model-performance inference.

For one cue in the first run of each subject's training and evaluation
session, the counterfactual changed the cue and all later raw EEG values,
with maximum future-input change from **99.219 to 131.494 uV**. All **18/18**
proposed windows remained bitwise equal. This real-data check agrees with
the input boundary in the proposed implementation. It does not establish
real-time causal filtering or classifier utility.

The revised pass used MNE 1.12.1, MOABB 1.6.1, NumPy 2.5.2 and SciPy 1.18.1,
and took **426.00 seconds**. Its observed free disk was **30.765 to 28.964 GiB**,
available RAM **8.339 to 8.354 GiB**, and process RSS **0.687 to 0.835 GiB**
before/after; these are machine snapshots while another project also ran.
The 20 GiB disk and 4 GiB RAM audit guards passed at all measured checkpoints. The separate
10 GiB control-fit startup guard was not used or satisfied by this audit.

The revised receipt's envelope SHA-256 is
`3327faa236306f6a83ce28a53be541bebd934fcad53023ca6f468e80436c6770`;
its file SHA-256 is
`14accc31cb041b17cda1a670bbaae635a1fee53500d3ebbce95608a12ae69be5`.
It pins the wrapper and 11 audit source/configuration files plus all 18 raw
files. Subject 01's two raw hashes
matched the pre-existing config pins. The remaining 16 raw hashes are
recorded observations; they have no pre-existing trusted config pins.
After publication, an independent readback reproduced the revised envelope
digest, matched all 11 pinned source/configuration hashes and all 18 raw file
hashes, confirmed all 5,184 cue details and signal summaries matched the
historical receipt, and confirmed all 18 representative invariance checks
remained exactly equal. The historical first receipt has envelope SHA-256
`5ca3ca8b1a2ac2a0b06a0624685ebae8c1ad3835afc9a6351ebf7bc6b3094276`
and file SHA-256
`35ab3fc0d351c7d4552ffceb3ee82d1fc5d3a61567fa34721c6dfe553f7e0f8b`.
Its signal measurements agree, but its source script did not yet rehash raw
inputs after processing. Ruff and strict mypy passed on the revised script.

This audit supports a versioned control rebuild decision. It does not sign
Gate A: saved no-future artifacts, a matched control model evaluation and
the preset Gate A decision remain outstanding.
