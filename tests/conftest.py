import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from open_bugs import OPEN_BUGS  # noqa: E402

from app import create_app  # noqa: E402

TEST_KEY = "test-key-not-a-secret-0000"
AUTH = {"X-API-Key": TEST_KEY}


def pytest_configure(config):
    config.addinivalue_line("markers", "seeded(bug_id): regression test for a seeded bug")


def pytest_collection_modifyitems(config, items):
    """A regression test whose bug is still open must fail. Run with --runxfail to see it red."""
    for item in items:
        marker = item.get_closest_marker("seeded")
        if marker and marker.args[0] in OPEN_BUGS:
            item.add_marker(
                pytest.mark.xfail(reason=f"{marker.args[0]} open (seeded on purpose)", strict=True)
            )


@pytest.fixture
def paths(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "daily.txt").write_bytes(b"daily report\n")
    return {
        "DB_PATH": str(tmp_path / "events.db"),
        "REPORTS_DIR": str(reports),
        "RULES_DIR": str(ROOT / "rules"),
        "tmp": tmp_path,
    }


@pytest.fixture
def app(paths, monkeypatch):
    monkeypatch.setenv("SENTINEL_API_KEY", TEST_KEY)
    overrides = {k: v for k, v in paths.items() if k != "tmp"}
    # Surface server errors as HTTP 500 responses, the way a real client sees them.
    overrides["PROPAGATE_EXCEPTIONS"] = False
    return create_app(overrides)


@pytest.fixture
def client(app):
    return app.test_client()


def sample(rule_id: str, kind: str) -> dict:
    return json.loads((ROOT / "samples" / rule_id / f"{kind}.json").read_text(encoding="utf-8"))


def event(**changes) -> dict:
    base = {
        "ts": "2026-11-17T10:00:00",
        "src_ip": "10.0.0.20",
        "dst_ip": "10.0.0.5",
        "user": "alice",
        "message": "user login ok",
    }
    return base | changes
