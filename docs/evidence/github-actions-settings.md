# GitHub Actions settings for this repository (B-09)

Captured 2026-11-17T17:07Z with `gh api`. These are repository settings, so they do not show in the code. This file is their evidence.

```console
$ gh api repos/maximilian200123/sentinel-lite/actions/permissions
{"enabled":true,"allowed_actions":"all","sha_pinning_required":true}
$ gh api repos/maximilian200123/sentinel-lite/actions/permissions/workflow
{"default_workflow_permissions":"read","can_approve_pull_request_reviews":false}
$ gh api -X PATCH repos/maximilian200123/sentinel-lite -F allow_forking=false
{"message":"Allow forks setting can only be changed on org-owned private repositories","status":"422"}
```

- `sha_pinning_required: true`. GitHub refuses to run any step that uses an action by tag or branch, so the pinning rule is enforced by the platform as well as by tests.
- `default_workflow_permissions: read`. A workflow with no `permissions:` block still gets a read-only token.
- `can_approve_pull_request_reviews: false`. A workflow token cannot approve a PR.
- Forking cannot be disabled on a personal private repo. Only invited collaborators can see it, and fork PRs run under `pull_request` with no secrets.
