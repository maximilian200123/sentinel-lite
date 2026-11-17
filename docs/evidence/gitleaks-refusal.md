# gitleaks refuses a fake key at commit time (R-02)

Run on branch chore/governance with `make setup` hooks installed. The key is a fake placeholder, shortened here so the scanner does not flag this file.
The project rule `sentinel-api-key` in `.gitleaks.toml` fires. gitleaks' generic rule alone
skips values containing "FAKE" (verified: same value, no custom rule -> `no leaks found`).

```console
$ cat app/demo_key.py
SENTINEL_API_KEY = "sl_api_Hq8Z…FAKE"
$ git add app/demo_key.py && git commit -m "feat: add demo key"
[WARNING] Unstaged files detected.
[INFO] Stashing unstaged files to .\.cache\pre-commit\patch1794935645-6668.
Detect hardcoded secrets.................................................Failed
- hook id: gitleaks
- exit code: 1
Finding:     SENTINEL_API_KEY = "REDACTED
Secret:      REDACTED
RuleID:      sentinel-api-key
Entropy:     4.923182
File:        app/demo_key.py
Line:        1
Fingerprint: app/demo_key.py:sentinel-api-key:1
7:14PM INF 0 commits scanned.
7:14PM INF scanned ~55 bytes (55 bytes) in 43.2ms
7:14PM WRN leaks found: 1
don't commit to branch...................................................Passed
detect private key.......................................................Passed
check for added large files..............................................Passed
check yaml...........................................(no files to check)Skipped
check json...........................................(no files to check)Skipped
[INFO] Restored changes from .\.cache\pre-commit\patch1794935645-6668.
# pre-commit exited 1: commit refused, HEAD unchanged
$ git log --oneline -1
2fbc3ea Merge PR #1: fix(ci) B-09
```
