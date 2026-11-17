"""Behaviour the service must keep through every fix."""

import pytest
from conftest import AUTH, ROOT, event, sample

from app.intel import LocalFeedProvider, MispProvider
from app.pipeline import INDICATOR_TAG, process
from app.rules import load_rules


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_ingest_then_search(client):
    assert client.post("/ingest", json=event(user="alice"), headers=AUTH).status_code == 201
    assert client.post("/ingest", json=event(user="bob"), headers=AUTH).status_code == 201
    body = client.get("/events/search?user=alice", headers=AUTH).get_json()
    assert body["count"] == 1
    assert body["events"][0]["user"]["name"] == "alice"


def test_enrichment_changes_the_outcome(client):
    bad = client.post("/ingest", json=event(src_ip="203.0.113.66"), headers=AUTH).get_json()["event"]
    clean = client.post("/ingest", json=event(src_ip="10.0.0.20"), headers=AUTH).get_json()["event"]
    assert INDICATOR_TAG in bad["tags"]
    assert bad["event"]["risk_score"] > clean["event"]["risk_score"]
    assert bad["threat"]["indicator"]["provider"] == "local-feed"
    assert INDICATOR_TAG not in clean["tags"]
    assert "threat" not in clean


def test_intel_check(client):
    assert client.get("/intel/check?ip=198.51.100.23", headers=AUTH).get_json()["matched"] is True
    assert client.get("/intel/check?ip=10.0.0.1", headers=AUTH).get_json()["matched"] is False


@pytest.mark.parametrize("rule_id", ["SL-0001", "SL-0002"])
def test_rule_matches_positive_sample_only(rule_id):
    rules = [r for r in load_rules(str(ROOT / "rules")) if r.id == rule_id]
    intel = LocalFeedProvider(str(ROOT / "data" / "intel_feed.json"))
    assert f"rule:{rule_id}" in process(sample(rule_id, "positive"), intel, rules)["tags"]
    assert f"rule:{rule_id}" not in process(sample(rule_id, "negative"), intel, rules)["tags"]


def test_report_download(client):
    resp = client.get("/reports/daily.txt", headers=AUTH)
    assert resp.status_code == 200
    assert resp.data == b"daily report\n"


def test_missing_report_is_404(client):
    assert client.get("/reports/nope.txt", headers=AUTH).status_code == 404


def test_rules_reload(client):
    resp = client.post("/admin/rules/reload", headers=AUTH)
    assert resp.status_code == 200
    assert resp.get_json()["loaded"] == ["SL-0002", "SL-0001"]


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class _FakeSession:
    """Stands in for requests.Session; returns a recorded MISP restSearch response."""

    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return _FakeResponse(
            {"response": {"Attribute": [
                {"type": "ip-src", "value": "203.0.113.9", "event_id": "42", "comment": "scanner"},
            ]}}
        )


def test_misp_provider_parses_rest_search():
    session = _FakeSession()
    misp = MispProvider("https://misp.local/", "misp-key-placeholder", session=session)
    assert misp.lookup("203.0.113.9")["description"] == "MISP event 42: scanner"
    assert misp.lookup("10.0.0.1") is None
    url, kwargs = session.calls[0]
    assert url == "https://misp.local/attributes/restSearch"
    assert kwargs["json"]["type"] == ["ip-src", "ip-dst"]
    assert len(session.calls) == 1  # indicators are pulled once, then served from the index
