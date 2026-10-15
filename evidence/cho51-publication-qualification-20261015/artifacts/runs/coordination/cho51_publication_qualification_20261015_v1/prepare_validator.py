"""Prepare a fresh, synthetic-only publication qualification child; never launch it."""
import ast
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
prior = ROOT / 'runs/coordination/cho51_recorder_qualification_20261015_v1/validate_003.py'
text = prior.read_text(encoding='utf-8')

def change(old, new):
    global text
    if text.count(old) != 1:
        raise ValueError('unambiguous reviewed validator replacement required: ' + old)
    text = text.replace(old, new)

change('"""Run only prepared synthetic collector cases inside a fresh native parent Job."""',
       '"""Run only mocked51 publication boundaries and fabricated publication-byte checks."""')
change("str(ROOT / 'docs/phase2/cho51_recorder_collection_v1/test_collector_shared.py'),",
       "*[str(ROOT / node) for node in pins['test_nodes']],")
change('results.items == 20', "results.items == pins['expected_cases']")
change('and not unexpected and not any(path.exists() for path in pause_paths))',
       "and len(results.calls) == pins['expected_cases']\n"
       "             and all(row['phase'] == 'call' and row['outcome'] == 'passed' for row in results.calls)\n"
       '             and not unexpected and not any(path.exists() for path in pause_paths))')
change("str(OUT / 'pytest-temp')", "str(OUT / 't')")
change("'cho51_recorder_synthetic_qualification_v1'", "'cho51_publication_synthetic_qualification_v1'")
change("'passed': qualified, 'pytest_exit': int(code), 'collected_cases': results.items,",
       "'passed': qualified, 'pytest_exit': int(code), 'collected_cases': results.items,\n"
       "    'pins_sha256': args.expect_pins,")
change("'fixture_asset_loader_replaced': True, 'real_input_composition_qualified': False,",
       "'dependency_mocked_publication_boundaries': pins['dependency_mocked_boundaries'],\n"
       "    'hybrid_composition_cases': pins['hybrid_composition_cases'],\n"
       "    'fabricated_publication_byte_checks': pins['publication_byte_cases'],\n"
       "    'actual_asset_loader_invoked': False, 'real_input_composition_qualified': False,\n"
       "    'actual_publication_history_verified': False, 'selected_tensors_verified': False,\n"
       "    'weight_blobs_are_fabricated_and_not_deserialized': True,")
ast.parse(text)
with (RUN / 'validate.py').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(text)
print('Prepared fresh synthetic publication validator, no launch.')
