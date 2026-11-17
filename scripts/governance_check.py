"""Governance check for GitHub route 4 (R-01, R-06).

GitHub Free cannot protect main on a private repo, so this proves it after the fact:
every commit on main after the tag baseline-vulnerable must belong to a merged pull
request whose `ci` workflow passed on the PR head. That is the Free-plan stand-in for
"PR required" plus "status checks required". The two commits up to the tag (register,
baseline) are the documented exception: they existed before the repo had any controls.

Run by .github/workflows/governance.yml on every push to main, or locally:
    GITHUB_TOKEN=... GITHUB_REPOSITORY=owner/repo python scripts/governance_check.py
"""

import json
import os
import subprocess
import sys
import urllib.request
from functools import cache

EXCEPTION_TAG = "baseline-vulnerable"
REQUIRED_WORKFLOW = "ci"
API = "https://api.github.com"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def api(path: str):
    req = urllib.request.Request(
        f"{API}/repos/{os.environ['GITHUB_REPOSITORY']}/{path}",
        headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                 "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310 (fixed https host)
        return json.load(resp)


def merged_pr(sha: str) -> dict | None:
    pulls = api(f"commits/{sha}/pulls")
    merged = [p for p in pulls if p.get("merged_at") and p["base"]["ref"] == "main"]
    return merged[0] if merged else None


@cache
def ci_passed(head_sha: str) -> bool:
    runs = api(f"actions/runs?head_sha={head_sha}&event=pull_request")["workflow_runs"]
    return any(r["name"] == REQUIRED_WORKFLOW and r["conclusion"] == "success" for r in runs)


def verdict(sha: str) -> tuple[bool, str]:
    pr = merged_pr(sha)
    if pr is None:
        return False, "NO MERGED PR"
    if not ci_passed(pr["head"]["sha"]):
        return False, f"PR #{pr['number']} CI NOT GREEN"
    return True, f"PR #{pr['number']} ci ok"


def main() -> int:
    head = os.environ.get("GOVERNANCE_REF", "HEAD")
    commits = git("rev-list", "--reverse", f"{EXCEPTION_TAG}..{head}").split()
    violations = 0
    for sha in commits:
        ok, status = verdict(sha)
        violations += not ok
        print(f"{sha[:7]}  {status:<22} {git('log', '-1', '--format=%s', sha).strip()}")
    print(f"\n{len(commits)} commits after {EXCEPTION_TAG}, {violations} violating governance")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
