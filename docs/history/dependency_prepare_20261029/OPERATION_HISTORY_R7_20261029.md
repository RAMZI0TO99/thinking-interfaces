# Dependency preparation revision 7: retained history

29 October 2026. This is a historical record; use the
[current milestone](../../phase2/cho51_p3_dependency_preparation_20261029.md) for
the current gate. R7 added a Q-only supported Windows schema query for the exact
fourteen unresolved API names, a retained mapping-receipt contract and explicit
platform entries for cabinet, fontsub and mswsock. P remained file-only.

The 77-source proposal and 192-method roster passed independent static review.
The planned native query and controls were not established by that review.

| Operation | Outcome |
| --- | --- |
| Q7 `94fcfa0a-573b-48a0-8e9b-fb980170b157` | Empty exit 1 after 5.54 s; startup journal ended at assembly_loaded; no query or tests; cause and cleanup unproved |
| Q7 `6451d9c4-0c30-42fc-8a47-caa520b2043d` | Fresh unchanged admission; tool exit 1 after 3.12 s, caller 2.47 s; first exact schema query returned 0x80004001 (E_NOTIMPL) |

The latter operation produced timestamp controls and an emitted native helper,
but no mapping receipt or Python test dispatch. Caller file, journal and guard
closure were recorded. The native helper's exception path did not publish the
acquired module-reference release result, so that release remains unproved.
The independent disposition is
`FAILED_P2Q_CONSUMED_API_QUERY_NATIVE_RELEASE_UNPROVED`. All 77 source, 732 runtime,
169 compiler and 2,591 predecessor pins matched during actual review.

P7's prepared proposal of 20,406 files / 3,455,814,776 bytes was never admitted.
It received no completed P source/coverage review or actual observation. Its
proposal, pins and Root hold remain preserved in the matching P7 phase directory.
No Q7 qualification or P7 acceptance exists.

The next design uses counted references to already-resident modules, exact-name
lookups with no loading fallback, and diagnostics published after native cleanup
on both success and failure. Its support and results require separate review
and fresh admission; it does not repair either Q7 attempt.

Records are under `runs/coordination/cho51_p3_dependency_prepare_20261029_q7`
and `..._p7`. The last accepted dependency suite remains Q6's 192 methods. The
117 candidate cases and 34 successor controls remain unexecuted, historical
custody remains unresolved, and scientific cells remain 0/1020.
