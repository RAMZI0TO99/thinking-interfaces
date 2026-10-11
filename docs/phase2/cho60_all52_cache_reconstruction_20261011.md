# Cho 60 Hz Profile B: all52 current cache reconstruction

11 October 2026 UTC. All52 subjects/10,520 epochs in
`data/processed/cho2017/profile_b_60hz_v1` reproduce exactly from the52 pinned
local Cho MAT recordings. All six cache fields agree: signal values, labels,
sessions, runs, trial indices and channel order, including shapes and dtypes.
Maximum absolute and per-subject RMS errors are0 in both the stored amplitude
units and physical volts. Both classes contain5,260 epochs. All raw recordings,
caches and52 manifest sidecars retain their hashes, sizes and mtimes; none was
rewritten. Current processing is reproduced; historical generation and
scientific eligibility are not authenticated by this comparison.

The frozen variant applies the base Profile B processing with only its notch
changed to60 Hz:0.1–75 Hz bandpass, original reference,200 Hz resampling,
four seconds after the cue,64 EEG channels and800 samples per epoch. Signals
are float32 values normalized by0.1mV, so one stored unit is0.0001V. Exact
comparison uses those stored values directly. Tolerance is independently
calculated in physical volts with ATOL1e-12V and RTOL1e-6, using float64
differences; no rounded voltage conversion precedes the equality check.

The actual owned synthetic probe passed six boundaries: frozen configuration,
local cues and epoch identities, amplitude scaling, exact stored comparison,
below/above physical-voltage tolerance plus identity rejection, and synthetic
60 Hz attenuation relative to a50 Hz notch control. The measured attenuation
was56.8685 dB against the previously declared6 dB engineering minimum. This
synthetic measurement is not real-data scientific accuracy or model evidence.
The probe ran for18.4967879 native seconds and its complete root review passed.

Real comparisons ran as three disjoint scopes:

| Scope | Subject IDs | Epochs | Native seconds | Inner/native deadline |
| --- | --- | ---: | ---: | --- |
| First subject, receipt reused | 001..001 | 200 | 24.2686972 | 300/330s |
| Disjoint group A | 002..026 | 5,080 | 196.5673159 | 458/488s |
| Disjoint group B | 027..052 | 5,240 | 200.5359361 | 472/502s |

Subject001's complete200-epoch receipt was reused without numerical replay.
Remaining group bounds use twice its measured6.7517231-second subject work
plus at least120 seconds fixed overhead. Both stay below the unchanged
600-second supervisor attempt maximum. Group B required complete group A
review and physical release before a fresh admission.

Every actual scope retained startup10 GiB RAM, active4 GiB RAM,20 GiB disk,
process4 GiB and aggregate Job5 GiB caps; CPU/native/Torch threads were1,
with one owned Job and genuine local/peer pause sensors. Peak real Job commit
was2,953,322,496 bytes. All37 cumulative created owned
Jobnames were freshly absent after the complete review. The imported runtime
contained3,195 freshly checked files, identical across the probe and all real
scopes. Installed-loader class-name and class-stacking edge-effect warnings
were retained. Cho class-block order does not certify original acquisition
chronology.

All scopes executed at Git`798064ee5dd953f9ebb39c83b8042a4747abbd95` and canonical
Source`3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529`/432 files. Quality pointer4eb4d556
was retained; the older full suite was not replayed or extended to certify
this candidate namespace. Separate root receipt checks and the metadata-only
aggregate are self-review, not independent scientific acceptance. Existing
failed/refused attempts and historical receipts remain unchanged.

The completed Profile A result remains170 subjects/20,621 epochs across BCI,
Cho and MMIDB. Profile B's52 Cho subjects are the same participants; this
second cache family adds no independent research subjects. This phase opens
no checkpoint, constructs/fits no model, invokes no recorder and consumes no
original LaBraM case attempt. Original attempts remain spent/zero. The81
current original controls and450 dated historical reference records remain.

Gate A, all seven owner decisions and the experiment freeze remain unsigned.
Checkpoint-SHA-bound actual pretraining cohort/target overlap evidence is
still missing. The [updated provenance request](checkpoint_provenance_request_draft_20261011_cho60.md)
is prepared and unsent, with no recipient/channel selected or third party
contacted. The older11 October draft remains byte-exact. The existing
[cohort intake contract](checkpoint_cohort_review_contract_20261010.md) and
[owner decision packet](cho_owner_decision_packet_20261010.md) govern those
next prerequisites. The [engineering addendum](cho_owner_decision_engineering_addendum_20261011.md)
maps this new evidence to each of the seven undecided owner responses.
No further scientific/model operation is admitted by this
engineering result, and no new30-hour window or peer quiet/compute grant is
inferred.
