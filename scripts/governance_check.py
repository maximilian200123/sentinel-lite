"""Governance check for GitHub route 4 (R-01, R-06).

GitHub Free cannot protect main on a private repo, so this proves it after the fact:
every commit on main after the tag baseline-vulnerable must belong to a merged pull
request. The two commits up to that tag (register, baseline) are the documented
exception: they existed before the repository had any controls.

Run by .github/workflows/governance.yml on every push to main, or locally:
    GITHUB_TOKEN=... GITHUB_REPOSITORY=owner/repo python scripts/governance_check.py
"""

import json
import os
import subprocess
import sys
import urllib.request

EXCEPTION_TAG = "baseline-vulnerable"
API = "https://api.github.com"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def merged_prs(repo: str, sha: str, token: str) -> list[int]:
    req = urllib.request.Request(
        f"{API}/repos/{repo}/commits/{sha}/pulls",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310 (fixed https host)
        pulls = json.load(resp)
    return [p["number"] for p in pulls if p.get("merged_at") and p["base"]["ref"] == "main"]


def main() -> int:
    repo, token = os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"]
    head = os.environ.get("GOVERNANCE_REF", "HEAD")
    commits = git("rev-list", "--reverse", f"{EXCEPTION_TAG}..{head}").split()
    violations = 0
    for sha in commits:
        prs = merged_prs(repo, sha, token)
        subject = git("log", "-1", "--format=%s", sha).strip()
        status = f"PR #{prs[0]}" if prs else "NO MERGED PR"
        violations += not prs
        print(f"{sha[:7]}  {status:<13} {subject}")
    print(f"\n{len(commits)} commits after {EXCEPTION_TAG}, {violations} without a merged PR")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
