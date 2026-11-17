"""Runtime settings for Sentinel-Lite. Secrets come only from the environment."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def load_settings() -> dict:
    return {
        # Clients send this in X-API-Key. No default: without it, nothing authenticates.
        "API_KEY": os.environ.get("SENTINEL_API_KEY") or None,
        "HOST": "127.0.0.1",
        "PORT": int(os.environ.get("SENTINEL_PORT", "5000")),
        "DB_PATH": os.environ.get("SENTINEL_DB", str(BASE_DIR / "instance" / "events.db")),
        "REPORTS_DIR": str(BASE_DIR / "reports"),
        "RULES_DIR": str(BASE_DIR / "rules"),
        "INTEL_FEED": str(BASE_DIR / "data" / "intel_feed.json"),
    }
