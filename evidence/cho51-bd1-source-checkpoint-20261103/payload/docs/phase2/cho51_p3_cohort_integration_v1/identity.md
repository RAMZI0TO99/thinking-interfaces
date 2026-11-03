# Cohort, census, fixture target and expected context

## Three distinct identity domains

Q360 is exactly cohort.json, copied from CM5's ordered selected_ids, whose
LF-terminated ASCII identity digest is
321e076ba18c3bb413d5c7f70f34b03e3780bce1712e5ff4f03fd7f6e4b60a08.
The canonical manifest has closed fields count, ids, ids_sha256, name, schema;
name=CM6-Q360-20261103 and schema=cho51_cm6_qualification_cohort_v1.
Its raw pin is36161 bytes /
e654b35a3c8a969d60d8f602f75f967bdf0711b4fb71491d0d0094673ac40dde.
The raw-file pin and the identity-list digest are different domains.

C initially equals the complete frozen CM5 source roster876/38. Its identity
digest is f6a3081e3becb650c5485cd70121a644ebdcebde278499fe85a385764b317739.
Future C contains every baseline identity and exact baseline test-module pin,
plus explicitly reviewed additions in new modules; frozen predecessor files
cannot be edited to fit a new collection. Q is a subset of C, not its prefix.
The baseline516 C-minus-Q identities retain all their original obligations.
Every new test outside Q is held with explicit unqualified debt. Held scheduling
is distinct from a skipped/deselected eligibility flag. No obligation is removed
by leaving it outside the cohort.

H has the frozen CM4 full836/36 and selected320, with original literal digests
and module pins. Existing CM5 commands/CM4 parsers remain H-local. New CM6 event
case i means Q.ids[i],0<=i<Q.count; it never means C.ids[i] or H.ids[i]. Compute
explicit identity joins Q->C and H->C after full collection checks. Adding a held
identity before an existing name changes C ordinals, but cannot change Q ordinals.
No implicit integer conversion, relabelled schema or rewritten historical pin.

## Canonical expected inputs

All new raw JSON is exact immutable bytes, ASCII with canonical sorted keys,
compact comma/colon separators, ensure_ascii=True and one final LF. Reject
duplicate/unknown keys, bool-as-integer, malformed UTF-8/JSON, noncanonical bytes,
unbounded strings/containers/depth/nodes or inconsistent counts before views.
Full method IDs are safe dotted ASCII identifiers up to192 characters (the
current maximum is153; Q maximum139), not the old128-character token shortcut.
The last two components are class and test_ method. Module names are at most128
characters; components use [A-Za-z_][A-Za-z0-9_]*. This is name integrity, not
original code-object identity. Context names and hashes never contain free text.

Expected cohort pin P_Q and descriptor pin P_D are separate exact (bytes,sha256)
tuples supplied by the caller independently of observations. Check positive
bounded integer sizes and64 lowercase hexadecimal hashes, then actual raw pins.
Their supplied values carry no authority. An operational caller must obtain them
from an independently accepted source/admission boundary, never from collection,
tables, events, terminal, output join or a caller-created Facts object.

Descriptor D is closed cho51_cm6_expected_census_v1 with fields schema, cohort,
census, modules, tests, source_set, runtime_set, producer_set. Its contents:

- cohort: closed name,count,ids_sha256,bytes,sha256, exactly matching Q raw bytes.
- census: closed count,module_count,ids_sha256. Counts equal the exact lists.
- modules: ordered unique rows with module,bytes,sha256. Every named module owns
  at least one declared test; its exact row set equals the test-module set.
- tests: ordered unique rows with id,schedule,obligation. schedule is COHORT iff
  id is in Q, otherwise HELD. COHORT obligation is null. HELD obligation is closed
  kind,id_sha256; kind is BASELINE_HELD for the original516, NEW_TEST_UNQUALIFIED
  for added tests, and id_sha256 is SHA256 of the exact ASCII id without LF.
- source_set,runtime_set,producer_set: lowercase64 hashes of separately pinned
  input manifests. Shape alone does not verify original source/runtime custody.

C IDs and module rows are ordinal ASCII sorted. C count876..4096; test modules
38..256; exact Q360 for the adopted profile. Every baseline876 identity and38
module pins must remain present and byte-identical. All added test ownership,
module pins and debt rows must be explicit before observing a report. D's ID
digest is SHA256 of ordered ids joined with LF plus final LF, not its raw hash.
Per-input byte/node caps can refuse a descriptor even when these counts fit.
Non-test source/dependency closure is separate from this test-module census.

The mechanical cohort format permits1..360 distinct sorted IDs to avoid a new
codec for each future finite supplemental cohort. Only exact Q360 is adopted in
this design. A future supplemental profile must independently define its membership,
baseline-held/deferred accounting and budgets; those semantics are not admitted
by accepting a generic count or a supplied matching hash. An unsupported profile
must refuse the integration policy check before collection or producer entry.

## Acyclic context binding

First verify Q and D against independently expected P_Q/P_D and semantic joins.
K is SHA256 of canonical bytes of this closed object:
{domain:'cho51_cm6_context_v1', operation:O, cohort:Q.ids_sha256,
census:D.census.ids_sha256, descriptor:{bytes:P_D.bytes,sha256:P_D.sha256}}.
O is an externally expected canonical nonzero lowercase UUID. All downstream
raw inputs carry O and K; none can declare a replacement expected pin.

Input manifests and Q precede D. D contains no own hash, K, event/terminal/output
hash or output join pin. The source_set manifest may pin Q and code/tests, but
must exclude D, later reports and any manifest/review that depends on D. The
external admission/source candidate pins D separately. K then precedes collection,
tables and events; terminal pins the exact constructor inputs and closed events;
the final output join pins all raw inputs. No source embeds its own hash, no test
embeds its own module pin, and no output is used to derive its own expectation.
Every source/runtime/producer manifest still needs its original complete join;
supplied hash equality never supplies that missing authority.
