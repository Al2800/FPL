"""Load versioned FPL rules from control/rules/ YAML."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES_PATH = REPO_ROOT / "control" / "rules" / "2026-27.yaml"


def ruleset_bytes(path: Path | None = None) -> bytes:
    """Return canonical evidence bytes independent of checkout line endings."""

    rules_path = path or DEFAULT_RULES_PATH
    return rules_path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def ruleset_sha256(path: Path | None = None) -> str:
    """Hash the canonical ruleset evidence bytes."""

    return hashlib.sha256(ruleset_bytes(path)).hexdigest()


def load_rules(path: Path | None = None) -> dict[str, Any]:
    rules_path = path or DEFAULT_RULES_PATH
    data = yaml.safe_load(ruleset_bytes(rules_path).decode("utf-8"))
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


# Imported after the loader primitives are defined because rules_activation
# compiles the indexed catalogue while this module remains the public API.
from src.scoring.rules_activation import (  # noqa: E402,F401
    RulesetActivationError,
    assert_ruleset_activatable,
    build_ruleset_activation,
    ruleset_semantic_diff,
)
