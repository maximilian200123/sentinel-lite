# GitHub route 4: why governance is evidence-based

Account `maximilian200123` is on GitHub Free and the repository is private. Both ways of
protecting `main` server-side were tried through the API on 2026-11-17 and refused:

```console
$ gh api -X POST repos/maximilian200123/sentinel-lite/rulesets --input protect-main.json
{"message":"Upgrade to GitHub Pro or make this repository public to enable this feature.","status":"403"}

$ gh api repos/maximilian200123/sentinel-lite/branches/main/protection
{"message":"Upgrade to GitHub Pro or make this repository public to enable this feature.","status":"403"}
```

So the controls for R-01 are, in order:

1. **Prevent locally.** `.githooks/pre-commit` runs `no-commit-to-branch`, and `.githooks/pre-push`
   (`scripts/guard_push.py`) refuses pushes to `main` and non-fast-forward pushes.
2. **Prevent for the agent.** Claude Code deny rules and a PreToolUse hook (`.claude/`, Phase 4).
3. **Detect on the server.** `.github/workflows/governance.yml` fails on every push to `main` that
   contains a commit without a merged PR (`scripts/governance_check.py`).

What GitHub Free *did* allow on this private repo (see `github-actions-settings.md`): the
required-SHA-pinning Actions policy and a read-only default workflow token.

The same policy refused the old `ci-baseline` workflow on PR #1 before any step ran
(run https://github.com/maximilian200123/sentinel-lite/actions/runs/44133668336):

```
##[error]The actions actions/checkout@v4 and actions/setup-python@v5 are not allowed in
maximilian200123/sentinel-lite because all actions must be pinned to a full-length commit SHA.
```
