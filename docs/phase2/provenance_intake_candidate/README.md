# Cohort metadata inspection candidate

## Current metadata checker: synthetic qualification passed, 10 October UTC

The separate standard-library intake checker passed26 synthetic cases and
both CLI paths in an actual guarded metadata-only Job. Native0.9254373s,
peak aggregate40,886,272bytes; root's57-check execution self-review passed.
Startup10/active4RAM/disk20GiB and process2.25/Job2.5GiB,60/90s remained.
All14 owned Job names freshly absent, handles/awake scope released.

The candidate enforces1MiB, strict JSON/checkpoint/approval/attempt boundaries
and reports incomplete or populated-but-unverified declarations. It does not
authenticate authors, read cited evidence or infer verified cohort overlap.
No actual cohort response, model work, recorder action or scientific admission
occurred. All seven owner decisions and Gate A/freeze remain unsigned; the
request stays unsent and both original attempts spent, zero remaining.
Source3114ec43/432 and existing quality4eb4d556 remain; old full-suite receipts
do not certify the new documentation namespace. Pro2 requests no pause.

See the [executed metadata qualification](../cohort_intake_completeness_20261010.md). Older sections retain their dates/scopes.


## Completeness refinement: prepared, execution pending

The current refinement also reports absent target mappings/exposure declarations,
per-dataset identifiers and evidence claim lists. Three new regression cases are
prepared. The older 23-case receipt below qualifies its recorded earlier bytes;
the changed candidate needs its own fresh guarded qualification.

## Current metadata checker: synthetic qualification passed, 10 October UTC

The separate standard-library intake checker passed23 synthetic cases and
both CLI paths in an actual guarded metadata-only Job. Native1.1905499s,
peak aggregate40,214,528bytes; root's56-check execution self-review passed.
Startup10/active4RAM/disk20GiB and process2.25/Job2.5GiB,60/90s remained.
All13 owned Job names freshly absent, handles/awake scope released.

The candidate enforces1MiB, strict JSON/checkpoint/approval/attempt boundaries
and reports incomplete or populated-but-unverified declarations. It does not
authenticate authors, read cited evidence or infer verified cohort overlap.
No actual cohort response, model work, recorder action or scientific admission
occurred. All seven owner decisions and Gate A/freeze remain unsigned; the
request stays unsent and both original attempts spent, zero remaining.
Source3114ec43/432 and existing quality4eb4d556 remain; old full-suite receipts
do not certify the new documentation namespace. Pro2 requests no pause.

See the [executed metadata qualification](../cohort_intake_checker_20261010.md). Older sections retain their dates/scopes.


This standard-library candidate checks the format of a future cohort declaration
against the pinned blank reference template. It is outside the canonical scientific
implementation and is not a cohort authenticator, overlap verifier or case worker.
At preparation, execution qualification is pending; no passing test is claimed.

It reads at most 1 MiB from one regular local metadata file. Duplicate keys,
non-finite/overflow numbers, excessive depth/text, unexpected fields, changed
checkpoint identities and altered scientific/attempt flags are rejected. It
never opens referenced evidence, follows URLs, imports model libraries or writes
to the recorder. Nulls and empty lists retain an unknown finding.

The successful report distinguishes incomplete declarations from populated but
unverified declarations. Both always report unknown target overlap, false
scientific verification/admission and zero original case attempts remaining.
Claimant identity, complete-coverage statements, inventories and checksums remain
submitted claims, even when every required declaration is present.

Use the candidate only after its separate guarded synthetic qualification is
reviewed. An explicit invocation will read the nominated local JSON file and print
a metadata report:

```powershell
python -I -S -B docs/phase2/provenance_intake_candidate/inspect_cohort.py --input <metadata.json>
```

The reference is a byte-for-byte copy of the
[blank template](../checkpoint_cohort_evidence_template_20261010.json), pinned at
SHA-256 `d62cb5450578fa8ea0e90856cb314eb183db93f401a64e1aae5d28f4f536ceab`.
Its local `.gitattributes` retains LF bytes across checkouts. Submitted bodies
may use valid UTF-8 JSON whitespace; their exact raw SHA-256 is reported.

For a populated declaration, dataset entries require `dataset`, `version`,
`identifier_namespace`, string lists `subject_identifiers`/`recording_identifiers`
and `coverage_statement`. Namespace records require `name`, `dataset`, `version`
and `definition`; splits require `dataset`, `version`, `name`, `definition`.
Exclusion records require `dataset`, `version`, `scope`, `statement` and
`evidence_reference`. Mapping records require `training_identifier`,
`evaluation_identifier` and `mapping_evidence_reference`. Evidence records require
`reference`, `description`, `source_date_utc`, nullable `sha256` and string-list
`supported_claims`. All are declarations; no referenced bytes are retrieved.
Prepared context, checkpoint identity, target names and review/attempt flags in
the reference are read-only. A received declaration needs a separate custody and
review receipt rather than changing those preparer flags.

The [unsigned review contract](../checkpoint_cohort_review_contract_20261010.md)
still controls the evidence distinction. The [owner packet](../cho_owner_decision_packet_20261010.md)
remains unsigned and the provenance request unsent. No parser-format success
changes those gates or admits the exhausted original LaBraM case.
