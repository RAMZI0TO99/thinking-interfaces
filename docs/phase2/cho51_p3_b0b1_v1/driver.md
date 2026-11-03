# B1 finite driver and the first qualification entry

## E1_PROTOCOL scope

E1_PROTOCOL is a proposed distinct prerequisite operation: one native G0 and
one native S0, one96-byte request and one bounded reply. No test child, Python
runtime, module discovery, numerical work, Q/S selection or original117/V34
execution occurs. All those obligations remain held. An E1 result would qualify
only its exact protocol/ownership/guard observations, never all of B0/B1 or the
full runner.

The first candidate scenario is NOMINAL_ECHO. The design qualification matrix
also retains distinct fault/negative/overflow/closure scenarios as obligations;
their exact native inputs/effects and separate admissions must be settled before
use. Do not infer permission to combine them into an unbounded batch or to drive
arbitrary code through a scenario number.

The request is fixed little-endian binary, exactly96 bytes:
magic4, version2, opcode2, O16, nonce16, scenario2, flags2, payload_length4,
payload32 and reserved16. Opcode is ECHO_SHA256, payload length32, flags and
reserved bytes zero; O/nonce come from independently adopted input. The normal
response is exactly80 bytes: magic4, version2, flags2, O16, nonce16, result4,
payload_length4 and SHA256(payload)32. Full digest is retained. No truncated
hash, textual coercion, dynamic path, callback, address or script is accepted.

S0 emits at most128 bytes on each original stdout/stderr stream across the
complete declared normal/failure domain. This is an E1 source-domain obligation
below the unchanged1MiB original caps, not a new full-profile guard or permission
to discard original output. G0's original reply is<=256 stdout bytes and<=128
stderr bytes; the proposed H0 complete response is<=8192 text bytes in1..64
chunks and the external return<=4096 text bytes. These bounds require a real
reviewed transport/source grammar including failure, cancellation and loader
routes. No existing generic tool is asserted to meet it. Outside that domain,
foreseeable work refuses before effects; an unexpected overflow after effects
consumes/refuses with the actual bounded prefix.

For NOMINAL_ECHO, S0 closes every writer after the exact reply and waits only
under the original deadline. A closed dispatcher validates the request before
its target behavior, executes once, latches the first refusal and accepts no
second request or leaked entry capability. EOF, an exact frame and matching
nonce establish different predicates; neither one substitutes for the others.

## Required independent entry record

Before any experiment, Root needs an independently source-reviewed, freshly
pinned entry record naming:
- E1_PROTOCOL and the exact one scenario, target claim and nonclaims;
- independently adopted H0 authority/guards/observation/retention and earlier
  accepted dependencies, without a G0/S0 self-qualification edge;
- exact source/runtime/build/image/input manifests and original native capability
  acquisition, including unsupported ABI and pre-creation failure decisions;
- unused O, distinct M, exact original T0/stop mechanism and current resources;
- exact request bytes, expected response fields/digest and allowed native calls;
- every input/type/effect/failure/allocation/ownership population and all33
  inherited reservations, with explicit reserved-unused roles;
- complete original O/tool/capture and M final-retention/closure route,
  independent source/result-review provenance and a finite clock budget.

Only the scoped target functional result may be unknown inside this already
bounded basis. Unknown H0 effectiveness, isolation, source/dependency reachability,
resource/failure bounds, final witness retention or required control membership
is a refusal before effects. Neither old Q/P acceptance nor PC1 consistent facts
supply any of these predicates.

Runtime/build artifacts must come from separately reviewed, guarded and accepted
build provenance. Compilation, loading, hashing, copying and failed preparation
are not free outside-clock work. This design neither builds artifacts nor grants
such a build. The current record is a design only; no actual native admission,
host identity, runtime manifest or available resource sample is fabricated.

## Finite state and failure ownership

| State/edge | Required original evidence | Failure rule |
| --- | --- | --- |
| UNADMITTED -> BOUND | H0 adoption, native capabilities, unused O/M, T0/guard/capture before effects | No basis: REFUSED_UNADMITTED |
| BOUND -> CREATED | Exact G0/S0 image, original process/thread/Job identities, inheritance and pre-resume checks | Possible effect consumes O; H0 owns cleanup even on ambiguous creation |
| CREATED -> REQUESTED | Exact96 request bytes written once; pending I/O retained | Short/failed/duplicate request retains actual prefix and latches refusal |
| REQUESTED -> REPLIED | Exact80 normal bytes or declared finite negative prefix with source/offset/order | Malformed/oversize/mismatched reply never becomes PASS |
| REPLIED -> REVOKED | All entry capabilities disabled; no second request or queued invocation | Late/reentrant attempt accounted independently; no model counter shortcut |
| REVOKED -> DRAINED | Every admitted native I/O settled; original EOF/error and writer ownership | Cancel request alone is insufficient; keep buffer/handle until completion |
| DRAINED -> O_CLOSED | Actual G0/S0/process/Job/pipe closure, full original inputs and tool/capture return observed externally | Unknown owner/EOF/transport stays INCOMPLETE_REFUSED/UNKNOWN |
| O_CLOSED -> M_CLOSED | Once-only16 roles, exact final census/publication and independently retained final host witness | Self-attestation or missing final retention prevents acceptance |

G0 cannot report its own future exit. S0 cannot supply the independent evidence
used to qualify its own behavior. A report cannot pin its own final bytes.
After an effect may have occurred, the attempt stays consumed; no retry, new
UUID, partial resume, relaxed clock, role transfer or synthetic cleanup is allowed.

Negative protocol behavior may be a valid expected qualification observation
only when its required original guards, retained raw evidence and owned closure
are complete. Lost transport or a partial trace cannot be relabeled a complete
negative merely because a refusal was expected. Native faults, secondary
refusal failure, timeout/stop/resource loss and unexpected loader behavior have
separate retained outcomes and the same original cleanup bounds.

## Metadata suffix and first-entry decision

The proposed E1 metadata suffix has an additional deadline
min(original T0+90, observed O return+25 seconds). This is a stricter bound inside
the original whole clock, not a reset or a second window. Failure to finish
independent review, publication and closure within it refuses; no human-review
pause supplies headroom. Up to251 periodic suffix samples plus32 transition
samples fit320 record positions if the actual provider implements this schedule.

The finite representation allocations are conditional. Complete source/native
costs, F/M, original host availability and the final M retained witness are
NOT_ESTABLISHED. **Current E1 admission: REFUSED_UNADMITTED.** Native source
implementation may proceed separately; no actual entry follows from this design.