---
name: hooks-live-on-the-branch
description: core.hooksPath=.githooks only guards branches that contain .githooks/
type: correction
---

The first commit-on-main refusal demo went through: `main` did not yet contain `.githooks/`,
so git found no hook to run (PR #2). The stray commit was local and was discarded unpushed.

**Correction:** a guard committed to a feature branch protects nothing until it is merged.
Run "is this refused?" demos only on a branch that contains the guard, and record any failed
attempt in the evidence instead of hiding it.
