"""Load versioned FPL rules from control/rules/ YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES_PATH = REPO_ROOT / "control" / "rules" / "2026-27.yaml"


def load_rules(path: Path | None = None) -> dict[str, Any]:
    rules_path = path or DEFAULT_RULES_PATH
    with rules_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict) or "meta" not in data:
        raise ValueError(f"Invalid rules file: {rules_path}")
    return data


def index_rules(rules: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Flatten category lists into rule_id -> rule mapping."""
    indexed: dict[str, dict[str, Any]] = {}
    for key, value in rules.items():
        if key in {"meta", "launch_verification_checklist"}:
            continue
        if isinstance(value, list):
            for rule in value:
                rule_id = rule["rule_id"]
                if rule_id in indexed:
                    raise ValueError(f"Duplicate rule_id: {rule_id}")
                indexed[rule_id] = rule
    return indexed


def get_rule(rules: dict[str, Any], rule_id: str) -> dict[str, Any]:
    indexed = index_rules(rules)
    if rule_id not in indexed:
        raise KeyError(rule_id)
    return indexed[rule_id]


def required_categories() -> list[str]:
    """Section 5.3 categories that WP-01 must cover."""
    return [
        "squad",
        "lineup",
        "transfers",
        "prices",
        "chips",
        "scoring",
        "defensive_contributions",
        "bonus",
        "automatic_substitutions",
        "captain_fallback",
        "fixtures",
        "corrections",
        "deadlines",
        "exceptional_events",
    ]
