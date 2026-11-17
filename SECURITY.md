# Security policy

Sentinel-Lite is a lab project. The commit tagged `baseline-vulnerable` contains ten
**deliberately planted** vulnerabilities (B-01 to B-10), documented in
`docs/BUG-REPORT.md`. Do not deploy that tag anywhere, and never bind the service to
anything but `127.0.0.1`.

## Reporting

Open a private security advisory on this repository (Security → Advisories → Report a
vulnerability), or contact the repository owner directly. Please do not open a public
issue. Include the commit, a reproduction that runs against `127.0.0.1` only, and the
impact you expect.

## Secrets

Every secret in this repository's history is a fake placeholder. Real values come from
the environment (`.env`, never committed; see `.env.example`). gitleaks runs in
pre-commit and in CI with a project rule for the `sl_api_` key prefix.

## Supported versions

Only `main` is maintained.
