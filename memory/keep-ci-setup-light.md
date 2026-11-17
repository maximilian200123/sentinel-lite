---
name: keep-ci-setup-light
description: make setup must not install git hooks in CI; it builds gitleaks with Go (~80 s)
type: correction
---

After PR #2, `make setup` in CI ran `pre-commit install-hooks`, which builds gitleaks through
Go on every run and took the `test` job from 14 s to 81 s.

**Correction:** hook installation sits behind `ifndef CI` in the Makefile. CI scans for secrets
with its own checksum-pinned gitleaks binary, so nothing is lost.
