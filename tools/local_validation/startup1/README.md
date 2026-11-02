# Startup1 diagnostic implementation candidate

Owned source only; unexecuted until independent source review and fresh SQ/D
admission. No original L/LQ2/LP2 source is changed. This is a diagnostic of one
fresh owned PowerShell probe, not a P caller or a positive startup qualification.

Invoke exactly the pinned PowerShell executable with `-NoLogo -NoProfile
-NonInteractive -File D:/Aenv/pro3/tools/local_validation/startup1/diagnostic.ps1
-Capsule <absolute-path> -CapsuleBytes <integer> -CapsuleSha256 <lowercase-sha256>`.
The controller internally selects `pdh_probe.ps1`, `fast_probe.ps1`,
`stall_probe.ps1` or one of four fixed negative fixture files. Each child has
exactly three script arguments: original UTC,
original QPC and frequency. Production role D selects PDH only. The two fixtures
are implementation-specific qualification sources and are permitted only by
Q_STARTUP_CONTROL under the SQ caller's actual512MiB/process,768MiB aggregate
outer Job. Their nested PNative Job does not raise the outer effective limits;
the enclosing Q reference is a join, not JSON proof of that physical containment.

## Closed capsule

`contract.py` is the supplied-record contract for Q and saved-record review.
Its parser performs no file/process/sensor operations. `diagnostic.ps1` owns the
real effect path; SQ actual fast/stall controls must exercise that source, not
substitute a Python mirror. Source leaves are exactly the twelve names in
`contract.SOURCE_LEAVES`; qualification freezes their real hashes separately.

Capsule fields, exactly:

`schema issuer operation_id role probe created_utc expires_utc project_root
stop_path output_root helper q2_qualification q2_actual_review source_review
adoption qualification sources caller_runtime environment limits safety enclosing_q`.

Schema is `cho51_startup_capsule_v1`, issuer project_root, canonical UUID, role
D/Q_STARTUP_CONTROL. D permits only pdh; Q permits fast/stall/empty/malformed/
reordered/partial. Project
root/stop path are fixed to this project. Output root is a new absent UUID
directory under runs/coordination. The create-new claim is the once-only grant;
directory creation is not claimed as an atomic exclusive operation. Existing or
raced claims refuse. Admission covers the original caller plus15 seconds.

Ref means exactly `path bytes sha256`, with canonical absolute path and bounded
exact integer size/lowercase digest. Pins are exactly `bytes sha256`. Helper adds
`native_identity` as the existing qualified `volume:fileid` string. Sources maps
the twelve absolute source paths to pins. Caller_runtime is `executable version
files`; executable is a Ref, files is the complete finite Ref array. Runtime
requires the exact PSHOME top-level DLL/EXE/JSON census, absent unreviewed culture
DLLs/config aliases, and coverage of each non-dynamic loaded managed assembly
Location before load and before final verification. Resident .NET/PowerShell
and dynamic runtime assemblies remain explicit local platform trust; disk pins
are not loaded-code attestation.

Bootstrap validates capsule/control/source/executable pins before loading the
existing exact Q2 PNative bytes. Initial byte-load trust and native-ID sequencing
are explicit: the native ID reader is in that helper, so no pre-load ID claim
is made. The ID is compared immediately afterward before Owner construction.
Full runtime pins stream after native guard readiness, before any probe child.
All runtime/input bytes/IDs and the runtime census are checked again at closeout.
Hash chunks are64KiB; guard-active checkpoints use the independent guard's75ms
resource/stop observations, maximum250ms age, rather than repeated per-chunk
ancestry queries. No performance claim exists until execution.

Environment keys are exactly SystemRoot,WINDIR,PATH,HOME,USERPROFILE,TEMP,TMP,
OMP_NUM_THREADS,MKL_NUM_THREADS,OPENBLAS_NUM_THREADS,CUDA_VISIBLE_DEVICES and
PYTEST_DISABLE_PLUGIN_AUTOLOAD. Windows roots are C:/Windows; PATH is the pinned
pwsh directory plus C:/Windows/System32. HOME/USERPROFILE/TEMP/TMP equal output_root.
Thread/autoload values are1; CUDA is-1. Unknown output-root entries refuse final
verification. No global configuration, PDH cache or old caller is changed.

