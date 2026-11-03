# Real case/suite boundary: finite failure-domain contract

The independent supplied verifier is implementable without a real executor.
A production case/suite boundary is not yet implementable under accepted runtime
authority. The following obligations are explicit blockers, not tests passed by
successful supplied fixtures. Frozen sources and original failure receipts remain.

## Audited source boundaries

Source references use repository files or the four external reference-only
stdlib pins in the frozen CM2 phase-edges inventory. They are not runtime pins.

| Boundary | Concrete source | Required closure before real admission |
| --- | --- | --- |
| Body/setup SkipTest | Retained unittest/case.py:61-63 calls str(e) before addSkip | New nonformatting case executor using original exception identity; preserve skip/cleanup/stop semantics; poison-string qualification |
| Fixture SkipTest / ErrorHolder | Retained unittest/suite.py:238-245 builds a description and formats exception | Direct bounded owner/phase/slot route; no _ErrorHolder or string-derived owner; preserve actual callback cardinality |
| Nested subtests | Retained case.py:521-547 restores outcome and propagates _ShouldStop | Explicit finite entry/unwind semantics and source mapping, or pre-admission refusal; no flattening or invented enclosing SUBPASS |
| Per-case lifecycle | Retained case.py:609-687, including doCleanups and class cleanup exception collection | Preserve setup/body/teardown/LIFO cleanup/duration/primary outcome/stop order, decorated skip and setup-failure variants |
| Module cleanup | Retained case.py:135-145 raises only the first collected exception | Preserve the real reference callback semantics; distinguish emitted callbacks from underlying cleanup failures; no claim every underlying failure is an emitted event |
| Assertion and expected-exception failure | Retained case.py:729-748 and assertion-specific repr/diff/assertRaises paths | Finite reachable operand/type/message/size domains and all intermediate effects, including wrong/no-exception paths |
| Mock diagnostics | Selected project tests use unittest.mock helpers | Inventory every reached failure formatter, operand and callback; absence on the normal path is insufficient |
| Project helper exception formatting | sc1/native_backend.py:125,134,139,165; sc1/publisher.py:291 | Formatting occurs before slicing; bound the complete input/intermediate/effect domain or use a separately reviewed successor preserving obligations |
| Parser/path error conversion | hb1/common.py:absolute_path wraps its predecessor refusal with str(error) | Bound exact predecessor error source and domain; do not call a general wrapper nonformatting merely because this API uses primitive inputs |
| Interpreter/bootstrap/native errors | Pre-entry, loader/compiler, uncaught exception and outer tool paths | Bound original raw/error/envelope production including cancellation; retain ownership/cleanup evidence |

Each reachable route needs an exact source pin and location, phase/owner, eligible
type identities and finite input lengths, exception and recursion bounds, maximum
intermediate allocations/encoded output, file/native/process effects, stop and
cleanup action, original evidence destination and adversarial qualification.
Unknown or open rows prevent real admission. Fixed messages in a test double
establish only that supplied fixture's scope. A post-format slice gives no bound
on allocation, raising/reentry or effects during __str__/__repr__ itself.

## Dispatcher equivalence and producer trust

No monkeypatch of frozen unittest/project classes and no fallback TextTestResult
or TextTestRunner. A versioned future dispatcher must be independently reviewed
against the exact retained reference semantics and qualified separately. It must
map original exceptions without arbitrary formatting; preserve setup omissions,
LIFO cleanup, every actual cleanup callback, special-outcome order, stopTest
finally behavior, failfast and later class/module fixture failures.

PASS remains provisional until method cleanup, restoration and final suite
completion. A module cleanup implementation that reports only one exception
must not silently become an all-exceptions reporter without an explicit semantic
amendment and roster/evidence review. A result override alone cannot implement
this boundary or prove assertion/helper domains.

Future original lifecycle evidence must distinguish actual method cleanup,
actual subcase entry/unwind, suite fixture completion, producer refusal (including
after footer), restoration and final source verification. CM2 carries none of
these complete witnesses. A separately reviewed versioned event/attestation
contract and exact existing-slot allocation are prerequisites; this design does
not assign new event meaning to PASS/END/FOOTER or authorize extra files.

Native guard/stop/clock/resource enforcement must remain outside tested mutable
globals and mocked surfaces. The tested interpreter cannot certify its own
original capture, parent census or complete closure. Native authority, code/trace
identity, fresh admission and independent actual review remain separate gates.

## Refusal and retained evidence

Unknown type/code/location, nested route, unbounded formatter, capture loss,
restoration drift, reentry, missing callback or swallowed producer refusal makes
the whole operation ineligible. Preserve original bounded prefix and attributed
failure; never fabricate a completed trace, case, suite, EOF or footer. Execute
only the original bounded owned cleanup, consume attempts after effects may have
occurred, and retain UNKNOWN custody where original proof is absent. No restart,
new UUID, deadline reset or successful model may erase that disposition.
