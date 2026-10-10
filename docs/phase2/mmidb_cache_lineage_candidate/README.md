# MMIDB subject 001 cache reconstruction candidate

This separate engineering candidate checks one existing Profile A artifact
against the three already downloaded EEGMMIDB 1.0.0 recordings S001R04,
S001R08 and S001R12. It calls the frozen project preprocessing functions and
does not save or replace any processed artifact. It is outside the canonical
source fingerprint and requires its own exact-byte receipts.

The runtime probe imports the actual scientific environment, exercises the
processing and comparison with synthetic data, measures physical thread
counts, and records imported module file hashes. Only a fresh reviewed probe
permits the separately guarded real reconstruction. Each scope has one fresh
attempt, a 120-second inner deadline and a 150-second native watchdog.

Startup/active RAM and free disk floors are 10/4/20 GiB. Process/aggregate Job
limits are 4/5 GiB, below the unchanged original 6/7.5 GiB model-case limits.
Network connections, subprocesses and filesystem mutations outside the owned
attempt are rejected by the worker's Python audit hook. This is an engineering
boundary, not an operating-system sandbox for hostile native libraries.

Labels, session/run/trial identities, channel order, shape and dtype must agree
exactly. Signals must be finite and agree at absolute 1e-12 V plus relative
1e-6 tolerance; exact equality and error magnitudes are also reported. These
are the previously declared engineering alignment tolerances, not scientific
accuracy thresholds. A mismatch is retained and never repaired by changing
the input, tolerance, source or cache.

No checkpoint, model, training, evaluation recorder, original case attempt,
cohort eligibility decision, Gate A acceptance or experiment freeze is supplied.
A matching reconstruction demonstrates current processing reproducibility for
these pinned inputs, not authenticated historical cache-generation lineage.
