"""Detection rules loaded from rules/*.yaml: safe YAML, then a strict schema."""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

RULE_ID = re.compile(r"SL-\d{4}")
ATTACK_ID = re.compile(r"T\d{4}(\.\d{3})?")
MATCH_FIELDS = {"message", "user.name", "source.ip", "destination.ip"}
REQUIRED = {"id": str, "title": str, "attack": str, "risk": int, "match": dict}


class RuleError(ValueError):
    """A rule file that is not valid YAML data or does not fit the schema."""


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    attack: str
    risk: int
    field: str
    contains: tuple[str, ...]

    def matches(self, event: dict) -> bool:
        value = event
        for part in self.field.split("."):
            value = value.get(part, {}) if isinstance(value, dict) else {}
        if not isinstance(value, str):
            return False
        text = value.lower()
        return any(needle.lower() in text for needle in self.contains)


def parse_rule(doc: object, source: str) -> Rule:
    if not isinstance(doc, dict):
        raise RuleError(f"{source}: a rule must be a mapping")
    if extra := set(doc) - set(REQUIRED):
        raise RuleError(f"{source}: unknown keys {sorted(extra)}")
    for key, kind in REQUIRED.items():
        if not isinstance(doc.get(key), kind) or isinstance(doc.get(key), bool):
            raise RuleError(f"{source}: '{key}' must be a {kind.__name__}")
    match = doc["match"]
    contains = match.get("contains")
    if not RULE_ID.fullmatch(doc["id"]) or not ATTACK_ID.fullmatch(doc["attack"]):
        raise RuleError(f"{source}: id must look like SL-0001 and attack like T1110.001")
    if not 0 <= doc["risk"] <= 100:
        raise RuleError(f"{source}: risk must be 0-100")
    if set(match) != {"field", "contains"} or match["field"] not in MATCH_FIELDS:
        raise RuleError(f"{source}: match needs field (one of {sorted(MATCH_FIELDS)}) and contains")
    if not (isinstance(contains, list) and contains and all(isinstance(c, str) and c for c in contains)):
        raise RuleError(f"{source}: match.contains must be a non-empty list of strings")
    return Rule(doc["id"], doc["title"], doc["attack"], doc["risk"], match["field"], tuple(contains))


def load_rules(rules_dir: str) -> list[Rule]:
    """All rules or none: one bad file raises RuleError and nothing is replaced."""
    rules = []
    for path in sorted(Path(rules_dir).glob("*.yaml")):
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise RuleError(f"{path.name}: not plain YAML data ({exc.__class__.__name__})") from exc
        rules.append(parse_rule(doc, path.name))
    return rules
