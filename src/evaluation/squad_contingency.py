"""Paired evaluation of the opt-in squad-contingency objective."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd

from src.evaluation.outcome_scorer import score_revealed_outcome
from src.forecasting.appearance_distribution import calibration_hash
from src.forecasting.calibrate_live_faithful import (
    ForecastParameters,
    build_calibration_cases,
    load_season_rows,
    predictions,
)
from src.forecasting.live_faithful import artifact_hash
from src.optimisation.initial_squad import optimise_initial_squad
from src.optimisation.io import fingerprint
from src.optimisation.solver import solve
from src.optimisation.types import SolverInput
from src.orchestration.policy_state import state_hash
from src.orchestration.validated_plan import validate_and_freeze_plan
from src.scoring.rules_loader import load_rules, ruleset_sha256


LOCKED_PARAMETERS = ForecastParameters(
    prior_equivalent_minutes=1350.0,
    start_prior_equivalent_matches=2.0,
    cameo_minutes=10.0,
    team_fixture_scale=0.25,
    player_prior_reliability_minutes=900.0,
    event_model_weight=0.0,
    recent_minutes_weight=0.5,
)


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _autosub_points(outcome: Mapping[str, Any]) -> float:
    points = {
        str(row["player_id"]): float(row["total_points"])
        for row in outcome["aggregated_players"]
    }
    return float(
        sum(points[str(row["player_in_id"])] for row in outcome["substitutions"])
    )


def _net_points(plan: Mapping[str, Any], outcome: Mapping[str, Any]) -> int:
    return int(outcome["gross_points"]) - int(plan["finance"]["hit_cost"])


def paired_decision_row(
    *,
    scope: str,
    gameweek: int,
    episode_id: str,
    control_plan: Mapping[str, Any],
    control_outcome: Mapping[str, Any],
    challenger_plan: Mapping[str, Any],
    challenger_outcome: Mapping[str, Any],
    observed_sha256: str,
    hidden_outcome_sha256: str,
    ruleset_sha256_value: str,
    challenger_wall_ms: float,
) -> dict[str, Any]:
    """Compare two validated plans scored against one hidden outcome."""

    control_lineup = control_plan["lineup"]
    challenger_lineup = challenger_plan["lineup"]
    control_net = _net_points(control_plan, control_outcome)
    challenger_net = _net_points(challenger_plan, challenger_outcome)
    return {
        "scope": str(scope),
        "gameweek": int(gameweek),
        "episode_id": str(episode_id),
        "bindings": {
            "observed_sha256": str(observed_sha256),
            "hidden_outcome_sha256": str(hidden_outcome_sha256),
            "ruleset_sha256": str(ruleset_sha256_value),
            "control_plan_sha256": str(control_plan["content_sha256"]),
            "challenger_plan_sha256": str(challenger_plan["content_sha256"]),
            "control_outcome_sha256": str(control_outcome["content_sha256"]),
            "challenger_outcome_sha256": str(
                challenger_outcome["content_sha256"]
            ),
        },
        "decision_changes": {
            "transfers": control_plan["transfers"] != challenger_plan["transfers"],
            "starting_xi": (
                set(control_lineup["starting_xi_ids"])
                != set(challenger_lineup["starting_xi_ids"])
            ),
            "bench_order": (
                control_lineup["bench_ids"] != challenger_lineup["bench_ids"]
            ),
            "captain": (
                control_lineup["captain_id"] != challenger_lineup["captain_id"]
            ),
            "vice_captain": (
                control_lineup["vice_captain_id"]
                != challenger_lineup["vice_captain_id"]
            ),
        },
        "decisions": {
            "control": {
                "transfers": deepcopy(list(control_plan["transfers"])),
                "starting_xi_ids": list(control_lineup["starting_xi_ids"]),
                "bench_ids": list(control_lineup["bench_ids"]),
                "captain_id": str(control_lineup["captain_id"]),
                "vice_captain_id": str(control_lineup["vice_captain_id"]),
            },
            "challenger": {
                "transfers": deepcopy(list(challenger_plan["transfers"])),
                "starting_xi_ids": list(
                    challenger_lineup["starting_xi_ids"]
                ),
                "bench_ids": list(challenger_lineup["bench_ids"]),
                "captain_id": str(challenger_lineup["captain_id"]),
                "vice_captain_id": str(
                    challenger_lineup["vice_captain_id"]
                ),
            },
        },
        "control": {
            "net_points": control_net,
            "gross_points": int(control_outcome["gross_points"]),
            "hit_cost": int(control_plan["finance"]["hit_cost"]),
            "transfers": int(control_plan["finance"]["transfer_count"]),
            "automatic_substitutions": len(control_outcome["substitutions"]),
            "automatic_substitution_points": _autosub_points(control_outcome),
            "captain_source": str(control_outcome["captain"]["source"]),
        },
        "challenger": {
            "net_points": challenger_net,
            "gross_points": int(challenger_outcome["gross_points"]),
            "hit_cost": int(challenger_plan["finance"]["hit_cost"]),
            "transfers": int(challenger_plan["finance"]["transfer_count"]),
            "automatic_substitutions": len(
                challenger_outcome["substitutions"]
            ),
            "automatic_substitution_points": _autosub_points(
                challenger_outcome
            ),
            "captain_source": str(challenger_outcome["captain"]["source"]),
            "wall_ms": round(float(challenger_wall_ms), 6),
        },
        "delta_challenger_minus_control": {
            "net_points": challenger_net - control_net,
            "gross_points": (
                int(challenger_outcome["gross_points"])
                - int(control_outcome["gross_points"])
            ),
            "hit_cost": (
                int(challenger_plan["finance"]["hit_cost"])
                - int(control_plan["finance"]["hit_cost"])
            ),
            "automatic_substitutions": (
                len(challenger_outcome["substitutions"])
                - len(control_outcome["substitutions"])
            ),
            "automatic_substitution_points": (
                _autosub_points(challenger_outcome)
                - _autosub_points(control_outcome)
            ),
        },
        "validation": {
            "control": str(control_plan["validation"]["status"]),
            "challenger": str(challenger_plan["validation"]["status"]),
        },
    }


def _summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("paired evaluation requires at least one row")
    changes = {
        key: sum(bool(row["decision_changes"][key]) for row in rows)
        for key in (
            "transfers",
            "starting_xi",
            "bench_order",
            "captain",
            "vice_captain",
        )
    }
    deltas = [int(row["delta_challenger_minus_control"]["net_points"]) for row in rows]
    wall = [float(row["challenger"]["wall_ms"]) for row in rows]
    return {
        "pairs": len(rows),
        "decision_change_weeks": sum(any(row["decision_changes"].values()) for row in rows),
        "decision_changes": changes,
        "control_net_points": sum(int(row["control"]["net_points"]) for row in rows),
        "challenger_net_points": sum(
            int(row["challenger"]["net_points"]) for row in rows
        ),
        "net_points_delta": sum(deltas),
        "mean_net_points_delta": float(sum(deltas) / len(deltas)),
        "control_automatic_substitution_points": sum(
            float(row["control"]["automatic_substitution_points"]) for row in rows
        ),
        "challenger_automatic_substitution_points": sum(
            float(row["challenger"]["automatic_substitution_points"])
            for row in rows
        ),
        "challenger_wall_ms": {
            "total": float(sum(wall)),
            "mean": float(sum(wall) / len(wall)),
            "max": float(max(wall)),
        },
        "all_plans_valid": all(
            row["validation"] == {
                "control": "passed",
                "challenger": "passed",
            }
            for row in rows
        ),
    }


def paired_decision_hash(rows: Sequence[Mapping[str, Any]]) -> str:
    """Hash deterministic decisions and outcomes while excluding wall time."""

    projection = deepcopy(list(rows))
    for row in projection:
        row.get("control", {}).pop("wall_ms", None)
        row.get("challenger", {}).pop("wall_ms", None)
    return _canonical_hash(projection)


def evaluate_sealed_forks(
    *,
    reports_root: Path,
    episodes_root: Path,
    calibration: Mapping[str, Any],
    rules_path: Path,
    gameweeks: Iterable[int] = tuple(range(2, 39)),
) -> dict[str, Any]:
    """Run isolated policy-on forks from immutable 2025/26 control states."""

    calibration_value = deepcopy(dict(calibration))
    if calibration_value.get("content_sha256") != calibration_hash(
        calibration_value
    ):
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
        control_plan = _read(
            report_root / "forecast_optimizer/validated-plan.json"
        )
        control_outcome = _read(
            report_root / "forecast_optimizer/realised-outcome.json"
        )
        canonical_active_chip = control_plan["active_chip"]
        revealed_at = str(control_outcome["revealed_at"])
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
        challenger_input["squad_contingency_policy"] = "probabilistic_v1"
        challenger_input["appearance_calibration"] = calibration_value
        start = perf_counter()
        solver_output = solve(
            SolverInput.from_dict(challenger_input),
            rules=rules,
            ruleset_sha256=rules_hash,
        )
        wall_ms = (perf_counter() - start) * 1000.0
        challenger_plan = validate_and_freeze_plan(
            episode_id=str(manifest["episode_id"]),
            policy_arm=str(state["policy_arm"]),
            state=state,
            candidate=solver_output["selected"],
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
        "longitudinal": False,
        "rows": rows,
        "summary": _summary(rows),
        "decision_sha256": paired_decision_hash(rows),
        "source_bindings": source_bindings,
    }


def _reference_policy() -> dict[str, Any]:
    return {
        "policy_id": "w10-locked-reference-squad-v1",
        "policy_version": "1.0",
        "horizon_gameweeks": 1,
        "discount_factors": [1.0],
        "arms": {
            "deterministic": {
                "kind": "optimiser",
                "uncertainty_penalty": 0.0,
            }
        },
        "objective": {
            "autosub_weight": 0.0,
            "bench_weight": 0.0,
            "early_wildcard_risk_weight": 0.0,
            "new_signing_shrinkage": 0.0,
            "promoted_team_shrinkage": 0.0,
            "transfer_optionality_weight": 0.0,
            "world_cup_fatigue_weight": 0.0,
        },
        "search": {
            "beam_width": 1500,
            "candidate_limit_per_position": 24,
            "cheapest_per_position": 8,
            "retained_squads": 2,
        },
    }


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _locked_market(
    *,
    prediction_frame: pd.DataFrame,
    target_rows: pd.DataFrame,
    gameweek: int,
    season: str,
    rules: Mapping[str, Any],
    rules_hash: str,
) -> tuple[list[dict[str, Any]], list[str], float, datetime, list[dict[str, Any]]]:
    predicted = prediction_frame.loc[prediction_frame["GW"] == gameweek].copy()
    observed = target_rows.loc[
        (target_rows["GW"] == gameweek)
        & target_rows["position"].isin(("GKP", "DEF", "MID", "FWD"))
    ].copy()
    if predicted.empty or observed.empty:
        raise ValueError(f"locked market has no rows for GW{gameweek}")
    metadata = (
        observed.sort_values(["code", "fixture"], kind="mergesort")
        .groupby("code", as_index=False)
        .agg(
            name=("name", "first"),
            team=("team", "first"),
            value=("value", "first"),
            position=("position", "first"),
            first_kickoff=("kickoff_time", "min"),
        )
    )
    market_frame = predicted.merge(
        metadata,
        on=["code", "position"],
        how="inner",
        validate="one_to_one",
    )
    market_frame = market_frame.loc[
        market_frame["value"].notna() & (market_frame["value"] > 0)
    ].copy()
    first_kickoff = pd.to_datetime(
        observed["kickoff_time"], utc=True
    ).min().to_pydatetime()
    cutoff = first_kickoff - timedelta(minutes=90)
    players: list[dict[str, Any]] = []
    for row in market_frame.sort_values("code", kind="mergesort").itertuples(
        index=False
    ):
        players.append(
            {
                "player_id": str(row.code),
                "web_name": str(row.name),
                "position": str(row.position),
                "club_id": str(row.team),
                "now_cost": round(float(row.value) / 10.0, 1),
                "available_at": _iso(cutoff),
                "expected_points": [
                    max(0.0, float(row.live_faithful_expected_points))
                ],
                "start_probability": [
                    float(row.live_faithful_start_probability)
                ],
                "uncertainty": [0.0],
                "status": "a",
                "fixture_count": int(row.fixture_count),
            }
        )
    packet = {
        "schema_version": "1.0",
        "decision_id": f"w10:{season}:gw{gameweek:02d}:reference-squad",
        "season": season,
        "decision_cutoff": _iso(cutoff),
        "captured_at": _iso(cutoff),
        "ruleset_id": str(rules["meta"]["ruleset_id"]),
        "ruleset_sha256": rules_hash,
        "feature_state_sha256": _canonical_hash(
            {
                "season": season,
                "gameweek": gameweek,
                "players": players,
            }
        ),
        "forecast_model_version": "live-faithful-v1-locked",
        "horizon_gameweeks": [gameweek],
        "discount_factors": [1.0],
        "players": players,
    }
    squad_result = optimise_initial_squad(
        packet,
        policy=_reference_policy(),
        arm_mode="deterministic",
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    selected_ids = [
        str(value) for value in squad_result["selected"]["squad_player_ids"]
    ]
    bank = float(squad_result["selected"]["bank"])
    outcomes = [
        {
            "player_id": str(row.code),
            "fixture": str(row.fixture),
            "position": str(row.position),
            "minutes": int(row.minutes),
            "total_points": int(row.total_points),
        }
        for row in observed.itertuples(index=False)
        if str(row.code) in set(selected_ids)
    ]
    return players, selected_ids, bank, cutoff, outcomes


def _locked_state(
    *,
    season: str,
    gameweek: int,
    policy_arm: str,
    squad_ids: Sequence[str],
    bank: float,
    market: Sequence[Mapping[str, Any]],
    rules: Mapping[str, Any],
    rules_hash: str,
) -> dict[str, Any]:
    indexed = {str(row["player_id"]): row for row in market}
    squad = [
        {
            "player_id": player_id,
            "position": str(indexed[player_id]["position"]),
            "club_id": str(indexed[player_id]["club_id"]),
            "purchase_price": float(indexed[player_id]["now_cost"]),
            "current_price": float(indexed[player_id]["now_cost"]),
            "selling_price": float(indexed[player_id]["now_cost"]),
        }
        for player_id in squad_ids
    ]
    state: dict[str, Any] = {
        "schema_version": "1.0",
        "state_id": f"w10:{season}:gw{gameweek:02d}:{policy_arm}",
        "status": "active",
        "origin": {"type": "locked_neutral_reference"},
        "policy_arm": policy_arm,
        "season": season,
        "gameweek": gameweek,
        "ruleset_id": str(rules["meta"]["ruleset_id"]),
        "ruleset_sha256": rules_hash,
        "previous_state_sha256": None,
        "transition_id": None,
        "squad": squad,
        "bank": round(float(bank), 1),
        "free_transfers": 1,
        "chips_available": [],
        "chip_history": [],
        "cumulative_points": 0,
    }
    state["content_sha256"] = state_hash(state)
    return state


def evaluate_locked_lineups(
    *,
    vaastav_root: Path,
    calibration: Mapping[str, Any],
    rules_path: Path,
    gameweeks: Iterable[int] = tuple(range(1, 39)),
) -> dict[str, Any]:
    """Evaluate same-squad off/on lineup decisions on locked 2024/25 data."""

    calibration_value = deepcopy(dict(calibration))
    if calibration_value.get("content_sha256") != calibration_hash(
        calibration_value
    ):
        raise ValueError("appearance calibration hash mismatch")
    prior, prior_lineage = load_season_rows(
        "2023-24", vaastav_root=vaastav_root
    )
    target, target_lineage = load_season_rows(
        "2024-25", vaastav_root=vaastav_root
    )
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
        challenger_data["squad_contingency_policy"] = "probabilistic_v1"
        challenger_data["appearance_calibration"] = calibration_value
        challenger_input = SolverInput.from_dict(challenger_data)
        control_start = perf_counter()
        control_output = solve(
            control_input, rules=rules, ruleset_sha256=rules_hash
        )
        control_wall_ms = (perf_counter() - control_start) * 1000.0
        challenger_start = perf_counter()
        challenger_output = solve(
            challenger_input, rules=rules, ruleset_sha256=rules_hash
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
        rows.append(row)
    return {
        "scope": "locked_2024_25_same_squad_lineup",
        "longitudinal": False,
        "rows": rows,
        "summary": _summary(rows),
        "decision_sha256": paired_decision_hash(rows),
        "source_lineage": [prior_lineage, target_lineage],
        "cutoff_policy": (
            "first recorded kickoff minus the historical 90-minute FPL "
            "deadline interval; no unstructured evidence is used"
        ),
        "rules_compatibility": (
            "2025/26 historical catalogue used only for unchanged squad, "
            "formation, autosub and captain-fallback boundaries; 2024/25 "
            "realised points are the recorded official totals"
        ),
    }


def build_contingency_report(
    *,
    calibration: Mapping[str, Any],
    locked: Mapping[str, Any],
    descriptive: Mapping[str, Any],
    production_default_before: str = "none",
) -> dict[str, Any]:
    """Build the owner-review packet without changing production policy."""

    locked_summary = locked["summary"]
    descriptive_summary = descriptive["summary"]
    gates = {
        "locked_non_negative_realised_value": (
            float(locked_summary["net_points_delta"]) >= 0.0
        ),
        "locked_has_decision_differences": (
            int(locked_summary["decision_change_weeks"]) > 0
        ),
        "locked_all_plans_valid": bool(locked_summary["all_plans_valid"]),
        "descriptive_all_plans_valid": bool(
            descriptive_summary["all_plans_valid"]
        ),
        "appearance_calibration_hash_valid": (
            calibration.get("content_sha256") == calibration_hash(calibration)
        ),
        "production_owner_approval": False,
    }
    evidence_gates = {
        key: value
        for key, value in gates.items()
        if key != "production_owner_approval"
    }
    report: dict[str, Any] = {
        "schema_version": "1.0",
        "report_id": "squad-contingency-v1-paired-evaluation",
        "policy": {
            "challenger": "probabilistic_v1",
            "production_default_before": str(production_default_before),
            "production_default_changed": False,
            "promotion_change": (
                "single owner-ratified policy-data field; not performed by "
                "this evaluation"
            ),
        },
        "appearance_calibration_sha256": str(
            calibration["content_sha256"]
        ),
        "locked_2024_25": deepcopy(dict(locked)),
        "descriptive_2025_26": deepcopy(dict(descriptive)),
        "promotion_gates": gates,
        "evidence_gate_passed": all(evidence_gates.values()),
        "promotion_eligible": all(gates.values()),
        "decision": (
            "eligible_for_owner_review"
            if all(evidence_gates.values())
            else "reject_or_defer"
        ),
        "limitations": [
            (
                "The locked 2024/25 gate evaluates same-squad lineup, bench and "
                "captain decisions rather than a longitudinal transfer policy."
            ),
            (
                "The 2025/26 forks start from each sealed canonical state and "
                "hold transfers at zero for both arms; their lineup deltas are "
                "isolated and cannot be summed as a new season path."
            ),
            (
                "Historical reference squads are point-in-time neutral optimiser "
                "constructs, not observed human manager squads."
            ),
        ],
    }
    report["content_sha256"] = artifact_hash(report)
    return report
