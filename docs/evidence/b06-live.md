# B-06 live check: key required, debug off

`make run` on branch `fix/b-06-auth-debug`, probed from the same machine with no key and a guessed key.

```console
$ curl -s -w " %{http_code}" http://127.0.0.1:5000/health
{"status":"ok"}
 200
$ curl -s -w " %{http_code}" -X POST http://127.0.0.1:5000/ingest -H "Content-Type: application/json" -d @samples/SL-0001/positive.json
{"error":"missing or invalid API key"}
 401
$ curl -s -w " %{http_code}" -X POST http://127.0.0.1:5000/admin/rules/reload -H "X-API-Key: guessed-key"   # gitleaks:allow (deliberately wrong key, not a secret)
{"error":"missing or invalid API key"}
 401

# server log
 * Debug mode: off
 * Running on http://127.0.0.1:5000
```

On `baseline-vulnerable` the same server logged `Debugger is active!` and a debugger PIN, and both requests returned 201/200.
