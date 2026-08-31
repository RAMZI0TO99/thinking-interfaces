# Phase I channel canonicalisation

All downstream code receives canonical names through the shared `Epoch` record.

| Dataset | Source form | Policy |
|---|---|---|
| BCI IV 2a | Named 10-20 EEG channels from MOABB | Preserve order; normalize against MNE standard-1005 case. |
| Cho2017 | 64 EEG plus 4 EMG channels | Select EEG only; validate all 64 against standard-1005. |
| MMIDB | Dot-padded names such as `Fc3.` and `C3..` | Strip trailing dots/space, then resolve case against standard-1005. |

Duplicate names after canonicalisation are a hard error. LaBraM electrode
positions are resolved from these names at inference time. Montage masking also
accepts names only, so a dataset's channel order cannot silently change the mask.

MMIDB subjects S088, S089, S092, and S100 are retained under explicit structural
validation rather than silently excluded. Sampling rate, channel order, complete
four-second windows, and recognized T1/T2 annotations are checked on load.
