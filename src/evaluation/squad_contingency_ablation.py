"""Component ablation for the probabilistic_v1 squad-contingency objective."""

from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
from itertools import permutations
from time import perf_counter
from typing import Any, Iterable, Mapping, Sequence

from src.evaluation.squad_contingency import (
    LOCKED_PARAMETERS,
    _canonical_hash,
    _iso,
    _locked_market,
    _locked_state,
    _read,
    _summary,
    paired_decision_hash,
    paired_decision_row,
)
from src.forecasting.appearance_distribution import (
    AppearanceDistribution,
    calibration_hash,
    distribution_for_player,
)
from src.forecasting.calibrate_live_faithful import (
    build_calibration_cases,
    load_season_rows,
    predictions,
)
from src.forecasting.live_faithful import artifact_hash
from src.optimisation.simple_plan import choose_starting_xi_rows
from src.optimisation.io import fingerprint
from src.optimisation.solver import solve
from src.optimisation.squad_contingency import (
    SquadContingencyError,
    _best_captain_pair,
    _rank_key,
    evaluate_contingency_lineup,
    expected_auto_sub_points,
)
from src.optimisation.types import SolverInput
from src.orchestration.validated_plan import validate_and_freeze_plan
from src.scoring.rules_loader import get_rule, load_rules, ruleset_sha256
from src.scoring.validator import legal_formations
from src.evaluation.outcome_scorer import score_revealed_outcome


ABLATION_COMPONENTS: tuple[str, ...] = (
    "bench_order_only",
    "xi_formation",
    "captain_vice_fallback",
)

COMPONENT_IDENTIFICATION: dict[str, dict[str, Any]] = {
    "bench_order_only": {
        "identified": True,
        "target_term": "expected legal auto-substitution from ordered bench",
    },
    "captain_vice_fallback": {
        "identified": True,
        "target_term": "captain zero-minute vice fallback",
    },
    "xi_formation": {
        "identified": False,
        "target_term": None,
        "reason": (
            "probabilistic_v1 has no independent XI/formation probability term; "
            "its XI changes are interactions with bench and captain optimization"
        ),
    },
}


def _appearance_map(
    players: Sequence[Mapping[str, Any]],
    calibration: Mapping[str, Any],
) -> dict[str, AppearanceDistribution]:
    return {
        str(player["player_id"]): distribution_for_player(player, calibration)
        for player in players
    }


def _captain_extra(
    *,
    captain_id: str,
    vice_id: str,
    starting_xi: Sequence[Mapping[str, Any]],
    appearances: Mapping[str, AppearanceDistribution],
    active_chip: str | None,
) -> float:
    indexed = {str(player["player_id"]): player for player in starting_xi}
    captain = indexed[str(captain_id)]
    vice = indexed[str(vice_id)]
    extra_multiplier = 2 if active_chip and "triple_captain" in active_chip else 1
    captain_points = float(captain["expected_points"])
    fallback = appearances[str(captain_id)].zero * float(vice["expected_points"])
    return float(extra_multiplier * (captain_points + fallback))


def _bench_contingency_value(
    *,
    starting_xi: Sequence[Mapping[str, Any]],
    bench: Sequence[Mapping[str, Any]],
    formation: Mapping[str, int],
    appearances: Mapping[str, AppearanceDistribution],
    constraints: Mapping[str, Any],
    active_chip: str | None,
) -> float:
    if active_chip and "bench_boost" in active_chip:
        return float(sum(float(player["expected_points"]) for player in bench))
    auto_sub = expected_auto_sub_points(
        starting_xi=starting_xi,
        bench=bench,
        appearances=appearances,
        formation=formation,
        constraints=constraints,
    )
    return float(auto_sub["total"])


def _xi_expected_points(starting_xi: Sequence[Mapping[str, Any]]) -> float:
    return float(sum(float(player["expected_points"]) for player in starting_xi))


def _lineup_result(
    *,
    formation: Mapping[str, int],
    starting_xi: Sequence[Mapping[str, Any]],
    bench: Sequence[Mapping[str, Any]],
    captain_id: str,
    vice_captain_id: str,
    evaluation: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "formation": dict(formation),
        "starting_xi": list(starting_xi),
        "bench": list(bench),
        "captain_id": str(captain_id),
        "vice_captain_id": str(vice_captain_id),
        "expected_xi_points": round(float(evaluation["planning_value"]), 2),
        "contingency": dict(evaluation),
    }