Limits are exactly `contract.LIMITS`: startup/work5, cleanup deadline10, whole15,
RAM4GiB, disk20GiB, P4096/5120MiB, sample freshness250ms. In Q role the additional
managed caller cap is512MiB and actual outer Q containment is SQ's responsibility.
Safety is exactly `contract.SAFETY` with false historical/scientific flags and
zero candidate/control executions. Enclosing_q is null in D; Q has exactly
`operation_id admission limits`, with a distinct operation and512/768 limits.
Qualification is null for Q controls; D requires fresh accepted qualification.

## Authority records

Source review is `cho51_startup_source_review_v1`, status ACCEPTED_SOURCE_STARTUP1,
with exactly `schema status reviewer authors created_utc sources design
design_acceptance findings checks limitations`. Sources must equal the complete
current capsule map. Reviewer/author IDs are exact strings matching
`[a-z][a-z0-9_-]{0,63}`; authors is a nonempty bounded unique array and the reviewer
is outside it. Findings must be an empty array before helper load. Checks and
limitations are bounded string arrays. The same typed independent-identity check
also covers design and predecessor/current actual reviews. Design and acceptance are Refs to the actual accepted
design/Root acceptance; their existing nested relative references are resolved
to this project and exactly joined. The design review uses `design {path,sha256}`.

Adoption is `cho51_startup_adoption_v1`, ADOPTED_STARTUP_DIAGNOSTIC_ONLY,
with exactly `schema status author created_utc source_review design
design_acceptance q2_qualification q2_actual_review helper limits bootstrap_effects
safety`. Author is project_root. Effects are exactly retained_helper_load,
empty_job_and_native_guard,one_fixed_probe in that order. It joins the actual
Q2 PE/source/actual/Root controls, helper ID and unchanged native custody checks.

Fresh D qualification is `cho51_startup_qualification_v1`,
QUALIFIED_STARTUP1_MECHANISMS_ONLY, with exactly `schema status author created_utc
source_review actual_review operation_id accepted_controller_sources controls
owned_lifecycle_closed safety`. Source map and review match current startup
bytes, controls are exactly fast/stall, closure true. Actual review must expose
ACCEPTED_STARTUP1_TESTED_SCOPE, its operation/reviewer/authors/created_utc,
accepted_controller_sources, startup_source_review_sha256, controls,
actual_tool_exit_code0, owned_lifecycle_closed true and empty findings. It joins
the standalone D source-review hash separately from the full SQ source review.
Order is source review <= actual review <= Root qualification <= admission;
source review <= adoption <= admission. Actual and source reviewers differ.

## Timer and retained outputs

Two native samples have at least200ms between the first call's end and the second
call's start. Owner.Start is complete before scheduling a direct managed Action
bound to Owner.Dispose for original elapsed5 seconds; an original-process5-second
hard kill remains armed through pre-dispatch/Start, so a stalled Start cannot
overlap Dispose. There is no Poll, ExitCode, Owner.Check or second Dispose while
that callback can run. Cancellation registration Dispose joins the callback
before custody is read. Its ordinary disposed Boolean is never a join claim.
The10-second cleanup hard kill and15-second whole hard kill use the original
cached controller Process handle. Failures consume the UUID and may remain unknown.

An independent guard calls only Owner.Sample during/after Dispose. Static source
shows that method uses current-process APIs and interlocked aggregate fields,
not closed Job/stdio state. It covers resource/stop/time while main blocks and
through final publication; shutdown wait/runspace/PowerShell handles are joined
and closed. A guard fault self-terminates the original controller, with no claim
that an absent receipt proves its cleanup.

The five create-new original-writer outputs are claim.json, stdout.bin, stderr.bin,
observation.json and journal.json. An external output Ref has exactly
`path bytes sha256 native_identity`. Every output's original ID is in the external
return outputs array; observation also contains stdout/stderr/claim refs. No
self-hash is embedded. All inputs and outputs are rehashed on original handles
before release; final directory entries must match the five owned outputs.

Saved observation fields are exactly `schema operation_id role probe origin
status markers marker_error stdout stderr claim managed_runtime exit_code
exit_code_status termination_cause deadline owned_lifecycle_closed
guard_shutdown_pending safety`. Schema is cho51_startup_observation_v1; status
stays provisional_diagnostic_only. Origin is utc/qpc/frequency. Managed_runtime
contains before/after assembly rows and top_level_census_count. Deadline contains
target_qpc,cancel_observed_qpc,registration_joined. The original exit handle closes
in Dispose; exit_code is null, exit_code_status unavailable_original_handle_closed_by_dispose,
termination_cause unobserved. No passing child, native termination branch or old
failure cause is inferred.

