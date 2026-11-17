# A commit on main is refused locally (R-01)

Captured on `main` right after PR #2 merged, so `.githooks/pre-commit` exists on the branch
(the attempt before the merge is explained in `push-refusals.md`). The README change was then discarded.

```console
$ git branch --show-current
main
$ git add README.md && git commit -m "docs: direct edit on main"
Detect hardcoded secrets.................................................Passed
don't commit to branch...................................................Failed
- hook id: no-commit-to-branch
- exit code: 1
detect private key.......................................................Passed
check for added large files..............................................Passed
check yaml...........................................(no files to check)Skipped
check json...........................................(no files to check)Skipped
# commit exit code: 1
$ git log --oneline -1
a23c4e3 Merge PR #2: chore(governance) route 4 controls
```
