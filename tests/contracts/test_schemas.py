"""WP-03: every Section 9 entity has a schema and validating example."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    jsonschema = None

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "control" / "schemas"
CATALOG = SCHEMAS / "catalog.yaml"

SECTION_9_ENTITIES = {
    # 9.1
    "players",
    "player_identities",
    "player_team_history",
    "player_position_history",
    "teams",
    "team_identities",
    "club_managers",
    "competitions",
    "seasons",
    "gameweeks",
    "fixtures",
    "fixture_revisions",
    # 9.2
    "player_match_events",
    "player_match_stats",
    "player_gameweek_stats",
    "team_match_stats",
    "player_prices",
    "player_availability",
    "player_discipline",
    "set_piece_roles",
    # 9.3
    "manager_snapshots",
    "manager_squads",
    "manager_finance",
    "manager_chips",
    "manager_transfers",
    "manager_gameweek_picks",
    # 9.4
    "source_documents",
    "document_passages",
    "extracted_claims",
    "claim_entities",
    "claim_conflicts",
    "decision_signals",
    "proposed_adjustments",
    # 9.5
    "forecast_runs",
    "player_projections",
    "simulation_runs",
    "optimizer_runs",
    "candidate_plans",
    "agent_runs",
    "agent_reviews",
    "rule_validations",
    "final_proposals",
    "approvals",
    "executions",
    "decision_outcomes",
    "retrospectives",
}


def _load_schema(rel: str) -> dict:
    path = SCHEMAS / rel
    schema = json.loads(path.read_text(encoding="utf-8"))
    # Resolve local $ref to _defs by inlining $defs
    defs = json.loads((SCHEMAS / "_defs.json").read_text(encoding="utf-8"))["$defs"]
    return schema, defs


def _rewrite_refs(obj, defs):
    if isinstance(obj, dict):
        if set(obj.keys()) == {"$ref"} and "/$defs/" in obj["$ref"]:
            name = obj["$ref"].split("/$defs/")[-1]
            return defs[name]
        return {k: _rewrite_refs(v, defs) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_rewrite_refs(v, defs) for v in obj]
    return obj


def test_catalog_covers_section_9():
    catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    names = {e["entity"] for e in catalog["entities"]}
    assert names == SECTION_9_ENTITIES


def test_each_schema_has_valid_example():
    assert jsonschema is not None, "jsonschema package required"
    catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    for entry in catalog["entities"]:
        schema, defs = _load_schema(entry["schema"])
        schema = _rewrite_refs(schema, defs)
        example_path = SCHEMAS / entry["example"]
        assert example_path.exists(), entry["entity"]
        example = json.loads(example_path.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(example)


def test_temporal_entities_require_observed_and_available():
    catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    for entry in catalog["entities"]:
        if not entry["temporal"]:
            continue
        schema, _ = _load_schema(entry["schema"])
        required = set(schema["required"])
        assert {"observed_at", "available_at"} <= required, entry["entity"]


def test_identity_resolution_example_exists():
    path = SCHEMAS / "examples" / "identity_resolution_cross_season.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["player"]["player_uid"]
    assert len(data["identities"]) >= 2
    assert data["identities"][0]["source_player_id"] != data["identities"][1]["source_player_id"]