Final stdout is one bounded JSON record, cho51_startup_external_return_v1. Exact
fields are in `contract.validate_external_return`: operation/role/probe, status/
failure, original origin/caller/elapsed, authority/native-ID/final-input/final-output
verification, registration join, custody/owned closure, original stream closure,
guard/observation/outputs, actual_tool_return_pending and scope flags. Success
status is observed_diagnostic_only only with nonempty valid role-appropriate
marker evidence and completed final checks, never startup qualification. Custody includes
every required original Job/process/stdio/watchdog closure flag, Fault/errors and
overflow. Guard has ready/stop/done/error/last/samples/first/second/joined/closed/
completion_wait_closed. Actual external return still requires Root's separate
complete tool observation within15 seconds.

Probe markers use schema cho51_startup_probe_marker_v1 and exact fields
sequence,event,origin_utc,origin_qpc,frequency,qpc,elapsed_seconds,detail. PDH names
are assembly_load_begin/end,counter_ctor_begin/end,first_sample_begin/end and
counter_dispose_begin/end; probe_error preserves an exception boundary. Fast is
fixture_fast_begin/end. Stall is fixture_stall_begin followed by an intentional
owned indefinite wait, not a successful child. All markers must obey sequence,
typed monotonic original clocks and the shared5-second range. Partial bytes remain
retained even on malformed protocol. Empty/malformed evidence is not success.

Q imports only startup1.contract then startup1.test_diagnostic; no candidate imports.
DiagnosticContractTests has42 supplied-data methods. Actual SQ fast/stall controls
exercise the PowerShell paths; source review, supplied tests, actual controls and
independent result acceptance remain different claims. Scientific cells0/1020;
117 candidate cases and34 successor controls remain unexecuted.

## Revision2 real-controller negative controls

S1 marker validation preserves every raw byte and each validated partial row but
sets sticky failure on malformed, empty or wrong-prefix evidence. Fast requires
both begin/end, stall exactly its one declared begin, and D requires a nonempty
valid ordered PDH prefix without probe_error. A valid partial PDH prefix is an
observation boundary, not positive complete startup qualification. Failure still
finishes original-input/output verification, publication, native closure and guard
closure; it cannot become observed_diagnostic_only after successful cleanup.

Capsule fields/CLI are unchanged. The following fixture probe values are Q-only,
each selecting one fixed three-argument script; there is no arbitrary file or
mode override. SQ's actual index separately orders all eight named controls:

| SQ name | Capsule probe | Required real-controller outcome |
| --- | --- | --- |
| fast | fast | observed_diagnostic_only with both fast markers |
| stall | stall | observed_diagnostic_only with the declared stall marker and owned closure |
| empty | empty | refused; empty_probe.ps1 emits no stdout; nonempty marker evidence required |
| malformed | malformed | refused; malformed_probe.ps1 emits one valid begin then broken JSON; valid row and raw suffix retained |
| reordered | reordered | refused; reordered_probe.ps1 emits end before begin; ordered marker prefix refuses |
| partial | partial | refused; partial_probe.ps1 emits only fast begin; complete fast markers required |
| review_findings | fast | refused before helper load for nonempty startup review findings |
| review_identity | fast | refused before helper load for a malformed reviewer identity |

The S1 failures exit1, use external status refused and failure prefix
`marker evidence refused:`, and retain all five output/native-ID rows with final
verification/closure true. Saved observation status is refused_marker_evidence;
marker_error is nonempty. The malformed JSON diagnostic text is parser-dependent;
the prefix and retained evidence, not incidental exception wording, define refusal.

S2 uses explicitly Q-owned synthetic review records that retain accepted status,
correct source/design/window joins and a matching cloned adoption.source_review
reference, isolating the invalid findings or identity check. It does not modify a
genuine accepted review. Expected external result is refused/exit1, with failure
containing `unresolved startup source review findings` or
`startup source review reviewer identity`, respectively. Authority/native-ID flags
are false, custody/observation null, outputs empty, no Dispose registration/owned
child, final verification false, original streams closed and guard unstarted.
The SQ parent must separately prove its original controller process/Job closure.
No exit code or JSON assertion alone proves that no child/helper effect occurred.

The eleven added supplied-record cases cover the marker and typed review contract;
the six actual negative controller invocations are separate decisive path controls.
Only fresh reviewed SQ execution can establish their outcomes.
