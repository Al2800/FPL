"""Adapt validated manual manager state plus live forecasts into SolverInput / GDR.

Manual entry remains the mechanism (ADR-0005). This module never opens a
browser, authenticates to FPL, or writes account state.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from src.optimisation.io import fingerprint
from src.optimisation.solver import solve
from src.optimisation.types import SolverInput
from src.orchestration.validated_plan import validate_and_freeze_plan
from src.reporting.baseline_comparison import baseline_comparison_from_solver
from src.reporting.decision_record import build_decision_record
from src.scoring.rules_loader import load_rules, ruleset_sha256
from src.scoring.validator import selling_price


class LiveSolverAdapterError(ValueError):
    """Raised when manager state and forecasts cannot form a legal solver input."""


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise LiveSolverAdapterError(f"{label} must be a JSON object")
    return dict(value)


def _index_players(rows: Any, *, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list) or not rows:
        raise LiveSolverAdapterError(f"{label} must be a non-empty array")
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise LiveSolverAdapterError(f"{label} entries must be objects")
        player_id = str(row.get("player_id") or "")
        if not player_id:
            raise LiveSolverAdapterError(f"{label} entry is missing player_id")
        if player_id in indexed:
            raise LiveSolverAdapterError(f"{label} contains duplicate player_id {player_id}")
        indexed[player_id] = dict(row)
    return indexed


def build_live_solver_input(
    *,
    manager_state: Mapping[str, Any],
    forecast: Mapping[str, Any],
    active_chip: str | None = None,
    max_transfers: int = 3,
    allow_hits: bool = True,
) -> SolverInput:
    """Combine normalised manager state with a forecast market into SolverInput."""

    state = _require_mapping(manager_state, "manager_state")
    market_forecast = _require_mapping(forecast, "forecast")
    for field in ("season", "gameweek", "ruleset_id", "bank", "free_transfers"):
        if field not in state:
            raise LiveSolverAdapterError(f"manager_state is missing {field}")
    if str(market_forecast.get("season")) != str(state["season"]):
        raise LiveSolverAdapterError("forecast season does not match manager_state")
    if int(market_forecast.get("gameweek")) != int(state["gameweek"]):
        raise LiveSolverAdapterError("forecast gameweek does not match manager_state")
    if not 0 <= int(max_transfers) <= 3:
        raise LiveSolverAdapterError("max_transfers must be between 0 and 3")

    owned = _index_players(state.get("squad"), label="manager_state.squad")
    forecast_players = _index_players(market_forecast.get("players"), label="forecast.players")
    missing_owned = sorted(set(owned) - set(forecast_players))
    if missing_owned:
        raise LiveSolverAdapterError(
            f"forecast market is missing owned player(s): {missing_owned}"
        )

    players: list[dict[str, Any]] = []
    for player_id, forecast_row in sorted(forecast_players.items(), key=lambda item: item[0]):
        try:
            position = str(forecast_row["position"])
            club_id = str(forecast_row["club_id"])
            now_cost = round(float(forecast_row["now_cost"]), 1)
            expected_points = round(float(forecast_row["expected_points"]), 2)
        except (KeyError, TypeError, ValueError) as exc:
            raise LiveSolverAdapterError(
                f"forecast player {player_id} is missing required market fields"
            ) from exc
        owner = owned.get(player_id)
        purchase_price: float | None = None
        owner_selling: float | None = None
        if owner is not None:
            if str(owner.get("position")) != position:
                raise LiveSolverAdapterError(
                    f"owned player {player_id} position disagrees with forecast"
                )
            if str(owner.get("club_id")) != club_id:
                raise LiveSolverAdapterError(
                    f"owned player {player_id} club disagrees with forecast"
                )
            current = round(float(owner.get("current_price", owner.get("now_cost"))), 1)
            if current != now_cost:
                raise LiveSolverAdapterError(
                    f"owned player {player_id} current price disagrees with forecast"
                )
            purchase_price = round(float(owner["purchase_price"]), 1)
            owner_selling = round(float(owner["selling_price"]), 1)
            now_cost = current
        row: dict[str, Any] = {
            "player_id": player_id,
            "web_name": str(
                forecast_row.get("web_name")
                or (owner.get("web_name") if owner else None)
                or player_id
            ),
            "position": position,
            "club_id": club_id,
            "now_cost": now_cost,
            "expected_points": expected_points,
            "status": str(forecast_row.get("status") or "a"),
            "purchase_price": purchase_price,
        }
        if owner_selling is not None:
            row["selling_price"] = owner_selling
        if market_forecast.get("content_sha256"):
            row["forecast_view_sha256"] = str(market_forecast["content_sha256"])
        if market_forecast.get("model_version"):
            row["forecast_model_version"] = str(market_forecast["model_version"])
        players.append(row)

    chips = [str(value) for value in state.get("chips_available") or []]
    return SolverInput(
        season=str(state["season"]),
        gameweek=int(state["gameweek"]),
        ruleset_id=str(state["ruleset_id"]),
        bank=round(float(state["bank"]), 1),
        free_transfers=int(state["free_transfers"]),
        squad_player_ids=[str(row["player_id"]) for row in state["squad"]],
        players=players,
        active_chip=active_chip if active_chip is not None else state.get("active_chip"),
        chips_available=chips,
        max_transfers=int(max_transfers),
        allow_hits=bool(allow_hits),
    )


def assert_owned_selling_prices(
    solver_input: SolverInput,
    *,
    rules: Mapping[str, Any],
) -> None:
    """Fail closed if owned selling prices disagree with the active ruleset."""

    owned = set(solver_input.squad_player_ids)
    for player in solver_input.players:
        player_id = str(player["player_id"])
        if player_id not in owned:
            continue
        purchase = float(player["purchase_price"])
        current = float(player["now_cost"])
        expected = selling_price(purchase, current, dict(rules))
        supplied = player.get("selling_price")
        if supplied is None:
            raise LiveSolverAdapterError(
                f"owned player {player_id} is missing selling_price"
            )
        if round(float(supplied), 1) != expected:
            raise LiveSolverAdapterError(
                f"owned player {player_id} selling_price expected {expected:.1f}, "
                f"got {float(supplied):.1f}"
            )


def build_live_decision_record(
    *,
    manager_state: Mapping[str, Any],
    solver_input: SolverInput,
    solver_output: Mapping[str, Any],
    rules: Mapping[str, Any],
    ruleset_sha256_value: str,
    validate: bool = False,
) -> dict[str, Any]:
    """Assemble a Gameweek Decision Record from adapter + optimiser outputs."""

    state = _require_mapping(manager_state, "manager_state")
    selected = solver_output.get("selected")
    if not isinstance(selected, Mapping):
        raise LiveSolverAdapterError("solver output has no selected plan")
    baseline = baseline_comparison_from_solver(dict(solver_output))
    market = {
        str(player["player_id"]): {
            "player_id": str(player["player_id"]),
            "position": player["position"],
            "club_id": str(player["club_id"]),
            "now_cost": player["now_cost"],
        }
        for player in solver_input.players
    }
    predecessor = {
        "policy_arm": "live_forecast_optimizer",
        "season": solver_input.season,
        "gameweek": solver_input.gameweek,
        "ruleset_id": str(rules["meta"]["ruleset_id"]),
        "ruleset_sha256": ruleset_sha256_value,
        "squad": [
            {
                "player_id": str(row["player_id"]),
                "position": str(row["position"]),
                "club_id": str(row["club_id"]),
                "purchase_price": float(row["purchase_price"]),
                "current_price": float(row["current_price"]),
                "selling_price": float(row["selling_price"]),
            }
            for row in state["squad"]
        ],
        "bank": float(state["bank"]),
        "free_transfers": int(state["free_transfers"]),
        "chips_available": list(state.get("chips_available") or []),
    }
    predecessor["content_sha256"] = fingerprint(predecessor)
    cutoff = str(state.get("cutoff") or state.get("decision_cutoff") or state["available_at"])
    deadline = str(state["deadline"])
    validated_plan = validate_and_freeze_plan(
        episode_id=(
            f"live:{state.get('manager_id', 'manager')}:gw{solver_input.gameweek:02d}"
        ),
        policy_arm="live_forecast_optimizer",
        state=predecessor,
        candidate=dict(selected),
        decision_market=market,
        active_chip=solver_input.active_chip,
        frozen_at=cutoff,
        rules=dict(rules),
        ruleset_sha256=ruleset_sha256_value,
    )
    plans_summary = []
    for name, plan in (solver_output.get("plans") or {}).items():
        if not plan:
            continue
        lineup = plan.get("lineup") if isinstance(plan.get("lineup"), Mapping) else {}
        starting = lineup.get("starting_xi_ids") or lineup.get("starting_xi") or []
        starting_ids = [
            str(player["player_id"] if isinstance(player, Mapping) else player)
            for player in starting
        ]
        plans_summary.append(
            {
                "strategy": plan.get("strategy", name),
                "objective": plan["objective"],
                "hit_cost": plan.get("hit_cost", 0),
                "transfers": plan.get("transfers") or [],
                "starting_xi": starting_ids,
                "captain_id": (
                    None
                    if lineup.get("captain_id") is None
                    else str(lineup.get("captain_id"))
                ),
            }
        )
    names = {
        str(player["player_id"]): str(player.get("web_name") or player["player_id"])
        for player in solver_input.players
    }
    lineup = selected.get("lineup") or {}
    return build_decision_record(
        {
            "record_id": (
                f"gdr_live_{state.get('manager_id', 'manager')}_gw{solver_input.gameweek}"
            ),
            "gameweek": solver_input.gameweek,
            "season": solver_input.season,
            "decision_cutoff": cutoff,
            "deadline": deadline,
            "observed_at": str(state.get("observed_at") or state["available_at"]),
            "available_at": str(state["available_at"]),
            "ruleset_id": solver_input.ruleset_id,
            "manager_state": {
                "manager_id": state.get("manager_id"),
                "manager_state_id": state.get("manager_state_id"),
                "bank": float(state["bank"]),
                "free_transfers": int(state["free_transfers"]),
                "chips_available": list(state.get("chips_available") or []),
                "squad_player_ids": list(solver_input.squad_player_ids),
                "content_sha256": state.get("content_sha256"),
            },
            "projections_summary": {
                "n_players": len(solver_input.players),
                "model_versions": ["live_forecast"],
                "source": "live_forecast_adapter",
            },
            "candidate_plans": plans_summary,
            "validated_plan": validated_plan,
            "recommendation": {
                "strategy": selected.get("strategy", "highest_ev"),
                "objective": selected.get("objective"),
                "captain_name": names.get(str(lineup.get("captain_id")), str(lineup.get("captain_id"))),
                "vice_captain_name": names.get(
                    str(lineup.get("vice_captain_id")),
                    str(lineup.get("vice_captain_id")),
                ),
                "validated_plan_sha256": validated_plan["content_sha256"],
            },
            "baseline_comparison": baseline,
            "alternatives": {
                "conservative": (
                    {
                        "strategy": "no_transfer",
                        "objective": ((solver_output.get("plans") or {}).get("no_transfer") or {}).get(
                            "objective"
                        ),
                    }
                    if (solver_output.get("plans") or {}).get("no_transfer")
                    else None
                ),
                "aggressive": (
                    {
                        "strategy": "hit",
                        "objective": ((solver_output.get("plans") or {}).get("hit") or {}).get(
                            "objective"
                        ),
                    }
                    if (solver_output.get("plans") or {}).get("hit")
                    else None
                ),
            },
            "evidence": {
                "supporting_claim_ids": [],
                "conflicting_claim_ids": [],
                "conflict_ids": [],
                "proposed_adjustment_ids": [],
            },
            "validation": {
                "squad": {"ok": bool((selected.get("validation") or {}).get("squad_ok"))},
                "lineup": {"ok": bool((selected.get("validation") or {}).get("lineup_ok"))},
                "chips_ok": bool((selected.get("validation") or {}).get("chips_ok", True)),
            },
            "approval": {"status": "pending"},
            "execution": {"mode": "manual", "notes": "Advisory live adapter — no account writes"},
            "outcome": None,
            "retrospective": None,
            "provenance": {
                "source_ids": ["manual-manager-state", "live-forecast", "wp07-optimiser"],
                "transformation_version": "live-solver-adapter-0.1",
                "ruleset_id": solver_input.ruleset_id,
            },
            "pipeline": {
                "components": [
                    "orchestration.live_solver_adapter",
                    "optimisation.solve",
                    "reporting.decision_record",
                ],
                "orchestration": "plain_python",
                "solver_version": solver_output.get("solver_version"),
                "input_fingerprint": solver_output.get("input_fingerprint"),
                "output_fingerprint": solver_output.get("output_fingerprint"),
            },
        },
        validate=validate,
    )


def adapt_solve_and_record(
    *,
    manager_state: Mapping[str, Any],
    forecast: Mapping[str, Any],
    rules_path: Any,
    active_chip: str | None = None,
    max_transfers: int = 3,
    validate_record: bool = False,
) -> dict[str, Any]:
    """Build SolverInput, solve, and return solver artefacts plus a GDR."""

    rules = load_rules(rules_path)
    rules_hash = ruleset_sha256(rules_path)
    solver_input = build_live_solver_input(
        manager_state=manager_state,
        forecast=forecast,
        active_chip=active_chip,
        max_transfers=max_transfers,
    )
    assert_owned_selling_prices(solver_input, rules=rules)
    solver_output = solve(solver_input, rules=rules, ruleset_sha256=rules_hash)
    record = build_live_decision_record(
        manager_state=manager_state,
        solver_input=solver_input,
        solver_output=solver_output,
        rules=rules,
        ruleset_sha256_value=rules_hash,
        validate=validate_record,
    )
    return {
        "solver_input": solver_input.as_dict(),
        "solver_output": deepcopy(dict(solver_output)),
        "decision_record": record,
    }
