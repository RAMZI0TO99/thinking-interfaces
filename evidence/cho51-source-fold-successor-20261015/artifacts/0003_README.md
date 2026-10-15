# Public diagnostic source-fold candidate

`run_probe(output, method, model_config, *, set_protected_inputs)` constructs a
fresh physical synthetic fixture and invokes the unchanged public
`BCIEEGNetSourceSelector.run_fold` or `BCILaBraMSourceSelector.run_fold`. The
fixture preserves all52 declared subjects, canonical protocol/configuration
bytes,64 channels and EEGNet512/full12-block embed200 LaBraM800 samples. Its
small `.mat` provenance markers are synthetic bytes; they are never decoded as
recordings. Random initialized templates load no pretrained weights.

Each method declares two engineering rates,0.001 and0.0005; only the first is
executed for this diagnostic. Outer subject02 is excluded completely. Training
uses subject03 through52 in order, one actual two-trial SGD step each. Subject01
receives one actual ten-trial support update and two fixed withheld queries.
The unchanged canonical shot levels remain1/5/10/20. The declared maximum is51
gradient steps. Official SGD hooks independently check51 real updates, finite
selected gradients/parameters and exact selected parameter counts; the child
also observes actual backward and step calls. No source/private fitting
function, loader, candidate, loss, cohort, or admission guard is patched.
EEGNet source and support both declare the same1,000,000 input scale from
stored volts to microvolts; this explicit unit conversion preserves input bytes.

Before the diagnostic fold, the actual public `run_selection()` rejects its
unchanged5,253-update complete workload against the declared51-update budget,
before any optimizer update. This separately exercises complete-run admission;
it does not execute those folds or establish complete-selector resource bounds.

The callback receives all four subject02 paths and `True` after fixture
construction, before selector construction/folding. It receives the same paths
and `False` in `finally`. The native child implements read denial and keeps
planned negative probes separate from zero permitted actual target reads.
Full physical input hashes, source context and global Torch/NumPy/Python RNG
are checked around the fold. Canonical source/support code checks its source,
frozen state and held-out query state, while this probe checks the real history,
source order, masks, changes, support partition and exact rational metrics.

`fold-evidence.json` preserves the exact public engineering envelope, literally
`complete=false`, with one fold and no selected candidate. The actual public
complete-selection verifier refuses this unmodified record at its payload
schema boundary: `selection evidence has missing or unexpected fields`.
Complete-only fields are deliberately absent. This proves diagnostic evidence
cannot enter that admission path; it does not establish a winner or complete
selection. `probe-result.json` records the actual fold, refusal,51 optimizer
observations and input/evidence hashes. Synthetic artifacts remain outside the
compact evidence archive.

Fresh source review/pins and native resource admission are required before any
execution. Each method's planned native cap is600s,4096/5120MiB process/Job,
RAM10GiB startup/4GiB active,disk20GiB,Torch1/1, hidden GPUs and current pause
paths. These are engineering bounds. No whole selector, fitted publication,
recorder, study cell, scientific admission or original-case attempt is claimed.
