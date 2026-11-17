"""B-03 probe: try to read a marker file outside reports/ through /reports/<name>.

    PYTHONPATH=. python scripts/probes/b03_traversal.py

In-process, no network. The marker sits next to the reports directory, the way
instance/events.db or .env sit next to reports/ in a real checkout.
"""

import os
import tempfile
from pathlib import Path

os.environ["SENTINEL_API_KEY"] = "k-demo-0000000000"
from app import create_app  # noqa: E402

AUTH = {"X-API-Key": "k-demo-0000000000"}
root = Path(tempfile.mkdtemp())
(root / "reports").mkdir()
(root / "reports" / "daily.txt").write_bytes(b"daily report\n")
(root / "outside-marker.txt").write_bytes(b"B03-MARKER: file outside reports/")

client = create_app({"DB_PATH": str(root / "e.db"), "REPORTS_DIR": str(root / "reports"),
                     "PROPAGATE_EXCEPTIONS": False}).test_client()
for name in ("daily.txt", "..%2foutside-marker.txt", "..%5coutside-marker.txt",
             "%2e%2e%2foutside-marker.txt", "....%2f%2foutside-marker.txt"):
    resp = client.get("/reports/" + name, headers=AUTH)
    leaked = b"B03-MARKER" in resp.data
    print(f"/reports/{name:32} -> HTTP {resp.status_code}{'  LEAKED marker' if leaked else ''}")
