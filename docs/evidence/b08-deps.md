# B-08: dependency audit after the fix

Before: `docs/evidence/pip-audit-baseline.txt` (requests 2.31.0, 3 advisories; `flask` and `pyyaml` unpinned).

## Direct pins (`requirements.txt`)
```
flask==3.1.3
pyyaml==6.0.3
requests==2.34.2
```

## Full tree (`constraints.txt`, from `make lock`, only releases at least 14 days old)
```
Flask==3.1.3
Jinja2==3.1.6
MarkupSafe==3.0.4
PyYAML==6.0.3
Werkzeug==3.1.9
blinker==1.9.0
certifi==2026.10.23
charset-normalizer==3.5.2
click==8.5.0
idna==3.20
itsdangerous==2.2.0
requests==2.34.2
urllib3==2.8.0
```

## `make audit` with no ignores left
```
$ pip-audit --no-deps --disable-pip -r constraints.txt
No known vulnerabilities found
```
