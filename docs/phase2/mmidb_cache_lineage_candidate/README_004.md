# Exact blocked directory-probe accounting, revision 004

The instrumented diagnostic identified exactly two blocked os.mkdir events
from data/__init__.py calling data/runtime.py. Both shared cache directories
already exist. pathlib.mkdir(exist_ok=True) suppresses PermissionError when
the path is an existing directory, so imports continued while the final
zero-denial assertion correctly refused a passing receipt.

This revision still denies both directory creation requests. It records
them as expected only for the exact two existing, non-reparse directory
paths. Successful completion requires exactly two such denials, zero
network or subprocess attempts and zero other outside writes. No directory
creation or shared-directory mutation is allowed by this accounting change.
All previous workers and failed receipts remain untouched. The actual
configuration, preprocessing functions, twelve comparison/hash boundaries,
signal tolerance and resource limits remain unchanged.

One fresh corrected probe is defined. Only its actual passing receipt and
root execution review can admit one subject001 reconstruction. This cannot
admit a model/case, cohort decision, Gate A acceptance or experiment freeze.
