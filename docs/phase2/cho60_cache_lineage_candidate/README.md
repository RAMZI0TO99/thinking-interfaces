# Cho60Hz ProfileB reconstruction candidate

This separate data engineering scope reconstructs existing versioned60Hz
ProfileB inputs from pinned local Cho MATs using the installed local Cho
conversion/default annotations and unchanged `data.profile_b` collection.
It preserves original reference,0.1–75Hz FIR,60Hz notch,200Hz resampling,
four-second post-cue epochs without baseline subtraction, and scaling in
units of0.1mV. Each existing stored float32 and all identities are compared.
Exact equality uses the original stored values. Tolerance/errors are evaluated
in float64 physical volts, with existing1e-12V absolute/1e-6 relative bounds;
scaled values are never mislabeled as volts or recast before exact comparison.

The six-boundary owned synthetic probe measures frozen config, cues/schema,
amplitude scaling, exact comparison, physical tolerance/identity rejection
and60Hz attenuation against a synthetic50Hz control (predeclared6dB minimum).
It must have complete reviewed execution and physical release before real
subject001 can be admitted. Disjoint remaining2..26/27..52 groups require
the complete measured first comparison; groupB also requires groupA review.
Every stage has a fresh finite single-attempt current-Git/input/runtime
admission, startup10/active4RAM/disk20GiB, process4/Job5GiB and CPU/native/Torch1.
Inner bounds remain at most the immutable600-second primitive maximum.

The unchanged qualified Cho local resolver and `worker_common_004.py` are
copied into the private attempt package. The common helper's legacy schema
contains MMIDB; exact stage/protocol/operation/input bindings define this scope.
Only receipts and owned synthetic/runtime files are written. Raw data, caches,
manifests, weights, frozen implementation, original attempts and scientific
decisions are preserved. No model, checkpoint, fitting, recorder, scientific
cohort/eligibility, GateA/freeze signature or original-case reset is admitted.
