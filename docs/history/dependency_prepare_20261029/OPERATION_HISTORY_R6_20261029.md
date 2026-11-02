# Dependency preparation revision 6: retained history

29 October 2026. This supplements the [earlier history](OPERATION_HISTORY.md).
Use the [current milestone](../../phase2/cho51_p3_dependency_preparation_20261029.md)
for the current gate. These records do not authorize execution or replay.

P5's duplicate-descriptor refusal was followed by bounded file inspection of
the 888 selected PE images. Two pinned extensions, `hf_xet.pyd` and
`_safetensors_rust.pyd`, contain repeated normal descriptors for `kernel32.dll`.
Revision 6 preserves ordered names, raw descriptors, positions and explicit
edge occurrence counts. It retains all existing range, termination, name,
memory, deadline and output checks.

The first unadmitted R6 draft failed source review because a 768-character
error-message limit could truncate an importer path. All 31 draft/review files
were preserved in Q6's `source-revision1`. The revised source reports a separate
bounded `failed_importer` field and keeps the error-message cap. An existing
test method exercises a longer path; the suite remains 192 methods.

| Operation | Outcome |
| --- | --- |
| Q6 `4fdea069-da0e-4307-a592-cf13db036307` | Empty exit 1 after 5.49 s; five startup events end at `assembly_loaded`; no test execution or caller receipt; cause and cleanup unproved |
| Q6 `f85f64bf-2c9e-4eb0-afae-b83410ecfd05` | Fresh UUID/admission, unchanged limits; exit 0 after 13.17 s; 192 methods, eight UTC controls and two native fault controls independently accepted |
| P6 `4e339349-0eca-4611-8e85-c697ba7b4aae` | Exit 1 after 76.14 s; all 888 selected PE images parsed, then 17 unresolved native dependency names; owned closure independently accepted |

Q6's successful operation checked 71 source, 732 runtime, 169 compiler and 2,284
preservation pins. P6 checked 33 source, 732 runtime and 2,512 predecessor pins.
The reviewed P6 proposal contained 20,404 files / 3,455,779,816 bytes. Its 46
provisional outputs total 23,186,346 bytes. No accepted physical map or final
full input verification follows from that failed operation.

The unresolved list contains `cabinet.dll`, `fontsub.dll`, `mswsock.dll`, and
fourteen exact API-contract names. The ordinary DLLs were found in System32 by
file inspection. Similar versioned namespace entries are not treated as proof
that those exact API contracts resolve. The proposed next successor uses a
separately reviewed, bounded Q-only native schema query and file-only P receipt
consumption. Static diagnosis alone does not establish query results.

Receipts, independent reviews, Root dispositions and diagnoses remain in
`runs/coordination/cho51_p3_dependency_prepare_20261029_q6` and the matching
`..._p6` directory. Earlier failures and custody limitations remain unchanged.
The 117 candidate tests and 34 successor controls remain unexecuted; scientific
cells remain 0/1020 and the final freeze unsigned.
