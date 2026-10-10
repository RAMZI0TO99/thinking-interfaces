# Private Cho B file-cache prototype

This Windows-only operational prototype keeps verified source episodes in a
private file tier so an evicted subject can be restored without decoding its
NPZ/raw inputs again. It is **not wired into production or admitted for another
training case**. The unchanged canonical source remains `b7452847` /431 files.
New operational code is separately pinned and tested; the historical canonical
quality receipt does not certify this prototype.

The [prototype](disk_backed_snapshot.py) is an exact copy of the executed bytes:
SHA-256 `521772373625feaa11c5b0e36cf4353e83dd9ccd88f8ff401d85a44a557a384c`.
The original first version and its failed clear-compatibility test are retained
in local evidence. The corrected version passed **23 synthetic checks**:
15 existing input/selector tests and8 new file-cache checks. These include
exact linear/full/LoRA model, loss/history, evidence and RNG equivalence;
source/configuration tampering; read-only write/delete protection; eviction;
disk-budget fallback; clearing; and cleanup with outstanding borrowed views.
The original LRU loader-call-count test was replaced because reduced decoding
after eviction is the intended behavior; exact returned arrays are still checked.

## Measured source loading

The original512MiB LRU was traced using the first two full source-validation
loading orders:100 loads,100 misses,88 evictions,51 unique non-target subjects.
It took **105.4028 seconds** inside `snapshot.load`. The prototype repeated
those same100 loads with exact array hashes and ordering, then one additional
fully warmed50-subject loading order:

| Loading order | Prototype load time | Result |
|---|---:|---|
| First | 63.6728s | Verified and sealed50 source subjects |
| Second | 1.9754s | One new original load and49 file restores |
| Third | 0.5370s | 50 file restores |

The first two orders totaled65.6483s, about37.7% below the separately measured
original trace. This is a loader comparison, not a full-case runtime or accuracy
claim. The150-load trace made51 original loads and99 file restores, with zero
disk-budget bypasses. No model was constructed or fitted. Cache files were
verified and removed. Maximum private cache bytes were **2,111,365,672**, below
the2GiB budget. The logical resident LRU remained512MiB; the OS controls physical
residency of read-only file mappings. Measured Job aggregate peak was
2,762,768,384 bytes (about2.573GiB), within the unchanged7.5GiB guard.

The root milestone review passed145 checks, accepting executed diagnostic,
fixture and physical-cleanup evidence. It is self-review, not independent
approval of a case result. Both earlier real LaBraM attempts remain spent.
Scientific Gate A/freeze remain unsigned and checkpoint pretraining cohort
provenance remains unverified.

## Ownership and lifetime

The prototype composes the original `_ChoBInputSnapshot`. First loads use its
unchanged verified loader. File restores enter the original LRU and pass its
normal catalog, asset, episode, configuration and source-file metadata checks.
All original touched files are unconditionally rehashed at `verify`, along
with every active private cache file. Windows read handles deny write/delete
sharing, and mappings are read-only. No raw data or weights are modified.

The cache directory must be an explicitly owned temporary directory. The
prototype creates a unique child directory and uses at most2GiB of private
files per instance. Retained mapped episodes count against the512MiB logical
LRU. `clear()` discards reusable entries and preserves original provenance pins.
Borrowed read-only views remain valid; files that Windows cannot yet delete
remain charged against the disk budget. Call `close()` after releasing all
borrowed episode/array views. Cleanup refuses outstanding views and can be
retried after release. It never invalidates live arrays or deletes raw inputs.

Before integration, define selector success/failure cleanup, multiple-instance
aggregate disk budgeting and interrupted-worker cleanup in the owned guard.
Do not register an unbounded global cache. Keep caller-owned writable batches,
source-only isolation, exact trial order/precision and tamper detection.
Coordinate frozen-file ownership before any production edit. Any changed
canonical implementation/test/configuration requires fresh matching quality
and source-bound prerequisites. Further real training needs a reviewed recorder
recovery plan; no third attempt is available in the spent case ledger.

## Reproducing the local diagnostic

The locally saved operational harness is
`runs/coordination/cache_performance_20261008_v1`. It contains the no-fit traces,
fixture adapter,180/240-second private Job guards and native guard with30-second
cleanup reserve. The private Job adapter is separately pinned to historical
operational bytes. These runtime receipts, inputs and harness files are excluded
from Git; this recipe alone is not a self-contained execution release.

Use fresh attempt directories, settled source/operation/runtime pins and actual
startup10GiB/active4GiB RAM, disk20GiB floors. Preserve6GiB process/7.5GiB Job
caps. The shared pause file is polled during guarded execution. The original
case480/520/600-second limits and protocol are unchanged.

- [Actual original100-load trace](../../../runs/coordination/cache_performance_20261008_v1/original_lru_001/result.json)
- [Actual23-check fixture result](../../../runs/coordination/cache_performance_20261008_v1/disk_fixture_002/result.json)
- [Actual150-load prototype trace](../../../runs/coordination/cache_performance_20261008_v1/disk_roster_001/result.json)
- [145-check root milestone review](../../../runs/coordination/cache_performance_20261008_v1/cache_performance_root_review_001.json)
- [Pinned encoder forward diagnostic](../../../runs/coordination/cache_performance_20261008_v1/encoder_forward_001/result.json)

