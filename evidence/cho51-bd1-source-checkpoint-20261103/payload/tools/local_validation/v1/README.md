# Local validation v1: bounded supplied-data foundation

This directory implements only the I/O-free foundation of the independently
reviewed [local validation design](../../../docs/phase2/cho51_p3_local_validation_contract_20261029.md).
It contains no launcher, operational admission parser or Q/P/L/V/C supervisor.
Source review and separately admitted qualification remain required before any
execution, including these new unit cases. No tests have been executed by the
implementation author.

`records.py` checks strict UTF-8 JSON (duplicate keys, signed 64-bit integers,
finite floats, exact scalar types, depth32, 200,000 nodes, 32KiB strings and8MiB
encoded records). Canonical encoding is bounded. Windows paths are conservative
ASCII slash spellings; drive letters are uppercase. UNC, device, stream, dot,
8.3, reparse assertions, hardlink assertions and case/native-identity collisions
are refused. Path checking is lexical; supplied facts are never authenticated.

Closed foundation record schemas are defined by code, with no optional fields:

- `cho51_lv_native_identity_v1`: schema, volume_serial (16 lowercase hex),
  file_id (32 lowercase hex), volume_kind (`local_fixed`), filesystem (`NTFS` or
  `ReFS`). These are caller-supplied facts, not observed handles.
- `cho51_lv_file_descriptor_v1`: schema, path, native_identity, file_type
  (`regular`), reparse_point (exact false), link_count (exact integer1), bytes,
  sha256. `validate_file_descriptor` returns a defensive JSON copy.
- `cho51_lv_directory_descriptor_v1`: schema, path, native_identity, file_type
  (`directory`), reparse_point (exact false).
- `cho51_lv_observed_snapshot_v1`: schema, label, role (`source`, `runtime`,
  `package` or `metadata`), root, complete_enumeration (exact true), directories,
  files. Every ancestor from the drive root needs an ordinary directory fact.
  Entries must fit the declared root and have unique paths/native identities.
  `complete_enumeration` is an input assertion, never a completeness finding.

`preparation.py` joins initial/final snapshots and explicit required-input pins,
checks census membership/content/identity/facts and enforces25,000 files,
4GiB total,2GiB per file and depth32. Each role requires a nonempty snapshot.
Each whole supplied snapshot set also obeys the8MiB/200,000-node JSON bound;
the file caps do not relax the stricter record representation bounds.
It never expands a recipe, enumerates a directory, reads a package or infers
transitive closure. The output has `complete_manifest=false`,
`runtime_qualified=false`, `launch_authorized=false` and
`scientific_admission=false`. No positive values can be requested through its
API. Mutating returned data cannot promote another returned record.

`hash_supplied_stream(stream, expected_bytes, checkpoint)` reads from the supplied
stream's current position using at most64KiB requests, checks exact-True
checkpoints before and after every read, verifies length with an EOF probe and
hashes incrementally. It does not open, seek or close a stream. The adapter and
checkpoint are trusted supplied capabilities: they can perform I/O or block,
and this primitive provides no independent watchdog or retained native identity.
Do not supply project/data/runtime streams before separate operational admission.

The supplied collection verifier binds25 exact function tallies (39 mapping and
78 telemetry),117 unique full node IDs and an ordered canonical digest. Optional
`expected_order` binds a later roster to an accepted earlier one. The34 control
names match the design's successor roster, including the two local-window names;
all supplied values must be exact Boolean true. These checks do not collect,
import or run tests, authenticate producers or establish passing outcomes.

Output-only schemas (`cho51_lv_stream_digest_v1`, `cho51_lv_census_comparison_v1`,
`cho51_lv_preparation_proposal_v1`, `cho51_lv_supplied_roster_check_v1`,
`cho51_lv_supplied_control_check_v1`) describe only these pure calculations.
They are not operational receipts and have no deserializer granting authority.
Operational schemas and the complete control chain await a separately reviewed
supervisor implementation.

`test_foundation.py` supplies adversarial stdlib `unittest` source for this
foundation. It uses in-memory fixtures and streams, with separate cases for
JSON/type/bound attacks, Windows aliases, identity/ancestry facts, census drift,
required-pin joins, aggregate refusal, chunk/checkpoint contracts and supplied
117/34 roster errors. These cases are neither the117 candidates nor the34
successor controls, and do not complete the original48-case matrix.

Future work includes real native retained handles/read sharing, bounded
enumeration and directory resampling, complete dependency/loader closure and
platform trust qualification, admission/claim/Job ownership/watchdogs/resources,
guard installation, physical JUnit/phase reports, authenticated result handoff,
caller-return evidence, independent actual review and closeout. None is supplied
or certified here. Historical custody remains UNRESOLVED, attempts004/005/006
retain their existing dispositions and scientific cells remain0/1020.
