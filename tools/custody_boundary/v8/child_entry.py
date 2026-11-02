"""Fixed probe or admitted owned-fixture tests; never writes inventory evidence."""
import importlib.util
import sys
import unittest
import io
import json
from pathlib import Path

HERE = Path(__file__).absolute().parent


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in {'tests', 'inventory'}:
        raise ValueError('fixed child command required')
    attempt = Path(sys.argv[2])
    if not attempt.is_absolute() or not attempt.is_dir():
        raise ValueError('attempt required')
    if sys.argv[1] == 'inventory':
        return 0
    spec = importlib.util.spec_from_file_location('_inventory_tests', HERE / 'test_inventory.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.FIXTURE_ROOT = attempt / 'test-fixtures'
    class BoundedText(io.StringIO):
        def write(self, text):
            if self.tell() + len(text) > 65536:
                raise ValueError('test report bound')
            return super().write(text)
    report = BoundedText()
    result = unittest.TextTestRunner(stream=report, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    payload = {'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'skipped': len(result.skipped), 'successful': result.wasSuccessful() and result.testsRun > 0 and not result.skipped,
        'report': report.getvalue(), 'launch_authorized': False, 'scientific_admission': False}
    with (attempt / 'test-report.json').open('xb') as stream:
        stream.write((json.dumps(payload, indent=2) + '\n').encode())
        stream.flush()
    return 0 if result.wasSuccessful() and result.testsRun > 0 and not result.skipped else 1


if __name__ == '__main__':
    raise SystemExit(main())
