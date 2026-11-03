# Conditional report allocation and feasibility

This is a design reservation proposal, not a runnable parent map or a write
authorization. It extends the frozen CM1 report-only minimum30/17,711,104 bytes.
The existing full collection and event reservations carry versioned CM4 payloads
under a future separately reviewed operational mapping. Their caps remain1MiB
and2MiB; old artifacts are not rewritten. Extra tables, descriptor and terminal
have explicit reservations rather than hidden sidecars or borrowed closeout roles.

Every proposed ordinary path is relative to one fresh parent root
R = D:/Aenv/pro3/runs/coordination/cho51_p3_cm4_unadmitted/<parent UUID>.
This is an inert design namespace: do not create a runtime parent there. Each
ordinary reservation uses the parent transaction, publisher_role=null in the
parent map, with the writer named below. Distinct metadata UUID M owns exactly
the unchanged16 closeout roles at R/closeout/<role>_<M>.json, with exact HB1 caps.
The parent and metadata UUIDs must differ. A qualified successor path validator
is required; do not patch or bypass the frozen HB1 prefix validator.

| Relative path | Writer | Reserved bytes |
| --- | --- | ---: |
| caller/collection.json | collection adapter |1048576|
| caller/events.ndjson | event producer |2097152|
| caller/stdout.raw | external capture owner |1048576|
| caller/stderr.raw | external capture owner |1048576|
| caller/return.json | outer caller |65536|
| caller/journal.ndjson | outer caller |131072|
| caller/input-inventory.json | outer caller |4194304|
| caller/guard-closure.json | external guard owner |131072|
| caller/tables.json | fixed-table adapter |1048576|
| caller/evidence-join.json | outer join recorder after terminal closes |65536|
| supervisor/input-manifest.json | supervisor |4194304|
| supervisor/journal.ndjson | supervisor |131072|
| supervisor/command.json | supervisor |65536|
| supervisor/output-census.json | external census owner |131072|
| supervisor/loaded-code.json | external code observer |65536|
| supervisor/return-closure.json | supervisor |65536|
| supervisor/producer-terminal.json | external terminal observer |65536|
| closeout: unchanged16 named roles | Root fixed-slot publisher |3293184|

Thus report-only proposed minimum is33 files /18,890,752 reserved bytes:
caller10/10,878,976; supervisor7/4,718,592; closeout16/3,293,184. These allocations
fit their partition caps arithmetically, but do not enumerate native/bootstrap/
compiler/test effects, capture chunk metadata or failure artifacts. They do not
prove complete allocation or runtime feasibility. No actual file is allocated
here; documents and coordination records are source-phase metadata, not runtime
report reservations. All necessary additional runtime writes need exact reviewed
path/owner/transaction/cap before effects, with no borrowed C-export window.

Dependency direction is acyclic: fixed source/roster/table definitions and unused
authority precede collection/events; terminal pins closed events; descriptor pins
collection/events/tables/terminal; independent analysis pins descriptor and original
evidence. No event or terminal includes the later descriptor hash, no candidate
contains its own hash, and no source identity depends on a test's self hash.
Supplied hashes are integrity links, not original authority or completeness proof.

The frozen current normal callback mapping1096=280*3+254+2 contains no CM4
lifecycle. Under the explicit conditional assumptions of exactly280 ordinary
passing cases,254 flat subcase outcomes, one cleanup and one duration per case,
no extra fixture outcomes/traces, and four suite/restoration/input events, CM4
uses1096+560+508+4 = **2168 records /1,110,016 bytes at512 per record**.
Terminal is separately reserved64KiB, not a2169th event. This leaves1928 record
positions within4096 in that conditional scenario only. It is not an actual
output observation or proof of every failure/subcase/fixture route. The earlier
1096/1000/860 results retain their different wire/roster scopes.

Keep all original caps: global256 files/64MiB; fixtures160/32MiB; supervisor40/8MiB;
caller40/20MiB; closeout16/4MiB; per-file8MiB and all16 role caps. Charge unused,
failed, partial, temporary, copy and unexpected writes; complete original parent
census precedes any projection. Inner native fixture publication is not admitted;
its original32-file/4MiB combined and16 auxiliary/901120 limits remain unchanged.

Retain whole90/work60/cleanup5/hard65/child55 seconds; suite40/native12/fault2,
startup5; sample gap200ms/freshness250ms; process512MiB/Job768MiB; RAM4GiB/free
disk20GiB; one CPU/library thread, hidden GPUs, original stop and owned cleanup.
Child deadline remains min(T0+55,T0+60-F-M); final-work F and margin M remain
unproved. No outside-clock compilation/collection or resumed reviewer resets T0.

Raw stdout/stderr each remain1MiB; raw_tool_return1MiB and external_return64KiB.
The1MiB-control-byte counterexample still needs6,291,456 escaped payload bytes
before envelopes. Cross-stream order means external observed merge order only;
EOF/error/pipe/tool closure remains distinct from quiet, exit or footer. Complete
capture, formatter/recursive effects, original lifecycle/observer/native custody,
finite asynchronous closeout, final reserves and peak memory remain
NOT_ESTABLISHED. No cap widening, truncation or complete-operation acceptance
follows from the report arithmetic. P and every original execution hold remain.
