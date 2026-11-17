# Seeded bug report

Ten bugs were planted on purpose in the commit tagged `baseline-vulnerable`.
Each one has regression tests that fail on that tag (`docs/evidence/baseline-red.txt`)
and is fixed in its own pull request. A section is added here by the PR that fixes the bug.

Line numbers refer to the tag: `git show baseline-vulnerable:<path>`.

## B-09, Insecure CI workflow

- **Risk IDs / CWE / ATT&CK:** R-04 / CWE-829 (inclusion of functionality from an untrusted control sphere) / T1195.002 (compromise software supply chain).
- **Where:** `.github/workflows/ci-baseline.yml:4` (`pull_request_target`), `:8` (`permissions: write-all`), `:14` and `:17` (`actions/checkout@v4`, `actions/setup-python@v5`), `:16` (checks out the PR head).
- **How it was introduced:** this is the workflow most tutorials show. `@v4` reads like a version pin. `pull_request_target` is a common trick to get secrets into PR builds, and `write-all` makes permission errors go away. Each line looks like a convenience.
- **How it can be exploited:** there are two paths.
  1. A tag is mutable. Whoever controls `actions/checkout` (or steals its maintainer token) can move `v4` to new code, and every run executes it with this repo's token. This is the pattern behind the 2025 `tj-actions/changed-files` compromise.
  2. `pull_request_target` runs with the base repository's token and secrets but, because of `ref: head.sha`, checks out and executes the PR's code. Anyone who can open a PR runs `make`/`pytest` code of their choice with a `write-all` token.

  Safe local reproduction: `zizmor` reports both on the baseline file (`docs/evidence/zizmor-b09.md`). The tests `tests/test_repo_policy.py::test_b09_*` fail on the tag.
- **Impact on this app (C/I/A):** the token can push code to `main`, edit releases and read the source. Integrity of everything the professor clones is lost (I = 5). Confidentiality: all repository content and any repository secret (C = 4).
- **Blast radius beyond this app:** a write token lets an attacker push a commit that plants a new hardcoded secret (chains with B-01), rewrites `requirements.txt` (B-08), or edits `memory/` so the AI agent's next session is steered (B-10). Under route 4 there is no server-side branch protection, so the token is the only thing between a PR and `main`. If the student reuses the workflow in other repos, the same tag hijack hits all of them at once.
- **Likelihood x Impact before / after:** 3 x 5 = 15 (High) → 1 x 4 = 4 (Low).
- **The fix:** the workflow is replaced by `.github/workflows/ci.yml`.
  - Every action is pinned to a full commit SHA, with the tag kept in a trailing comment.
  - The default permission is `contents: read`.
  - The trigger is `pull_request`, which gets a read-only token and no secrets for fork PRs, instead of `pull_request_target`.
  - `persist-credentials: false` keeps the token out of `.git/config`.
  - A `workflow-lint` job runs zizmor on every PR, so a regression is caught.
  - Repository settings: GitHub's required-SHA-pinning policy is on and the default workflow token is read-only.

  Fixed in PR #1.
- **Proof the fix works:** `tests/test_repo_policy.py::test_b09_third_party_actions_pinned_to_commit_sha`, `::test_b09_default_permissions_are_read_only` and `::test_b09_no_pull_request_target` pass on `main`. zizmor reports no findings on `ci.yml`, versus 3 high and 1 medium on the baseline (`docs/evidence/zizmor-b09.md`). The `workflow-lint` CI job runs on every PR.
- **Residual risk:**
  - A SHA pins what runs, not whether it is safe. An action that was already malicious when pinned still runs, so I stays 4.
  - Pins go stale. Dependabot with a cooldown would keep them current; it is not enabled yet.
  - Three layers enforce pinning. GitHub's "require SHA pinning" Actions policy works on this Free private repo and is on. The default workflow token is read-only (`docs/evidence/github-actions-settings.md`). The policy test and zizmor catch it in review. Repository settings can be changed back by the owner, so the test and zizmor stay as the in-repo check.
