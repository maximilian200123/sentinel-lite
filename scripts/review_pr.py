"""Mechanical half of skills/review-pr: scan a branch's added lines for the banned
patterns in CLAUDE.md and check the register and open-bug list are consistent.

    python scripts/review_pr.py [base]      # base defaults to origin/main

Prints a markdown table for the PR's "Agent review" section. Exit 1 on any finding.
It cannot judge design or intent; the skill adds that part.
"""

import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

# (check name, file filter, pattern on an added line). Prose that only mentions a
# pattern (markdown, comments, tests that assert on it, this file) is skipped.
BANNED = [
    ("Hardcoded secret", r"\.py$|\.ya?ml$|\.toml$|\.json$",
     r"(?i)(api[_-]?key|secret|token|passw(or)?d)\s*[:=]\s*['\"][A-Za-z0-9_\-]{12,}['\"]"),
    ("String-built SQL", r"\.py$",
     r"(?i)f[\"'](SELECT|INSERT|UPDATE|DELETE)\b"
     r"|(SELECT|INSERT|UPDATE|DELETE)\b.*[\"']\s*(%|\+|\.format)"),
    ("Unsafe YAML load", r"\.py$", r"yaml\.load\(|yaml\.(Unsafe|Full)?Loader\b"),
    ("Debug mode on", r"\.py$", r"debug\s*=\s*True"),
    ("Bind to all interfaces", r"\.py$|\.ya?ml$|Makefile$", r"0\.0\.0\.0"),
    ("Unpinned action", r"\.github/workflows/.*\.ya?ml$", r"uses:\s*(?!\./)[^@\s]+@(?![0-9a-f]{40}\b)"),
    ("Over-broad workflow token", r"\.github/workflows/.*\.ya?ml$", r"write-all|pull_request_target"),
    ("Hook bypass", r"", r"--no-verify|core\.hooksPath(?![\s=]*\.githooks)"),
]
SKIP_FILES = r"^(docs/|memory/|skills/|tests/|scripts/review_pr\.py)|\.md$"
COMMENT = re.compile(r"^\s*(#|//)")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def added_lines(base: str) -> list[tuple[str, str]]:
    out, path = [], None
    for line in git("diff", "--unified=0", f"{base}...HEAD").splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("+") and path:
            out.append((path, line[1:]))
    return out


def scan(lines: list[tuple[str, str]]) -> dict[str, list[str]]:
    found = {name: [] for name, _, _ in BANNED}
    for path, text in lines:
        if re.search(SKIP_FILES, path) or COMMENT.match(text):
            continue
        for name, file_re, pattern in BANNED:
            if re.search(file_re, path) and re.search(pattern, text):
                found[name].append(f"`{path}`: `{text.strip()[:80]}`")
    return found


def consistency(base: str) -> list[str]:
    """Bugs closed in this branch must carry their docs and register evidence."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from open_bugs import OPEN_BUGS

    try:
        before = set(re.findall(r'"(B-\d\d)":', git("show", f"{base}:scripts/open_bugs.py")))
    except subprocess.CalledProcessError:  # base predates the open-bug list
        before = set()
    closed = sorted(before - set(OPEN_BUGS))
    problems = []
    report = (ROOT / "docs" / "BUG-REPORT.md").read_text(encoding="utf-8")
    risks = yaml.safe_load((ROOT / "docs" / "risk-register.yaml").read_text(encoding="utf-8"))["risks"]
    for bug in closed:
        if f"## {bug}," not in report:
            problems.append(f"{bug} closed but has no section in docs/BUG-REPORT.md")
        rows = [r for r in risks if bug in r["bugs"]]
        if not any(r["evidence"] for r in rows):
            problems.append(f"{bug} closed but its register row(s) have no evidence")
    return [f"closed in this branch: {', '.join(closed) or 'none'}"] + problems


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
    lines = added_lines(base)
    found = scan(lines)
    notes = consistency(base)
    print(f"Mechanical review of {len(lines)} added lines against `{base}`:\n")
    print("| Check | Result |\n|---|---|")
    for name, hits in found.items():
        print(f"| {name} | {'; '.join(hits) if hits else 'none'} |")
    print(f"| Register / bug report | {'; '.join(notes)} |")
    failed = any(found.values()) or len(notes) > 1
    print(f"\nresult: {'FINDINGS, fix before opening the PR' if failed else 'clean'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
