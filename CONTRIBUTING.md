# Contributing

Every change, from a person or from the AI agent, reaches `main` through a pull request.

## Setup

```sh
make setup   # venv, dev tools, and git hooks (core.hooksPath = .githooks)
```

`make setup` points git at `.githooks/`:
- `pre-commit` runs gitleaks, `no-commit-to-branch` (main), private-key and large-file checks.
- `pre-push` refuses any push to `main` and any non-fast-forward (force) push.

Never bypass them with `--no-verify`. The governance workflow fails if a commit reaches
`main` without a merged pull request, and the agent's PreToolUse hook blocks the flag.

## Flow

1. Branch from `main`: `fix/b-0X-<topic>`, `feat/<topic>`, `chore/<topic>`, `docs/<topic>`.
2. Commit with [Conventional Commits](https://www.conventionalcommits.org/):
   `fix(api): parameterize event search (B-02)`.
3. Run `make check` (lint, register check, tests, bandit, pip-audit). It must pass.
4. Run the `review-pr` skill and fill in the pull request template, including the
   **Agent review** section and the risk and bug IDs.
5. Merge with a merge commit (not squash) after CI passes, so every commit on `main`
   traces to its PR.

## Fixing a seeded bug

Follow `skills/fix-seeded-bug/SKILL.md`. In short: delete the bug's entry from
`scripts/open_bugs.py` (its regression tests now gate), fix the code until they pass,
update `docs/risk-register.yaml` (`make register`) and `docs/BUG-REPORT.md`.

## GitHub route

Route 4 (GitHub Free, evidence-based governance). See `docs/PROJECT.md`.
