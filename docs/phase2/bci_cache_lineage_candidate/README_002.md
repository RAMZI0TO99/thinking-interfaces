# Revised BCI runtime fixture

The installed BNCI converter reads `age`, `gender`, and `artifacts` when
`dataset_code="BNCI2014-001"` and a subject ID are supplied. The original
synthetic fixture omitted those fields. Source review found this before any
probe attempt was created. `probe_bci.py` and its original preparation remain
preserved; they are not qualified for execution.

`probe_bci_002.py` supplies synthetic metadata and checks the converter's
result as well as units, the 500-sample cue offset, four-class epoch shape,
and original channel/trial identities. It requires its own fresh `probe_002`
plan and guarded admission. A successful older MMIDB probe does not qualify
this BCI path. No BCI runtime result is asserted by this source correction.

Real BCI reconstruction still needs a separately admitted worker bound to
the complete, reviewed revised probe and its measured runtime. No model,
checkpoint, fitting, scientific gate, or exhausted original case is admitted.
