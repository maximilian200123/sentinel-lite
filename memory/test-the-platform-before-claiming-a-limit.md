---
name: test-the-platform-before-claiming-a-limit
description: Probe GitHub's API before writing that a feature needs a paid plan
type: correction
---

The first draft of the B-09 report said GitHub's "require SHA pinning" policy needs a paid
plan on a private repo. One API call showed it works on Free (`sha_pinning_required: true`,
PR #1). Rulesets and branch protection really are refused (HTTP 403, `docs/evidence/github-route.md`).

**Correction:** before documenting a platform limit, try the call (`gh api ...`) and keep the
response as evidence. Write "refused with 403" or "enabled", never "probably needs Pro".
