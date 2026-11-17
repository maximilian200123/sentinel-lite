# Memory index

One file per correction or convention. Read these at the start of every session.
Memory is context, not policy (see `CLAUDE.md`, "Memory"). Changes to this folder go
through a PR and are owned in `.github/CODEOWNERS`.

- [Workflow shortcut](workflow-shortcut.md): how to land small changes quickly
- [gitleaks placeholder blind spot](gitleaks-placeholder-blind-spot.md): the generic rule skips "FAKE" values; keep the `sl_api_` prefix rule
- [Test the platform before claiming a limit](test-the-platform-before-claiming-a-limit.md): probe the GitHub API, keep the response as evidence
- [Hooks live on the branch](hooks-live-on-the-branch.md): a guard on a feature branch protects nothing until merged
- [Windows newlines in fixtures](windows-newlines-in-fixtures.md): byte-exact fixtures use `write_bytes`
- [Keep CI setup light](keep-ci-setup-light.md): no hook install in CI