def choose_ablated_contingency_lineup(
    squad: Sequence[Mapping[str, Any]],
    *,
    component: str,
    formations: Sequence[Mapping[str, int]],
    calibration: Mapping[str, Any],
    constraints: Mapping[str, Any],
    active_chip: str | None,
) -> dict[str, Any]:
    """Choose a lineup with exactly one probabilistic_v1 component enabled."""

    if component not in ABLATION_COMPONENTS:
        raise ValueError(
            f"component must be one of {ABLATION_COMPONENTS}, got {component!r}"
        )
    ranked = sorted((dict(player) for player in squad), key=_rank_key)
    appearances = _appearance_map(ranked, calibration)
    control = choose_starting_xi_rows(ranked, formations=formations)

    if component == "bench_order_only":
        starting = control["starting_xi"]
        formation = control["formation"]
        captain_id, vice_id = (
            str(control["captain_id"]),
            str(control["vice_captain_id"]),
        )
        bench_gkp = next(
            player for player in control["bench"] if player["position"] == "GKP"
        )
        outfield = [
            player for player in control["bench"] if player["position"] != "GKP"
        ]
        best: tuple[tuple[float, tuple[str, ...]], dict[str, Any]] | None = None
        for ordered_outfield in permutations(outfield):
            ordered_bench = [bench_gkp, *ordered_outfield]
            bench_value = _bench_contingency_value(
                starting_xi=starting,
                bench=ordered_bench,
                formation=formation,
                appearances=appearances,
                constraints=constraints,
                active_chip=active_chip,
            )
            score = (
                _xi_expected_points(starting)
                + _captain_extra(
                    captain_id=captain_id,
                    vice_id=vice_id,
                    starting_xi=starting,
                    appearances=appearances,
                    active_chip=active_chip,
                )
                + bench_value
            )
            identity = tuple(
                str(player["player_id"])
                for player in [*starting, *ordered_bench]
            )
            key = (-score, identity)
            evaluation = evaluate_contingency_lineup(
                starting_xi=starting,
                bench=ordered_bench,
                formation=formation,
                calibration=calibration,
                constraints=constraints,
                active_chip=active_chip,
                appearance_distributions=appearances,
            )
            result = _lineup_result(
                formation=formation,
                starting_xi=starting,
                bench=ordered_bench,
                captain_id=captain_id,
                vice_captain_id=vice_id,
                evaluation=evaluation,
            )
            if best is None or key < best[0]:
                best = (key, result)
        if best is None:
            raise SquadContingencyError("bench-order ablation could not be built")
        return best[1]

    if component == "captain_vice_fallback":
        starting = control["starting_xi"]
        formation = control["formation"]
        bench = control["bench"]
        bench_value = _bench_contingency_value(
            starting_xi=starting,
            bench=bench,
            formation=formation,
            appearances=appearances,
            constraints=constraints,
            active_chip=active_chip,
        )
        xi_points = _xi_expected_points(starting)
        extra_multiplier = 2 if active_chip and "triple_captain" in active_chip else 1
        captain_id, vice_id, captain_extra, _ = _best_captain_pair(
            starting, appearances, extra_multiplier=extra_multiplier
        )
        score = xi_points + bench_value + captain_extra
        evaluation = evaluate_contingency_lineup(
            starting_xi=starting,
            bench=bench,
            formation=formation,
            calibration=calibration,
            constraints=constraints,
            active_chip=active_chip,
            appearance_distributions=appearances,
        )
        return _lineup_result(
            formation=formation,
            starting_xi=starting,
            bench=bench,
            captain_id=captain_id,
            vice_captain_id=vice_id,
            evaluation={
                **evaluation,
                "planning_value": round(score, 6),
            },
        )

    # There is no separable probabilistic XI term in probabilistic_v1. Its XI
    # changes arise only when bench and captain terms are jointly optimized.
    # Preserve the policy-off decision and expose the effect as unidentified;
    # do not invent a heuristic proxy and call it a causal ablation.
    starting = control["starting_xi"]
    bench = control["bench"]
    formation = control["formation"]
    evaluation = evaluate_contingency_lineup(
        starting_xi=starting,
        bench=bench,
        formation=formation,
        calibration=calibration,
        constraints=constraints,
        active_chip=active_chip,
        appearance_distributions=appearances,
    )
    return _lineup_result(
        formation=formation,
        starting_xi=starting,
        bench=bench,
        captain_id=str(control["captain_id"]),
        vice_captain_id=str(control["vice_captain_id"]),
        evaluation={
            **evaluation,
            "planning_value": float(control["expected_xi_points"]),
            "component_identified": False,
            "unidentified_reason": COMPONENT_IDENTIFICATION["xi_formation"]["reason"],
        },
    )

