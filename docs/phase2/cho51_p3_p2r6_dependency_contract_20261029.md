# P2 revision6 occurrence-preserving PE metadata observation

29 October2026. Source-only successor; independent review, fresh Q6/P6 pins,
admissions, actual results and Root adoption remain separate gates. All frozen
sources/attempts are unchanged. The [local validation contract](cho51_p3_local_validation_contract_20261029.md),
[P2 contract](cho51_p3_p2_dependency_contract_20261029.md), strict transport,
[revision4 performance contract](cho51_p3_p2r4_dependency_contract_20261029.md)
and [revision5 API-host contract](cho51_p3_p2r5_dependency_contract_20261029.md)
retain their substantive guards and trust boundaries.

P5 operation `a5578f8d-53d5-47bf-8c75-c360e886c4c0` is consumed with
`FAILED_P2_P_CONSUMED_OWNED_CLOSED`, exit1 and accepted new owned closure. It
refused `duplicate import descriptor`; physical-map and final-full-verification
acceptance remain false. Its actual review, Root disposition and static PE
descriptor diagnosis are required pins in both new source rosters. Neither
this implementation nor those partial artifacts replay/accept that attempt.

The file-only diagnosis inspected bounded PE metadata ranges for888 selected
paths without loading images. It found two normal-import tables with repeated
`kernel32.dll` entries: `hf_xet/hf_xet.pyd` at descriptor indices0/15 in a25-row
table, and `safetensors/_safetensors_rust.pyd` at indices1/4 in a10-row table.
Fresh64KiB stream hashes of those two images match the saved P5 pins. The
independent metadata sweep reported no other refusal in its bounded header,
range, RVA/name and termination checks. This is a scoped static observation,
not execution of the project parser, whole-map freshness, loader/ABI acceptance
or proof that every future native edge will resolve.

Repeated DLL names identify repeated table occurrences, not by themselves a
malformed range, absent terminator or invalid name. Different descriptor rows
can refer to the same module while carrying distinct thunk/other fields. R6
therefore removes only the name-uniqueness assumption. It does not ignore a
descriptor or collapse its evidence. `pe.imports` now emits version2 metadata:
normal/delay name arrays in original descriptor order, including repeats, plus
each occurrence's table kind, index, descriptor RVA, name RVA, normalized name
and exact raw descriptor bytes as hex. All source bytes stay pinned/retained.

Every existing bound and structural refusal remains: exact original-handle
range reads,64KiB read limit, file/header/optional-header/section bounds,
supported architecture/magic, unambiguous backed RVA mapping, bounded ASCII
basename with allowed suffix, at most4096 descriptors per table, zero-row
termination within the declared directory and RVA-form delay descriptors.
A repeated row with a bad name RVA, unsupported delay flags, missing zero
terminator or other malformed structure still refuses. No repeated name grants
an exemption from any of those checks.

Physical resolution remains one question per normalized basename. The version2
edge explicitly records every normal/delay table index and its occurrence
count; its unique-basename grouping is no longer a silent loss of multiplicity.
This also accepts existing synthetic observation dictionaries containing only
the two name arrays, deriving their occurrence positions from those arrays.
Explicit platform/API trust, fresh used-platform presence, selected physical
candidates, unresolved-edge refusal and ambiguous-search limitations remain.
No platform image, API name or host is added, and no loader/ABI claim follows.

Occurrence-bearing pages remain subject to the unchanged8MiB/200,000-node
record and64MiB/256-output caps. PE and edge batches flush before conservative
byte/node packing thresholds, without deleting occurrence rows or enlarging
caps. Individual rows and final pages still pass the exact bounded serializer;
an unrepresentable row/output set refuses. PE aggregate occurrence accounting
still counts every name against100,000, including repeated descriptors. Parser
refusals now identify the exact importer, retaining the original cause. The
bounded stdout receipt carries a separate `failed_importer` field, copied from
the validated pinned absolute path (existing4096-character lexical bound).
That field is null for other errors. It is independent of the unchanged
768-character human error-message truncation, so a valid long importer path is
not lost. The existing1MiB stream and all record/output caps remain unchanged.
An existing Q method checks a >768-character canonical importer through the
same helper and outer formatter; the192-method roster is unchanged.

Existing Q methods are expanded with repeated normal/delay descriptor fixtures,
ordered/raw occurrence evidence, explicit edge multiplicity and repeated-table
malformed/unterminated cases. No method is added: the proposed roster stays192
under the unchanged192 cap, with eight UTC and two native fault controls subject
to fresh execution/review. The sources have not been imported, compiled or
tested by this author. Static metadata diagnosis alone does not qualify them.

All R4 guard/performance mechanics remain, including fresh stop/ancestor/leaf
checks with lexical-only caching, original retained inputs, provisional pages,
one mandatory full original-byte/identity and initial/final census check after
PE/result publication, and bounded original-handle output handoff and closure.
Q90/60/5 seconds and512/768MiB, P300/240/5 seconds and4096/5120MiB,4GiB
available RAM/20GiB disk, one thread, hidden GPUs and every physical/JSON/output
cap are unchanged. A new operation can still refuse on another unqualified
native dependency; the metadata sweep creates no implicit portability grant.

The117 candidate tests/34 controls remain unexecuted. L/V/C, Git execution,
native search, ABI and loaded-resource/origin qualification remain separate.
Historical custody remains UNRESOLVED; P3 closure remains unproved, Q1 unproved,
004 consumed,005 held,006 unadmitted, scientific cells0/1020 and final freeze
unsigned. No old failure, cleanup uncertainty or retry permission is rewritten.
