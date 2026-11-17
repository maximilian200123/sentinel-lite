# Refused pushes to main (R-01, GitHub route 4)

Captured on branch `chore/governance` (PR #2) after `make setup` set `core.hooksPath=.githooks`.
GitHub Free gives no server-side protection on this private repo (`github-route.md`), so these
refusals come from `.githooks/pre-push` -> `scripts/guard_push.py`, and anything that gets past
them (`--no-verify`) is caught after the fact by the governance workflow (section 5).

The pre-commit refusal of a commit on `main` (`no-commit-to-branch`) is captured in
`commit-on-main-refused.md`. It can only run after this PR merges, because before that `main`
has no `.githooks/` directory. The first attempt, before the merge, went through on a local
`main` and was discarded unpushed. That is why the hook has to live on `main` itself.

## 2. Direct push to main (pre-push guard)
$ git push origin HEAD:main
guard_push: push to refs/heads/main refused: open a pull request instead
error: failed to push some refs to 'https://github.com/maximilian200123/sentinel-lite.git'
# exit code 1

## 3. Force push to main (pre-push guard)
$ git push --force origin HEAD:main
guard_push: push to refs/heads/main refused: open a pull request instead
error: failed to push some refs to 'https://github.com/maximilian200123/sentinel-lite.git'
# exit code 1

## 4. Force push rewriting a pushed feature branch (pre-push guard, non-fast-forward)
$ git push --force origin chore/governance
guard_push: non-fast-forward push to refs/heads/chore/governance refused: history rewrite (force push)
error: failed to push some refs to 'https://github.com/maximilian200123/sentinel-lite.git'
# exit code 1

## Remote state after all attempts
$ git ls-remote origin refs/heads/main refs/heads/chore/governance
46f5f0256eefd638045dec3425249f4cbf598ae4	refs/heads/chore/governance
2fbc3ea6a4d8b3ed210b609f818e9380ebb2a3a1	refs/heads/main
# exit code 0


## 5. Governance check on a commit that has not been merged through a PR

```console
$ GOVERNANCE_REF=origin/chore/governance python scripts/governance_check.py
ba31fce  PR #1         fix(ci): pin actions to SHAs, read-only token, no pull_request_target (B-09)
2fbc3ea  PR #1         Merge PR #1: fix(ci) B-09
46f5f02  NO MERGED PR  chore(governance): local guards, governance workflow, repo policy files

3 commits after baseline-vulnerable, 1 without a merged PR
# exit code 1
```

On `main` the same script runs in `.github/workflows/governance.yml` on every push.
