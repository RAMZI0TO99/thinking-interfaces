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
