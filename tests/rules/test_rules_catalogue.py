"""WP-01 acceptance: every Section 5.3 category is covered with sourced rules."""

from pathlib import Path

import yaml

from src.scoring.rules_loader import index_rules, load_rules, required_categories

REPO = Path(__file__).resolve().parents[2]
GOLDEN = REPO / "evals" / "golden-cases" / "rules-2026-27.yaml"


def test_all_required_categories_present():
    rules = load_rules()
    for category in required_categories():
        assert category in rules, f"missing category {category}"
        assert isinstance(rules[category], list) and rules[category], f"{category} empty"


def test_every_rule_has_status_source_and_verification():
    indexed = index_rules(load_rules())
    assert indexed
    for rule_id, rule in indexed.items():
        assert rule.get("status") in {
            "confirmed",
            "inherited",
            "provisional",
            "disputed",
            "retired",
        }, rule_id
        assert rule.get("source_url"), rule_id
        assert rule.get("verified_at"), rule_id
        assert "value" in rule, rule_id


def test_live_catalogue_is_fully_verified_after_owner_ready_audit():
    indexed = index_rules(load_rules())
    assert all(rule["status"] == "confirmed" for rule in indexed.values())
    assert all(rule["verified_at"] == "2026-07-27" for rule in indexed.values())
    assert all(rule["source_published_at"] for rule in indexed.values())
    assert "chips.boundary_restrictions" in indexed

def test_golden_cases_cover_each_rule_family():
    cases = yaml.safe_load(GOLDEN.read_text(encoding="utf-8"))["cases"]
    families = {c["family"] for c in cases}
    expected = {
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
    }
    assert expected <= families