def _solver_rows(players: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in players:
        item = dict(row)
        if isinstance(item.get("expected_points"), list):
            item["expected_points"] = float(item["expected_points"][0])
        if isinstance(item.get("start_probability"), list):
            item["start_probability"] = float(item["start_probability"][0])
        rows.append(item)
    return rows


def _ablation_candidate(
    *,
    lineup: Mapping[str, Any],
    bank: float,
    hit_cost: int = 0,
) -> dict[str, Any]:
    contingency = dict(lineup["contingency"])
    return {
        "strategy": "ablation",
        "transfers": [],
        "hit_cost": int(hit_cost),
        "bank_after": round(float(bank), 1),
        "objective": round(float(contingency["planning_value"]) - float(hit_cost), 4),
        "lineup": {
            "formation": dict(lineup["formation"]),
            "starting_xi_ids": [
                str(player["player_id"]) for player in lineup["starting_xi"]
            ],
            "bench_ids": [str(player["player_id"]) for player in lineup["bench"]],
            "captain_id": str(lineup["captain_id"]),
            "vice_captain_id": str(lineup["vice_captain_id"]),
        },
        "validation": {
            "squad_ok": True,
            "lineup_ok": True,
            "chips_ok": True,
        },
        "contingency": contingency,
        "objective_without_hits": round(float(contingency["planning_value"]), 4),
    }


def _solve_ablation(
    solver_input: SolverInput,
    *,
    component: str,
    rules: Mapping[str, Any],
) -> dict[str, Any]:
    squad_ids = [str(value) for value in solver_input.squad_player_ids]
    indexed = {str(row["player_id"]): row for row in solver_input.players}
    squad_rows = [_solver_rows([indexed[player_id]])[0] for player_id in squad_ids]
    lineup = choose_ablated_contingency_lineup(
        squad_rows,
        component=component,
        formations=legal_formations(dict(rules)),
        calibration=dict(solver_input.appearance_calibration or {}),
        constraints=get_rule(rules, "lineup.formation_constraints")["value"],
        active_chip=solver_input.active_chip,
    )
    return {"selected": _ablation_candidate(lineup=lineup, bank=solver_input.bank)}


def evaluate_locked_component(
    *,
    component: str,
    vaastav_root,
    calibration: Mapping[str, Any],
    rules_path,
    gameweeks: Iterable[int] = tuple(range(1, 39)),
) -> dict[str, Any]:
    """Evaluate one ablation component on locked 2024/25 same-squad lineups."""

    calibration_value = deepcopy(dict(calibration))
    if calibration_value.get("content_sha256") != calibration_hash(calibration_value):
        raise ValueError("appearance calibration hash mismatch")
    prior, prior_lineage = load_season_rows("2023-24", vaastav_root=vaastav_root)
    target, target_lineage = load_season_rows("2024-25", vaastav_root=vaastav_root)
    cases = build_calibration_cases(
        prior_rows=prior,
        target_rows=target,
        prior_season="2023-24",
        target_season="2024-25",
    )
    forecast = predictions(cases, LOCKED_PARAMETERS)
    rules = load_rules(rules_path)
    rules_hash = ruleset_sha256(rules_path)
    rows: list[dict[str, Any]] = []
    for gameweek in gameweeks:
        market, squad_ids, bank, cutoff, outcome_rows = _locked_market(
            prediction_frame=forecast,
            target_rows=target,
            gameweek=int(gameweek),
            season="2024-25",
            rules=rules,
            rules_hash=rules_hash,
        )
        base = {
            "season": "2024-25",
            "gameweek": int(gameweek),
            "ruleset_id": str(rules["meta"]["ruleset_id"]),
            "bank": bank,
            "free_transfers": 1,
            "squad_player_ids": squad_ids,
            "players": [
                {
                    **row,
                    "expected_points": float(row["expected_points"][0]),
                    "start_probability": float(row["start_probability"][0]),
                    "purchase_price": (
                        float(row["now_cost"])
                        if str(row["player_id"]) in set(squad_ids)
                        else None
                    ),
                }
                for row in market
            ],
            "active_chip": None,
            "chips_available": [],
            "max_transfers": 0,
        }
        control_input = SolverInput.from_dict(base)
        challenger_data = deepcopy(base)
        challenger_data["appearance_calibration"] = calibration_value
        challenger_input = SolverInput.from_dict(challenger_data)
        control_start = perf_counter()
        control_output = solve(
            control_input, rules=rules, ruleset_sha256=rules_hash
        )
        control_wall_ms = (perf_counter() - control_start) * 1000.0
        challenger_start = perf_counter()
        challenger_output = _solve_ablation(
            challenger_input,
            component=component,
            rules=rules,
        )
        challenger_wall_ms = (perf_counter() - challenger_start) * 1000.0
        episode_id = f"w10:2024-25:gw{int(gameweek):02d}:locked-lineup"
        control_state = _locked_state(
            season="2024-25",
            gameweek=int(gameweek),
            policy_arm="forecast_optimizer",
            squad_ids=squad_ids,
            bank=bank,
            market=market,
            rules=rules,
            rules_hash=rules_hash,
        )
        challenger_state = _locked_state(
            season="2024-25",
            gameweek=int(gameweek),
            policy_arm="evidence_challenger",
            squad_ids=squad_ids,
            bank=bank,
            market=market,
            rules=rules,
            rules_hash=rules_hash,
        )
        control_plan = validate_and_freeze_plan(
            episode_id=episode_id,
            policy_arm="forecast_optimizer",
            state=control_state,
            candidate=control_output["selected"],
            decision_market=base["players"],
            active_chip=None,
            frozen_at=_iso(cutoff),
            rules=rules,
            ruleset_sha256=rules_hash,
        )
        challenger_plan = validate_and_freeze_plan(
            episode_id=episode_id,
            policy_arm="evidence_challenger",
            state=challenger_state,
            candidate=challenger_output["selected"],
            decision_market=base["players"],
            active_chip=None,
            frozen_at=_iso(cutoff),
            rules=rules,
            ruleset_sha256=rules_hash,
        )
        hidden = {
            "schema_version": "1.0",
            "episode_id": episode_id,
            "season": "2024-25",
            "gameweek": int(gameweek),
            "reveal_after": "proposal_frozen",
            "player_outcomes": [
                {
                    "element": row["player_id"],
                    "fixture": row["fixture"],
                    "position": row["position"],
                    "minutes": row["minutes"],
                    "total_points": row["total_points"],
                }
                for row in outcome_rows
            ],
        }
        revealed_at = _iso(cutoff + timedelta(days=10))
        control_outcome = score_revealed_outcome(
            control_plan,
            hidden,
            revealed_at=revealed_at,
            rules=rules,
            ruleset_sha256=rules_hash,
        )
        challenger_outcome = score_revealed_outcome(
            challenger_plan,
            hidden,
            revealed_at=revealed_at,
            rules=rules,
            ruleset_sha256=rules_hash,
        )
        row = paired_decision_row(
            scope="locked_2024_25_same_squad_lineup",
            gameweek=int(gameweek),
            episode_id=episode_id,
            control_plan=control_plan,
            control_outcome=control_outcome,
            challenger_plan=challenger_plan,
            challenger_outcome=challenger_outcome,
            observed_sha256=fingerprint(base),
            hidden_outcome_sha256=_canonical_hash(hidden),
            ruleset_sha256_value=rules_hash,
            challenger_wall_ms=challenger_wall_ms,
        )
        row["control"]["wall_ms"] = round(control_wall_ms, 6)
        row["reference_squad_sha256"] = fingerprint(
            {"squad_player_ids": squad_ids, "bank": bank}
        )
        row["ablation_component"] = str(component)
        rows.append(row)
    return {
        "scope": "locked_2024_25_same_squad_lineup",
        "component": str(component),
        "identification": deepcopy(COMPONENT_IDENTIFICATION[str(component)]),
        "longitudinal": False,
        "rows": rows,
        "summary": _summary(rows),
        "decision_sha256": paired_decision_hash(rows),
        "source_lineage": [prior_lineage, target_lineage],
    }


def evaluate_descriptive_component(
    *,
    component: str,
    reports_root,
    episodes_root,
    calibration: Mapping[str, Any],
    rules_path,
    gameweeks: Iterable[int] = tuple(range(2, 39)),
) -> dict[str, Any]:
    """Evaluate one ablation component on sealed 2025/26 same-state forks."""

    from src.optimisation.io import fingerprint

    calibration_value = deepcopy(dict(calibration))
    if calibration_value.get("content_sha256") != calibration_hash(calibration_value):
        raise ValueError("appearance calibration hash mismatch")
    rules = load_rules(rules_path)
    rules_hash = ruleset_sha256(rules_path)
    rows: list[dict[str, Any]] = []
    source_bindings: list[dict[str, Any]] = []
    for gameweek in gameweeks:
        report_root = reports_root / f"gw-{int(gameweek):02d}"
        episode_root = episodes_root / f"gw-{int(gameweek):02d}"
        setup = report_root / "setup/arms/forecast_optimizer"
        raw_input = _read(setup / "reviewed-engine-input.json")
        state = _read(setup / "starting-policy-state.json")
        canonical_plan = _read(report_root / "forecast_optimizer/validated-plan.json")
        canonical_outcome = _read(
            report_root / "forecast_optimizer/realised-outcome.json"
        )
        canonical_active_chip = canonical_plan["active_chip"]
        revealed_at = str(canonical_outcome["revealed_at"])
        shared = _read(report_root / "shared-context.json")
        manifest = _read(episode_root / "episode-manifest.json")
        hidden = _read(episode_root / "hidden-outcome.json")
        identity = _read(episode_root / "identity-map.json")

        control_input = deepcopy(raw_input)
        control_input["max_transfers"] = 0
        control_input["allow_hits"] = False
        control_input.pop("squad_contingency_policy", None)
        control_input.pop("appearance_calibration", None)
        control_start = perf_counter()
        control_solver_output = solve(
            SolverInput.from_dict(control_input),
            rules=rules,
            ruleset_sha256=rules_hash,
        )
        control_wall_ms = (perf_counter() - control_start) * 1000.0
        control_plan = validate_and_freeze_plan(
            episode_id=str(manifest["episode_id"]),
            policy_arm=str(state["policy_arm"]),
            state=state,
            candidate=control_solver_output["selected"],
            decision_market=control_input["players"],
            active_chip=canonical_active_chip,
            frozen_at=str(manifest["deadline"]),
            rules=rules,
            ruleset_sha256=rules_hash,
        )
        challenger_input = deepcopy(control_input)
        challenger_input["appearance_calibration"] = calibration_value
        start = perf_counter()
        challenger_output = _solve_ablation(
            SolverInput.from_dict(challenger_input),
            component=component,
            rules=rules,
        )
        wall_ms = (perf_counter() - start) * 1000.0
        challenger_plan = validate_and_freeze_plan(
            episode_id=str(manifest["episode_id"]),
            policy_arm=str(state["policy_arm"]),
            state=state,
            candidate=challenger_output["selected"],
            decision_market=challenger_input["players"],
            active_chip=canonical_active_chip,
            frozen_at=str(manifest["deadline"]),
            rules=rules,
            ruleset_sha256=rules_hash,
        )
        identity_index = {
            str(row["fpl_player_id"]): str(row["canonical_id"])
            for row in identity["players"]
        }
        control_outcome = score_revealed_outcome(
            control_plan,
            hidden,
            revealed_at=revealed_at,
            rules=rules,
            ruleset_sha256=rules_hash,
            player_identity_map=identity_index,
            identity_map_sha256=str(shared["identity_map_sha256"]),
        )
        challenger_outcome = score_revealed_outcome(
            challenger_plan,
            hidden,
            revealed_at=revealed_at,
            rules=rules,
            ruleset_sha256=rules_hash,
            player_identity_map=identity_index,
            identity_map_sha256=str(shared["identity_map_sha256"]),
        )
        rows.append(
            paired_decision_row(
                scope="descriptive_2025_26_same_state_lineup_fork",
                gameweek=int(gameweek),
                episode_id=str(manifest["episode_id"]),
                control_plan=control_plan,
                control_outcome=control_outcome,
                challenger_plan=challenger_plan,
                challenger_outcome=challenger_outcome,
                observed_sha256=str(shared["observed_sha256"]),
                hidden_outcome_sha256=str(shared["hidden_outcome_sha256"]),
                ruleset_sha256_value=rules_hash,
                challenger_wall_ms=wall_ms,
            )
        )
        rows[-1]["control"]["wall_ms"] = round(control_wall_ms, 6)
        rows[-1]["transfer_search"] = "held_constant_at_zero_for_both_arms"
        rows[-1]["ablation_component"] = str(component)
        source_bindings.append(
            {
                "gameweek": int(gameweek),
                "reviewed_engine_input_sha256": fingerprint(raw_input),
                "starting_policy_state_sha256": str(state["content_sha256"]),
                "episode_manifest_sha256": fingerprint(manifest),
                "hidden_outcome_sha256": str(shared["hidden_outcome_sha256"]),
            }
        )
    return {
        "scope": "descriptive_2025_26_same_state_lineup_fork",
        "component": str(component),
        "identification": deepcopy(COMPONENT_IDENTIFICATION[str(component)]),
        "longitudinal": False,
        "rows": rows,
        "summary": _summary(rows),
        "decision_sha256": paired_decision_hash(rows),
        "source_bindings": source_bindings,
    }


def _decision_signature(decisions: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "starting_xi_ids": sorted(decisions["starting_xi_ids"]),
        "bench_ids": list(decisions["bench_ids"]),
        "captain_id": str(decisions["captain_id"]),
        "vice_captain_id": str(decisions["vice_captain_id"]),
    }


def _matches_v1(ablation_row: Mapping[str, Any], v1_row: Mapping[str, Any]) -> bool:
    return _decision_signature(ablation_row["decisions"]["challenger"]) == (
        _decision_signature(v1_row["decisions"]["challenger"])
    )


def _attribution_for_scope(
    *,
    component_results: Mapping[str, Mapping[str, Any]],
    v1_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    v1_by_gw = {int(row["gameweek"]): row for row in v1_rows}
    by_component: dict[str, Any] = {}
    reconciliation: dict[str, Any] = {}
    for component, result in component_results.items():
        summary = result["summary"]
        matching_weeks = 0
        loss_weeks: list[dict[str, Any]] = []
        for row in result["rows"]:
            gameweek = int(row["gameweek"])
            v1_row = v1_by_gw[gameweek]
            if _matches_v1(row, v1_row):
                matching_weeks += 1
            delta = int(row["delta_challenger_minus_control"]["net_points"])
            if delta != 0:
                loss_weeks.append(
                    {
                        "gameweek": gameweek,
                        "net_points_delta": delta,
                        "matches_probabilistic_v1": _matches_v1(row, v1_row),
                        "decision_changes": dict(row["decision_changes"]),
                    }
                )
        identification = deepcopy(
            dict(result.get("identification", COMPONENT_IDENTIFICATION[component]))
        )
        by_component[component] = {
            "identified": bool(identification["identified"]),
            "identification": identification,
            "net_points_delta": int(summary["net_points_delta"]),
            "decision_change_weeks": int(summary["decision_change_weeks"]),
            "decision_changes": dict(summary["decision_changes"]),
            "all_plans_valid": bool(summary["all_plans_valid"]),
            "decision_sha256": str(result["decision_sha256"]),
        }
        reconciliation[component] = {
            "weeks_matching_probabilistic_v1": matching_weeks,
            "non_zero_weeks": loss_weeks,
        }
    v1_delta = sum(
        int(row["delta_challenger_minus_control"]["net_points"]) for row in v1_rows
    )
    loss_weeks = [
        {
            "gameweek": int(row["gameweek"]),
            "net_points_delta": int(row["delta_challenger_minus_control"]["net_points"]),
            "decision_changes": dict(row["decision_changes"]),
        }
        for row in v1_rows
        if int(row["delta_challenger_minus_control"]["net_points"]) != 0
    ]
    marginal_sum = sum(
        by_component[c]["net_points_delta"]
        for c in by_component
        if by_component[c]["identified"]
    )
    return {
        "probabilistic_v1_net_points_delta": int(v1_delta),
        "marginal_component_sum": marginal_sum,
        "residual_unattributed": int(v1_delta) - marginal_sum,
        "residual_interpretation": (
            "joint interaction plus any structurally unidentified component; "
            "not a causal component estimate"
        ),
        "by_component": by_component,
        "probabilistic_v1_non_zero_weeks": loss_weeks,
        "reconciliation": reconciliation,
    }


def build_ablation_report(
    *,
    calibration: Mapping[str, Any],
    w10_report: Mapping[str, Any],
    locked_components: Mapping[str, Mapping[str, Any]],
    descriptive_components: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Build the sealed ablation packet without changing production policy."""

    locked_v1 = w10_report["locked_2024_25"]
    descriptive_v1 = w10_report["descriptive_2025_26"]
    _verify_ablation_w10_bindings(
        component_results=locked_components,
        w10_rows=locked_v1["rows"],
        scope="locked_2024_25",
        require_reference_squad=True,
    )
    _verify_ablation_w10_bindings(
        component_results=descriptive_components,
        w10_rows=descriptive_v1["rows"],
        scope="descriptive_2025_26",
        require_reference_squad=False,
    )
    locked_attribution = _attribution_for_scope(
        component_results=locked_components,
        v1_rows=locked_v1["rows"],
    )
    descriptive_attribution = _attribution_for_scope(
        component_results=descriptive_components,
        v1_rows=descriptive_v1["rows"],
    )
    report: dict[str, Any] = {
        "schema_version": "1.0",
        "report_id": "squad-contingency-ablation-v1",
        "policy": {
            "reference_challenger": "probabilistic_v1",
            "production_default": "none",
            "production_default_changed": False,
            "ablation_components": list(ABLATION_COMPONENTS),
        },
        "reference": {
            "w10_report_id": str(w10_report["report_id"]),
            "w10_content_sha256": str(w10_report["content_sha256"]),
            "appearance_calibration_sha256": str(
                calibration["content_sha256"]
            ),
            "probabilistic_v1_locked_decision_sha256": str(
                locked_v1["decision_sha256"]
            ),
            "probabilistic_v1_descriptive_decision_sha256": str(
                descriptive_v1["decision_sha256"]
            ),
        },
        "locked_2024_25": {
            "probabilistic_v1": {
                "summary": deepcopy(dict(locked_v1["summary"])),
                "decision_sha256": str(locked_v1["decision_sha256"]),
            },
            "components": deepcopy(
                {
                    component: {
                        "component": component,
                        "identification": deepcopy(
                            dict(result.get("identification", COMPONENT_IDENTIFICATION[component]))
                        ),
                        "summary": dict(result["summary"]),
                        "decision_sha256": str(result["decision_sha256"]),
                    }
                    for component, result in locked_components.items()
                }
            ),
            "attribution": locked_attribution,
        },
        "descriptive_2025_26": {
            "probabilistic_v1": {
                "summary": deepcopy(dict(descriptive_v1["summary"])),
                "decision_sha256": str(descriptive_v1["decision_sha256"]),
            },
            "components": deepcopy(
                {
                    component: {
                        "component": component,
                        "identification": deepcopy(
                            dict(result.get("identification", COMPONENT_IDENTIFICATION[component]))
                        ),
                        "summary": dict(result["summary"]),
                        "decision_sha256": str(result["decision_sha256"]),
                    }
                    for component, result in descriptive_components.items()
                }
            ),
            "attribution": descriptive_attribution,
        },
        "v2_proposal": {
            "status": "preregistered_not_fitted",
            "selection_on_2025_26": False,
            "train_seasons": ["2022-23", "2023-24"],
            "historical_component_selection_eligible": False,
            "historical_scopes": {
                "2024-25": "exploratory_after_outcome_access",
                "2025-26": "exploratory_after_outcome_access",
            },
            "promotion_gate_season": "2026-27",
            "prospective_protocol": {
                "freeze_before_first_deadline": True,
                "midseason_component_selection_allowed": False,
                "production_approval_required": True,
            },
            "rationale": (
                "Component ablation findings inform which v2 terms to retain, "
                "but no parameter or policy weight may be fit on 2024/25 or "
                "2025/26 — both are exploratory after this ablation observed "
                "their outcomes. Appearance calibration continues to train "
                "only on 2022/23 and 2023/24. The sole promotion gate is the "
                "genuinely prospective 2026/27 season (not yet observed at "
                "analysis time), which was not used in any design decision "
                "for this ablation."
            ),
        },
        "limitations": [
            (
                "Bench-order and captain/vice arms enable one separable planning "
                "term while holding other decisions at policy-off control. The "
                "XI/formation effect is explicitly unidentified because "
                "probabilistic_v1 has no independent XI probability term."
            ),
            (
                "Marginal component deltas do not sum to the joint "
                "probabilistic_v1 delta because v1 optimises all components "
                "together."
            ),
            (
                "Descriptive 2025/26 forks cannot override the locked 2024/25 "
                "promotion gate or be used to select a v2 policy."
            ),
        ],
    }
    report["content_sha256"] = artifact_hash(report)
    return report


def run_full_ablation(
    *,
    repo_root,
    calibration: Mapping[str, Any],
    w10_report: Mapping[str, Any],
    artifact_root=None,
    locked_gameweeks: Iterable[int] = tuple(range(1, 39)),
    descriptive_gameweeks: Iterable[int] = tuple(range(2, 39)),
) -> dict[str, Any]:
    """Run all component arms and assemble the sealed ablation report."""

    artifacts = repo_root if artifact_root is None else artifact_root
    vaastav_root = artifacts / "data/raw/vaastav/Fantasy-Premier-League/data"
    rules_path = repo_root / "control/rules/2025-26.yaml"
    reports_root = artifacts / "reports/benchmarks/2025-26"
    episodes_root = artifacts / "data/benchmark-v0/episodes/v1/2025-26"
    locked_components: dict[str, dict[str, Any]] = {}
    descriptive_components: dict[str, dict[str, Any]] = {}
    for component in ABLATION_COMPONENTS:
        locked_components[component] = evaluate_locked_component(
            component=component,
            vaastav_root=vaastav_root,
            calibration=calibration,
            rules_path=rules_path,
            gameweeks=locked_gameweeks,
        )
        descriptive_components[component] = evaluate_descriptive_component(
            component=component,
            reports_root=reports_root,
            episodes_root=episodes_root,
            calibration=calibration,
            rules_path=rules_path,
            gameweeks=descriptive_gameweeks,
        )
    return build_ablation_report(
        calibration=calibration,
        w10_report=w10_report,
        locked_components=locked_components,
        descriptive_components=descriptive_components,
    )


def _verify_ablation_w10_bindings(
    *,
    component_results: Mapping[str, Mapping[str, Any]],
    w10_rows: Sequence[Mapping[str, Any]],
    scope: str,
    require_reference_squad: bool,
) -> None:
    """Require a complete one-to-one same-state join to the sealed W10 rows."""

    binding_keys = (
        "observed_sha256",
        "hidden_outcome_sha256",
        "ruleset_sha256",
        "control_plan_sha256",
        "control_outcome_sha256",
    )
    w10_by_gw: dict[int, Mapping[str, Any]] = {}
    for row in w10_rows:
        gameweek = int(row["gameweek"])
        if gameweek in w10_by_gw:
            raise ValueError(f"{scope}: duplicate W10 row for gw{gameweek}")
        w10_by_gw[gameweek] = row
    expected_gameweeks = set(w10_by_gw)

    for component in ABLATION_COMPONENTS:
        if component not in component_results:
            raise ValueError(f"{scope}: missing ablation component {component!r}")
        result = component_results[component]
        rows_by_gw: dict[int, Mapping[str, Any]] = {}
        for row in result.get("rows", []):
            gameweek = int(row["gameweek"])
            if gameweek in rows_by_gw:
                raise ValueError(
                    f"{scope} ablation {component!r}: duplicate row for gw{gameweek}"
                )
            rows_by_gw[gameweek] = row
        actual_gameweeks = set(rows_by_gw)
        if actual_gameweeks != expected_gameweeks:
            missing = sorted(expected_gameweeks - actual_gameweeks)
            extra = sorted(actual_gameweeks - expected_gameweeks)
            raise ValueError(
                f"{scope} ablation {component!r}: incomplete same-state join; "
                f"missing={missing}, extra={extra}"
            )
        for gameweek, row in rows_by_gw.items():
            w10_row = w10_by_gw[gameweek]
            if str(row.get("episode_id")) != str(w10_row.get("episode_id")):
                raise ValueError(
                    f"{scope} ablation {component!r} gw{gameweek}: "
                    "episode_id does not match W10 row"
                )
            if require_reference_squad and row.get(
                "reference_squad_sha256"
            ) != w10_row.get("reference_squad_sha256"):
                raise ValueError(
                    f"{scope} ablation {component!r} gw{gameweek}: "
                    "reference_squad_sha256 does not match W10 row"
                )
            ablation_bindings = row.get("bindings", {})
            w10_bindings = w10_row.get("bindings", {})
            for key in binding_keys:
                if ablation_bindings.get(key) != w10_bindings.get(key):
                    raise ValueError(
                        f"{scope} ablation {component!r} gw{gameweek}: "
                        f"bindings.{key} does not match W10 row"
                    )

def verify_w10_reference(w10_report: Mapping[str, Any]) -> None:
    """Ensure the sealed W10 report is intact and content hash is valid."""

    if w10_report.get("report_id") != "squad-contingency-v1-paired-evaluation":
        raise ValueError("unexpected W10 report identifier")
    if artifact_hash(w10_report) != w10_report.get("content_sha256", ""):
        raise ValueError(
            "W10 content_sha256 mismatch — report has been modified"
        )
    if int(w10_report["locked_2024_25"]["summary"]["net_points_delta"]) != -10:
        raise ValueError("W10 locked net_points_delta is no longer -10")
    if int(w10_report["descriptive_2025_26"]["summary"]["net_points_delta"]) != 22:
        raise ValueError("W10 descriptive net_points_delta is no longer 22")
