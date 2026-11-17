"""Detection rules loaded from rules/*.yaml."""

from dataclasses import dataclass
from pathlib import Path

import yaml


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


def load_rules(rules_dir: str) -> list[Rule]:
    rules = []
    for path in sorted(Path(rules_dir).glob("*.yaml")):
        with open(path, encoding="utf-8") as f:
            doc = yaml.load(f, Loader=yaml.Loader)
        rules.append(
            Rule(
                id=doc["id"],
                title=doc["title"],
                attack=doc["attack"],
                risk=doc["risk"],
                field=doc["match"]["field"],
                contains=tuple(doc["match"]["contains"]),
            )
        )
    return rules
