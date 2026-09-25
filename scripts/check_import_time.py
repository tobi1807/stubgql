"""Fail if `import stubgql` exceeds the cold-start budget.

stubgql often runs in short-lived environments such as Lambda, where import
time is paid on every cold start.
"""

import re
import subprocess
import sys

BUDGET_MS = 500


def main() -> int:
    result = subprocess.run(
        [sys.executable, "-X", "importtime", "-c", "import stubgql"],
        capture_output=True,
        text=True,
        check=True,
    )
    # Lines look like: "import time:   self [us] | cumulative | imported package"
    pattern = re.compile(r"import time:\s+\d+\s+\|\s+(\d+)\s+\|\s+stubgql$")
    for line in result.stderr.splitlines():
        match = pattern.search(line)
        if match:
            elapsed_ms = int(match.group(1)) / 1000
            print(f"import stubgql: {elapsed_ms:.1f} ms (budget {BUDGET_MS} ms)")
            return 0 if elapsed_ms <= BUDGET_MS else 1
    print("could not find stubgql in -X importtime output", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
