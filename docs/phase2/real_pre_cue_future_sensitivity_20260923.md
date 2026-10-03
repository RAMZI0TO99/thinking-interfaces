# Real-run pre-cue future-input sensitivity

**Status:** preliminary, read-only Gate A diagnostic on 23 September 2026.
No control artifact, model, threshold or scientific result was changed. Gate A
remains unsigned.

The [diagnostic script](../../scripts/diagnose_real_pre_cue_future_sensitivity.py)
read the locally cached BCI IV 2a subject 01 training file, selected session
`0train`, run `0`, and compared eight chronologically first cues: two each of
left hand, right hand, feet and tongue. The run has 48 cues. Its raw file
SHA-256
`054f02e70cf9c4ada1517e9b9864f45407939c1062c6793516585c6f511d0325`
matches `configs/bci_iv_2a.toml`. Profile A settings were 8–30 Hz FIR,
common-average reference, 128 Hz resampling and a one-second pre-cue window.
The script verified that its manually indexed current-pipeline windows match
`preprocess_pre_cue_run` exactly for every selected cue.

Three signal conditions were compared per cue:

1. **Current:** the production zero-phase filter runs across the full raw
   recording before the window is cut.
2. **Prefix-only:** only raw samples strictly before that cue are filtered,
   referenced and resampled. This has no post-cue input, but its new filter
   and resampling edge can itself change the last part of the window.
3. **Flat future:** the run retains the same length and pre-cue samples, while
   every sample from that cue onward is replaced by the last observed pre-cue
   value. The same production filter, reference and resampler are applied.
   This isolates sensitivity to the observed future stream under a specific
   artificial continuation; it is not a deployable causal filter.

The absolute current-minus-alternative signal differences across 22 channels
and 128 samples per cue were:

| Alternative | Median per-cue maximum | Largest per-cue maximum | Median per-cue RMS | Largest per-cue RMS |
| --- | ---: | ---: | ---: | ---: |
| Flat future | 3.093 µV | 4.377 µV | 0.205 µV | 0.335 µV |
| Prefix-only | 6.141 µV | 11.031 µV | 0.566 µV | 1.560 µV |

Every selected cue had a nonzero flat-future difference. The current
pre-cue epochs had RMS amplitudes of 2.20–3.48 µV. The flat-future
comparison confirms that the current pre-cue samples depend on the actual
post-cue samples in this run. The larger prefix-only differences combine
that dependency with endpoint behavior, so they should not be interpreted as
an estimate of contamination alone.

The local resource guard passed before and after loading: disk free 32.22
GiB against the 20 GiB project floor; available RAM 8.68 then 8.63 GiB
against this diagnostic's 4 GiB floor. MNE was 1.12.1. The production
`data/pre_cue.py` SHA-256 was
`b8d60c0ad8bb1247e00e08697529f7e94964279342e759da1a3858a1cb4a91c6`;
`configs/base.toml` SHA-256 was
`02c8e3011abfcafe170f791ec688c791b2187d8e547dd3b2655bae2b5eedf2c4`.
The diagnostic script SHA-256 was
`2c60b2a227ca33e93a9b3d701a7c13a4370e9b762767494de14775f1ff8b40a1`.
Run with
`.venv\Scripts\python.exe -m scripts.diagnose_real_pre_cue_future_sensitivity`
from the repository root to print all eight per-cue measurements.
The [write-once per-cue receipt](../../runs/phase2/gate_a_diagnostics/20260923_real_future/real_pre_cue_future_sensitivity.json)
records the corrected eight-row output and reviewed script hash; its envelope
SHA-256 is `6f1c0177af2be81ff93fccbb9f2ad425156d287b9ff64e30c4f04ba6b5de400c`.

No direct control-model accuracy was calculated. The existing control route
would refit a model, and this bounded diagnostic did not retrain. One run and
eight cues cannot quantify the full control's performance effect or justify
Gate A acceptance. A predeclared all-run sensitivity and an independent Gate
A decision remain separate work.
