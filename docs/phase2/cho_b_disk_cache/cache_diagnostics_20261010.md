# Completed cache diagnostics, 10 October 2026

The bounded diagnostic phase completed: the inference selector adapter passed
15 checks, all51 source subjects have reviewed no-fit query results, the original
seeded iterator was sampled, and all221 distinct source-step input batches were
forwarded with exact original/cold/copied/warm logits. These are executed
engineering diagnostics and root self-reviews. Production integration, a full
real-data selector run, a480-second case completion and scientific acceptance
remain unproved.

Fresh numerical execution used clean Git
`8c5b25173ce8a1a36c331e7169b9d4420b48d0ae`; the first25 subjects retain their
historical execution Git `2dead17802e36ecc837eff70f80d130c6e18ce41`. Canonical
Source remains `b7452847edf2ee5d8a46638c6cf6549080cb44adbe37142277b364b5898dd442`
/431 files. Each execution review rechecked33 selected runtime files, relevant
operation/input pins, the quality pointer and the four spent case artifacts.
The historical quality suite was not rerun and does not certify these new
operational files.

## Executed evidence

| Operation | Actual result | Root execution review |
| --- | --- | --- |
| Inference selector adapter |15/15 fixture checks;21.644s native time |123 checks |
| Complete source-only query cohort |51 subjects,8269 query trials,1035 distinct batches; exact logits |768 checks |
| Original source-iterator sampling |5151 visits,221 distinct subject/ordered-position-pair keys,4930 repeats;4.281s |153 checks |
| Real source-step batch forwards |221 distinct input-byte keys,442 cache hits,663 cached forward rows;224.778s |852 checks |

Receipt links below are local evidence. Every acceptance is root self-review,
not an independent peer acceptance or an accepted real case.

- [15-check adapter execution review](../../../runs/coordination/cache_performance_20261008_v1/inference_scope_available_execution_root_review_20261010_002.json)
- [All51 query execution review](../../../runs/coordination/cache_performance_20261008_v1/source_query_available_combined_root_review_20261010_006.json)
- [All18 query-scope physical-release observations](../../../runs/coordination/cache_performance_20261008_v1/source_query_available_all_scope_release_20261010_006.json)
- [Original sampler execution review](../../../runs/coordination/cache_performance_20261008_v1/source_sampler_trace_execution_root_review_20261010_001.json)
- [Actual source-batch execution review](../../../runs/coordination/cache_performance_20261008_v1/source_step_feature_execution_root_review_20261010_004.json)

## Query cohort and timings

Five historical five-subject operations cover `subject_02` through `subject_26`.
Thirteen fresh two-subject operations cover `subject_27` through `subject_52`.
The accepted fresh map is `source_query_s01_a001` through `s08_a001`,
`s09_a002`, `s10_a001`, `s11_a001`, `s12_a002`, and `s13_a001`.
The combined review binds each operation's actual source, resource envelope,
terminal receipts and physical release. Completed-unit numerical reuse and the
runner's `-ValidateOnly` recheck actually executed; completed units were not replayed.

The query worker retained its original no-grad diagnostic route and the
`f55fa5be` feature cache. It measured1035 misses,2070 hits and no bypass/eviction.
Totals across the18 operations are:

| Forward scope | Measured total |
| --- | ---: |
| One original query pass |409.660740s |
| One cold feature pass |411.078756s |
| Two warm feature passes |5.180118s |
| Summed disjoint retained feature values |6,615,200 bytes |

Normalizing the two warm passes gives about158.17 times lower forward time than
one original pass. This comparison combines dates, separate model preparations
and independent cache instances. It excludes loading, model preparation,
optimization, support fitting and other selector work. It neither executes one
full51-subject query cache instance nor establishes original inference-query
integration or a full-case speedup. The separately tested inference-compatible
cache and adapter supply their own mode/lifecycle evidence.

The fresh13 accepted query operations used697.035925s summed native time.
Their maximum measured Job commit was1,516,998,656 bytes; including the older
five operations, the maximum was3,114,643,456 bytes. These are operation peaks,
not a whole-host release or a complete selector memory qualification.

## Actual original source-step inputs

The sampling-only operation used a local CPU generator with the original seed11
over verified catalog cardinalities. It instantiated no model, read no weights
and decoded no signals. Its103 sampling traces represent the two-candidate
leave-one-source-out fits and final fit without executing them. It observed221
distinct ordered position-pair keys and4930 repeated visits across5151 declared
source steps. Sampling alone did not measure feature hits.

