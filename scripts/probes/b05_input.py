"""B-05 probe: malformed and oversized bodies sent to /ingest.

    PYTHONPATH=. python scripts/probes/b05_input.py

In-process, no network. A 500 means the app trusted the input; a 400 or 413 means it refused it.
"""

import json
import os
import tempfile

os.environ["SENTINEL_API_KEY"] = "k-demo-0000000000"
from app import create_app  # noqa: E402

AUTH = {"X-API-Key": "k-demo-0000000000"}
GOOD = {"ts": "2026-11-17T10:00:00", "src_ip": "10.0.0.20", "dst_ip": "10.0.0.5",
        "user": "alice", "message": "user login ok"}
CASES = {
    "valid event": json.dumps(GOOD),
    "array body": "[]",
    "not JSON": "ts=now",
    "missing fields": json.dumps({"ts": GOOD["ts"]}),
    "bad timestamp": json.dumps(GOOD | {"ts": "yesterday"}),
    "bad IP": json.dumps(GOOD | {"src_ip": "not-an-ip"}),
    "number as message": json.dumps(GOOD | {"message": 12345}),
    "object as user": json.dumps(GOOD | {"user": {"$ne": ""}}),
    "2 MB message": json.dumps(GOOD | {"message": "A" * 2_000_000}),
}

client = create_app({"DB_PATH": tempfile.mkdtemp() + "/e.db", "PROPAGATE_EXCEPTIONS": False}).test_client()
for label, body in CASES.items():
    resp = client.post("/ingest", data=body, content_type="application/json", headers=AUTH)
    print(f"{label:18} -> HTTP {resp.status_code}")
