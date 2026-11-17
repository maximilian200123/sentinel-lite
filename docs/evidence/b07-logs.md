# B-07: the same request logged before and after the fix

Request: `POST /ingest` with header `X-API-Key: test-key-not-a-secret-0000` and
`"message": "ok\nFORGED admin login accepted"` (a newline inside the JSON string).

## Before (`baseline-vulnerable`)

```
ingest user=alice message=ok
FORGED admin login accepted headers={'User-Agent': 'Werkzeug/3.1.9', 'Host': 'localhost', 'Content-Type': 'application/json', 'Content-Length': '136', 'X-Api-Key': 'test-key-not-a-secret-0000'}
```

Two problems are visible. The attacker's text starts a second line that a log reader or SIEM
parser takes as its own event. The API key is written in clear.

## After (this branch)

```
ingest user=alice src_ip=10.0.0.1 message=ok\x0aFORGED admin login accepted [REDACTED]
```

The message also contained a value in the `sl_api_` key format, which is redacted. Headers are no
longer logged at all, and the configured key is redacted wherever it appears.
