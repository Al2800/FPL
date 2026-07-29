"""Contracts for squad-contingency component ablation."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.evaluation.squad_contingency import paired_decision_hash
from src.evaluation.squad_contingency_ablation import (
    ABLATION_COMPONENTS,
    COMPONENT_IDENTIFICATION,
    _verify_ablation_w10_bindings,
    build_ablation_report,
    choose_ablated_contingency_lineup,
    evaluate_descriptive_component,
    evaluate_locked_component,
    verify_w10_reference,
)
from src.forecasting.live_faithful import artifact_hash
from src.optimisation.solver import solve
from src.optimisation.types import SolverInput
from src.scoring.rules_loader import get_rule, load_rules, ruleset_sha256
from src.scoring.validator import legal_formations


ROOT = Path(__file__).resolve().parents[2]
VAASTAV_ROOT = ROOT / "data/raw/vaastav/Fantasy-Premier-League/data"
SEALED_EPISODES = ROOT / "data/benchmark-v0/episodes/v1/2025-26"


def _mini_squad() -> list[dict]:
    certain = (0.0, 0.0, 1.0)
    doubtful = (0.4, 0.1, 0.5)
    return [
        {
            "player_id": "g1",
            "position": "GKP",
            "club_id": "1",
            "now_cost": 4.5,
            "expected_points": 4.0,
            "start_probability": 0.9,
            "appearance_distribution": {
                "zero": certain[0],
                "under_60": certain[1],
                "60_plus": certain[2],
                "source": "test",
            },
        },
        {
            "player_id": "g2",
            "position": "GKP",
            "club_id": "1",
            "now_cost": 4.0,
            "expected_points": 3.0,
            "start_probability": 0.1,
            "appearance_distribution": {
                "zero": doubtful[0],
                "under_60": doubtful[1],
                "60_plus": doubtful[2],
                "source": "test",
            },
        },
        *[
            {
                "player_id": f"d{i}",
                "position": "DEF",
                "club_id": "1",
                "now_cost": 4.5,
                "expected_points": float(5 - i * 0.2),
                "start_probability": 0.8,
                "appearance_distribution": {
                    "zero": 0.1,
                    "under_60": 0.1,
                    "60_plus": 0.8,
                    "source": "test",
                },
            }
            for i in range(1, 6)
        ],
        *[
            {
                "player_id": f"m{i}",
                "position": "MID",
                "club_id": "1",
                "now_cost": 5.5,
                "expected_points": float(6 - i * 0.2),
                "start_probability": 0.8,
                "appearance_distribution": {
                    "zero": 0.1,
                    "under_60": 0.1,
                    "60_plus": 0.8,
                    "source": "test",
                },
            }
            for i in range(1, 6)
        ],
        *[
            {
                "player_id": f"f{i}",
                "position": "FWD",
                "club_id": "1",
                "now_cost": 5.0,
                "expected_points": float(5 - i * 0.2),
                "start_probability": 0.8,
                "appearance_distribution": {
                    "zero": 0.1,
                    "under_60": 0.1,
                    "60_plus": 0.8,
                    "source": "test",
                },
            }
            for i in range(1, 4)
        ],
    ]


def _uncertain_squad() -> list[dict]:
    """Squad with risky high-ceiling players alongside reliable lower-ceiling ones.

    The first DEF and MID have high expected_points but very low
    start_probability, so that appearance-weighted ranking (start_probability ×
    expected_points) selects them last rather than first.
    """
    certain = (0.0, 0.0, 1.0)
    return [
        {
            "player_id": "g1",
            "position": "GKP",
            "club_id": "1",
            "now_cost": 4.5,
            "expected_points": 4.0,
            "start_probability": 0.9,
            "appearance_distribution": {
                "zero": certain[0],
                "under_60": certain[1],
                "60_plus": certain[2],
                "source": "test",
            },
        },
        {
            "player_id": "g2",
            "position": "GKP",
            "club_id": "1",
            "now_cost": 4.0,
            "expected_points": 3.0,
            "start_probability": 0.1,
            "appearance_distribution": {
                "zero": 0.9,
                "under_60": 0.05,
                "60_plus": 0.05,
                "source": "test",
            },
        },
        # Risky DEF: high expected_points, very low start_probability.
        {
            "player_id": "d_risky",
            "position": "DEF",
            "club_id": "1",
            "now_cost": 5.0,
            "expected_points": 8.0,
            "start_probability": 0.1,
            "appearance_distribution": {
                "zero": 0.9,
                "under_60": 0.05,
                "60_plus": 0.05,
                "source": "test",
            },
        },
        *[
            {
                "player_id": f"d{i}",
                "position": "DEF",
                "club_id": "1",
                "now_cost": 4.5,
                "expected_points": float(4 - i * 0.1),
                "start_probability": 0.9,
                "appearance_distribution": {
                    "zero": 0.05,
                    "under_60": 0.05,
                    "60_plus": 0.9,
                    "source": "test",
                },
            }
            for i in range(1, 5)
        ],
        # Risky MID: high expected_points, very low start_probability.
        {
            "player_id": "m_risky",
            "position": "MID",
            "club_id": "1",
            "now_cost": 6.0,
            "expected_points": 9.0,
            "start_probability": 0.1,
            "appearance_distribution": {
                "zero": 0.9,
                "under_60": 0.05,
                "60_plus": 0.05,
                "source": "test",
            },
        },
        *[
            {
                "player_id": f"m{i}",
                "position": "MID",
                "club_id": "1",
                "now_cost": 5.5,
                "expected_points": float(5 - i * 0.1),
                "start_probability": 0.9,
                "appearance_distribution": {
                    "zero": 0.05,
                    "under_60": 0.05,
                    "60_plus": 0.9,
                    "source": "test",
                },
            }
            for i in range(1, 5)
        ],
        *[
            {
                "player_id": f"f{i}",
                "position": "FWD",
                "club_id": "1",
                "now_cost": 5.0,
                "expected_points": float(5 - i * 0.2),
                "start_probability": 0.9,
                "appearance_distribution": {
                    "zero": 0.05,
                    "under_60": 0.05,
                    "60_plus": 0.9,
                    "source": "test",
                },
            }
            for i in range(1, 4)
        ],
    ]


def _calibration() -> dict:
    return json.loads(
        (ROOT / "control/models/appearance-distribution-v1.json").read_text(
            encoding="utf-8"
        )
    )


def test_each_component_changes_only_its_decision_lever() -> None:
    rules = load_rules(ROOT / "control/rules/2025-26.yaml")
    constraints = get_rule(rules, "lineup.formation_constraints")["value"]
    calibration = _calibration()
    squad = _mini_squad()
    formations = legal_formations(rules)
    control = solve(
        SolverInput.from_dict(
            {
                "season": "test",
                "gameweek": 1,
                "ruleset_id": rules["meta"]["ruleset_id"],
                "bank": 0.0,
                "free_transfers": 1,
                "squad_player_ids": [row["player_id"] for row in squad],
                "players": squad,
                "max_transfers": 0,
            }
        ),
        rules=rules,
        ruleset_sha256=ruleset_sha256(ROOT / "control/rules/2025-26.yaml"),
    )
    control_lineup = control["selected"]["lineup"]
    bench_only = choose_ablated_contingency_lineup(
        squad,
        component="bench_order_only",
        formations=formations,
        calibration=calibration,
        constraints=constraints,
        active_chip=None,
    )
    xi_only = choose_ablated_contingency_lineup(
        squad,
        component="xi_formation",
        formations=formations,
        calibration=calibration,
        constraints=constraints,
        active_chip=None,
    )
    captain_only = choose_ablated_contingency_lineup(
        squad,
        component="captain_vice_fallback",
        formations=formations,
        calibration=calibration,
        constraints=constraints,
        active_chip=None,
    )

    assert set(player["player_id"] for player in bench_only["starting_xi"]) == set(
        control_lineup["starting_xi_ids"]
    )
    assert bench_only["captain_id"] == control_lineup["captain_id"]
    assert bench_only["vice_captain_id"] == control_lineup["vice_captain_id"]
    assert sorted(player["player_id"] for player in bench_only["bench"]) == sorted(
        control_lineup["bench_ids"]
    )

    # xi_formation arm: bench GKP must be first slot and bench is not permuted.
    assert xi_only["bench"][0]["position"] == "GKP"
    # With uniform start_probability (0.8) the appearance-weighted ranking
    # produces the same XI and captain as the pure expected-points control.
    assert set(p["player_id"] for p in xi_only["starting_xi"]) == set(
        control_lineup["starting_xi_ids"]
    )
    assert xi_only["captain_id"] == control_lineup["captain_id"]

    assert [player["player_id"] for player in captain_only["bench"]] == list(
        control_lineup["bench_ids"]
    )
    assert set(player["player_id"] for player in captain_only["starting_xi"]) == set(
        control_lineup["starting_xi_ids"]
    )


def test_xi_formation_effect_is_unidentified_without_invented_proxy() -> None:
    """The production objective has no separable probabilistic XI term."""

    rules = load_rules(ROOT / "control/rules/2025-26.yaml")
    constraints = get_rule(rules, "lineup.formation_constraints")["value"]
    calibration = _calibration()
    squad = _uncertain_squad()
    formations = legal_formations(rules)
    control = solve(
        SolverInput.from_dict(
            {
                "season": "test",
                "gameweek": 1,
                "ruleset_id": rules["meta"]["ruleset_id"],
                "bank": 0.0,
                "free_transfers": 1,
                "squad_player_ids": [row["player_id"] for row in squad],
                "players": squad,
                "max_transfers": 0,
            }
        ),
        rules=rules,
        ruleset_sha256=ruleset_sha256(ROOT / "control/rules/2025-26.yaml"),
    )
    xi_diagnostic = choose_ablated_contingency_lineup(
        squad,
        component="xi_formation",
        formations=formations,
        calibration=calibration,
        constraints=constraints,
        active_chip=None,
    )
    control_lineup = control["selected"]["lineup"]
    assert [p["player_id"] for p in xi_diagnostic["starting_xi"]] == list(
        control_lineup["starting_xi_ids"]
    )
    assert [p["player_id"] for p in xi_diagnostic["bench"]] == list(
        control_lineup["bench_ids"]
    )
    assert xi_diagnostic["captain_id"] == control_lineup["captain_id"]
    assert xi_diagnostic["vice_captain_id"] == control_lineup["vice_captain_id"]
    assert xi_diagnostic["contingency"]["component_identified"] is False
    assert COMPONENT_IDENTIFICATION["xi_formation"]["identified"] is False

def test_verify_w10_reference_checks_content_hash() -> None:
    """verify_w10_reference must reject a tampered W10 report."""
    w10 = json.loads(
        (ROOT / "reports/evaluation/squad-contingency-v1.json").read_text(
            encoding="utf-8"
        )
    )
    # Valid report must not raise.
    verify_w10_reference(w10)

    # A tampered report (wrong content_sha256) must raise.
    tampered = deepcopy(w10)
    tampered["content_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="content_sha256"):
        verify_w10_reference(tampered)


@pytest.mark.skipif(not VAASTAV_ROOT.exists(), reason="approved vaastav artifacts absent")
def test_single_locked_component_is_legal_and_hash_stable() -> None:
    calibration = _calibration()
    result = evaluate_locked_component(
        component="bench_order_only",
        vaastav_root=ROOT / "data/raw/vaastav/Fantasy-Premier-League/data",
        calibration=calibration,
        rules_path=ROOT / "control/rules/2025-26.yaml",
        gameweeks=(2,),
    )

    assert result["summary"]["all_plans_valid"] is True
    assert result["component"] == "bench_order_only"
    assert len(result["decision_sha256"]) == 64
    changed = deepcopy(result["rows"])
    changed[0]["challenger"]["wall_ms"] = 999.0
    assert paired_decision_hash(result["rows"]) == paired_decision_hash(changed)


@pytest.mark.skipif(
    not SEALED_EPISODES.exists(), reason="sealed benchmark episodes absent"
)
def test_single_descriptive_component_preserves_sealed_artifacts() -> None:
    reports = ROOT / "reports/benchmarks/2025-26"
    episodes = ROOT / "data/benchmark-v0/episodes/v1/2025-26"
    protected = [
        reports
        / "gw-02/setup/arms/forecast_optimizer/reviewed-engine-input.json",
        reports / "gw-02/forecast_optimizer/validated-plan.json",
        episodes / "gw-02/hidden-outcome.json",
    ]
    before = {path: path.read_bytes() for path in protected}
    calibration = _calibration()

    result = evaluate_descriptive_component(
        component="captain_vice_fallback",
        reports_root=reports,
        episodes_root=episodes,
        calibration=calibration,
        rules_path=ROOT / "control/rules/2025-26.yaml",
        gameweeks=(2,),
    )

    assert result["summary"]["all_plans_valid"] is True
    assert result["scope"] == "descriptive_2025_26_same_state_lineup_fork"
    assert {path: path.read_bytes() for path in protected} == before


def _component_rows_from_w10(rows: list[dict]) -> dict[str, dict]:
    return {
        component: {
            "component": component,
            "identification": deepcopy(COMPONENT_IDENTIFICATION[component]),
            "rows": deepcopy(rows),
        }
        for component in ABLATION_COMPONENTS
    }


def test_same_state_binding_rejects_missing_duplicate_and_mismatch() -> None:
    w10 = json.loads(
        (ROOT / "reports/evaluation/squad-contingency-v1.json").read_text(
            encoding="utf-8"
        )
    )
    locked_rows = w10["locked_2024_25"]["rows"][:2]
    components = _component_rows_from_w10(locked_rows)
    _verify_ablation_w10_bindings(
        component_results=components,
        w10_rows=locked_rows,
        scope="locked_test",
        require_reference_squad=True,
    )

    missing = deepcopy(components)
    missing["bench_order_only"]["rows"].pop()
    with pytest.raises(ValueError, match="incomplete same-state join"):
        _verify_ablation_w10_bindings(
            component_results=missing,
            w10_rows=locked_rows,
            scope="locked_test",
            require_reference_squad=True,
        )

    duplicate = deepcopy(components)
    duplicate["bench_order_only"]["rows"].append(
        deepcopy(duplicate["bench_order_only"]["rows"][0])
    )
    with pytest.raises(ValueError, match="duplicate row"):
        _verify_ablation_w10_bindings(
            component_results=duplicate,
            w10_rows=locked_rows,
            scope="locked_test",
            require_reference_squad=True,
        )

    mismatched = deepcopy(components)
    mismatched["bench_order_only"]["rows"][0]["bindings"][
        "control_plan_sha256"
    ] = "0" * 64
    with pytest.raises(ValueError, match="control_plan_sha256"):
        _verify_ablation_w10_bindings(
            component_results=mismatched,
            w10_rows=locked_rows,
            scope="locked_test",
            require_reference_squad=True,
        )

def test_report_keeps_scopes_separate_and_references_w10() -> None:
    calibration = _calibration()
    w10 = json.loads(
        (ROOT / "reports/evaluation/squad-contingency-v1.json").read_text(
            encoding="utf-8"
        )
    )
    verify_w10_reference(w10)
    summary = {
        "pairs": 1,
        "decision_change_weeks": 1,
        "decision_changes": {
            "transfers": False,
            "starting_xi": True,
            "bench_order": False,
            "captain": False,
            "vice_captain": False,
        },
        "net_points_delta": -1,
        "all_plans_valid": True,
    }
    locked_components = {
        component: {
            "component": component,
            "summary": deepcopy(summary),
            "decision_sha256": "a" * 64,
            "identification": deepcopy(COMPONENT_IDENTIFICATION[component]),
            "rows": deepcopy(w10["locked_2024_25"]["rows"]),
        }
        for component in ABLATION_COMPONENTS
    }
    descriptive_components = {
        component: {
            **deepcopy(result),
            "rows": deepcopy(w10["descriptive_2025_26"]["rows"]),
        }
        for component, result in locked_components.items()
    }
    report = build_ablation_report(
        calibration=calibration,
        w10_report=w10,
        locked_components=locked_components,
        descriptive_components=descriptive_components,
    )

    assert report["policy"]["production_default_changed"] is False
    assert report["reference"]["w10_content_sha256"] == w10["content_sha256"]
    assert report["locked_2024_25"]["probabilistic_v1"]["summary"][
        "net_points_delta"
    ] == -10
    assert report["descriptive_2025_26"]["probabilistic_v1"]["summary"][
        "net_points_delta"
    ] == 22
    assert report["v2_proposal"]["selection_on_2025_26"] is False
    assert report["v2_proposal"]["promotion_gate_season"] == "2026-27"
    assert report["content_sha256"] == artifact_hash(report)
    # Attribution must include an explicit residual reconciling v1 vs marginal sum.
    for scope in ("locked_2024_25", "descriptive_2025_26"):
        attr = report[scope]["attribution"]
        assert "residual_unattributed" in attr
        marginal_sum = sum(
            attr["by_component"][c]["net_points_delta"]
            for c in attr["by_component"]
            if attr["by_component"][c]["identified"]
        )
        assert attr["residual_unattributed"] == (
            attr["probabilistic_v1_net_points_delta"] - marginal_sum
        )


def test_committed_ablation_report_matches_contract() -> None:
    report = json.loads(
        (
            ROOT / "reports/evaluation/squad-contingency-ablation-v1.json"
        ).read_text(encoding="utf-8")
    )
    w10 = json.loads(
        (ROOT / "reports/evaluation/squad-contingency-v1.json").read_text(
            encoding="utf-8"
        )
    )

    assert report["content_sha256"] == artifact_hash(report)
    assert report["reference"]["w10_content_sha256"] == w10["content_sha256"]
    assert set(report["policy"]["ablation_components"]) == set(ABLATION_COMPONENTS)
    assert report["v2_proposal"]["promotion_gate_season"] == "2026-27"
    for scope in ("locked_2024_25", "descriptive_2025_26"):
        for component in ABLATION_COMPONENTS:
            entry = report[scope]["components"][component]
            assert len(entry["decision_sha256"]) == 64
            assert entry["summary"]["all_plans_valid"] is True
        attr = report[scope]["attribution"]
        assert "residual_unattributed" in attr
        assert attr["probabilistic_v1_net_points_delta"] - attr[
            "residual_unattributed"
        ] == attr["marginal_component_sum"]
        assert attr["by_component"]["xi_formation"]["identified"] is False
    locked_attr = report["locked_2024_25"]["attribution"]
    assert locked_attr["probabilistic_v1_net_points_delta"] == -10
