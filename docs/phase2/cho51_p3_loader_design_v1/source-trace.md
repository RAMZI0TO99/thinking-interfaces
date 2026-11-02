# Static source trace informing L

29 October 2026. Root plus a separate read-only explorer inspected source text
and saved metadata. No interpreter, candidate import, collection, Git, native
probe or test ran. These findings define gates for implementation, not runtime
proof. Exact source hashes are retained in the phase's design input index.

## Candidate collection

The unchanged [test roster](../cho51_p3_local_validation_v1/test-roster.json)
contains 25 functions. Mapping has six singletons plus parameter groups
4/9/5/2/3/6/2/2, total39. Telemetry has four singletons plus
34/19/5/4/4/4/4, total78. IDs and order must come from real guarded L collection;
the static roster has neither. In particular, literal JSON parameter values
can affect pytest escaping and collision suffixes.

`docs/phase2/cho51_p3_adapter_v1/test_mapping.py:25` resolves ROOT during import.
The fixture declared at line62 performs synthetic metadata/source identity/
environment work only when invoked; L must never invoke it. Test-body monkeypatch
paths at lines276/337 are V concerns. Collection imports modules, evaluates
decorators and creates literal parameter data; none is proof of test execution.
`docs/phase2/cho51_worker_bridge_v1/worker_bridge.py:19` contains the dynamically
compiled, hash-checked planner route used later by the fixture. It is a distinct
allowed metadata operation, not permission to execute arbitrary compiled code.

## Early aliases and package graph

The original dependency-plan names safetensors file APIs, but
`evaluation/phase2_selected_source_store.py:28`,
`adaptation/source_checkpoint.py:18` and `evaluation/tcpl_publication.py:23`
bind `safetensors.torch.load` and `save` by value. The new implementation policy
must guard these in addition to `load_file`/`save_file` before canonical imports,
then compare retained aliases with installed blockers. The frozen original plan
is preserved; its incompleteness is resolved by a newly reviewed execution plan.

Canonical initialization reaches NumPy, Torch, SciPy, scikit-learn, MNE and
Braindecode. Braindecode's eager model imports reach torchaudio via
`.venv/Lib/site-packages/braindecode/models/brainmodule.py:16`. The P map's
conservative installed-code superset covers files, not permission to import
every module or package test. The finite source trace must distinguish eager,
lazy, metadata-query and dormant branches before actual admission.

## Windows native paths and compatibility

`.venv/Lib/site-packages/torch/__init__.py:169-288` computes torch/lib, exec-prefix
Library/bin, a possible distinct base Library/bin, userbase Library/bin and
prefix/bin. It may additionally select NVToolsExt/CUDA directories from controlled
environment/defaults. It enumerates all torch/lib DLLs, uses LoadLibraryExW
flags0x1100, and can mutate PATH then fall back to LoadLibraryW. The first L
design refuses that fallback; it does not edit Torch or pretend a full path
fixes dependent DLL lookup. Package initialization itself loads native code;
hidden GPUs do not imply no CUDA DLL initialization.

`torchaudio/_extension/utils.py:49-56` selects the first matching library file
and only warns on multiple matches. The new policy must require a unique exact
prepared choice. Its DLL load uses torch.ops.load_library. The `_init_dll_path`
PATH loop is called only on Windows Python>=3.8,<3.9, so it is not the selected
Python3.12 path. Branch analysis must use the actual runtime rather than treating
every source branch as executed. The CUDA-version check around lines116-130 is
not general binary/export compatibility.

Saved metadata reports Torch2.13.0+cu130 and torchaudio2.11.0. The inspected
torchaudio METADATA does not declare a Requires-Dist torch constraint; that
absence is not evidence that this pair is compatible. The L plan must identify
specific extension initialization, required symbols and safe version/ABI checks.
Actual failure remains a refused consumed attempt; no auto-upgrade or broader
compute probe is authorized.

## Resources and pytest behavior

MNE's exact `data/fsaverage/fsaverage-fiducials.fif` is the declared import-data
exception, never a wildcard for FIF/EEG. `_freesurfer.py:465-470` shows the
resource path and read_fiducials call; the trace does not by itself prove that
this branch runs in L. Source mapping must locate any actual eager call and
establish mediated read evidence before claiming observed resource coverage.
Library array initialization belongs to the narrow logged initialization phase,
before the full candidate numerical-constructor guard is installed.

The installed `_pytest/config/__init__.py:306-342` supplies version-specific
essential/default plugins, including subtests. The future runner must pin that
actual list and deliberately deny unused effectful plugins, cacheprovider and
stepwise. Environment-only autoload suppression does not reject a later direct
plugin registration. Importlib mode/plain assertions avoid unreviewed import and
assertion-rewrite bytecode behavior; plugin hook/fixture/run sentinels establish
the collect-only boundary. No pytest version compatibility has been executed.
