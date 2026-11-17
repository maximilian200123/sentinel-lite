"""Seeded bugs still open on this branch. Each fix PR deletes its own entry.

While a bug is listed:
- its regression tests are expected to fail (pytest marks them xfail, strict=True,
  so a test that starts passing without its entry being removed fails the run);
- the scanner findings it causes are excepted by ID, so make check still catches
  every finding that is NOT a known, documented, open seeded bug.

On main after Phase 5 this dict is empty and no exception remains.

    python scripts/open_bugs.py bandit      -> comma list for bandit -s
    python scripts/open_bugs.py pip-audit   -> --ignore-vuln flags for pip-audit
"""

import sys

OPEN_BUGS: dict[str, dict[str, list[str]]] = {
    "B-04": {"bandit": ["B506"]},
    "B-05": {},
    "B-08": {"pip-audit": ["PYSEC-2026-1873", "PYSEC-2026-1872", "PYSEC-2026-2275"]},
}


def exceptions(tool: str) -> list[str]:
    return [i for bug in OPEN_BUGS.values() for i in bug.get(tool, [])]


if __name__ == "__main__":
    tool = sys.argv[1]
    ids = exceptions(tool)
    if tool == "bandit":
        print(",".join(ids))
    elif tool == "pip-audit":
        print(" ".join(f"--ignore-vuln {i}" for i in ids))
    else:
        sys.exit(f"unknown tool {tool!r}")
