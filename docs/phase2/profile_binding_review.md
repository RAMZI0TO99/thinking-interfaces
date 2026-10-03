# BCI cross-profile episode binding

8 September 2026. Fourteenth bounded Phase II step.
The BCI trial-binding and encoder-input check is complete. P2 remains open;
this does not admit the measured pilot or scientific training.

## Implemented contract

`evaluation.phase2_profile_binding.load_bci_profile_b_episode` takes the project
root, adopted protocol, trusted Profile A catalog and saved episode envelope,
plus a shot level and independently admitted hashes for the A manifest, B artifact
and B manifest. Profile A artifact identity is already pinned in the catalog.
The existing protocol, profiles, thresholds, data and Phase I interfaces are unchanged.

The loader reconstructs the Profile A catalog from actual bytes and the frozen
amplitude threshold, then verifies the complete saved nested episode. It joins
**every original trial**, including rejected A rows, by session/run/original trial
index within the fixed BCI subject. The full A/B identity sets and labels must be
equal, without duplicates. Profile B row order may differ; row-number equality is
never assumed. A missing B trial cannot silently shrink support or query.

Only after the join succeeds are the selected support and common-query IDs mapped
to B rows. The unused maximum twenty-shot support pool never enters the query set.
Rejection is inherited exclusively from the audited A partition. No second
amplitude cutoff, extra scaling, resampling, filtering or learned transform occurs.

| Input property | Supported contract |
| --- | --- |
| Dataset/classes | BCI IV 2a subjects 01–09; feet, left hand, right hand, tongue, in that label-index order. |
| Montage | The fixed 22-channel BCI order; both artifacts and manifests must agree. Joint channel reordering is rejected in this version. |
| A arrays | Finite float32 `[trials,22,512]`; 128 Hz, four seconds, declared Profile A configuration and baseline. |
| B arrays | Finite float32 `[trials,22,800]`; 200 Hz, four seconds, 200-sample patches, declared Profile B configuration. |
| B units | Existing values represent 0.1 mV = 0.0001 V per stored unit. Additional input scale is exactly 1.0. |
| Trial metadata | Nonempty string sessions/runs, valid labels, nonnegative integer original indices and unique identities across all rows. |
| Configuration | Both profiles must match this version's explicit supported contract; manifest subject, shape, channels, sampling, units, patches and configuration hashes are checked. |

The returned `BCIProfileEpisode` contains owned NumPy support/query arrays and
integer labels. Its frozen `BCIProfileBinding` records the two artifact hashes,
two manifest hashes, protocol/episode identities, preprocessing/base configuration
identities, selected IDs, B row mappings, input/rejection counts and input contract.
Its digest can be included in a future model-run identity. Returned arrays can be
modified by their owner without changing saved inputs or a later load.

All pinned files are checked before loading and again before return. The loader
has no output publication, model fitting, query subset or tensor-override argument.
The new module is a data-binding interface; it does not replace the TCPL runner
or supply the future shared runner's subject-role and source-selection enforcement.

## Verification

Nine tests and 26 subtests cover every adopted shot level, independently expected
signals/labels after reversed B row order, rejection before partitioning, owned
outputs, missing/extra/duplicate trials, label changes even on rejected A trials,
invalid shapes/dtypes/nonfinite values, montage changes and invalid original indices.
Rehashed manifest-unit/subject/sampling/patch/config changes, altered catalogs,
episode tampering, threshold/base changes and input drift are rejected.

The initial focused run reported one failure: the concurrent-change mock targeted
a third module-local digest call, although the module performs two checks of B.
The test helper uses a separate unpatched digest import. Correcting the mock to
change the final check produced nine passing tests and 26 passing subtests.
The failure and diagnosis are retained. Formatting and type annotations were
then corrected; no production acceptance rule or comparison tolerance was weakened.

The real-data check independently reconstructed trial joins and support/query
membership from the original arrays, then compared every returned signal and
label exactly. All **nine subjects × four shot levels = 36 episode conditions**
passed. The same **4,458 unique common-query trials** remain across all shot levels:
496 per subject for subjects 01–08 and 490 for subject 09. All 36 A/B input and
manifest files and nine saved episode records retained their hashes.

A strictly loaded safe LaBraM checkpoint accepted `[6,22,800]` bound inputs:
four one-shot support examples and two common-query examples from subject 01.
It produced finite `[6,200]` CLS features. Model state and inputs were unchanged;
labels were not passed to the encoder and zero training steps occurred. Execution
used CPU float32, two threads, Python 3.12.14, Torch 2.13.0+cu130 and NumPy 2.5.2.
The checkpoint and model configuration match the earlier pinned identities.
This forward check is not a fresh reference-parity or accuracy experiment.

Full lint passes and strict types pass for 150 source files. Full regression:

```text
437 passed, 3 warnings, 640 subtests passed in 26.59s
```

The warnings are the existing EEGNet deprecation and classification warnings.
Source fingerprint:
`35118a06051592da4f7dec6ae5c8a68f35a63379121636d8ec782b49cd267f97`.
Git HEAD is `e378dfd5f65e53b7ae7da62c778e829b60c61b98`, dirty and uncommitted.
All pre-existing source/config/test files retain their before-step hashes.

Evidence is in `runs/phase2/profile_binding_checks/20260908_step14/`:
`receipt.json`, `pytest.log`, `lint_types_tool_output.json`,
`initial_test_failure.json`, `real_binding_check.py`, `real_binding_receipt.json`
and `documentation_receipt.json`. The real-data receipt retains each binding,
row mapping and input/audit hash without duplicating the signal files.

## Trust boundary and next step

Caller-supplied catalog/configuration and asset hashes are trusted admission
inputs. Hash consistency and matching metadata cannot independently prove physical
units or reconstruct the original filters. This step validates byte identity,
metadata consistency, partition preservation and a bounded encoder forward;
it does not repeat the historical raw-signal reconstruction or certify scientific
preprocessing for every subject. Saved manifests' descriptive summary statistics
and raw-file provenance are not regenerated here.

Profile B remains offline zero-phase preprocessing. No causal deployment claim,
target alignment fit, source-fit history, candidate selection or scientific score
is supplied. Cho/MMIDB profile preparation and the TCPL/E1 reference limitations
remain outstanding. Earlier receipts retain their original source identities.

Next bounded step: connect this binding to the LaBraM adaptation runner, beginning
with linear/partial/full support tuning and subject-role enforcement. The shared
six-method/anchor runner and complete source-selection workflow remain the larger
P2 package. Final free disk is 19.56 GiB, below the unchanged 20 GiB training floor.
Heavy training, source-bound control refresh and scientific gate approval remain
deferred.
