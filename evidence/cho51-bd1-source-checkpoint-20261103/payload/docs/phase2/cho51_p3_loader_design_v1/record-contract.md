# L record and interface contract

29 October 2026. Design specification, not executable schemas or successful
example records. Author: project Root. The [L design](../cho51_p3_loader_design_20261029.md)
sets behavior; this file fixes record boundaries for implementation. Implementation
must supply closed parsers and exact field tests before source acceptance.

## Shared types and invariants

Objects have exactly the named fields; no unknown keys, duplicate JSON keys,
nonfinite values, bool-as-int, implicit coercion or silent defaults. UTF-8 is
strict, Unicode strings contain no lone surrogates, JSON depth <=32 and nodes
<=200,000. A JSON record/frame is <=8MiB; the operation has <=64MiB/256 output
files including logs/configuration. Any missing required field refuses.

`Ref` has `path, bytes, sha256, role`: a canonical admitted absolute path,
nonnegative exact integer byte size, lowercase 64-hex digest and exact role enum
from the record's schema. It describes an existing retained input or published
output, never its own record or a future output. `RetainedRef` adds
`native_identity, owner, sharing`: volume serial/file ID/filesystem/local-fixed
facts from the qualified reader, exact owner role, and explicit read/write/delete
sharing facts. Static design refs have no runtime identity claim; every consumed
L file uses a RetainedRef in its actual custody record.

`Origin` is `utc, qpc, qpc_frequency`; `Tick` adds `elapsed_seconds`. UTC is the
strict contract format; QPC/frequency are bounded exact integers. All operation
records join the one genuine external origin and exact positive frequency.
`Operation` is `stage, operation_id, request, admission, origin` with stage L,
the same canonical UUID and exact refs. UUID uniqueness is claimed atomically,
not inferred from a filename. Failure state is monotonic and immutable.

`Safety` is exactly `historical_custody_closed, historical_operation_released,
historical_retry_allowed, restart_qualified, scientific_admission,
candidate_tests_executed, successor_controls_executed`; Boolean fields are false
and both execution counts are integer zero in L records. A new engineering
admission's authorization is a scoped field in that admission only. Do not
promote historical or scientific fields to authorize this new operation.

`Counters` has exactly the eight original names: `source_updates, restore_count,
support_updates, gradient_updates, target_inference_calls, query_count,
model_constructions, measured_cells`, all exact integer zero. Preserve separate
attempted-action events; zero completed counters cannot hide a denied attempt.

Workload identities and operator/control identities are separate. A later V
record may change its UUID/admission/runner stage only under reviewed stage
bindings; it cannot silently change the L candidate, dependency, initialization,
guard, import, resource, ABI or pytest configuration identities.

## Pre-execution records

All names below are distinct closed schema discriminators, prefixed
`cho51_l_` and suffixed `_v1`. Every record includes `schema`.

| Schema | Required remaining fields and constraints |
| --- | --- |
| `plan` | `status, authors, predecessor_p10, candidate_roster, source_manifest, initialization_groups, bootstrap, import_policy, native_policy, resource_policy, abi_policy, guard_policy, pytest_policy, environment, limits, safety`; status `DESIGN_BOUND_IMPLEMENTATION_PLAN`; each policy is a retained reviewed JSON ref, never an arbitrary object of new flags |
| `adoption` | `author, created_utc, design, implementation_review, qualification_q, preparation_p, plan, scoped_policy_replacement, safety`; author Root; exact positive reviews, new P acceptance and fixed local-contract replacement; no launch flag |
| `request` | `stage, operation_id, created_utc, adoption, plan, source_manifest, runtime_manifest, preparation_p, preparation_index, preparation_result, predecessor_reviews, command, cwd, roots, control_inputs, attempt_root, stop_path, environment, limits, forbidden_effects, requested_window, safety`; exact fixed command/roots/env; complete reviewed P pages and roles |
| `admission` | `issuer, created_utc, stage, operation_id, request, implementation_review, adoption, admitted_window, resource_observation, limits, permitted_command, attempt_root, stop_path, authorized_new_l_only, safety`; issuer Root, authorization exact true only for this UUID/command/window, no permission for V |
| `claim` | `operation, created_utc, original_caller_identity, attempt_root, request_digest`; atomic create-new, existing/unknown path refuses; identity includes original process generation evidence |

