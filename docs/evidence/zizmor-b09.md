# zizmor 1.32.0 --offline, B-09 before and after

## Before: .github/workflows/ci-baseline.yml at tag baseline-vulnerable
```
warning[artipacked]: credential persistence through GitHub Actions artifacts
  --> .github\workflows\ci-baseline.yml:14:9
   |
14 |         - uses: actions/checkout@v4
   |  _________^
15 | |         with:
16 | |           ref: ${{ github.event.pull_request.head.sha }}
   | |________________________________________________________^ does not set persist-credentials: false
   |
   = note: audit confidence → Low
   = note: this finding has an auto-fix
   = help: audit documentation → https://docs.zizmor.sh/audits/#artipacked

error[dangerous-triggers]: use of fundamentally insecure workflow trigger
 --> .github\workflows\ci-baseline.yml:4:3
  |
4 |   pull_request_target:
  |   ^^^^^^^^^^^^^^^^^^^ pull_request_target is almost always used insecurely
  |
  = note: audit confidence → Medium
  = help: audit documentation → https://docs.zizmor.sh/audits/#dangerous-triggers

error[unpinned-uses]: unpinned action reference
  --> .github\workflows\ci-baseline.yml:14:15
   |
14 |       - uses: actions/checkout@v4
   |               ^^^^^^^^^^^^^^^^^^^ action is not pinned to a hash (required by blanket policy)
   |
   = note: audit confidence → High
   = help: audit documentation → https://docs.zizmor.sh/audits/#unpinned-uses

error[unpinned-uses]: unpinned action reference
  --> .github\workflows\ci-baseline.yml:17:15
   |
17 |       - uses: actions/setup-python@v5
   |               ^^^^^^^^^^^^^^^^^^^^^^^ action is not pinned to a hash (required by blanket policy)
   |
   = note: audit confidence → High
   = help: audit documentation → https://docs.zizmor.sh/audits/#unpinned-uses

7 findings (3 suppressed, 1 unsafe fixes): 0 informational, 0 low, 1 medium, 3 high
```

## After: .github/workflows/ci.yml on fix/b-09-ci-hardening
```
No findings to report. Good job! (2 suppressed)
```
