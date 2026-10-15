"""Create an owned successor validator, without launching it or importing models."""
import ast
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
text = (ROOT / 'runs/coordination/cho51_publication_qualification_20261015_v1/validate.py').read_text(encoding='utf-8')

def change(old, new):
    global text
    if text.count(old) != 1:
        raise ValueError('unambiguous predecessor replacement required: ' + old)
    text = text.replace(old, new)

change('"""Run only mocked51 publication boundaries and fabricated publication-byte checks."""',
       '"""Qualify strict tensor metadata/native boundaries and prepare an untrained fixture."""')
change('OUT.mkdir(exist_ok=False)', "OUT.mkdir(exist_ok=False)\nTENSOR_WORKSPACE = RUN / 'case_001'\nif TENSOR_WORKSPACE.exists():\n    raise ValueError('unused tensor workspace required')\nfixture_phase = False\ngit_queries = 0")
change('def audit(event, values):', '''def owned(path):
    return path.is_relative_to(OUT) or path.is_relative_to(TENSOR_WORKSPACE)

def fixture_git(values):
    global git_queries
    import subprocess
    executable, arguments, cwd, environment = values
    git = Path(pins['git_executable'])
    forms = [
        [pins['git_command_executable'], '--no-optional-locks', 'rev-parse', '--verify', 'HEAD'],
        [pins['git_command_executable'], '--no-optional-locks', 'status', '--porcelain', '--untracked-files=all'],
    ]
    match = arguments in forms if isinstance(arguments, list) else arguments in [subprocess.list2cmdline(row) for row in forms]
    frame = sys._getframe(1)
    source_stack = False
    while frame:
        if frame.f_code.co_name == 'capture_source' and Path(frame.f_code.co_filename).resolve() == ROOT / 'core/provenance.py':
            source_stack = True
        frame = frame.f_back
    if (not fixture_phase or not match or not source_stack or environment is not None
            or cwd is None or Path(cwd).resolve() != OUT / 'f'
            or (executable is None and os.name != 'nt')
            or (executable is not None and Path(executable).resolve() != git)):
        refuse('subprocess.Popen', values)
    git_queries += 1

def audit(event, values):''')
change("elif event.startswith('socket.') or event in {'subprocess.Popen', 'os.system', 'os.startfile'}:",
       "elif event == 'subprocess.Popen':\n        fixture_git(values)\n    elif event.startswith('socket.') or event in {'os.system', 'os.startfile'}:")
change('if writing and not path.is_relative_to(OUT)', 'if writing and not owned(path)')
change("if not path.is_relative_to(OUT) and not (event == 'os.mkdir' and path.is_dir()):",
       "if not owned(path) and not (event == 'os.mkdir' and path.is_dir()):")
change('torch.nn.Module.__init__ = no_model', 'original_model_init = torch.nn.Module.__init__\ntorch.nn.Module.__init__ = no_model')
anchor="], plugins=[results])"
change(anchor, anchor + '''
if code == 0 and len(results.calls) == pins['expected_cases'] and all(row['outcome'] == 'passed' for row in results.calls) and not denied:
    if any(path.exists() for path in pause_paths):
        raise ValueError('genuine peer pause before fixture construction')
    torch.nn.Module.__init__ = original_model_init
    torch.optim.Optimizer.__init__ = no_model
    torch.Tensor.backward = no_model
    torch.autograd.backward = no_model
    import importlib.util
    fixture_module_path = RUN / 'prepare_fixture.py'
    fixture_spec = importlib.util.spec_from_file_location('_cho51_tensor_fixture_preparation', fixture_module_path)
    fixture_module = importlib.util.module_from_spec(fixture_spec)
    fixture_spec.loader.exec_module(fixture_module)
    fixture_phase = True
    fixture_scope = fixture_module.prepare(OUT, TENSOR_WORKSPACE)
    fixture_phase = False
else:
    fixture_scope = None
''')
change("and not unexpected and not any(path.exists() for path in pause_paths))",
       "and fixture_scope is not None and not denied and not unexpected and not any(path.exists() for path in pause_paths))")
change("'cho51_publication_synthetic_qualification_v1'", "'cho51_tensor_contract_fixture_qualification_v1'")
change("    'dependency_mocked_publication_boundaries': pins['dependency_mocked_boundaries'],\n    'hybrid_composition_cases': pins['hybrid_composition_cases'],\n    'fabricated_publication_byte_checks': pins['publication_byte_cases'],\n    'actual_asset_loader_invoked': False, 'real_input_composition_qualified': False,\n    'actual_publication_history_verified': False, 'selected_tensors_verified': False,\n    'weight_blobs_are_fabricated_and_not_deserialized': True,",
       "    'mocked_native_and_digest_boundary_cases': pins['expected_cases'],\n    'fixture_prepared': fixture_scope, 'read_only_git_queries': git_queries,\n    'actual_input_or_selected_study_weights_used': False,\n    'actual_publication_history_verified': False, 'selected_tensors_verified': False,\n    'untrained_eegnet_fixture_constructed': fixture_scope is not None,\n    'tensor_restore_performed_in_this_job': False,")
ast.parse(text)
with (RUN / 'validate.py').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(text)

observer = (ROOT / 'runs/coordination/cho51_publication_qualification_20261015_v1/observe.py').read_text(encoding='utf-8')
observer = observer.replace('cho51_publication_native_resource_observation_v1', 'cho51_tensor_native_resource_observation_v1')
with (RUN / 'observe.py').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(observer)
print('Fresh tensor validator and observer prepared, no launch.')
