# No-future matched-control check on the Cho identity source

28 September 2026. A monitored, read-only
`scripts.run_no_future_matched_control --check-only` run completed against
source `5dce82b17ee36d791d78659900ba87cd1f3d4c425e1fc237bf0fd6cbb8198d20`
and its [exact-source quality archive](../../runs/phase2/quality_history/20260928_cho_analysis_identity_5dce82b1.json).
The [write-once run receipt](../../runs/phase2/gate_a_diagnostics/20260928_no_future_identity_binding_5dce82b1/receipt.json)
pins the command log, context, source and resource observations. Source and
quality remained stable. The command's exit code of 1 means that the
36-record diagnostic is incomplete; the wrapper accepted that expected
read-only inventory result.

The command performed its nine-subject preprocessing writer check before
building the matched-control context. The resulting audit reports **0 valid
and 36 missing** matched-control records, with no invalid or unexpected
record. It also reports `raw_files_verified: false`: the audit's final
record-bound raw verification runs only after all 36 records are present.
The writer check and the final record-bound verification are distinct steps.
There is no matched-control score or Gate A conclusion from this run.

The wrapper observed a minimum 9.185 GiB available RAM and 27.842 GiB free
disk over 436.3 seconds, above its 4 GiB active RAM and 20 GiB disk floors.
It performed no training and signed no gate. This check supersedes the
earlier [guarded-stop attempt](no_future_current_source_guarded_stop_20260928.md)
only for the new exact source; it does not refresh the separate 45
source-bound controls. Those remain 0 valid / 45 missing. The 10 GiB
control-fit startup guard, 256-step engineering selection cap, full Cho
scientific freeze and Gate A decision remain open.
