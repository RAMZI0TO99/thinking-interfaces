# P2 revision3 physical dependency preparation

This new implementation supplies a paged physical selector engine, bounded PE
import reader, closed P admission chain, and file-only P caller. Frozen P1/Q4
sources remain unchanged. Source text is not a passing test or an admission.

The new local `native_reader.py` validates ordinary canonical drive paths before
adding extended transport only at CreateFileW/scandir/no-follow stat calls.
Manifest metadata census uses the same helper. Canonical descriptors, native
final-path identity, hardlink/reparse/ancestry and all bounds stay unchanged.
The failed P2 attempt and its261-character unselected census leaf remain frozen;
the new source neither skips that path nor changes system long-path policy.

The Q-only `build_native.ps1` emits `caller_native.cs` to a create-new managed PE.
P loads the exact Q-qualified PE from retained bytes; P never compiles native
code. `invoke_p.ps1` owns one Python supervisor in an atomic Windows Job and
authenticates its output descriptors through the original stdout pipe, exact
bytes and native file identities. All receiver handles stay open to closeout.

`manifest.py` retains the selected union and initial/final directory censuses.
Files, census entries and absence observations are separate bounded pages.
`pe.py` reads import metadata without loading images. `native_policy.json`
declares the local Windows trust boundary, including an exact API-set namespace;
only used, present platform image paths satisfy platform edges. Alternative
physical DLL candidates are explicit and require later loader selection review.

The [implementation contract](../../../docs/phase2/cho51_p3_p2r3_dependency_contract_20261029.md)
defines the gates, fixed limits and evidence boundaries. Neither the proposed
map nor a P receipt grants L/V/C execution, scientific eligibility or historical
custody repair. Complete runtime closure requires later loaded-origin/resource
enforcement. No candidate or package imports occur here.


