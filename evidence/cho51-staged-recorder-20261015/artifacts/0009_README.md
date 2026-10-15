# Staged restoration of the accepted EEGNet publication

This separately versioned candidate restores the immutable accepted source
publication from the complete EEGNet v4 run. It does not retrain the model or
create a new source claim. The old v4 detached resource refusal and linked
failed parent transaction remain historical failures.

`restore.py` copies `cho51_complete_eegnet_v2.selection.verify_publication`
exactly, with two changes: the keyword-only `detached_output` parameter and
`output = Path(detached_output)`. All other function text is unchanged. Shared
helpers and constants come from the frozen v2 selection module. In particular,
its `_context` still uses its own adjacent frozen `inputs.py`; no staged copy
can replace the input authentication helper.

The caller must independently pin the actual accepted historical source result
and preserve its original request, claim, source and fixture identities. It must
validate that `detached_output` is an existing, resolved absolute directory in
a fresh staged workspace outside the old v4 workspace and fixture. The copied
function also refuses an output directory containing `detached-result.json`.
The copied detached result retains the original
`cho51_complete_eegnet_detached_result_v1` schema and old request/pins fields;
any new staged qualification wrapper must state the new launch provenance
separately and must not relabel it as a fresh source or parent transaction.

The independently guarded process retains the existing RAM requirements,
native deadline and memory caps, target input protection, complete selection
history and optimizer trace verification, physical input/source checks, global
RNG checks, and both public full-state restore calls. Each public store call
retains the fixed one-MiB weights bound and delegates to the unchanged canonical
restoration code. No RAM check, restoration decoder or model contract is
weakened.

This module does not use a recorder, reset a failed attempt, create an
engineering terminal, execute target prediction, admit scientific work, or
consume an original-case attempt. Importing or statically parsing it proves no
runtime restoration. Only a fresh accepted guarded staged launch can establish
the restoration result, and that result cannot retroactively make the failed
v4 parent transaction successful.
