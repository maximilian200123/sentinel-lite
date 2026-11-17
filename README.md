# Sentinel-Lite

A small log-enrichment service for the ULBS Cybersecurity Master, Module 4 lab
(Risk and Damage Management, AI-driven security engineering).

> **This commit is deliberately vulnerable.** It is tagged `baseline-vulnerable` and
> carries ten seeded bugs (B-01 to B-10), each mapped to a row in
> `RISK-REGISTER.xlsx`. Every bug is fixed later in its own pull request.
> Run it on `127.0.0.1` only.

```sh
make setup   # venv + pinned dev tools, all inside this folder
make run     # http://127.0.0.1:5000/health
make test    # suite; seeded-bug tests are expected failures while open
make test-seeded   # the seeded-bug regression tests as plain tests (red here)
```
