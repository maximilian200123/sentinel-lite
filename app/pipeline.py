"""Normalize -> enrich -> detect. Each step takes and returns an ECS-like event dict."""

from datetime import datetime

from app.intel import IntelProvider
from app.rules import Rule

BASE_RISK = 10
INDICATOR_TAG = "threat.indicator.matched"


def normalize(raw: dict) -> dict:
    return {
        "@timestamp": datetime.fromisoformat(raw["ts"]).isoformat(),
        "source": {"ip": raw["src_ip"]},
        "destination": {"ip": raw["dst_ip"]},
        "user": {"name": raw["user"]},
        "message": raw["message"],
        "event": {"risk_score": BASE_RISK},
        "tags": [],
    }


def _raise_risk(event: dict, amount: int) -> None:
    event["event"]["risk_score"] = min(100, event["event"]["risk_score"] + amount)


def enrich(event: dict, intel: IntelProvider) -> dict:
    indicator = intel.lookup(event["source"]["ip"])
    if indicator:
        event["tags"].append(INDICATOR_TAG)
        event["threat"] = {
            "indicator": {
                "ip": indicator["value"],
                "description": indicator.get("description", ""),
                "provider": intel.name,
            }
        }
        _raise_risk(event, indicator.get("score", 50))
    return event


def detect(event: dict, rules: list[Rule]) -> dict:
    for rule in rules:
        if rule.matches(event):
            event["tags"].append(f"rule:{rule.id}")
            event.setdefault("rule", []).append(
                {"id": rule.id, "name": rule.title, "attack": rule.attack}
            )
            _raise_risk(event, rule.risk)
    return event


def process(raw: dict, intel: IntelProvider, rules: list[Rule]) -> dict:
    return detect(enrich(normalize(raw), intel), rules)
