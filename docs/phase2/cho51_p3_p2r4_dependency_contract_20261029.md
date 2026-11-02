# P2 revision4 bounded performance successor

29 October2026. Proposed implementation-specific successor, not operational
admission or a successful runtime result. The [local validation contract](cho51_p3_local_validation_contract_20261029.md),
[P2 contract](cho51_p3_p2_dependency_contract_20261029.md) and
[revision3 transport contract](cho51_p3_p2r3_dependency_contract_20261029.md)
retain their substantive guards and trust boundaries. Frozen sources, spent
attempts and original receipts remain unchanged.

Q3 operation `6eea128b-74d5-48a4-b685-880b3ed1addf` has accepted184-method
qualification, eight timestamp controls and two native fault controls. P3
operation `f8ed9509-0bd6-40f0-a66e-ab4ec6fa7b02` failed its original240-second
work deadline. It retained39 partial outputs including a physical index; those
artifacts do not constitute acceptance. Its Root status is
`FAILED_P2_P_CONSUMED_DEADLINE_CLOSURE_UNPROVED`: the new owned lifecycle is
unproved, physical map and native PE closure unaccepted, and retry false. This
successor pins the P3 actual review and Root disposition as context, never as a
grant. It does not convert that operation or historical custody into closure.

The successor removes three kinds of repeated work without extending any clock,
resource allowance, selected scope or effect permission:

1. P4 absence checks cache only a bounded tuple of lexical ancestor strings.
   Every invocation still makes a fresh no-follow `os.stat` call for each
   ancestor and then the leaf. Every ancestor must be a directory without
   reparse/device attributes. Only an actual missing-leaf exception establishes
   absence; permissions, unknown errors, missing/non-directory ancestors and a
   present leaf refuse. No metadata, absence, stop decision or resource sample
   is cached. This replaces the old per-ancestor lstat-plus-following-is_dir
   pair with one no-follow query. The existing call sites and independent guard
   sample cadence/freshness checks remain unchanged.
2. The new retained reader calls `retain_directory` once for the file's immediate
   parent. That existing method already traverses and retains every ancestor
   under the same native identity/type/volume/final-path checks. The old outer
   loop invoked that complete prefix traversal separately for every ancestor.
   Original directory handles, final directory verification and the file's
   before/after hash facts remain unchanged. Extended transport, single-link,
   reparse/device, alias and local NTFS guards stay in force.
3. `prepare` retains and initially hashes every exact selected input and captures
   the complete initial census, publishing bounded provisional pages/index.
   It no longer performs two complete final checks itself. Its saved index is
   `PROVISIONAL_PHYSICAL_MAP_REQUIRES_FINAL_VERIFICATION`, with final verification
   and every acceptance/launch/scientific flag false. The supervisor removes
   its earlier duplicate full pass and mandates one complete `Prepared.verify`
   **after** PE observation and result publication, while every original input
   and output handle remains live. That pass rehashes every retained input
   through its original handle, checks native identities/facts, re-enumerates
   the complete bounded census/absences and verifies original output handles.
   Missing/added/changed selected or unselected members still refuse. Each
   explicit call to `Prepared.verify` repeats the full work; no verification
   result is memoized.

The saved result and provisional index remain pre-verification publications.
Neither can establish completion on its own. Only a successful final pass,
output verification, guarded original-handle closure, bounded stdout handoff
and genuine caller return can support later independent actual review. The
stdout field `final_full_input_verification_completed_before_release` records
that scoped provisional observer outcome; it does not rewrite saved pending
flags or adopt a physical map. Failure at any subsequent step prevents caller
acceptance. The parent continues authenticating outputs by original native
identities and byte pins under the same handoff contract.

The proposed Q4 roster is191 methods: the184 predecessor methods plus four
injected-stat tests proving fresh ancestor/leaf checks after cache hits, reparse
or non-directory refusal and unknown/present-leaf refusal, and three native
JSON cases that add selected/unselected members or change an optional absence
after provisional preparation and require final verification to fail. No global
os/Path monkeypatch is used. The30 reader methods target the new reader fork;
the Q bootstrap short-control reader remains the predecessor implementation.
Q source pins bind the new sources and the P3 failure records. A source roster
is not a passing test report; separate Q4 qualification and P4 admission are
required. These version names refer to the dependency Q4 phase, not the older
Q4 reader qualification.

All original limits remain: Q90/60/5 seconds and512/768MiB; P300/240/5 seconds
and4096/5120MiB, available RAM4GiB and disk20GiB, one thread, hidden GPUs,
original caller UTC/QPC origins, hard deadlines, stop control, sampling
freshness, process/Job/pipe ownership,64KiB chunks,25,000 files/4GiB aggregate/
2GiB per file/depth32 and bounded JSON/pages/outputs. No cached resource result,
later clock origin, relaxed sampling, larger limit or early acceptance is
introduced. The changed timing/performance has not been measured by this work;
an admitted successor can still refuse its unchanged deadlines.

The117 candidate tests/34 controls remain unexecuted. L/V/C, Git execution,
native search, ABI and loaded-resource/origin qualification remain separate.
Historical custody stays UNRESOLVED, Q1 cause/cleanup unproved,004 consumed,
005 held,006 unadmitted, scientific cells0/1020 and final freeze unsigned.
The P3 cleanup uncertainty remains explicit and is not repaired here.
