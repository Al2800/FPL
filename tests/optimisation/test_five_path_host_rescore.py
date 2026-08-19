from __future__ import annotations

import json
from pathlib import Path

from src.optimisation.five_path_squads import (
    PATHS,
    PLAYERS,
    host_rescore_path,
    host_rescore_paths,
    validate_path_rules,
)
from src.scoring.rules_loader import load_rules, ruleset_sha256


REPO = Path(__file__).resolve().parents[2]
RULES_PATH = REPO / "control" / "rules" / "2026-27.yaml"
POLICY_PATH = REPO / "control" / "policies" / "initial-squad-2026-27.json"
RULES = load_rules(RULES_PATH)
RULES_HASH = ruleset_sha256(RULES_PATH)


def policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def packet_for_paths() -> dict:
    players = []
    for player in PLAYERS.values():
        players.append(
            {
                "player_id": player["player_id"],
                "web_name": player["web_name"],
                "position": player["position"],
                "club_id": player["club_id"],
                "now_cost": player["now_cost"],
                "available_at": "2026-08-14T10:00:00Z",
                "expected_points": [4.0, 3.8, 3.6, 3.4, 3.2, 3.0],
                "start_probability": [0.85] * 6,
                "uncertainty": [0.3] * 6,
            }
        )
    return {
        "schema_version": "1.0",
        "decision_id": "seed:2026-27:five-path",
        "season": "2026-27",
        "decision_cutoff": "2026-08-21T17:30:00Z",
        "captured_at": "2026-08-19T12:00:00Z",
        "ruleset_id": RULES["meta"]["ruleset_id"],
        "ruleset_sha256": RULES_HASH,
        "feature_state_sha256": "b" * 64,
        "forecast_model_version": "test-five-path-v1",
        "horizon_gameweeks": [1, 2, 3, 4, 5, 6],
        "discount_factors": [1.0, 0.9, 0.81, 0.729, 0.6561, 0.59049],
        "players": players,
    }


def test_five_path_ids_are_official_and_rules_valid() -> None:
    assert PLAYERS["Haaland"]["player_id"] == "411"
    assert PLAYERS["Calafiori"]["player_id"] == "8"
    assert PLAYERS["Kinsky"]["player_id"] == "496"
    assert PLAYERS["Xhaka"]["player_id"] == "544"
    for path in PATHS:
        checked = validate_path_rules(path, rules=RULES)
        assert checked["squad_ok"] is True
        assert checked["lineup_ok"] is True


def test_host_rescore_scores_c_d_e_on_same_packet() -> None:
    scored = host_rescore_paths(
        packet_for_paths(),
        [path for path in PATHS if path["path_id"].startswith(("C-", "D-", "E-"))],
        policy=policy(),
        rules=RULES,
        ruleset_sha256=RULES_HASH,
        arm_modes=("robust", "deterministic"),
    )
    assert [row["path_id"] for row in scored] == [
        "C-premium-override-advisory",
        "D-death-zone-playing-15",
        "E-minutes-first",
    ]
    for row in scored:
        for arm in ("robust", "deterministic"):
            assert row["arms"][arm]["ok"] is True
            assert row["arms"][arm]["objective"] > 0
            assert row["arms"][arm]["validation_ok"] is True
        assert (
            row["arms"]["deterministic"]["objective"]
            >= row["arms"]["robust"]["objective"]
        )


def test_host_rescore_reports_unknown_player_without_raising() -> None:
    empty = packet_for_paths()
    empty["players"] = [row for row in empty["players"] if row["player_id"] != "411"]
    path_c = next(
        path for path in PATHS if path["path_id"] == "C-premium-override-advisory"
    )
    scored = host_rescore_path(
        empty,
        path_c,
        policy=policy(),
        rules=RULES,
        ruleset_sha256=RULES_HASH,
        arm_modes=("robust",),
    )
    assert scored["arms"]["robust"]["ok"] is False
    assert "unknown players" in scored["arms"]["robust"]["error"]
    assert "411" in scored["arms"]["robust"]["error"]
