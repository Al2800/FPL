"""Contracts for the exploratory GW1 structured-prior seed branch."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from src.orchestration.historical_seed_counterfactual import (
    PREDEADLINE_EXCLUSIONS,
    build_candidate_pool,
    build_counterfactual_seed,
    decompose_seed_result,
)


REPO = Path(__file__).resolve().parents[2]
VAASTAV = REPO / "data" / "raw" / "vaastav" / "Fantasy-Premier-League" / "data"
EPISODES = REPO / "data" / "benchmark-v0" / "episodes" / "v2" / "2025-26"


def _pool() -> dict:
    return build_candidate_pool(
        gw1_path=VAASTAV / "2025-26" / "gws" / "gw1.csv",
        current_players_path=VAASTAV / "2025-26" / "players_raw.csv",
        previous_players_path=VAASTAV / "2024-25" / "players_raw.csv",
        identity_map_path=EPISODES / "gw-01" / "identity-map.json",
        episode_root=EPISODES,
    )


def test_candidate_pool_is_field_whitelisted_and_deterministic() -> None:
    first = _pool()
    second = _pool()

    assert first == second
    assert first["candidate_count"] == 689
    assert first["content_sha256"] == second["content_sha256"]
    assert "total_points" in first["explicitly_excluded_gw1_fields"]
    assert "xP" in first["explicitly_excluded_gw1_fields"]
    assert set(PREDEADLINE_EXCLUSIONS) == {383}
    assert 383 not in {row["fpl_element_id"] for row in first["players"]}
    assert all("total_points" not in row for row in first["players"])


def test_counterfactual_seed_is_legal_and_differs_from_control() -> None:
    control = json.loads(
        (
            REPO / "control" / "seeds" / "2025-26" / "official-scout-gw1.json"
        ).read_text(encoding="utf-8")
    )
    seed = build_counterfactual_seed(_pool(), control)
    positions = Counter(row["position"] for row in seed["squad"])
    clubs = Counter(row["club_id"] for row in seed["squad"])
    ids = {row["player_id"] for row in seed["squad"]}
    control_ids = {row["player_id"] for row in control["squad"]}

    assert positions == Counter({"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3})
    assert max(clubs.values()) <= 3
    assert round(sum(row["purchase_price"] for row in seed["squad"]) + seed["bank"], 1) == 100.0
    assert len(ids) == 15
    assert ids != control_ids
    assert set(seed["initial_plan"]["starting_xi_ids"]).issubset(ids)
    assert set(seed["initial_plan"]["bench_ids"]).issubset(ids)
    assert len(seed["initial_plan"]["starting_xi_ids"]) == 11
    assert len(seed["initial_plan"]["bench_ids"]) == 4
    assert seed["initial_plan"]["captain_id"] in seed["initial_plan"]["starting_xi_ids"]
    assert seed["initial_plan"]["vice_captain_id"] in seed["initial_plan"]["starting_xi_ids"]
    assert seed["initial_plan"]["captain_id"] != seed["initial_plan"]["vice_captain_id"]
    assert "exploratory_production_ineligible" in seed["limitations"]


def test_decomposition_separates_seed_week_from_carried_policy(tmp_path: Path) -> None:
    control = tmp_path / "control"
    branch = tmp_path / "branch"
    for gameweek, control_points, branch_points in ((1, 56, 62), (2, 50, 47)):
        for root, weekly, cumulative in (
            (control, control_points, 56 if gameweek == 1 else 106),
            (branch, branch_points, 62 if gameweek == 1 else 109),
        ):
            path = root / f"gw-{gameweek:02d}"
            path.mkdir(parents=True)
            (path / "run-summary.json").write_text(
                json.dumps(
                    {
                        "arms": {
                            "forecast_optimizer": {
                                "net_points": weekly,
                                "cumulative_points": cumulative,
                                "transfers": 0 if gameweek == 1 else 1,
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

    result = decompose_seed_result(
        control_root=control,
        branch_root=branch,
        stop_gameweek=2,
    )

    assert result["decomposition"]["gw1_initial_seed_realised_delta"] == 6
    assert result["decomposition"]["gw2_to_stop_policy_and_carried_state_delta"] == -3
    assert result["decomposition"]["total_delta"] == 3
    assert "not a pure seed-only causal effect" in result["decomposition"]["interpretation"]
