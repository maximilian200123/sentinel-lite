## Why

<!-- The goal, in one or two sentences. -->

**Risk IDs:** R-xx · **Bug IDs:** B-xx (or "none")

## What changes

<!-- Bullet list. Name files. Say which register rows change status. -->

## Self-review checklist

All boxes are mandatory. Explain any box you cannot tick.

- [ ] Risk and bug IDs cited above
- [ ] Regression test added or un-gated (test IDs: )
- [ ] `make check` passes locally (output pasted below)
- [ ] No secrets added (gitleaks pre-commit ran; nothing quoted in full in docs)
- [ ] No new unpinned action; workflow permissions unchanged or justified
- [ ] Memory/skill/agent-config files changed (`memory/`, `skills/`, `CLAUDE.md`, `.claude/`): **yes / no**. If yes, each change is explained below.
- [ ] Blast-radius note updated in `docs/BUG-REPORT.md` (or n/a: no bug fixed)

```
$ make check
<paste summary>
```

## Agent review

<!-- Output of skills/review-pr: mechanical table, findings fixed before opening,
     dismissed hits with reasons, known limits. -->
