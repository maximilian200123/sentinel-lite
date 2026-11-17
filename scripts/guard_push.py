"""pre-push guard (R-01). Git calls it with the remote name and URL as arguments
and one line per ref on stdin: <local ref> <local sha> <remote ref> <remote sha>.

Refuses:
- any push that updates or deletes the remote main branch (changes reach main by PR);
- any non-fast-forward update (a force push rewriting history the remote already has).

GitHub Free cannot enforce this server-side on a private repo, so it runs here, and
the governance workflow detects anything that gets past it (git push --no-verify).
"""

import subprocess
import sys

PROTECTED = "refs/heads/main"
ZERO = "0" * 40


def is_ancestor(old: str, new: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", old, new], capture_output=True, check=False
    ).returncode == 0


def problems(lines: list[str]) -> list[str]:
    found = []
    for line in lines:
        local_ref, local_sha, remote_ref, remote_sha = line.split()
        if remote_ref == PROTECTED:
            found.append(f"push to {remote_ref} refused: open a pull request instead")
        elif remote_sha != ZERO and local_sha != ZERO and not is_ancestor(remote_sha, local_sha):
            found.append(f"non-fast-forward push to {remote_ref} refused: history rewrite (force push)")
    return found


def main() -> int:
    found = problems([ln for ln in sys.stdin.read().splitlines() if ln.strip()])
    for p in found:
        print(f"guard_push: {p}", file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
