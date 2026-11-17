"""B-02 probe: send SQL injection payloads to /events/search in-process (no network).

    PYTHONPATH=. python scripts/probes/b02_sqli.py

Works on any checkout, including `git worktree add <dir> baseline-vulnerable`.
"""

import os
import tempfile

os.environ["SENTINEL_API_KEY"] = "k-demo-0000000000"
from app import create_app  # noqa: E402

AUTH = {"X-API-Key": "k-demo-0000000000"}
PAYLOADS = (
    "alice",
    "x' OR '1'='1",
    "x' UNION SELECT json_object('user', json_object('name', sqlite_version())) --",
)

client = create_app({"DB_PATH": tempfile.mkdtemp() + "/e.db", "PROPAGATE_EXCEPTIONS": False}).test_client()
for user in ("alice", "bob"):
    event = {"ts": "2026-11-17T10:00:00", "src_ip": "10.0.0.1", "dst_ip": "10.0.0.2",
             "user": user, "message": "m"}
    client.post("/ingest", json=event, headers=AUTH)
for payload in PAYLOADS:
    resp = client.get("/events/search", query_string={"user": payload}, headers=AUTH)
    body = resp.get_json() or {}
    names = [e.get("user", {}).get("name") for e in body.get("events", [])]
    print(f"user={payload!r}\n  -> HTTP {resp.status_code}, count={body.get('count')}, "
          f"user.name values={names}")
