"""Launch-context enrichment for the initial-squad checkpoint packet."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from src.forecasting.launch_context import artifact_hash, world_cup_csv_hash
from src.ingestion.acquisition import content_hash
from src.orchestration.initial_squad_checkpoint import build_initial_squad_packet
from src.scoring.rules_loader import load_rules, ruleset_sha256


REPO = Path(__file__).resolve().parents[2]
DEADLINE = "2026-08-21T17:30:00Z"
RULES_PATH = REPO / "control/rules/2026-27.yaml"


def _bootstrap() -> dict:
    return {
        "events": [{"id": 1, "deadline_time": DEADLINE}],
        "teams": [
            {"id": 1, "code": 101, "name": "Promoted"},
            {"id": 2, "code": 102, "name": "Established"},
        ],
        "elements": [
            {
                "id": 1,
                "code": 10,
                "web_name": "Promoted New",
                "element_type": 3,
                "team": 1,
                "now_cost": 55,
                "status": "a",
                "ep_next": "6.0",
                "chance_of_playing_next_round": None,
            },
            {
                "id": 2,
                "code": 20,
                "web_name": "New Signing",
                "element_type": 3,
                "team": 2,
                "now_cost": 70,
                "status": "a",
                "ep_next": "7.0",
                "chance_of_playing_next_round": None,
            },
            {
                "id": 3,
                "code": 30,
                "web_name": "Transferred",
                "element_type": 2,
                "team": 2,
                "now_cost": 50,
                "status": "a",
                "ep_next": "4.5",
                "chance_of_playing_next_round": None,
            },
            {
                "id": 4,
                "code": 40,
                "web_name": "Established",
                "element_type": 1,
                "team": 2,
                "now_cost": 45,
                "status": "a",
                "ep_next": "3.5",
                "chance_of_playing_next_round": None,
            },
            # Extra players so a legal squad can be formed under 2026/27 counts.
            *[
                {
                    "id": 100 + index,
                    "code": 1000 + index,
                    "web_name": f"Fill {index}",
                    "element_type": element_type,
                    "team": 2,
                    "now_cost": 40 + index,
                    "status": "a",
                    "ep_next": "2.0",
                    "chance_of_playing_next_round": None,
                }
                for index, element_type in enumerate(
                    [1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4],
                    start=1,
                )
            ],
        ],
    }


def _write_context(tmp_path: Path, *, bootstrap_sha: str, world_cup_sha: str) -> Path:
    context = {
        "schema_version": "1.0",
        "season": "2026-27",
        "status": "test",
        "observed_at": "2026-07-20T08:00:00Z",
        "source_bindings": {
            "official_bootstrap": {
                "observed_at": "2026-07-20T08:00:00Z",
                "sha256": bootstrap_sha,
            },
            "world_cup_priors": {"sha256": world_cup_sha},
        },
        "promoted_teams": [{"team_id": 1, "team_code": 101, "name": "Promoted"}],
        "promoted_team_ids": [1],
        "new_player_codes": [10, 20],
        "transferred_player_codes": [10, 30],
        "classification_policy": {
            "precedence": [
                "promoted_team",
                "new_to_fpl",
                "transferred_player",
                "established",
            ],
            "expected_class_counts": {
                "promoted_team": 1,
                "new_to_fpl": 1,
                "transferred_player": 1,
                "established": 15,
            },
        },
        "cold_start_risk": {
            "promoted_team": 0.1,
            "new_to_fpl": 0.08,
            "transferred_player": 0.08,
            "established": 0.0,
        },
        "world_cup_policy": {
            "fatigue_tier_score": {
                "none": 0.0,
                "moderate": 0.35,
                "high": 0.7,
                "extreme": 1.0,
            },
            "gameweek_fade": [1.0, 1.0, 0.5, 0.5, 0.25, 0.0],
        },
    }
    context["content_sha256"] = artifact_hash(context)
    path = tmp_path / "launch-context.json"
    path.write_text(json.dumps(context, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_world_cup(tmp_path: Path) -> tuple[Path, str]:
    rows = [
        {
            "fpl_code": "10",
            "fatigue_prior": "high",
            "wc_minutes": "420",
            "elimination_date": "2026-07-15",
            "return_to_training_date": "",
            "observed_at": "2026-07-20T07:00:00Z",
        }
    ]
    digest = world_cup_csv_hash(rows)
    path = tmp_path / "world-cup.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    assert content_hash(path.read_bytes()) == digest
    return path, digest


def _policy() -> dict:
    return json.loads(
        (REPO / "control/policies/initial-squad-2026-27.json").read_text(encoding="utf-8")
    )


def _verified(
    tmp_path: Path,
    *,
    with_launch_context: bool,
) -> dict:
    bootstrap = _bootstrap()
    bootstrap_body = (json.dumps(bootstrap, sort_keys=True) + "\n").encode("utf-8")
    bootstrap_path = tmp_path / "bootstrap.json"
    bootstrap_path.write_bytes(bootstrap_body)
    bootstrap_sha = content_hash(bootstrap_body)

    fixtures_body = b"[]\n"
    fixtures_path = tmp_path / "fixtures.json"
    fixtures_path.write_bytes(fixtures_body)
    fixtures_sha = content_hash(fixtures_body)

    rules_sha = ruleset_sha256(RULES_PATH)
    families = {
        "official_bootstrap": {
            "status": "admitted",
            "mandatory": True,
            "artifact_path": str(bootstrap_path),
            "artifact_sha256": bootstrap_sha,
            "observed_at": "2026-07-20T08:00:00Z",
            "available_at": "2026-07-20T08:00:00Z",
            "source_id": "fpl-official-endpoints",
        },
        "official_fixtures": {
            "status": "admitted",
            "mandatory": True,
            "artifact_path": str(fixtures_path),
            "artifact_sha256": fixtures_sha,
            "observed_at": "2026-07-20T08:00:00Z",
            "available_at": "2026-07-20T08:00:00Z",
            "source_id": "fpl-official-endpoints",
        },
        "ruleset": {
            "status": "admitted",
            "mandatory": True,
            "artifact_path": str(RULES_PATH),
            "artifact_sha256": rules_sha,
            "observed_at": "2026-07-20T08:00:00Z",
            "available_at": "2026-07-20T08:00:00Z",
            "source_id": "fpl-official-rules-news",
        },
        "promoted_team_priors": {
            "status": "degraded",
            "mandatory": False,
            "reasons": ["optional_promoted_team_priors_not_supplied"],
        },
        "world_cup_return_fatigue": {
            "status": "degraded",
            "mandatory": False,
            "reasons": ["optional_world_cup_return_fatigue_not_supplied"],
        },
        "transfers_and_signings": {
            "status": "degraded",
            "mandatory": False,
            "reasons": ["optional_transfers_and_signings_not_supplied"],
        },
    }
    bound_paths = {
        "official_bootstrap": bootstrap_path,
        "official_fixtures": fixtures_path,
        "ruleset": RULES_PATH,
    }
    if with_launch_context:
        world_path, world_sha = _write_world_cup(tmp_path)
        context_path = _write_context(
            tmp_path, bootstrap_sha=bootstrap_sha, world_cup_sha=world_sha
        )
        context_sha = content_hash(context_path.read_bytes())
        families["launch_context"] = {
            "status": "admitted",
            "mandatory": False,
            "artifact_path": str(context_path),
            "artifact_sha256": context_sha,
            "world_cup_priors_path": str(world_path),
            "world_cup_priors_sha256": world_sha,
            "observed_at": "2026-07-20T08:00:00Z",
            "available_at": "2026-07-20T08:00:00Z",
            "source_id": "derived-launch-context",
        }
        bound_paths["launch_context"] = context_path
    else:
        families["launch_context"] = {
            "status": "degraded",
            "mandatory": False,
            "reasons": ["launch_context_not_supplied"],
        }

    manifest = {
        "season": "2026-27",
        "checkpoint_id": "weekly-2026-07-20",
        "deadline": DEADLINE,
        "observed_at": "2026-07-20T08:00:00Z",
        "available_at": "2026-07-20T08:00:00Z",
        "account_writes": False,
        "ruleset_sha256": rules_sha,
        "families": families,
        "content_sha256": "a" * 64,
    }
    family_states = {
        family_id: {
            "state": "admitted" if family.get("status") == "admitted" else "unavailable",
            "manifest_status": family.get("status"),
            "mandatory": bool(family.get("mandatory", False)),
            "artifact_sha256": family.get("artifact_sha256"),
            "source_id": family.get("source_id", "unknown"),
            "reasons": list(family.get("reasons", [])),
        }
        for family_id, family in families.items()
    }
    return {
        "manifest_path": tmp_path / "manifest.json",
        "manifest": manifest,
        "checkpoint_id": "weekly-2026-07-20",
        "observed_at": "2026-07-20T08:00:00Z",
        "available_at": "2026-07-20T08:00:00Z",
        "deadline": DEADLINE,
        "bootstrap": bootstrap,
        "fixtures": [],
        "family_states": family_states,
        "bound_paths": bound_paths,
    }


def test_launch_context_enrichment_applies_cold_start_and_fatigue(tmp_path: Path) -> None:
    verified = _verified(tmp_path, with_launch_context=True)
    rules = load_rules(RULES_PATH)
    result = build_initial_squad_packet(
        verified,
        policy=_policy(),
        rules=rules,
        rules_hash=ruleset_sha256(RULES_PATH),
    )
    enrichment = result["launch_context_enrichment"]
    assert enrichment["status"] == "applied"
    assert enrichment["players_enriched"] >= 4
    by_id = {row["player_id"]: row for row in result["packet"]["players"]}
    assert by_id["1"]["promoted_team"] is True
    assert by_id["1"]["new_signing"] is True
    assert by_id["1"]["world_cup_fatigue"] == 0.7
    assert by_id["2"]["new_signing"] is True
    assert by_id["2"]["promoted_team"] is False
    assert by_id["4"]["promoted_team"] is False
    assert by_id["4"]["new_signing"] is False
    assert result["forecast_quality"]["status"] == "operational_baseline_only"
    assert "derived from admitted launch_context" in result["fallbacks"]["promoted_team_priors"]


def test_missing_launch_context_keeps_defaults_and_explicit_gap(tmp_path: Path) -> None:
    verified = _verified(tmp_path, with_launch_context=False)
    rules = load_rules(RULES_PATH)
    result = build_initial_squad_packet(
        verified,
        policy=_policy(),
        rules=rules,
        rules_hash=ruleset_sha256(RULES_PATH),
    )
    assert result["launch_context_enrichment"]["status"] == "unavailable"
    assert all(row["promoted_team"] is False for row in result["packet"]["players"])
    assert all(row["world_cup_fatigue"] == 0.0 for row in result["packet"]["players"])
    assert result["forecast_quality"]["manual_entry_eligible"] is False
