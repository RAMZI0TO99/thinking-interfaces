# P1 physical dependency preparation

Source proposal only until independent review and separate Q/P admission.
No command-line entry point exists. Root owns the supervisor, caller origin,
fresh runtime/source pins, stop/resource/watchdog controls, attempt ownership,
publication and cleanup evidence. No test has been executed by the author.

`parse_recipe(bytes)` and `validate_recipe(dict)` accept only the closed
`cho51_lv_physical_recipe_p1` schema. It contains explicit `scope_roots` and
4–256 labeled groups with `role`, `kind`, `root`, `seeds`, `suffixes`,
`excluded_dirs` and exact `pins` (`path`, `bytes`, `sha256`). All source,
runtime, package and metadata roles must occur. Seeds must be expected members.
Tree groups expand literal suffixes under fixed roots with explicit directory
name exclusions. Exact-file groups have one pin and no expansion. Group scope
overlap, alias spelling, unpinned selected files and missing expected files
refuse. Expected membership is checked before opening selected file bytes.
No wildcard, candidate import, package discovery, data/weight discovery or
compilation is performed. A reviewed recipe must explicitly exclude scientific
data/weights; choosing broad roots/suffixes is not a coverage review.

`PreparationSession(recipe, checkpoint).observe()` records initial and final
native observations and returns a bounded proposed physical-map report.
`verify()` rehashes retained files, checks ancestors and compares complete tree
entry censuses, including unselected entries and excluded-directory entries.
Excluded directory contents are outside the census by explicit recipe choice.
Exact-file groups deliberately make no parent-membership completeness claim.
The unchanged Q4 NTFS reader supplies native read-sharing-only handles,
hardlink/reparse/alias/fixed-volume checks and 64 KiB streaming hashes. The
unchanged v1 primitives validate snapshots and join all exact pins. Limits are
25,000 files, 4 GiB total, 2 GiB/file, depth32, reader enumeration limits,
and the stricter 8 MiB/200,000-node bounded JSON representation; exhaustion
refuses rather than truncating a successful map.

The caller keeps the session open through its own retained output publication,
calls `verify()` immediately before and after publication under the same caller
budget, and closes in `finally`, recording failures. Directory handles do not
freeze membership. No freshness assertion survives release. A failed partially
observed session must be closed and its attempt remains consumed.

The concrete physical dependency recipe is a separate review deliverable.
This engine cannot infer transitive completeness, metadata query coverage,
search-path/loader closure or ABI compatibility from supplied pins. Independent
coverage/pin review, actual result acceptance, ABI/native-loader qualification
and future operational admission are distinct. Every returned authority field
is false; caller success flags and review prose are not schema inputs.

The test module requires Root's Q runner to inject an absolute fresh
attempt-owned `FIXTURE_ROOT`. Fixtures are tiny JSON files only. Native positive
and negative cases are distinguished from the injected reparse predicate.
The author has performed text inspection only; source review and admitted
execution must establish actual results separately.