## Bounded frozen-feature reuse

The [earlier feature prototype](frozen_feature_cache_v2.py) has exact executed
SHA-256 `fcbb966e883725e9a4e0000aac7ced05695aec1fb19541e8c1695d56f372e3e6`.
It retains detached cls-token features in a32MiB LRU while executing the live
classifier head each time. Head gradients and updates still run normally.
Activation must be limited to an explicit source-selection scope; deactivate
and clear on both success and failure before any selected-model use.

Eligibility requires frozen float32 CPU eval-mode backbones, contiguous inputs
without gradients, no backbone hooks, no CPU autocast and no inference mode.
Trainable/full/LoRA backbones bypass. Keys include the explicit pinned recipe,
exact backbone state, every module's forward-function identity, channel order,
input bytes/shape and numerical execution settings. Normal in-place parameter/
buffer changes invalidate the cached state through PyTorch version counters.
Arbitrary `.data` mutation and arbitrary non-tensor architecture mutations are
unsupported; retain the original final frozen-state validation. This is a
pinned-recipe experiment, not a general cache for arbitrary models.

The final guarded fixture ran35 checks:15 existing input/selector checks,
8 file-store checks and12 feature checks. Exact original-versus-cached linear,
full and LoRA selector model/history/evidence/RNG comparisons passed, along with
head losses/gradients/updates, deepcopy reuse after `.eval()`, state and forward
invalidation, input keys, budgets, unsupported-mode bypasses, cleanup after an
injected selection failure and original forward behavior after selection returns.
The first copy-reuse check failed because two custom copied layout modules were
in training mode; production's copy-then-`.eval()` route resolves that condition.
A later new test used the wrong result field and was corrected. All failed
receipts and exact worker/prototype versions remain preserved. The intermediate
33-test pass has a stale `new_feature_tests=8` field; the final35-test receipt
correctly reports12. No historical receipt was rewritten.

The pinned real source subject02 no-fit diagnostic measured:

| Batch | Original forward mean | Feature hit mean | First copied-model reuse |
|---|---:|---:|---:|
| 2 | 81.337ms | 1.269ms | 12.445ms |
| 8 | 353.340ms | 2.068ms | 13.003ms |

Both first misses and22 subsequent hits/copy reuses produced bitwise original
logits. Retained features totaled8,000 bytes; model state and caller RNG were
unchanged. The feature namespace was cleared/deactivated and private source
files removed. Whole-model state hashing took about12ms per call. No optimizer,
training, target inputs, accuracy or recorder claim occurred. These sampled
timings do not guarantee a complete selector within the480-second case deadline.
Native execution completed in22.628s under the unchanged guarded limits.

The169-check root self-review accepts diagnostic and physical-release evidence,
not independent case approval. Canonical source remains `b7452847` /431 files;
the accepted canonical quality receipt was not rerun and does not certify these
separately tested operational files. Next is explicit operational scope lifetime,
progress instrumentation and interrupted-worker cleanup, before any production
ownership/integration decision or reviewed recorder recovery plan.

- [Actual35-check fixture result](../../../runs/coordination/cache_performance_20261008_v1/feature_fixture_004/result.json)
- [Pinned real source feature measurement](../../../runs/coordination/cache_performance_20261008_v1/feature_forward_001/result.json)
- [169-check root self-review](../../../runs/coordination/cache_performance_20261008_v1/feature_performance_root_review_001.json)

## Source-scope adapter and interrupted-worker cleanup

The current [feature code](frozen_feature_cache.py), SHA-256
`f55fa5be0c78a46ca0223cc51a01cb71ec0dd8a067af6ba0ec83045855dc5d93`, also
bypasses global PyTorch hooks and local backward pre-hooks. Its36-check fixture
verified callback counts as well as the earlier exact equivalence checks.
The hardened pinned real source-only check measured76.688ms original/1.177ms
cached for batch2 and339.275ms/2.069ms for batch8. These are a separate later
measurement; both sets of receipts remain unchanged.

The [one-use selector adapter](source_selection_cache_scope.py), SHA-256
`b5ac2391522a65ed8499a368af8fd62ba9b2dfec832d4484ad710d44ef1b5cca`,
temporarily replaces only owned instance attributes. It preserves existing
input provenance pins and original selection/SGD/evidence routines, caps the
resident input cache at512MiB within the scope, then restores the old limit.
It writes sequenced fit/fold start/completion events outside scientific evidence.
On return it restores the original input cache/methods and removes feature
wrappers from both initialization and selected source model. A failed fit's
traceback can retain a borrowed mapping; its original exception is preserved,
cleanup is marked deferred, and the registered directory remains for the guard.
Progress-sink failure also restores the owned instance state.