The subsequent `source_step_features_004` operation decoded the real source
catalogs, independently reproduced those221 pairs, and forwarded their actual
batch2 inputs through the frozen pretrained backbone and unfit head. It used
normal gradient-enabled caller context. Original and cold logits were compared
exactly, then a copied model traversed the subjects in reverse order, followed
by a warm original-model pass. All663 cached rows matched input/trial identities
and logits. Every head output retained its gradient graph; model states and
caller RNG were unchanged. No optimizer, loss, backward pass, parameter update,
real-data training, target-signal forward or accuracy calculation occurred.

| Source-forward measurement | Actual value |
| --- | ---: |
| One original pass |55.456230s |
| One cold feature pass |56.714842s |
| Two warm passes |1.119637s |
| Misses / hits / evictions |221 /442 /0 |
| Deliberately inactive original-reference bypasses |221 |
| Unexpected cache bypasses |0 |
| Retained frozen feature values |353,600 bytes |
| Native / guard elapsed |224.778203s /224.453262s |
| Maximum measured Job commit |1,467,752,448 bytes |

The native/guard limits stayed270/240 seconds. These batch forwards do not
execute the5151 optimizer steps or an entire selector. The repeated keys support
reuse only while actual input bytes, frozen backbone state, namespace and cache
retention remain supported. Equal-size catalogs sometimes share generator
positions, explaining why the observed221 keys are below the older conservative
1326-key bound; this supplies no case runtime guarantee.

## Available-resource envelope and preserved failures

The user's direction to work with available resources was applied in separate
diagnostic-only launchers. The original startup10GiB, process6GiB and Job7.5GiB
guard and real-case limits remain byte-for-byte unchanged.

The accepted adapter and first query pair used startup8GiB, process3.25GiB and
Job3.5GiB. Subsequent pairs, sampling and source forwards used startup7GiB,
process2.25GiB and Job2.5GiB. All retained active RAM4GiB, free disk20GiB,
CPU/Torch1, at most one owned Job, current byte pins and genuine pause sensors.
The source-forward retry additionally waited for10GiB available for15 seconds
before invoking its unchanged diagnostic guard. This finite entry wait changed
neither the model deadline nor a peer lease.

The original adapter startup refusal is preserved. Query `s09_a001` and
`s12_a001` were interrupted by the active RAM floor; they retain missing results
and failed receipts. Only fresh `a002` attempts were accepted after physical
release proofs. The old interrupted `g06_a001` remains excluded. An unentered
PowerShell reviewer with duplicate fields failed parsing and is preserved;
the fresh corrected006 runner/reviewer produced the accepted combined result.

Source-forward001 failed on a missing episode-record argument. Source-forward002
was interrupted by the active RAM floor. Source-forward003 completed its
comparisons but exited1 because its final counter condition wrongly rejected
the221 deliberately inactive original-reference forwards. It retains exit1 and
a missing result; a fresh worker corrected the predicate to require exactly221
reference bypasses. Only source-forward004 and its852-check execution review
are accepted. No failed receipt was overwritten or relabeled.

All reviewed Jobs were freshly absent, recorded process identities were absent
or exited, and query handles closed. Registered private model-data caches and
feature values were cleared. The adapter fixture deliberately retains only its
documented cleanup-refusal sentinels. Unrelated processes were not stopped.

## Integration step and limits

The next engineering step is owner-coordinated adoption of the exact tested
inference cache and selector adapter, followed by source review and the existing
guarded quality checks against the resulting source. Root owns the operational
diagnostic files and this recipe; frozen implementation ownership must be settled
before changing production files. The tested operational adapter wraps only its
owned selector instance, preserves the original fit/fold routines and restores
the instance, selected-model forward and input lifetime on exit.

Retain exact candidate pins: inference cache
`d5eff3a68996a6f6918fee0ace83572767f1ef3df1b85712989331443ce4c8c1`, adapter
`5fed1301b216efcebf0218a928046f9fad3b97d4ef59980a1a6ec8280b152e5b`,
and disk cache
`521772373625feaa11c5b0e36cf4353e83dd9ccd88f8ff401d85a44a557a384c`.
Do not reuse this execution Git as entry authority after documentation/source
changes; create fresh matching operation pins and attempt identities if another
bounded diagnostic is actually needed. The operational index now records
completed diagnostics rather than the obsolete pending query commands.

Both original real LaBraM case attempts remain spent. This phase admits no third
case, cap increase, real-data fit or scientific signature. Scientific Gate A,
the experiment freeze and checkpoint pretraining-cohort/target-overlap provenance
remain unresolved. Pro2 Source021 is lightweight peer scheduling only through
20:40UTC10October, with no runtime release or result acceptance inferred. No
genuine peer pause was present at this checkpoint. The original30-hour session
and obsolete quality watcher remain ended.
