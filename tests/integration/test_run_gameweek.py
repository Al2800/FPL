"""Integration contracts for the deterministic run_gameweek orchestrator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.optimisation.io import fingerprint, load_solver_input
from src.orchestration.run_gameweek import (
    RunGameweekError,
    run_gameweek,
    select_latest_predeadline_snapshot,
)
from src.reporting.decision_record import validate_decision_record
from src.scoring.rules_loader import load_rules, ruleset_sha256
from src.scoring.validator import selling_price


REPO = Path(__file__).resolve().parents[2]
GOLDEN = REPO / "evals" / "golden-cases" / "optimiser-gw3-input.json"
RULES_PATH = REPO / "control" / "rules" / "2026-27.yaml"
RULES = load_rules(RULES_PATH)
RULES_HASH = ruleset_sha256(RULES_PATH)


def _manager_state_and_forecast() -> tuple[dict, dict]:
    golden = load_solver_input(GOLDEN).as_dict()
    squad = []
    for player in golden["players"]:
        if player["player_id"] not in golden["squad_player_ids"]:
            continue
        purchase = float(player.get("purchase_price", player["now_cost"]))
        current = float(player["now_cost"])
        squad.append(
            {
                "player_id": str(player["player_id"]),
                "fpl_code": int(player["player_id"]),
                "web_name": player["web_name"],
                "position": player["position"],
                "club_id": str(player["club_id"]),
                "purchase_price": purchase,
                "current_price": current,
                "selling_price": selling_price(purchase, current, dict(RULES)),
            }
        )
    state = {
        "manager_state_version": "1.0",
        "manager_state_id": "manager-state:fixture:gw03:lab",
        "manager_id": "lab-manager",
        "season": golden["season"],
        "gameweek": golden["gameweek"],
        "observed_at": "2026-08-21T10:00:00Z",
        "available_at": "2026-08-21T10:00:00Z",
        "cutoff": "2026-08-21T16:00:00Z",
        "deadline": "2026-08-21T17:30:00Z",
        "ruleset_id": golden["ruleset_id"],
        "ruleset_sha256": RULES_HASH,
        "bank": golden["bank"],
        "free_transfers": golden["free_transfers"],
        "chips_available": list(golden["chips_available"]),
        "chip_history": [],
        "squad": squad,
        "content_sha256": "b" * 64,
    }
    forecast = {
        "season": golden["season"],
        "gameweek": golden["gameweek"],
        "model_version": "fixture-forecast-v0",
        "players": [
            {
                "player_id": str(player["player_id"]),
                "web_name": player["web_name"],
                "position": player["position"],
                "club_id": str(player["club_id"]),
                "now_cost": float(player["now_cost"]),
                "expected_points": float(player["expected_points"]),
                "status": player.get("status", "a"),
            }
            for player in golden["players"]
        ],
    }
    return state, forecast


def test_select_latest_predeadline_snapshot_enforces_point_in_time() -> None:
    deadline = "2026-08-21T17:30:00Z"
    selected = select_latest_predeadline_snapshot(
        [
            {"available_at": "2026-08-20T17:30:00Z", "path": "a"},
            {"available_at": "2026-08-21T15:30:00Z", "path": "b"},
            {"available_at": "2026-08-21T17:30:00Z", "path": "c"},
            {"available_at": "2026-08-21T17:31:00Z", "path": "late-ignored"},
        ],
        deadline=deadline,
    )
    assert selected["path"] == "c"

    with pytest.raises(RunGameweekError, match="No pre-deadline snapshots"):
        select_latest_predeadline_snapshot(
            [
                {"available_at": "2026-08-21T17:31:00Z", "path": "late"},
            ],
            deadline=deadline,
        )


def test_run_gameweek_produces_validated_reproducible_gdr(tmp_path: Path) -> None:
    state, forecast = _manager_state_and_forecast()
    out_a = tmp_path / "run-a"
    out_b = tmp_path / "run-b"
    snapshots = [
        {
            "available_at": "2026-08-20T17:30:00Z",
            "observed_at": "2026-08-20T17:30:00Z",
            "path": "old",
        },
        {
            "available_at": "2026-08-21T15:30:00Z",
            "observed_at": "2026-08-21T15:30:00Z",
            "path": "latest-ok",
        },
    ]

    first = run_gameweek(
        manager_state=state,
        forecast=forecast,
        snapshot_candidates=snapshots,
        evidence=None,
        rules_path=RULES_PATH,
        out_dir=out_a,
        validate_record=True,
    )
    second = run_gameweek(
        manager_state=state,
        forecast=forecast,
        snapshot_candidates=snapshots,
        evidence=None,
        rules_path=RULES_PATH,
        out_dir=out_b,
        validate_record=True,
    )

    validate_decision_record(first["record"])
    assert first["degraded"] is True
    assert "evidence_absent_fallback_deterministic" in first["degraded_reasons"]
    assert first["selected_snapshot"]["path"] == "latest-ok"
    assert (out_a / "decision-record.json").is_file()
    assert (out_a / "decision-record.txt").is_file()
    assert first["solver_output"]["selected"]["validation"]["squad_ok"] is True
    assert first["solver_output"]["selected"]["validation"]["lineup_ok"] is True

    # Identical inputs reproduce fingerprints (plan §3.2 success criterion 6).
    assert first["solver_input_fingerprint"] == second["solver_input_fingerprint"]
    assert first["solver_output_fingerprint"] == second["solver_output_fingerprint"]
    assert first["decision_record_sha256"] == second["decision_record_sha256"]
    assert fingerprint(first["record"]) == fingerprint(
        json.loads((out_b / "decision-record.json").read_text(encoding="utf-8"))
    )


def test_run_gameweek_requires_forecast_or_live_faithful_inputs() -> None:
    state, _forecast = _manager_state_and_forecast()
    with pytest.raises(RunGameweekError, match="forecast or live_faithful"):
        run_gameweek(manager_state=state, rules_path=RULES_PATH, validate_record=False)


def test_run_gameweek_missed_capture_freshness_flags_gdr(tmp_path: Path) -> None:
    from src.orchestration.freshness_monitor import evaluate_capture_freshness

    state, forecast = _manager_state_and_forecast()
    policy = json.loads(
        (REPO / "config" / "data_sources" / "2026-27-capture-scheduler.json").read_text(
            encoding="utf-8"
        )
    )
    freshness = evaluate_capture_freshness(
        policy=policy,
        bootstrap={
            "events": [
                {"id": 1, "deadline_time": "2026-08-21T17:30:00Z"},
            ]
        },
        scheduler_state={"terminal_job_ids": []},
        now="2026-08-21T16:01:00Z",
    )
    result = run_gameweek(
        manager_state=state,
        forecast=forecast,
        evidence={"status": "ok"},
        freshness_report=freshness,
        rules_path=RULES_PATH,
        out_dir=tmp_path / "fresh",
        validate_record=True,
    )
    assert result["degraded"] is True
    assert any(r.startswith("capture_missed:T-2h") for r in result["degraded_reasons"])
    assert result["record"]["freshness"]["capture"]["status"] == "degraded"


def test_run_gameweek_monte_carlo_attaches_distributions(tmp_path: Path) -> None:
    state, forecast = _manager_state_and_forecast()
    # Minimal one-player fixture covering the recommended XI captain when possible.
    squad_ids = {str(row["player_id"]) for row in state["squad"]}
    player = next(p for p in forecast["players"] if str(p["player_id"]) in squad_ids)
    monte_carlo = {
        "n_paths": 40,
        "seed": 99,
        "fixtures": [
            {
                "fixture_id": "fx-lab",
                "home_club_id": player["club_id"],
                "away_club_id": "opp",
                "expected_home_xg": 1.2,
                "expected_away_xg": 1.0,
            }
        ],
        "players": [
            {
                "player_id": str(p["player_id"]),
                "position": p["position"],
                "club_id": p["club_id"],
                "fixture_id": "fx-lab",
                "appearance": {"zero": 0.1, "under_60": 0.2, "60_plus": 0.7},
                "goals_per_90": 0.2,
                "assists_per_90": 0.15,
            }
            for p in forecast["players"]
            if str(p["player_id"]) in squad_ids and p["club_id"] == player["club_id"]
        ],
    }
    # Ensure every squad player has a sim row (away side if needed).
    covered = {row["player_id"] for row in monte_carlo["players"]}
    for p in forecast["players"]:
        pid = str(p["player_id"])
        if pid not in squad_ids or pid in covered:
            continue
        monte_carlo["fixtures"].append(
            {
                "fixture_id": f"fx-{pid}",
                "home_club_id": p["club_id"],
                "away_club_id": "opp",
                "expected_home_xg": 1.1,
                "expected_away_xg": 0.9,
            }
        )
        monte_carlo["players"].append(
            {
                "player_id": pid,
                "position": p["position"],
                "club_id": p["club_id"],
                "fixture_id": f"fx-{pid}",
                "appearance": {"zero": 0.1, "under_60": 0.2, "60_plus": 0.7},
                "goals_per_90": 0.15,
                "assists_per_90": 0.1,
            }
        )

    result = run_gameweek(
        manager_state=state,
        forecast=forecast,
        evidence={"status": "ok"},
        monte_carlo=monte_carlo,
        rules_path=RULES_PATH,
        out_dir=tmp_path / "mc",
        validate_record=True,
    )
    summary = result["record"]["projections_summary"]
    assert summary["p10"] <= summary["p50"] <= summary["p90"]
    assert summary["simulation"]["seed"] == 99
    with_dist = [
        plan for plan in result["record"]["candidate_plans"] if "points_distribution" in plan
    ]
    assert with_dist
    assert with_dist[0]["points_distribution"]["p10"] <= with_dist[0]["points_distribution"]["p90"]
