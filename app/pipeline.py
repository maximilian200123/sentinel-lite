"""Normalize -> enrich -> detect. Each step takes and returns an ECS-like event dict."""

import ipaddress
from datetime import datetime

from app.intel import IntelProvider
from app.rules import Rule

BASE_RISK = 10
INDICATOR_TAG = "threat.indicator.matched"
FIELDS = {"ts": 64, "src_ip": 64, "dst_ip": 64, "user": 128, "message": 4096}  # name -> max length


class InvalidEvent(ValueError):
    """The client sent something that is not a valid raw event."""


def normalize(raw: object) -> dict:
    """Parse an untrusted raw event (the API boundary): exact fields, strings, real IPs and time."""
    if not isinstance(raw, dict):
        raise InvalidEvent("body must be a JSON object")
    if missing := FIELDS.keys() - raw.keys():
        raise InvalidEvent(f"missing fields: {sorted(missing)}")
    if extra := raw.keys() - FIELDS.keys():
        raise InvalidEvent(f"unknown fields: {sorted(extra)}")
    for name, limit in FIELDS.items():
        if not isinstance(raw[name], str) or not raw[name] or len(raw[name]) > limit:
            raise InvalidEvent(f"'{name}' must be a non-empty string of at most {limit} characters")
    try:
        ts = datetime.fromisoformat(raw["ts"])
        src, dst = ipaddress.ip_address(raw["src_ip"]), ipaddress.ip_address(raw["dst_ip"])
    except ValueError as exc:
        raise InvalidEvent(str(exc)) from exc
    return {
        "@timestamp": ts.isoformat(),
        "source": {"ip": str(src)},
        "destination": {"ip": str(dst)},
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


def process(raw: object, intel: IntelProvider, rules: list[Rule]) -> dict:
    return detect(enrich(normalize(raw), intel), rules)
