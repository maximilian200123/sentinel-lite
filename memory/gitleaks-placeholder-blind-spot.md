---
name: gitleaks-placeholder-blind-spot
description: gitleaks' generic rule skips secrets whose value contains words like FAKE; use a prefix rule
type: correction
---

gitleaks' `generic-api-key` rule ignores values containing placeholder words such as "FAKE".
The seeded key `sl_api_…FAKE` and a demo key in the same format both passed the pre-commit
scan with the default rules (PR #2).

**Correction:** keep the project rule `sentinel-api-key` in `.gitleaks.toml` (`sl_api_` prefix).
When a new credential format appears, add a prefix rule for it, and prove the rule fires by
attempting a commit with a fake value. A scanner run that reports "no leaks" proves nothing
until you have seen it catch one.
