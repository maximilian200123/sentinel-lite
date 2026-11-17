"""Regression tests for the application bugs B-01 to B-07.

Each test reproduces the exploit with a harmless marker against the app in-process.
While a bug is open in scripts/open_bugs.py the test is xfail(strict); run
`make test-seeded` to see every one of them fail on the baseline.
"""

import json
import logging

import pytest
from conftest import AUTH, TEST_KEY, event

from app import create_app


def _overrides(paths):
    return {k: v for k, v in paths.items() if k != "tmp"} | {"PROPAGATE_EXCEPTIONS": False}


# B-01: hardcoded API key ---------------------------------------------------------


@pytest.mark.seeded("B-01")
def test_b01_api_key_comes_from_environment(monkeypatch, paths):
    monkeypatch.setenv("SENTINEL_API_KEY", "value-from-environment")
    assert create_app(_overrides(paths)).config["API_KEY"] == "value-from-environment"


@pytest.mark.seeded("B-01")
def test_b01_no_fallback_key_in_source(monkeypatch, paths):
    monkeypatch.delenv("SENTINEL_API_KEY", raising=False)
    assert create_app(_overrides(paths)).config["API_KEY"] is None


# B-02: SQL injection -------------------------------------------------------------


@pytest.mark.seeded("B-02")
def test_b02_search_is_not_injectable(client):
    client.post("/ingest", json=event(user="alice"), headers=AUTH)
    client.post("/ingest", json=event(user="bob"), headers=AUTH)
    resp = client.get("/events/search", query_string={"user": "x' OR '1'='1"}, headers=AUTH)
    assert resp.status_code == 200
    assert resp.get_json()["count"] == 0


# B-03: path traversal ------------------------------------------------------------


@pytest.mark.seeded("B-03")
@pytest.mark.parametrize("name", ["..%2foutside-marker.txt", "..%2f..%2f{tmp}%2foutside-marker.txt"])
def test_b03_reports_cannot_escape_reports_dir(client, paths, name):
    marker = paths["tmp"] / "outside-marker.txt"
    marker.write_text("B03-MARKER", encoding="utf-8")
    resp = client.get("/reports/" + name.format(tmp=paths["tmp"].name), headers=AUTH)
    assert b"B03-MARKER" not in resp.data
    assert resp.status_code == 404


# B-04: unsafe YAML ---------------------------------------------------------------


@pytest.mark.seeded("B-04")
def test_b04_rule_file_cannot_run_code(app, client, paths):
    rules = paths["tmp"] / "rules"
    rules.mkdir()
    marker = paths["tmp"] / "B04-MARKER"
    payload = f"!!python/object/apply:os.makedirs [{json.dumps(str(marker))}]\n"
    (rules / "evil.yaml").write_text(payload, encoding="utf-8")
    app.config["RULES_DIR"] = str(rules)
    resp = client.post("/admin/rules/reload", headers=AUTH)
    assert not marker.exists(), "YAML tag executed a Python call"
    assert resp.status_code == 400


@pytest.mark.seeded("B-04")
def test_b04_rule_file_must_match_schema(app, client, paths):
    rules = paths["tmp"] / "rules"
    rules.mkdir()
    (rules / "bad.yaml").write_text("id: SL-9999\ntitle: no match block\n", encoding="utf-8")
    app.config["RULES_DIR"] = str(rules)
    assert client.post("/admin/rules/reload", headers=AUTH).status_code == 400


# B-05: input validation and size limit -------------------------------------------

MALFORMED = {
    "array-body": "[]",
    "missing-fields": json.dumps({"ts": "2026-11-17T10:00:00"}),
    "bad-timestamp": json.dumps(event(ts="yesterday")),
    "bad-ip": json.dumps(event(src_ip="not-an-ip")),
    "wrong-type": json.dumps(event(message=12345)),
}


@pytest.mark.seeded("B-05")
@pytest.mark.parametrize("body", MALFORMED.values(), ids=MALFORMED.keys())
def test_b05_malformed_event_is_rejected_cleanly(client, body):
    resp = client.post("/ingest", data=body, content_type="application/json", headers=AUTH)
    assert resp.status_code == 400


@pytest.mark.seeded("B-05")
def test_b05_oversized_body_is_rejected(client):
    resp = client.post("/ingest", json=event(message="A" * 2_000_000), headers=AUTH)
    assert resp.status_code == 413


# B-06: authentication and debug mode ---------------------------------------------

PROTECTED = [
    ("post", "/ingest"),
    ("post", "/admin/rules/reload"),
    ("get", "/events/search?user=alice"),
    ("get", "/reports/daily.txt"),
    ("get", "/intel/check?ip=10.0.0.1"),
]


@pytest.mark.seeded("B-06")
@pytest.mark.parametrize("method,url", PROTECTED)
@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong-key"}], ids=["no-key", "wrong-key"])
def test_b06_endpoints_require_api_key(client, method, url, headers):
    kwargs = {"json": event()} if method == "post" else {}
    assert getattr(client, method)(url, headers=headers, **kwargs).status_code == 401


@pytest.mark.seeded("B-06")
def test_b06_debug_mode_is_off(app):
    assert app.debug is False


# B-07: log injection and secrets in logs -----------------------------------------


@pytest.mark.seeded("B-07")
def test_b07_log_lines_cannot_be_forged(client, caplog):
    caplog.set_level(logging.INFO, logger="sentinel")
    client.post("/ingest", json=event(message="ok\nFORGED admin login accepted"), headers=AUTH)
    lines = [r.getMessage() for r in caplog.records if r.name == "sentinel"]
    assert lines, "ingest must be logged"
    assert not any("\n" in line or "\r" in line for line in lines)


@pytest.mark.seeded("B-07")
def test_b07_api_key_never_logged(client, caplog):
    caplog.set_level(logging.DEBUG)
    client.post("/ingest", json=event(), headers=AUTH)
    assert caplog.records, "ingest must be logged"
    assert not any(TEST_KEY in r.getMessage() for r in caplog.records)
