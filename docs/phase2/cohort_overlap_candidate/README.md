# Declared checkpoint-cohort overlap candidate

This separate standard-library candidate compares declarations from the
existing bounded cohort template with the exact portable evaluation package.
It computes declared identifier intersections; it cannot authenticate the
claimant, verify the actual training run, prove coverage or decide eligibility.
All scientific verification/admission flags remain false.

The evaluation package is fixed to SHA-256
`b9ea3dfefed137a2264313bed1b7b3c392a1be799fbd767583500f44024bfc69`.
The existing intake helper and blank template remain unchanged. Public use
loads that helper from its adjacent original namespace; private qualification
uses byte-identical copies. The helper rejects oversized/duplicate-key JSON,
checkpoint drift, scientific signatures and original-case resets.

Each compared dataset needs one unambiguous declared version and identifier
namespace, an exact package hash/reference, and explicit training-to-evaluation
mappings. Target datasets use the package's canonical names. Multiple namespace
or version declarations cannot be disambiguated by the current template's
unqualified mapping fields and are refused. No aliases are inferred. Mapping
evidence references are declarations only and are never fetched or opened.

Declared subject matches combine explicit subject mappings with evaluation
subjects identified by mapped recording matches. Many training aliases may map
to one evaluation identity without inflating counts. Duplicate/conflicting
mapping keys, unknown/cross-dataset targets, undeclared training identifiers,
version mismatch and contradictory supplied intersection lists are refused.
Unmapped declarations are counted; zero matches never establishes exclusion or
independence. Empty/missing inventory remains unknown.

`compare_bytes(submission_bytes, evaluation_package_bytes)` returns the
metadata-only report. `declared_overlap.py --input FILE --evaluation-package
FILE` exposes the success/error CLI paths. The validation recipe uses only
owned synthetic submissions and the trusted package's metadata; it performs
no real cohort intake, scientific imports, model/checkpoint work or training.
