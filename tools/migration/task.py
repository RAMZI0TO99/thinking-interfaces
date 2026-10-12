"""Log a guarded setup subprocess; descendants remain in the parent's private Job."""

import json
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    out = Path(sys.argv[1])
    with (out / "command.log").open("xb") as log:
        result = subprocess.run(sys.argv[2:], stdout=log, stderr=subprocess.STDOUT, check=False)
    with (out / "command-result.json").open("x", encoding="utf-8") as stream:
        json.dump({"returncode": result.returncode}, stream)
    sys.exit(result.returncode)
