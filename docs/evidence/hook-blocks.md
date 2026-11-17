# PreToolUse hook blocks dangerous agent actions (B-10, R-01, R-02, R-03)

## 1. Hook fed exactly what Claude Code sends

Each row pipes a Claude Code `PreToolUse` payload (`{"tool_name", "tool_input", "cwd"}`) into
`.claude/hooks/guard.py`. Exit code 2 means Claude Code refuses the tool call and shows the
reason to the agent. The same cases are pytest tests (`tests/test_repo_policy.py::test_b10_*`).

| Tool | Input | Result | Reason shown to the agent |
|---|---|---|---|
| `Bash` | `git push origin main` | **blocked** (2) | pushing to main is blocked; open a pull request |
| `Bash` | `git push origin HEAD:main` | **blocked** (2) | pushing to main is blocked; open a pull request |
| `Bash` | `git push` | allowed (0) | - |
| `Bash` | `git push --force origin fix/b-02` | **blocked** (2) | force push / remote branch deletion is blocked; push a new commit instead |
| `Bash` | `git push --force-with-lease` | **blocked** (2) | force push / remote branch deletion is blocked; push a new commit instead |
| `Bash` | `git push origin +fix/b-02` | **blocked** (2) | force push (+refspec) is blocked |
| `Bash` | `git push origin --delete fix/b-02` | **blocked** (2) | force push / remote branch deletion is blocked; push a new commit instead |
| `Bash` | `git commit --no-verify -m 'skip hooks'` | **blocked** (2) | --no-verify skips the git hooks; fix what the hook reports instead |
| `Bash` | `git -c core.hooksPath=/dev/null commit -m x` | **blocked** (2) | changing core.hooksPath would switch off the git hooks |
| `Bash` | `git config core.hooksPath ''` | **blocked** (2) | changing core.hooksPath would switch off the git hooks |
| `Bash` | `cat .env` | **blocked** (2) | command touches secret material (.env, secrets/, keys, gh credentials) |
| `Bash` | `gh auth token` | **blocked** (2) | command touches secret material (.env, secrets/, keys, gh credentials) |
| `Bash` | `sed -i 's/exit 2/exit 0/' .claude/hooks/guard.py` | **blocked** (2) | the agent may not modify its own guardrails in .claude/ |
| `Read` | `.env` | **blocked** (2) | Read on secret material is blocked: C:/Users/me/Desktop/sentinel-lite/.env |
| `Write` | `.claude/settings.json` | **blocked** (2) | the agent may not modify its own guardrails in .claude/ |
| `Bash` | `git push -u origin fix/b-02-sql-injection` | allowed (0) | - |
| `Bash` | `make check` | allowed (0) | - |
| `Read` | `.env.example` | allowed (0) | - |
| `Read` | `.claude/hooks/guard.py` | allowed (0) | - |
A bare `git push` is allowed above because the branch was a feature branch. On `main` it is
blocked (`test_b10_hook_blocks_bare_push_while_on_main`).

## 2. Inside a live agent session

Claude Code loads `.claude/settings.json` (deny rules and hook) when a session **starts in
this folder**. The session that wrote this PR was started in the user's home folder, so the
hook was not active there. Its own attempt shows that:

```console
$ git push origin main          # agent, before the hook was loaded
Everything up-to-date           # nothing to push; the pre-push guard would refuse anything else
```

The transcript of a session started inside the repository is added in
`hook-live-session.md` after this PR merges.