Plan policy files must be finite closed data, not expressions or callbacks:

- Initialization rows: `ordinal, group_id, phase, modules, predecessor_groups,
  allowed_effect_ids, postcondition_ids`. Strict increasing ordinals; exact
  module names and retained source/extension refs in the import policy.
- Import rows: `module, kind, file_ref, namespace_paths, phase, initializer_group`.
  `kind` is source/extension/builtin/frozen/namespace; only the appropriate
  file/path fields may be null/empty, as specified for that kind. Source and
  extension entries require an exact file; namespace entries require exact
  ordered paths. Builtin/frozen entries join pinned interpreter bootstrap.
- Native rows: `requester, requested_name, mechanism, flags, search_directories,
  chosen_file, allowed_system_role, phase, delay_policy`. Exactly one chosen
  file or system role; no basename-only trust, broad family or discovery flag.
- Resource rows: `resource_id, file_ref, caller, phase, mode, maximum_bytes,
  mediation, observation_required`; read-only, existing exact P file;
  `mediation` identifies a qualified wrapper, not a mere assertion of coverage.
- ABI rows: `module, extension_file, machine, python_tag, initializer_symbol,
  required_exports, forwarder_targets, safe_queries, expected_metadata,
  compatibility_scope`. All callable safe queries have exact module/symbol,
  argument/result shape, effect budget and source rationale; numerical probes
  are forbidden. Dormant/delay exports are marked unqualified, not omitted.
- Guard rows: `guard_id, phase_installed, defining_module, symbol, equivalents,
  bound_aliases, sentinel, refusal_event`. Every required symbol/alias must exist
  and bind to the exact installed blocker before its consumer phase.
- Pytest policy: exact `version, config_ref, ordered_arguments, builtin_plugins,
  custom_plugin_refs, blocked_plugins, hooks, candidate_modules, static_roster,
  id_limits, no_fixture_or_test_execution`. Unknown registration is rejected
  before plugin hooks, not simply removed after registration.

Implementation-specific policies cannot be left as TODOs when requesting Q/P/L.
Their exact values are source-review inputs. This design intentionally supplies
no invented future binary hash, ABI success, node roster or admission.

## Authenticated child protocol and observations

Each dedicated report-pipe frame is `schema, operation_id, sequence, phase,
kind, payload`; sequence starts at zero and is contiguous, kind is one of the
closed payload schemas below. The frame header is a fixed unsigned length;
validate <=8MiB before allocation, bounded reads before parsing, one pending
frame, total output accounting and watchdog-covered backpressure. Exactly one
terminal frame is allowed. A nonce is not authentication: the original inherited
pipe endpoints and process/Job custody establish the producer. Parent timestamps
receipt and writes the final original-handle artifacts.

