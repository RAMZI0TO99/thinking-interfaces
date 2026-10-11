# BCI IV 2a cache reconstruction engineering candidate

Two separate finite stages: first, measure the actual local MAT conversion,
annotation and preprocessing runtime with an owned synthetic four-class MAT;
then, after fresh review/admission, reconstruct all nine existing Profile A
caches from the18 pinned local AxxT/AxxE MAT files. No network/download/cache
saving path is called. No checkpoint, model, fitting, inference or recorder
is supplied. No scientific eligibility, Gate A or freeze is signed.

The installed MOABB `_convert_mi` receives exactly the channel names/types,
dataset code, subject, ignore-artifacts and interval arguments from its
BNCI2014_001 loader. `SetRawAnnotations` applies the default dataset interval
[2,6], shifting each trial start by500 native samples at250Hz. The candidate
then calls frozen `data.profile_a.preprocess_run` and preserves the existing
Profile A channel names, session/run/trial schema and class labels.

Signals are compared with the qualified unchanged MMIDB worker helper at
absolute1e-12V/relative1e-6; identities, channels, shapes and dtypes are exact.
Any mismatch is retained without changing source, inputs or tolerances.
Input hashes/size/mtime are checked before/after processing. Synthetic output
and real metadata receipts live only in a fresh guarded attempt directory.

Floors10GiB startup/4GiB active RAM/20GiB disk, process4/Job5GiB caps,
CPU/Torch/native1 and one concurrent owned Job remain. Probe120/150seconds;
real reconstruction300/330seconds; one fresh attempt per stage. Original
model-case limits and spent attempts are unchanged. Current reconstruction
does not authenticate historical generation or checkpoint training coverage.
