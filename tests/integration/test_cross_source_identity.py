"""Cross-source identity resolution contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from src.data.identity_resolution import (
    IdentityResolutionError,
    normalise_name,
    require_resolved,
    resolve_identities,
)

REPO = Path(__file__).resolve().parents[2]


def _worked_items() -> list[dict]:
    return [
        {"entity_type": "team", "source_id": "fpl-official-endpoints", "source_entity_id": "1", "source_name": "Arsenal", "effective_at": "2026-08-01T00:00:00Z"},
        {"entity_type": "team", "source_id": "football-data-co-uk", "source_entity_id": "Arsenal", "source_name": "Arsenal", "effective_at": "2026-08-01T00:00:00Z"},
        {"entity_type": "fixture", "source_id": "fpl-official-endpoints", "source_entity_id": "1", "source_name": "Arsenal v Manchester United", "effective_at": "2026-08-15T15:00:00Z"},
        {"entity_type": "fixture", "source_id": "football-data-co-uk", "source_entity_id": "2026-08-15|Arsenal|Man United", "source_name": "Arsenal v Man United", "effective_at": "2026-08-15T15:00:00Z"},
        {"entity_type": "player", "source_id": "fpl-official-endpoints", "source_entity_id": "1", "source_name": "Bukayo Saka", "effective_at": "2026-08-01T00:00:00Z"},
    ]


def test_worked_fpl_and_results_identities_resolve_to_canonical_ids():
    report = require_resolved(resolve_identities(_worked_items(), season="2026-27"))
    assert report["records"][0]["canonical_id"] == report["records"][1]["canonical_id"]
    assert report["records"][2]["canonical_id"] == report["records"][3]["canonical_id"]
    assert report["metrics"] == {"total": 5, "resolved": 5, "review": 0, "unresolved": 0, "match_rate": 1.0}


def test_report_validates_and_identity_hash_is_order_independent():
    items = _worked_items()
    first = resolve_identities(items, season="2026-27")
    second = resolve_identities(list(reversed(items)), season="2026-27")
    schema = json.loads((REPO / "control/schemas/data/source-identity-map.json").read_text())
    Draft202012Validator(schema).validate(first)
    assert first["mapping_id"] == second["mapping_id"]


def test_alias_matching_is_normalised_but_exact():
    item = {"entity_type": "team", "source_id": "football-data-co-uk", "source_entity_id": "unknown", "source_name": "  MAN-UNITED ", "effective_at": "2026-08-01T00:00:00Z"}
    report = resolve_identities([item], season="2026-27")
    assert normalise_name("Man United") == normalise_name("  MAN-UNITED ")
    assert report["records"][0]["canonical_id"] == "team:manchester-united"
    assert report["records"][0]["resolution_method"] == "exact_alias"


def test_wrong_season_or_date_is_unresolved_and_fails_closed():
    report = resolve_identities(_worked_items()[:1], season="2025-26")
    assert report["metrics"]["unresolved"] == 1
    with pytest.raises(IdentityResolutionError, match="unresolved"):
        require_resolved(report)


def test_ambiguous_alias_enters_review_queue(tmp_path: Path):
    catalog = {
        "catalog_version": "test",
        "aliases": [
            {"entity_type": "team", "canonical_id": "team:a", "source_id": "test", "alias": "United", "seasons": ["2026-27"]},
            {"entity_type": "team", "canonical_id": "team:b", "source_id": "test", "alias": "United", "seasons": ["2026-27"]},
        ],
    }
    path = tmp_path / "aliases.yaml"
    path.write_text(yaml.safe_dump(catalog), encoding="utf-8")
    report = resolve_identities(
        [{"entity_type": "team", "source_id": "test", "source_name": "United"}],
        season="2026-27",
        catalog_path=path,
    )
    assert report["records"][0]["status"] == "review"
    assert report["records"][0]["candidates"] == ["team:a", "team:b"]
    with pytest.raises(IdentityResolutionError, match="review"):
        require_resolved(report)
