# Definition of done: final verification

Run on 2026-11-17 against `main` at `00b7613` (Merge PR #13), which is the last code change.
The docs PR that adds this file changes no code.

## 1. Fresh clone from GitHub: setup, check, run

```console
$ gh repo clone maximilian200123/sentinel-lite && cd sentinel-lite
$ make setup        # exit 0 in 108 s (venv, locked deps, .env with a random key, git hooks)
$ make check        # exit 0 in 7 s
All checks passed!
register: OK, 10 risks, all bugs mapped
71 passed in 3.10s
No known vulnerabilities found
build: app imports and serves /health
$ make run
 * Debug mode: off
 * Running on http://127.0.0.1:5000
$ curl -s http://127.0.0.1:5000/health
{"status":"ok"}
 200
$ curl -s -X POST http://127.0.0.1:5000/ingest -H "Content-Type: application/json" -d @samples/SL-0001/positive.json
{"error":"missing or invalid API key"}
 401
$ netstat -ano | grep ":5000 .*LISTENING"
  TCP    127.0.0.1:5000         0.0.0.0:0              LISTENING
```

Size of the fresh clone: 407 KB working tree plus 363 KB `.git` (limit 2 MB). Application code
is 452 lines (`app/*.py`). Runtime dependencies: 3 direct (`requirements.txt`, limit 4), 13 in the
locked tree (`constraints.txt`).

## 2. Every seeded regression test: red on the tag, green on main

Main's seeded tests (`-m seeded --runxfail`, modules `test_seeded_bugs.py` and
`test_repo_policy.py`) were copied into a worktree of `baseline-vulnerable` and run against
the tag's code, then against `main`.

```console
$ git worktree add wt baseline-vulnerable && cp -r tests/. wt/tests/ && cd wt
$ pytest -q --runxfail -m seeded tests/test_seeded_bugs.py tests/test_repo_policy.py
48 failed, 2 deselected in 0.69s
      1 test_repo_policy.py::test_b08_no_dependency_below_fixed_version
      1 test_repo_policy.py::test_b08_runtime_dependencies_are_pinned
      1 test_repo_policy.py::test_b09_default_permissions_are_read_only
      1 test_repo_policy.py::test_b09_no_pull_request_target
      1 test_repo_policy.py::test_b09_third_party_actions_pinned_to_commit_sha
      1 test_repo_policy.py::test_b10_agent_context_has_no_instruction_to_bypass_controls
      4 test_repo_policy.py::test_b10_hook_allows_normal_work
      1 test_repo_policy.py::test_b10_hook_blocks_bare_push_while_on_main
     10 test_repo_policy.py::test_b10_hook_blocks_dangerous_agent_action
      1 test_repo_policy.py::test_b10_settings_wire_deny_rules_and_hook
      1 test_seeded_bugs.py::test_b01_api_key_comes_from_environment
      1 test_seeded_bugs.py::test_b01_no_fallback_key_in_source
      1 test_seeded_bugs.py::test_b02_search_is_not_injectable
      2 test_seeded_bugs.py::test_b03_reports_cannot_escape_reports_dir
      1 test_seeded_bugs.py::test_b04_rule_file_cannot_run_code
      1 test_seeded_bugs.py::test_b04_rule_file_must_match_schema
      5 test_seeded_bugs.py::test_b05_malformed_event_is_rejected_cleanly
      1 test_seeded_bugs.py::test_b05_oversized_body_is_rejected
      1 test_seeded_bugs.py::test_b06_debug_mode_is_off
     10 test_seeded_bugs.py::test_b06_endpoints_require_api_key
      1 test_seeded_bugs.py::test_b07_api_key_never_logged
      1 test_seeded_bugs.py::test_b07_log_lines_cannot_be_forged

$ cd ../main && pytest -q --runxfail -m seeded tests/test_seeded_bugs.py tests/test_repo_policy.py
51 passed, 2 deselected
```

Every seeded test on the tag fails, and every one on main passes. The counts differ by three
because the B-09 tests run once per workflow file. The tag has one workflow
(`ci-baseline.yml`) and main has two (`ci.yml`, `governance.yml`). `make test-seeded` runs the
same selection. `scripts/open_bugs.py` is empty on main, so no test is xfail and no scanner
exception remains.

## 3. CI and governance on main

- `governance` on `00b7613`: **success**, https://github.com/maximilian200123/sentinel-lite/actions/runs/44142856136
- `ci` on `00b7613`: **success**, https://github.com/maximilian200123/sentinel-lite/actions/runs/44142856034

The governance workflow checks that every commit since `baseline-vulnerable` belongs to a
merged PR whose `ci` run on the PR head passed.

## 4. Every merged PR carries the checklist and an Agent review

Checked with `gh pr list --state all --json body`, looking for a ticked `- [x]` and the
`## Agent review` heading.

| PR | Merge commit | Checklist | Agent review | Title |
|---|---|---|---|---|
| #1 | `2fbc3ea` | yes | yes | fix(ci): pin actions to SHAs, read-only token, no pull_request_target (B-09) |
| #2 | `a23c4e3` | yes | yes | chore(governance): local guards, governance workflow, repo policy files |
| #3 | `eb76834` | yes | yes | ci: make check, gitleaks and build check on every PR; governance checks CI |
| #4 | `e585ec1` | yes | yes | feat(ai): CLAUDE.md, memory corrections, fix and review skills, PR template |
| #5 | `d93d31b` | yes | yes | fix(agent): deny rules and PreToolUse hook, remove poisoned memory (B-10) |
| #6 | `ac20c2b` | yes | yes | fix(config): read the API key from the environment, no fallback (B-01) |
| #7 | `e54bac1` | yes | yes | fix(api): require X-API-Key on every endpoint, debug off (B-06) |
| #8 | `1e95b8d` | yes | yes | fix(logging): escape control characters and redact keys in logs (B-07) |
| #9 | `fae985b` | yes | yes | fix(store): parameterize the event search query (B-02) |
| #10 | `2dac30b` | yes | yes | fix(api): confine report downloads to reports/ with a name allowlist (B-03) |
| #11 | `9a31090` | yes | yes | fix(rules): safe_load plus schema validation, keep rules on bad reload (B-04) |
| #12 | `c566ff3` | yes | yes | fix(deps): pin every runtime dependency, upgrade requests, lock the tree (B-08) |
| #13 | `00b7613` | yes | yes | fix(ingest): validate raw events at the boundary, cap body size (B-05) |

## 5. Where the other DoD items are proven

| Item | Evidence |
|---|---|
| Direct and force pushes to `main` refused | `push-refusals.md`, `commit-on-main-refused.md`, `tests/test_guard_push.py` |
| gitleaks catches a key locally and in CI | `gitleaks-refusal.md` (pre-commit refusal), `ci.yml` job `gitleaks` |
| Actions pinned to SHAs | `github-actions-settings.md` (repository policy on), `zizmor-b09.md`, `test_b09_*` |
| Hook blocks `git push origin main` by the agent | `hook-blocks.md`, `test_b10_hook_blocks_dangerous_agent_action` |
| Register: no formula errors, no Implemented row without evidence | `make register-check` (in `make check`): "register: OK, 10 risks, all bugs mapped". It checks that no cell holds an error value, that every score formula's inputs give 1-25, that every Implemented row has evidence and every evidence path exists. The workbook was not recalculated in Excel by the agent, so opening it once in Excel is the final check. |
| BUG-REPORT complete for all 10 bugs | `docs/BUG-REPORT.md`: 10 sections, index table, bug chains |
