"""Threat-intel providers. The service only depends on the IntelProvider interface."""

import json
from typing import Protocol


class IntelProvider(Protocol):
    name: str

    def lookup(self, ip: str) -> dict | None:
        """Return the indicator for this IP, or None when the IP is not known-bad."""


class LocalFeedProvider:
    """Reads indicators from a local JSON file shaped like a MISP attribute export."""

    name = "local-feed"

    def __init__(self, path: str):
        with open(path, encoding="utf-8") as f:
            feed = json.load(f)
        self._index = {i["value"]: i for i in feed["indicators"] if i["type"] in {"ip-src", "ip-dst"}}

    def lookup(self, ip: str) -> dict | None:
        return self._index.get(ip)


class MispProvider:
    """Pulls ip-src/ip-dst attributes from a MISP instance through its REST API.

    Not used by default: the lab laptop runs no MISP. Wire it in by passing an
    instance to create_app(intel=...). Tested against a recorded response.
    """

    name = "misp"

    def __init__(self, url: str, api_key: str, session=None, verify_tls: bool = True):
        import requests

        self._url = url.rstrip("/")
        self._api_key = api_key
        self._session = session or requests.Session()
        self._verify = verify_tls
        self._index: dict[str, dict] | None = None

    def pull(self) -> list[dict]:
        resp = self._session.post(
            f"{self._url}/attributes/restSearch",
            json={"returnFormat": "json", "type": ["ip-src", "ip-dst"], "to_ids": True},
            headers={"Authorization": self._api_key, "Accept": "application/json"},
            timeout=10,
            verify=self._verify,
        )
        resp.raise_for_status()
        return [
            {
                "type": a["type"],
                "value": a["value"],
                "score": 50,
                "description": f"MISP event {a['event_id']}: {a.get('comment', '')}".strip(),
            }
            for a in resp.json()["response"]["Attribute"]
        ]

    def lookup(self, ip: str) -> dict | None:
        if self._index is None:
            self._index = {i["value"]: i for i in self.pull()}
        return self._index.get(ip)