| Payload | Required fields |
| --- | --- |
| `checkpoint` | `state, tick, imports_digest, native_sequence, resources_digest, guard_digest, counters`; child checkpoints cover only L1-L5, no skipped/reversed phase; L0 and L6 are parent-owned states, never child assertions |
| `import_row` | `module, phase, origin, kind, loader_type, namespace_paths, retained_ref, initializer_group`; source/extension identity exact, no path-only join |
| `native_event` | `event_sequence, reason, phase, base, image_size, full_path, native_observer_generation, fault_flags`; reason load/unload, copied bounded strings, no missing/truncated row accepted |
| `native_join` | `event_sequence, retained_ref, system_role, requester_choice, snapshot_membership`; exact one physical ref/system role, explicitly separate event observation from trust inference |
| `resource_row` | `resource_id, phase, caller, retained_ref, mode, bytes_read, mechanism, outcome`; outcome observed/denied, denial always separately assessed; native-only declaration is not an observed row |
| `abi_row` | `module, phase, interpreter_identity, extension_ref, metadata_refs, symbol_results, safe_query_results, loaded_image_refs, scope, unqualified_paths`; exact finite planned check results, no claim of arbitrary computation compatibility |
| `guard_row` | `guard_id, phase, defining_symbol, blocker_identity, aliases, sentinel_result, denial_sequence`; alias identities checked without calling untrusted properties |
| `denial` | `ordinal, phase, mechanism, operation, target_role, expected_sentinel_id, before_effect, tick`; unknown/unplanned/candidate denials are failures even if swallowed |
| `collection_item` | `ordinal, nodeid, module, original_function_name, parameter_id, source_ref, item_type, collection_sequence`; exact function/module join, bounded IDs, source must be unchanged candidate |
| `collection_end` | `pytest_exit_code, collection_errors, collection_skips, deselected, item_count, function_counts, ordered_roster_sha256, fixture_setup_calls, runtest_protocol_calls, phase_report_calls`; all error/skip/deselection/execution counts zero, item_count117,25 exact counts |
| `terminal` | `status, first_failure, completed_state, observations_digest, counters, observer_shutdown, safety`; status provisional-complete/refused/unknown, cannot certify parent custody or caller return |

Observation pages use `schema, operation, kind, page_index, rows` with page
indexes contiguous per kind. Parent's `observation_index` has `operation,
pages, row_counts, ordered_roster_sha256, plan, preparation_result,
publication_status, safety`; every page has Ref, kind/count/index and is complete
before its index is published. Publication status remains provisional forever;
later actual review resolves it without rewriting the child or index.

## Completion, external review and V join

| Schema | Required remaining fields |
| --- | --- |
| `result` | `operation, plan, preparation_result, observation_index, collection_summary, abi_scope, resource_coverage, guard_coverage, counters, failures, publication_status, safety`; no unobserved/unmediated resource branch can count as covered |
| `custody_receipt` | `operation, caller_identity, child_identity, job_identity, assignment_evidence, limits, process_exits, job_empty, report_pipe_eof, stdout_eof, stderr_eof, observer_shutdown, final_input_verification, final_output_verification, original_handle_closure, resource_summary, final_tick, status, safety`; each unknown remains explicit and refuses acceptance |
| `external_return` | `operation, invocation, actual_exit_code, actual_return_tick, stdout_ref, stderr_ref, caller_return_ref, complete_tool_observation, whole_interval_valid, safety`; actual outer tool return, no child's self-report substitution |
| `actual_review` | `reviewer, authors, created_utc, operation_id, source_review, adoption, request, admission, result, observation_index, custody_receipt, external_return, checks, findings, status, accepted_scope, unqualified_scope, safety`; reviewer distinct from source/implementation author and source acceptance role |
| `qualification` | `author, created_utc, operation_id, actual_review, accepted_result, accepted_index, workload_identity, ordered_roster_sha256, exact_function_counts, observed_abi_scope, unqualified_scope, next_stage, safety`; Root only after positive complete actual review; next_stage V requires separate admission |

Every Boolean check is exact true where acceptance requires it; integers cannot
stand for booleans. Every linked record's schema, producer role, UUID, predecessor
operation, full command/limits, hashes and original clock domain must agree.
Reject substituted P10 provisional flags as proof of preparation acceptance;
consume its separate actual review/Root acceptance, or the fresh successor's
equivalent chain. No output hash is placed in an earlier request or its own body.

V's workload identity must bind the same candidate pins, exact dependency and
resource/search plan, initialization/guards, pytest config, full ordered roster
and safe ABI checks. V execution-specific control sources and request/UUID form
an explicitly reviewed separate identity, not an exception to common-workload
equality. A changed common file/environment requires new qualification and P/L
evidence before V; no old successful collect-only run can excuse drift.

Late return, missing EOF, missing native shutdown, final rehash failure, incomplete
report/record sequence, forbidden action, limits breach or unknown custody always
prevents acceptance. Failed results and partial outputs remain in the consumed
attempt. Design acceptance, L qualification and pipeline C are distinct records.
