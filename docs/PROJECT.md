# Sentinel-Lite: project report

## Goal and scope

The lab asks for a small security service, a risk register for it, and a governed way of
changing it with an AI agent. This project delivers all three.

- **The service** is a Flask API that ingests security events, enriches them with threat
  intelligence, tags them with ATT&CK-mapped detection rules and stores them. It is
  452 lines of application code and has three runtime dependencies.
- **The register** (`RISK-REGISTER.xlsx`, built from `docs/risk-register.yaml`) holds ten risks.
  It was written *before* the baseline code (Phase 1), so each seeded bug was placed against a
  risk that already existed, not the other way round.
- **The governance** means every change after the baseline arrived as a pull request with CI,
  a self-review checklist and an agent review. The repository holds the evidence for each of
  these.

Out of scope: production deployment, TLS, multi-user identity, a real MISP or Shodan
connection, containers.

## Risks

All ten rows are Implemented. "After" is the residual score once the control is in place.

| Risk | Asset | Bugs | Before (L x I) | After (L x I) | Status |
|---|---|---|---|---|---|
| R-01 | main branch of sentinel-lite (the code the professor clones) | B-10 | 4 x 4 = 16 | 2 x 4 = 8 | Implemented |
| R-02 | Service API key and any credential the agent can read | B-01, B-07 | 4 x 5 = 20 | 2 x 4 = 8 | Implemented |
| R-03 | AI agent context: CLAUDE.md, memory/, skills/ | B-10 | 3 x 4 = 12 | 2 x 3 = 6 | Implemented |
| R-04 | CI pipeline and its GITHUB_TOKEN | B-09 | 3 x 5 = 15 | 1 x 4 = 4 | Implemented |
| R-05 | Runtime dependencies (requirements.txt) | B-08 | 4 x 3 = 12 | 2 x 3 = 6 | Implemented |
| R-06 | main branch review quality | none | 4 x 4 = 16 | 3 x 4 = 12 | Implemented |
| R-07 | Stored security events (SQLite) and generated reports | B-02, B-03 | 4 x 4 = 16 | 1 x 4 = 4 | Implemented |
| R-08 | Ingest normaliser and detection rules | B-04, B-05 | 4 x 4 = 16 | 2 x 3 = 6 | Implemented |
| R-09 | Service control plane (/ingest, /admin/*) and its audit log | B-06, B-07 | 4 x 5 = 20 | 1 x 4 = 4 | Implemented |
| R-10 | Analyst triage queue fed by ingested events | none | 4 x 4 = 16 | 2 x 3 = 6 | Implemented |

Two rows carry no seeded bug.

- **R-06 (review quality)** is the one row whose residual stays Medium (12). It is explained
  below under "Review is agent-assisted, not enforced".
- **R-10 (missed malicious traffic)** is the reason the service exists. Enrichment is its
  control, and `docs/evidence/enrichment.md` shows it changing the outcome.

The ten seeded bugs, their exploits, blast radius and fixes are in `docs/BUG-REPORT.md`. It
ends with six bug chains, because several bugs only become critical in combination (B-06 with
B-04 gives anonymous code execution).

## Architecture

The diagram and module table are in `README.md`. The design decisions behind them:

- **One boundary for untrusted input.** `normalize` is the first pipeline step and the only
  place a raw event is parsed (B-05). Later steps trust its output.
- **One check for authentication.** The API key is checked once in `before_request`, so a new
  route is protected by default (B-06).
- **One module per external resource.** Only `store.py` touches SQLite (always with
  placeholders, B-02). Only `intel.py` talks to intelligence sources, through the
  `IntelProvider` interface.
- **Fail closed, keep working.** No key configured means nothing authenticates. A bad rule
  file is refused with 400 and the previous rules stay active (B-04), so detection never goes
  blind.
- **Loopback only.** The bind address is fixed to `127.0.0.1` in `config.py`, not read from
  the environment.

## Threat intelligence

`LocalFeedProvider` reads `data/intel_feed.json`, a small feed of RFC 5737 documentation IPs.
A match adds the `threat.indicator.matched` tag and a `threat.indicator` object, and raises
`event.risk_score`. From `docs/evidence/enrichment.md`, the same event scores 10 from a clean
source, 60 from a feed IP and 90 when the SSH brute-force rule also fires.

- **MISP.** `MispProvider` implements the same interface against MISP's
  `/attributes/restSearch`. It is tested with a recorded response
  (`tests/test_app.py::test_misp_provider_parses_rest_search`). It isn't wired in by default,
  because no MISP instance runs on the lab machine.
- **Shodan** is documented only. It would fit as a second provider that adds context (open
  ports, banners) rather than a verdict. Its rate limits and API key mean it belongs in a
  background job that fills a local cache, never in a request handler. `CLAUDE.md` states
  that rule.

## How the AI agent worked

The code, tests, register and PRs were produced by Claude Code, steered by the files below.
The student set the goal and the rules (`AGENT-PROMPT.md`, §3) and approved one-off actions
such as the gh login.

| File | Purpose |
|---|---|
| `CLAUDE.md`, `app/CLAUDE.md` | role, voice, banned patterns and which check catches each, stack conventions |
| `memory/` | five corrections learned during this project, each with why and how to apply |
| `skills/fix-seeded-bug/` | the procedure every fix PR followed: un-gate the test, see it red, fix, evidence, register, review |
| `skills/review-pr/` | the review that produces each PR's "Agent review" section (`scripts/review_pr.py` plus a judgment pass) |
| `.claude/settings.json`, `.claude/hooks/guard.py` | deny rules and a PreToolUse hook: no push to `main`, no force push, no `--no-verify`, no secrets, no edits to `.claude/` |
| `.github/pull_request_template.md` | the checklist every PR body carries |

**Memory is context, not policy.** B-10 showed why. A memory note told the agent to push to
`main` and skip tests, and in the baseline nothing stopped it. The fix keeps the useful part of
memory (real corrections, such as "gitleaks skips values containing FAKE" and "test the platform
before claiming a limit") and moves every rule that matters into something that runs: the
hook, the deny rules and the git hooks. `test_b10_agent_context_has_no_instruction_to_bypass_controls`
fails if a bypass instruction appears in the agent's context again.

**The agent made mistakes, and the record shows them.**

- gitleaks refused one of the agent's real commits (PR #7). An evidence file held a curl line
  with a deliberately wrong key, and the line now carries an inline allow with the reason.
- The agent's first "commit on `main` is refused" demo went through, because the hooks weren't
  on `main` yet. The commit was discarded before any push, redone after the merge (refused),
  and recorded as the memory note `hooks-live-on-the-branch`.
- The agent first claimed that GitHub's SHA-pinning policy needed a paid plan, then tested the
  API, enabled it and corrected the docs. That became the note
  `test-the-platform-before-claiming-a-limit`.

`docs/evidence/` keeps the output of each.

**One limit of the agent controls was observed.** Claude Code loads `.claude/` when a session
starts in the project folder. The session that built this project started in the home folder,
so its hook was inactive. That is documented in `docs/evidence/hook-blocks.md`, and the hook is
tested directly by `tests/test_repo_policy.py::test_b10_*`. A session started inside the repo
loads it.

### Review is agent-assisted, not enforced (R-06)

The agent's review sees the diff it wrote, and on GitHub Free nothing forces a second pair of
eyes before merge. So R-06 keeps likelihood 3 after its controls.

What does run on every PR:

- CI (`make check`, gitleaks, zizmor)
- the mechanical review script, which fails on banned patterns and on a closed bug without a
  report section or register evidence
- the governance workflow on `main`, which proves every commit came through a merged PR with
  green CI

What would lower R-06 further is an automated reviewer in GitHub Actions:

1. Store a model API key as an **encrypted repository secret** (Settings → Secrets → Actions).
   Never put it in the workflow file or `.env`.
2. Add a workflow on `pull_request` with `permissions: contents: read, pull-requests: write`
   only for that job, and actions pinned to commit SHAs like the rest.
3. Fork PRs don't receive repository secrets on `pull_request`, and that's the point. Never
   switch to `pull_request_target` to "fix" it, because that is exactly B-09.
4. Treat the reviewer's comments as findings to judge, not as approval. Required reviews would
   need GitHub Pro or an organization, which is route 1 or 2.

No API key was available for this lab, so this was not built (`AGENT-PROMPT.md`
configuration: no API key).

## Governance under route 4

The repo is private on a personal GitHub Free account. Rulesets and branch protection return
403 (`docs/evidence/github-route.md`). The controls that replace them, and the evidence for
each:

| Control | Where | Evidence |
|---|---|---|
| No commits on `main` locally | `.githooks/pre-commit` (`no-commit-to-branch`) | `docs/evidence/commit-on-main-refused.md` |
| No push or force push to `main` | `.githooks/pre-push` → `scripts/guard_push.py` | `docs/evidence/push-refusals.md`, `tests/test_guard_push.py` |
| The agent can't push, force, skip hooks or read secrets | `.claude/` | `docs/evidence/hook-blocks.md`, `tests/test_repo_policy.py::test_b10_*` |
| Secrets refused before commit and in CI | gitleaks with a project rule | `docs/evidence/gitleaks-refusal.md` |
| Actions pinned to SHAs, read-only token | repository policy + zizmor | `docs/evidence/github-actions-settings.md`, `docs/evidence/zizmor-b09.md` |
| Every commit on `main` came through a merged, green PR | `.github/workflows/governance.yml` | `docs/evidence/final-red-green.md` |

These are weaker than server-side protection in one way. Local hooks can be skipped by
someone who means to, for example with `git push --no-verify` from their own terminal. The
governance workflow detects that after the fact but cannot prevent it. Route 1 or 2 (GitHub
Pro, or the ULBS organization) would turn detection into prevention.

## Limits and what was not built

- **Not built:** secrets encryption with SOPS/age, a Dockerfile, image scanning (Trivy), SBOM
  (Syft) and signing (Cosign). The service runs from a venv, has no image to scan, and its one
  secret lives in a gitignored `.env`.
- **No rate limiting and a single shared API key** (B-06 residual).
- **No dependency hashes.** The lock pins versions, not file hashes (B-08 residual).
  Dependabot watches GitHub Actions only.
- **CODEOWNERS is advisory** on GitHub Free. It names the reviewer but cannot require them.
- **Heavy scanners run in CI only.** Local `make check` runs ruff, bandit, pip-audit and the
  tests in about 25 seconds. gitleaks runs locally as a pre-commit hook.
