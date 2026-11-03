# Explicit supplied lifecycle event grammar

Proposed verify_events(raw, operation, *, codes, fixtures, check) independently
parses cho51_cm4_event_v1. It accepts exact bytes, canonical ASCII/LF JSON lines,
the same closed thirteen fields as CM2: schema,seq,op,roster,event,case,sub,
fixture,kind,code,line,count,prefix. Primitive types are exact. Every row binds
the same operation and current full digest; selection is fixed by that registry
and the joined collection/descriptor. CM2/CM3 validators remain unchanged.

Keep 4096 total records, 512 bytes per line including LF, 2,097,152 stream bytes,
4095 nonfooter records / 2,096,640 nonfooter bytes and 128 frames per exception
group. Validate byte/record bounds before growth and retain a footer reservation.
Seq starts at1 and is contiguous. HEADER is first with count280. FOOTER is last,
count equals all preceding rows and prefix hashes those exact prior bytes; the
whole-file digest is distinct. Unsupported/malformed/incomplete data refuses,
never fabricates a footer, lifecycle record or completed trace. Chunked hashing
must handle the full2MiB with bounded scratch and checkpoints.

CM2 event-specific nullability, exact owner checks, trace ordering and negative
semantics apply with current full ordinals/selection, except for the explicit
successor rules below. These are new semantics, not claims that CM2 emitted them.
Exception kinds remain ASSERT,EXCEPTION,SYSTEM_EXIT,KEYBOARD_INTERRUPT; NONE is
used for nonexception records. UNSUPPORTED/unknown kind refuses. FAIL/ERROR/
SUBFAIL/XFAIL require1..128 immediate TRACE rows; SKIP/XPASS use NONE/count0;
FIXTURE_ERROR follows the same exception/skip distinction. Trace rows have exact
table code/line, owner/kind and ordinal1..N. None of these assert original trace
completeness, exception identity or origin.

| New event | Fields differing from null (besides common fields and kind=NONE) | Required transition |
| --- | --- | --- |
| SUITE_OPEN | event only | Exactly after HEADER, once; no case/fixture before it |
| SUB_ENTER | case,sub | Active case, next per-case sub ordinal, no active subcase/primary/cleanup/global negative |
| SUB_EXIT | case,sub | Same active flat subcase, after exactly one SUBPASS or SUBFAIL and its entire trace group; close it |
| CLEANUP_DONE | case | Once after all declared subcases exit, before duration, PASS/XFAIL/XPASS and CASE_END; no further case failure or subcase afterward |
| DURATION | case,count | Once after CLEANUP_DONE; count exact integer0..9223372036854775807 in supplied units; before PASS/XFAIL/XPASS, but may follow SKIP/failure |
| SUITE_CLOSE | event only | Once, no active case/subcase/trace; either all280 ended or a negative event explains the exact unstarted suffix |
| RESTORED | event only | Exactly after SUITE_CLOSE; declared restoration claim, no native authority |
| INPUTS_VERIFIED | event only | Exactly after RESTORED; declared final-input claim, no native authority |

For every new event prefix is null; code,line,fixture are null; count is null
except DURATION; case/sub are null unless listed. SUITE_OPEN begins the body;
INPUTS_VERIFIED must be followed by FOOTER. No result/fixture/case activity follows
SUITE_CLOSE. Late activity in a producer must latch refusal and be reflected in
the separate terminal snapshot, even if no new bytes can be appended.

CASE_START selects exactly the next full ordinal with no active case or sticky
negative. SUBPASS/SUBFAIL now require an existing matching SUB_ENTER, not merely
the next number. No nested entry is supported. The first negative blocks every
new case/subcase; an already open failing subcase must finish its trace and exit,
then the existing case's cleanup/stop and required suite cleanup may complete.
CASE_END.count is the number of completed declared subcase triplets, all entered
subcases must have exited. A missing outcome or exit is incomplete/refused.

The active subcase interval is closed: immediately after SUB_ENTER only its
matching SUBPASS or SUBFAIL is legal, followed by exactly that outcome's required
TRACE group (none for SUBPASS), then immediately the matching SUB_EXIT. No parent
outcome, other lifecycle event, fixture callback, new entry or unrelated trace
may interpose anywhere in that interval. A duplicate outcome also refuses.
After SUB_EXIT the normal active-case rules resume, preserving any sticky
negative; the enclosing failed case may then emit its permitted cleanup failures.
An original route requiring a different interleaving remains unmapped/refused,
never silently reordered to make a supplied triplet fit.

PASS requires CLEANUP_DONE then DURATION and no negative, and is exactly once.
FAIL/ERROR may repeat before CLEANUP_DONE, including mixed cleanup failures after
SKIP. SKIP is a negative primary before cleanup; XFAIL/XPASS are negative primary
after CLEANUP_DONE and DURATION. No FAIL/ERROR after XFAIL/XPASS/PASS. A failed
subcase does not invent a primary FAIL. CASE_END requires cleanup and duration,
no open subcase/trace, and either a primary outcome or a recorded case negative.
No callback can clear a negative. Fixture error rows retain CM2 unique-slot and
setup-before-affected-start / teardown-or-cleanup-after-affected-start-or-negative
rules, outside a case and before SUITE_CLOSE. A late fixture failure can negate
an otherwise all-PASS run. All fixture traces must finish before closure.

CM4 deliberately requires a duration occurrence for every completed supplied
case; CM2 made it optional. It does not require a real duration float conversion
or interpret supplied units as native time. A real dispatcher route that omits
duration or method cleanup (including decorated skip) cannot fabricate these
events: it produces incomplete/refused evidence under this subset. Before real
admission all eligible original routes need explicit mapping or an independently
reviewed extension. Actual setup/body/teardown/LIFO cleanup semantics, nested
unwinding, module cleanup exception suppression and stopTest-finally are not
qualified by these declarations. No original obligation is removed by refusal.

An independent parser checks these transitions directly, without replaying a
producer or trusting Facts. Valid raw output yields only immutable declared
lifecycle facts, started/passed/ended/subcase counts, negative flag, exact unstarted
suffix and raw/prefix hashes. All280 PASS with closure is still provisional until
terminal join. A supplied CLEANUP_DONE/RESTORED/INPUTS_VERIFIED record is a checked
claim in this grammar, not proof of actual cleanup/restoration/source recheck.
Original subcase/fixture population, hidden callbacks and all native custody
remain unavailable even when every declared triplet is present.