The [owned cleanup utility](owned_cache_cleanup.py), SHA-256
`66d44ab072280c48327674ecfa5c2ac709253cc7da4a90ba809c9665bbea29f7`,
registers one exact private directory under an owned attempt. After the owned
Job is physically empty/closed, parent cleanup verifies the registry/worker,
directory identities, absence of aliases/reparse points, permitted flat file
names and aggregate2GiB budget before deleting any cache file. It hashes each
file and removes only those files and their empty registered directory.
Unknown content, nested directories, changed identity, traversal and excess
bytes refuse cleanup. Input data, receipts and outside files are preserved.
Registration/cleanup receipts stay on disk. There is no recursive deletion.

Fifteen synthetic scope/cleanup checks passed, including exact linear/full/
LoRA evidence/model/RNG,7 completed fits/6 folds per complete fixture, sequenced
events, original-method restoration, injected failures and cleanup refusal
paths. Synthetic release flags in these utility tests are distinguished from
the separately executed Job interruption fixtures.

Actual fixtures held a read-only mapped1,843,272-byte cache file until a20-second
deadline or an attempt-local stop sensor ended the worker. Both owned Jobs
closed; parent cleanup removed the exact hashed registered file and directory,
with outside sentinels unchanged. The first stop test raised before saving a
guard/cleanup receipt; that failure remains missing those receipts. A later
fresh named-Job and known-PID absence proof allowed separate cache recovery.
The fixed repeat catches supervision errors, saves their chain and actual stop
reason, then runs registered cleanup after Job release. It preserves candidate
failure status. The local stop fixture never writes the peer's pause file.

The160-check root self-review accepts engineering/release evidence only. The
source remains `b7452847` /431 files and execution Git was clean `1f793cf`.
Neither production integration, another case attempt nor a scientific gate is
admitted. The code copies here preserve executed bytes; their runtime harness
uses its own phase directory and fresh operation pins. Do not execute recipe
copies against historical output directories or treat this folder as a release.

- [Actual15-check source scope/cleanup result](../../../runs/coordination/cache_performance_20261008_v1/scope_fixture_002/result.json)
- [Actual36-check hardened feature result](../../../runs/coordination/cache_performance_20261008_v1/feature_fixture_005/result.json)
- [Actual hardened real source no-fit measurement](../../../runs/coordination/cache_performance_20261008_v1/feature_forward_002/result.json)
- [Actual deadline cleanup](../../../runs/coordination/cache_performance_20261008_v1/cache_deadline_fixture_001/cache_cleanup.json)
- [Actual fixed local-stop guard](../../../runs/coordination/cache_performance_20261008_v1/cache_local_stop_fixture_002/guard.json)
- [Separate failed-stop scope recovery](../../../runs/coordination/cache_performance_20261008_v1/cache_local_stop_fixture_001/fresh_scope_absence_recovery.json)
- [160-check root self-review](../../../runs/coordination/cache_performance_20261008_v1/scope_interruption_root_review_001.json)

## Partial full-query trace and 10 October recovery

Five bounded groups completed25 non-target subjects and4078 query trials:
510 distinct batches,510 feature misses and1020 warm hits, with no evictions.
Every original/cold/warm query output was bitwise equal. Reversed subject/batch
order through a copied model reused the same features; repeated ordered passes
had identical trial/logit hashes. Original forwards totaled210.3179s, cold
feature forwards210.3504s and two warm passes2.6917s. Disjoint retained features
totaled3,262,400 bytes and the maximum measured Job peak was2.901GiB.

The223-check root self-review on10October accepts these25 source-only diagnostic
subjects and their recorded scope release. It does not accept full51 coverage,
a complete selector, accuracy or a single full-roster cache. Group6 was
interrupted after partial cold progress, with no terminal native/guard/result
receipt. Those missing receipts remain missing. A fresh named-Job absence proof
allowed separate recovery of204,808,000 registered private bytes, preserving
original inputs and all evidence. The interrupted attempt is still unaccepted.

The fresh resume maps group6 to `source_query_g06_a002` and groups7-11 to their
unused `a001` directories. Reused-result/operation/runtime pins, exact group
order, settled Git and actual resources are checked before execution. A source-
only validation mode checks the package without launching/importing a model.
The new progress stream allows concurrent reading. At the10October checkpoint
available RAM was about9.1-9.4GiB; model runs await the existing10GiB startup
floor while engineering Source work continues. The peer explicitly requested
no pause; its new Source021 scheduling authority is distinct from runtime.

Cold encoding was about as costly as original encoding on these batches.
Warm reuse gives a substantial measured reduction, but model fitting, support
adaptation, full-cohort data loading and integrity/state hashing still require
measurement. The remaining26 subjects and whole-case feasibility are unproven.
Do not reopen the spent case ledger or claim a480-second case result.

- [223-check partial query review](../../../runs/coordination/cache_performance_20261008_v1/source_query_partial_root_review_20261010_001.json)
- [Fresh interrupted-group absence proof](../../../runs/coordination/cache_performance_20261008_v1/source_query_g06_a001/fresh_scope_absence_20261010.json)
- [Separate private-cache recovery](../../../runs/coordination/cache_performance_20261008_v1/source_query_g06_a001/fresh_cache_recovery_20261010.json)
