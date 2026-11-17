"""Runtime settings for Sentinel-Lite."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Key that clients send in the X-API-Key header.
API_KEY = "sl_api_7Qm2Xv9Lk4Rt8Wn3Zp6Yb1FAKE"


def load_settings() -> dict:
    return {
        "API_KEY": API_KEY,
        "HOST": "127.0.0.1",
        "PORT": int(os.environ.get("SENTINEL_PORT", "5000")),
        "DB_PATH": os.environ.get("SENTINEL_DB", str(BASE_DIR / "instance" / "events.db")),
        "REPORTS_DIR": str(BASE_DIR / "reports"),
        "RULES_DIR": str(BASE_DIR / "rules"),
        "INTEL_FEED": str(BASE_DIR / "data" / "intel_feed.json"),
    }
