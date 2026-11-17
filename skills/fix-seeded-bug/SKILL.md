---
name: fix-seeded-bug
description: Fix one seeded bug (B-01 to B-10) end to end - reproduce, gate the regression test, fix, update register and bug report, review, open the PR. Use when asked to fix a B-xx bug.
---

# Fix a seeded bug

One bug per branch and per PR. Never fix a seeded bug as a side effect of other work.

## Steps

1. **Branch from up-to-date main.**
   `git switch main && git pull --ff-only && git switch -c fix/b-0X-<topic>`
2. **Reproduce.** Run the bug's regression tests as plain tests and confirm they fail *for
   the exploit*, not by accident. Read the assertion message:
   `.venv/Scripts/python -m pytest -q --runxfail -k b0X` (Linux: `.venv/bin/python`)
3. **Gate the test.** Delete the bug's entry from `scripts/open_bugs.py`. Its tests are now
   ordinary tests, and the bug's scanner exceptions (bandit or pip-audit IDs) are gone too.
   `make test` must now fail. If it doesn't, the test is too weak: stop and strengthen it first.
4. **Fix the code** at the root cause named in `docs/BUG-REPORT.md`'s class, with the fix the
   register's Control column promises. Do not edit, skip or loosen the regression test. If the
   test seems wrong, say so in the PR and get a human decision.
5. **Prove it.** `make check` passes, under 60 s. Run the exploit by hand once against
   `make run` on `127.0.0.1` with a harmless marker and keep the output if it adds evidence.
6. **Register.** In `docs/risk-register.yaml`, set the row's `status: Implemented` and point
   `evidence` at the test IDs, files and evidence docs (each must exist). Then run `make register`.
   Implemented with empty evidence fails the check.
7. **Bug report.** Add the bug's section to `docs/BUG-REPORT.md` with the template headings:
   where (file:line on `baseline-vulnerable`), how introduced, exploit, C/I/A impact,
   blast radius, L x I before/after, fix, proof, residual risk.
8. **Review.** Run `skills/review-pr` and fix what it finds before opening the PR.
9. **Commit and open the PR.** Use a conventional commit (`fix(<area>): <what> (B-0X)`) and
   push the branch (never `main`). Open the PR with the template, citing risk and bug IDs, with
   `make check` output and the Agent review pasted in.
10. **Merge** with a merge commit only after the `ci` workflow is green, then confirm that
    `governance` passes on `main`.
