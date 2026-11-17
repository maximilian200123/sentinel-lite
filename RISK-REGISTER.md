# Risk register

Generated from `docs/risk-register.yaml` by `scripts/build_register.py`. Do not edit by hand. The graded file is `RISK-REGISTER.xlsx`.

| ID | Register | Asset | Bugs | L x I | Inherent | Res. L x I | Residual | Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| R-01 | Operational | main branch of sentinel-lite (the code the professor clones) | B-10 | 4 x 4 | 16 (High) | 2 x 4 | 8 (Medium) | Implemented | .githooks/pre-push; scripts/guard_push.py; .github/workflows/governance.yml; .claude/hooks/guard.py; docs/evidence/push-refusals.md; docs/evidence/commit-on-main-refused.md; docs/evidence/github-route.md |
| R-02 | Operational | Service API key and any credential the agent can read | B-01, B-07 | 4 x 5 | 20 (High) | 2 x 4 | 8 (Medium) | Open | app/config.py; .env.example; scripts/init_env.py; tests/test_seeded_bugs.py::test_b01_api_key_comes_from_environment; .gitleaks.toml; .github/workflows/ci.yml; docs/evidence/gitleaks-refusal.md |
| R-03 | Operational | AI agent context: CLAUDE.md, memory/, skills/ | B-10 | 3 x 4 | 12 (Medium) | 2 x 3 | 6 (Low) | Implemented | .claude/settings.json; .claude/hooks/guard.py; tests/test_repo_policy.py::test_b10_hook_blocks_dangerous_agent_action; docs/evidence/hook-blocks.md; .github/CODEOWNERS |
| R-04 | Operational | CI pipeline and its GITHUB_TOKEN | B-09 | 3 x 5 | 15 (High) | 1 x 4 | 4 (Low) | Implemented | .github/workflows/ci.yml; tests/test_repo_policy.py::test_b09_third_party_actions_pinned_to_commit_sha; docs/evidence/zizmor-b09.md; docs/evidence/github-actions-settings.md |
| R-05 | Operational | Runtime dependencies (requirements.txt) | B-08 | 4 x 3 | 12 (Medium) | 2 x 3 | 6 (Low) | Open | - |
| R-06 | Operational | main branch review quality | - | 4 x 4 | 16 (High) | 3 x 4 | 12 (Medium) | Implemented | .github/pull_request_template.md; skills/review-pr/SKILL.md; scripts/review_pr.py; tests/test_review_pr.py::test_flags_banned_code; scripts/governance_check.py |
| R-07 | Internal | Stored security events (SQLite) and generated reports | B-02, B-03 | 4 x 4 | 16 (High) | 1 x 4 | 4 (Low) | Open | - |
| R-08 | Internal | Ingest normaliser and detection rules | B-04, B-05 | 4 x 4 | 16 (High) | 2 x 3 | 6 (Low) | Open | - |
| R-09 | Internal | Service control plane (/ingest, /admin/*) and its audit log | B-06, B-07 | 4 x 5 | 20 (High) | 1 x 4 | 4 (Low) | Open | app/__init__.py; tests/test_seeded_bugs.py::test_b06_endpoints_require_api_key; tests/test_seeded_bugs.py::test_b06_debug_mode_is_off; docs/evidence/b06-live.md |
| R-10 | External | Analyst triage queue fed by ingested events | - | 4 x 4 | 16 (High) | 2 x 3 | 6 (Low) | Open | - |

## Threat and control per risk

### R-01, main branch of sentinel-lite (the code the professor clones)
- Threat: AI agent or student pushes straight to main or force-pushes, landing unreviewed code or rewriting history
- Vulnerability: Agent runs git with the student's push rights; GitHub Free gives no server-side branch protection on a private repo
- Control and why the score drops: Local no-commit-to-branch and pre-push guard refuse commits on main, pushes to main and non-fast-forward pushes; Claude Code deny rules plus a PreToolUse hook block the same commands for the agent; governance workflow flags any commit on main without a merged PR. L drops to 2, not 1: client-side hooks can be skipped with --no-verify and the workflow detects after the fact instead of preventing.

### R-02, Service API key and any credential the agent can read
- Threat: Plaintext key committed to source or written to logs, then read by anyone with a clone or the log file (T1552.001)
- Vulnerability: API key hardcoded in app/config.py; request headers logged verbatim
- Control and why the score drops: Key read from the environment (.env.example documents it); gitleaks in pre-commit and in CI; log redaction of tokens. L drops because two independent scanners must both miss a key; I drops to 4 because the key no longer lives in history or logs, but a leaked key still opens the API.

### R-03, AI agent context: CLAUDE.md, memory/, skills/
- Threat: Memory poisoning (MITRE ATLAS AI agent context poisoning): a planted note steers later agent sessions to push to main, skip tests or read secrets (ATLAS AML.T0051.001)
- Vulnerability: Memory and skill files are trusted context, not reviewed, and nothing enforces the rules they state
- Control and why the score drops: CODEOWNERS covers memory/, skills/, .claude/ so changes arrive by PR; the dangerous actions are blocked by deny rules and a PreToolUse hook, so a poisoned note can persuade but cannot compel. I drops because the hook removes the worst outcomes; L drops because poisoned text must survive a PR review.

### R-04, CI pipeline and its GITHUB_TOKEN
- Threat: A third-party action's moving tag is repointed to malicious code, or a PR's code runs under pull_request_target with a write token (T1195.002)
- Vulnerability: Actions referenced by @v4 tags, permissions: write-all, pull_request_target checking out PR code
- Control and why the score drops: Every action pinned to a full commit SHA (tag in a comment) and GitHub's require-SHA-pinning Actions policy on; workflow and repo default token read-only; pull_request_target removed; zizmor lints the workflows on every PR. L drops to 1 because a SHA cannot be repointed; I stays 4 because a pinned action that was already malicious still runs.

### R-05, Runtime dependencies (requirements.txt)
- Threat: A dependency with a published CVE ships, or an unpinned install silently pulls a different version (T1195.001)
- Vulnerability: Unpinned requirements plus requests 2.31.0 (CVE-2024-35195, CVE-2024-47081, CVE-2026-25645)
- Control and why the score drops: All runtime dependencies pinned with ==, requests upgraded past every known advisory, pip-audit runs in make check and in CI and fails on any finding. L stays 2 because new CVEs are published between runs.

### R-06, main branch review quality
- Threat: An unreviewed or weakly reviewed change reaches main because the only reviewer is the author plus the agent that wrote it
- Vulnerability: No second human reviewer and no automated reviewer: Copilot review is not in Copilot Free and no model API key is available
- Control and why the score drops: PR template with a mandatory self-review checklist and a local skills/review-pr pass whose findings go in every PR body; CI checks run on every PR. Review is agent-assisted, not an enforced gate, so L only drops to 3. An Actions-based reviewer with a stored API key would bring it to 2.

### R-07, Stored security events (SQLite) and generated reports
- Threat: Caller of the API dumps or alters stored events via SQL injection, or reads arbitrary files via path traversal (T1190)
- Vulnerability: String-formatted SQL in /events/search; /reports/<name> joins user input to a path without checks
- Control and why the score drops: Parameterized queries; report names resolved and confined to reports/ with an allowlist. Regression tests send the exact payloads. L drops to 1 because both classes are removed, not filtered.

### R-08, Ingest normaliser and detection rules
- Threat: Malformed or oversized events crash the normaliser, or a crafted rule file runs code when rules are reloaded; detections go blind (T1499.004)
- Vulnerability: No input validation or body size limit on /ingest; rules loaded with an unsafe YAML loader
- Control and why the score drops: Pydantic model validates every event, request bodies capped, bad input returns 400 not 500; rules loaded with yaml.safe_load and checked against a schema. I drops to 3 because a flood of valid events can still slow ingest.

### R-09, Service control plane (/ingest, /admin/*) and its audit log
- Threat: Anyone who can reach the port injects events, reloads rules or uses the debug console; forged log lines hide the activity (T1190)
- Vulnerability: No authentication on ingest and admin; Flask debug=True; user input written to logs unescaped
- Control and why the score drops: API key required on ingest and admin, compared with hmac.compare_digest; debug off; bound to 127.0.0.1; newlines and control characters escaped in logs. L drops to 1 because an attacker now needs the key and local access.

### R-10, Analyst triage queue fed by ingested events
- Threat: Traffic from known-malicious IPs is stored with the same risk score as clean traffic and goes unnoticed (T1071)
- Vulnerability: No correlation of src_ip against threat intelligence
- Control and why the score drops: Ingest enriches every event through an IntelProvider (local feed, MISP provider available); a match adds threat.indicator.matched and raises risk_score. L stays 2 because the feed is only as fresh as its last pull.
