"""Deterministic bounded optimiser for a season-start FPL squad."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from src.optimisation.simple_plan import choose_starting_xi_rows
from src.scoring.rules_loader import get_rule
from src.scoring.validator import (
    POSITIONS,
    legal_formations,
    validate_lineup,
    validate_squad,
)


class InitialSquadError(ValueError):
    """Raised when an initial-squad experiment is unsafe or incomplete."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def initial_squad_hash(value: Mapping[str, Any]) -> str:
    """Hash stable semantics while excluding an embedded content hash."""

    projection = {
        key: item for key, item in value.items() if key != "content_sha256"
    }
    return hashlib.sha256(_canonical_bytes(projection)).hexdigest()


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise InitialSquadError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise InitialSquadError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _number_vector(
    value: Any,
    *,
    field: str,
    length: int,
    lower: float | None = None,
    upper: float | None = None,
) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise InitialSquadError(f"{field} must contain {length} values")
    result: list[float] = []
    for index, item in enumerate(value):
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise InitialSquadError(f"{field}[{index}] must be numeric")
        number = float(item)
        if lower is not None and number < lower:
            raise InitialSquadError(f"{field}[{index}] must be >= {lower}")
        if upper is not None and number > upper:
            raise InitialSquadError(f"{field}[{index}] must be <= {upper}")
        result.append(number)
    return result


def validate_initial_squad_packet(
    packet: Mapping[str, Any],
    *,
    rules: Mapping[str, Any],
    ruleset_sha256: str,
) -> dict[str, Any]:
    """Validate and normalise one immutable same-cutoff player forecast packet."""

    value = deepcopy(dict(packet))
    required = {
        "schema_version",
        "decision_id",
        "season",
        "decision_cutoff",
        "captured_at",
        "ruleset_id",
        "ruleset_sha256",
        "feature_state_sha256",
        "forecast_model_version",
        "horizon_gameweeks",
        "discount_factors",
        "players",
    }
    missing = sorted(required - set(value))
    if missing:
        raise InitialSquadError(
            f"Initial-squad packet missing fields: {', '.join(missing)}"
        )
    if value["ruleset_id"] != rules.get("meta", {}).get("ruleset_id"):
        raise InitialSquadError("Packet ruleset_id differs from supplied rules")
    if value["ruleset_sha256"] != ruleset_sha256:
        raise InitialSquadError("Packet ruleset_sha256 differs from supplied rules")
    for field in ("ruleset_sha256", "feature_state_sha256"):
        digest = str(value[field])
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise InitialSquadError(f"{field} must be a lower-case SHA-256")

    cutoff_text, cutoff = _timestamp(value["decision_cutoff"], "decision_cutoff")
    captured_text, captured = _timestamp(value["captured_at"], "captured_at")
    if captured > cutoff:
        raise InitialSquadError("Packet captured_at is after decision_cutoff")
    value["decision_cutoff"] = cutoff_text
    value["captured_at"] = captured_text

    gameweeks = value["horizon_gameweeks"]
    if (
        not isinstance(gameweeks, list)
        or not gameweeks
        or any(isinstance(item, bool) or not isinstance(item, int) for item in gameweeks)
    ):
        raise InitialSquadError("horizon_gameweeks must be a non-empty integer list")
    if gameweeks != list(range(gameweeks[0], gameweeks[0] + len(gameweeks))):
        raise InitialSquadError("horizon_gameweeks must be consecutive")
    discounts = _number_vector(
        value["discount_factors"],
        field="discount_factors",
        length=len(gameweeks),
        lower=0.0,
        upper=1.0,
    )
    if discounts[0] != 1.0:
        raise InitialSquadError("First discount factor must equal 1.0")
    value["discount_factors"] = discounts

    players = value["players"]
    if not isinstance(players, list):
        raise InitialSquadError("players must be a list")
    normalised: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, source in enumerate(players):
        if not isinstance(source, Mapping):
            raise InitialSquadError(f"players[{index}] must be an object")
        row = deepcopy(dict(source))
        player_required = {
            "player_id",
            "web_name",
            "position",
            "club_id",
            "now_cost",
            "available_at",
            "expected_points",
            "start_probability",
            "uncertainty",
        }
        player_missing = sorted(player_required - set(row))
        if player_missing:
            raise InitialSquadError(
                f"players[{index}] missing fields: {', '.join(player_missing)}"
            )
        player_id = str(row["player_id"])
        if not player_id or player_id in seen:
            raise InitialSquadError(f"Duplicate or empty player_id: {player_id}")
        seen.add(player_id)
        position = str(row["position"])
        if position not in POSITIONS:
            raise InitialSquadError(f"Unsupported position for {player_id}: {position}")
        cost = row["now_cost"]
        if isinstance(cost, bool) or not isinstance(cost, (int, float)) or float(cost) < 0:
            raise InitialSquadError(f"now_cost must be non-negative for {player_id}")
        available_text, available = _timestamp(
            row["available_at"], f"players[{index}].available_at"
        )
        if available > cutoff:
            raise InitialSquadError(
                f"Player {player_id} became available after decision_cutoff"
            )
        row.update(
            {
                "player_id": player_id,
                "web_name": str(row["web_name"]),
                "position": position,
                "club_id": str(row["club_id"]),
                "now_cost": round(float(cost), 1),
                "purchase_price": round(float(cost), 1),
                "available_at": available_text,
                "expected_points": _number_vector(
                    row["expected_points"],
                    field=f"players[{index}].expected_points",
                    length=len(gameweeks),
                    lower=0.0,
                ),
                "start_probability": _number_vector(
                    row["start_probability"],
                    field=f"players[{index}].start_probability",
                    length=len(gameweeks),
                    lower=0.0,
                    upper=1.0,
                ),
                "uncertainty": _number_vector(
                    row["uncertainty"],
                    field=f"players[{index}].uncertainty",
                    length=len(gameweeks),
                    lower=0.0,
                ),
                "status": str(row.get("status", "a")),
                "promoted_team": bool(row.get("promoted_team", False)),
                "new_signing": bool(row.get("new_signing", False)),
                "world_cup_fatigue": float(row.get("world_cup_fatigue", 0.0)),
                "transfer_optionality": float(row.get("transfer_optionality", 0.0)),
                "early_wildcard_risk": float(row.get("early_wildcard_risk", 0.0)),
            }
        )
        for field in (
            "world_cup_fatigue",
            "transfer_optionality",
            "early_wildcard_risk",
        ):
            if not 0.0 <= row[field] <= 1.0:
                raise InitialSquadError(f"{field} must be in [0, 1] for {player_id}")
        normalised.append(row)
    value["players"] = normalised

    position_counts = get_rule(dict(rules), "squad.position_counts")["value"]
    available_counts = Counter(
        row["position"] for row in normalised if row["status"] == "a"
    )
    for position, count in position_counts.items():
        if available_counts[position] < int(count):
            raise InitialSquadError(
                f"Not enough available {position} players for a legal squad"
            )

    supplied_hash = value.get("content_sha256")
    computed_hash = initial_squad_hash(value)
    if supplied_hash is not None and supplied_hash != computed_hash:
        raise InitialSquadError("Initial-squad packet content hash mismatch")
    value["content_sha256"] = computed_hash
    return value


def apply_initial_squad_adjustments(
    packet: Mapping[str, Any],
    adjustments: Sequence[Mapping[str, Any]],
    *,
    maximum_absolute_delta: float,
) -> dict[str, Any]:
    """Apply bounded, cited pre-cutoff point deltas to a copied packet."""

    value = deepcopy(dict(packet))
    cutoff_text, cutoff = _timestamp(value["decision_cutoff"], "decision_cutoff")
    value["decision_cutoff"] = cutoff_text
    by_id = {str(row["player_id"]): row for row in value["players"]}
    seen: set[str] = set()
    ledger: list[dict[str, Any]] = []
    for index, source in enumerate(adjustments):
        row = deepcopy(dict(source))
        required = {
            "player_id",
            "expected_points_delta",
            "available_at",
            "evidence_ids",
            "rationale",
        }
        missing = sorted(required - set(row))
        if missing:
            raise InitialSquadError(
                f"adjustments[{index}] missing fields: {', '.join(missing)}"
            )
        player_id = str(row["player_id"])
        if player_id in seen:
            raise InitialSquadError(f"Duplicate adjustment for {player_id}")
        if player_id not in by_id:
            raise InitialSquadError(f"Adjustment references unknown player {player_id}")
        seen.add(player_id)
        available_text, available = _timestamp(
            row["available_at"], f"adjustments[{index}].available_at"
        )
        if available > cutoff:
            raise InitialSquadError(
                f"Adjustment for {player_id} is available after decision_cutoff"
            )
        deltas = _number_vector(
            row["expected_points_delta"],
            field=f"adjustments[{index}].expected_points_delta",
            length=len(value["horizon_gameweeks"]),
        )
        if any(abs(delta) > maximum_absolute_delta for delta in deltas):
            raise InitialSquadError(
                f"Adjustment for {player_id} exceeds maximum absolute delta"
            )
        evidence_ids = row["evidence_ids"]
        if (
            not isinstance(evidence_ids, list)
            or not evidence_ids
            or any(not str(item) for item in evidence_ids)
        ):
            raise InitialSquadError(
                f"Adjustment for {player_id} requires evidence_ids"
            )
        target = by_id[player_id]
        target["expected_points"] = [
            round(max(0.0, float(point) + delta), 6)
            for point, delta in zip(target["expected_points"], deltas, strict=True)
        ]
        ledger.append(
            {
                "player_id": player_id,
                "expected_points_delta": deltas,
                "available_at": available_text,
                "evidence_ids": [str(item) for item in evidence_ids],
                "rationale": str(row["rationale"]),
            }
        )
    value.pop("content_sha256", None)
    value["adjustment_ledger"] = ledger
    value["content_sha256"] = initial_squad_hash(value)
    return value


def _arm_weights(policy: Mapping[str, Any], arm_mode: str) -> dict[str, float]:
    objective = dict(policy["objective"])
    arm = dict(policy["arms"][arm_mode])
    return {
        "bench": float(objective["bench_weight"]),
        "autosub": float(objective["autosub_weight"]),
        "uncertainty": float(arm["uncertainty_penalty"]),
        "promoted": float(objective["promoted_team_shrinkage"]),
        "new_signing": float(objective["new_signing_shrinkage"]),
        "fatigue": float(objective["world_cup_fatigue_weight"]),
        "optionality": float(objective["transfer_optionality_weight"]),
        "wildcard_risk": float(objective["early_wildcard_risk_weight"]),
    }


def _player_week_values(
    row: Mapping[str, Any],
    weights: Mapping[str, float],
) -> tuple[list[float], list[float], list[float]]:
    adjusted: list[float] = []
    planning: list[float] = []
    risk: list[float] = []
    shrinkage = (
        weights["promoted"] * int(bool(row["promoted_team"]))
        + weights["new_signing"] * int(bool(row["new_signing"]))
        + weights["fatigue"] * float(row["world_cup_fatigue"])
    )
    multiplier = max(0.0, 1.0 - shrinkage)
    for raw, uncertainty in zip(
        row["expected_points"], row["uncertainty"], strict=True
    ):
        context_value = float(raw) * multiplier
        penalty = weights["uncertainty"] * float(uncertainty)
        adjusted.append(round(context_value, 6))
        risk.append(round(penalty, 6))
        planning.append(round(max(0.0, context_value - penalty), 6))
    return adjusted, planning, risk


def _search_value(
    row: Mapping[str, Any],
    discounts: Sequence[float],
    weights: Mapping[str, float],
) -> float:
    _, planning, _ = _player_week_values(row, weights)
    horizon = sum(
        discount * points
        for discount, points in zip(discounts, planning, strict=True)
    )
    return round(
        horizon
        + weights["optionality"] * float(row["transfer_optionality"])
        - weights["wildcard_risk"] * float(row["early_wildcard_risk"]),
        8,
    )


def _shortlist(
    players: Sequence[Mapping[str, Any]],
    *,
    position: str,
    required: int,
    discounts: Sequence[float],
    weights: Mapping[str, float],
    candidate_limit: int,
    cheapest_limit: int,
) -> list[dict[str, Any]]:
    pool = [
        deepcopy(dict(row))
        for row in players
        if row["position"] == position and row["status"] == "a"
    ]
    for row in pool:
        row["_search_value"] = _search_value(row, discounts, weights)
    by_value = sorted(
        pool,
        key=lambda row: (
            -float(row["_search_value"]),
            float(row["now_cost"]),
            str(row["player_id"]),
        ),
    )[:candidate_limit]
    by_price = sorted(
        pool,
        key=lambda row: (
            float(row["now_cost"]),
            -float(row["_search_value"]),
            str(row["player_id"]),
        ),
    )[:cheapest_limit]
    unique = {str(row["player_id"]): row for row in [*by_value, *by_price]}
    result = sorted(
        unique.values(),
        key=lambda row: (
            -float(row["_search_value"]),
            float(row["now_cost"]),
            str(row["player_id"]),
        ),
    )
    if len(result) < required:
        raise InitialSquadError(f"Shortlist cannot fill required {position} slots")
    return result


def _remaining_minimum_cost(
    pools: Mapping[str, Sequence[Mapping[str, Any]]],
    remaining: Mapping[str, int],
    last_indices: Mapping[str, int],
) -> int | None:
    total = 0
    for position, count in remaining.items():
        if count <= 0:
            continue
        start = int(last_indices.get(position, -1)) + 1
        costs = sorted(
            int(round(float(row["now_cost"]) * 10))
            for row in pools[position][start:]
        )
        if len(costs) < count:
            return None
        total += sum(costs[:count])
    return total


def _compact_lineup(lineup: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "formation": deepcopy(dict(lineup["formation"])),
        "starting_xi": [str(row["player_id"]) for row in lineup["starting_xi"]],
        "bench": [str(row["player_id"]) for row in lineup["bench"]],
        "captain_id": str(lineup["captain_id"]),
        "vice_captain_id": str(lineup["vice_captain_id"]),
    }


def _evaluate_squad(
    squad: Sequence[Mapping[str, Any]],
    *,
    packet: Mapping[str, Any],
    policy: Mapping[str, Any],
    arm_mode: str,
    rules: Mapping[str, Any],
) -> dict[str, Any]:
    weights = _arm_weights(policy, arm_mode)
    formations = legal_formations(dict(rules))
    discounts = packet["discount_factors"]
    week_rows: list[dict[str, Any]] = []
    discounted_week_value = 0.0
    total_context_loss = 0.0
    total_risk_penalty = 0.0
    for index, gameweek in enumerate(packet["horizon_gameweeks"]):
        planning_rows: list[dict[str, Any]] = []
        for source in squad:
            row = deepcopy(dict(source))
            adjusted, planning, risk = _player_week_values(row, weights)
            row["raw_expected_points"] = float(row["expected_points"][index])
            row["context_expected_points"] = adjusted[index]
            row["expected_points"] = planning[index]
            row["risk_penalty"] = risk[index]
            planning_rows.append(row)
            total_context_loss += (
                row["raw_expected_points"] - row["context_expected_points"]
            ) * float(discounts[index])
            total_risk_penalty += risk[index] * float(discounts[index])

        lineup = choose_starting_xi_rows(planning_rows, formations=formations)
        by_id = {str(row["player_id"]): row for row in planning_rows}
        starters = [by_id[str(row["player_id"])] for row in lineup["starting_xi"]]
        bench = [by_id[str(row["player_id"])] for row in lineup["bench"]]
        starter_points = sum(float(row["expected_points"]) for row in starters)
        captain_bonus = float(by_id[str(lineup["captain_id"])]["expected_points"])
        bench_points = sum(float(row["expected_points"]) for row in bench)
        non_start_probability = sum(
            1.0 - float(row["start_probability"][index]) for row in starters
        ) / len(starters)
        bench_value = weights["bench"] * bench_points
        autosub_value = weights["autosub"] * bench_points * non_start_probability
        week_value = starter_points + captain_bonus + bench_value + autosub_value
        discount = float(discounts[index])
        discounted_week_value += discount * week_value
        week_rows.append(
            {
                "gameweek": int(gameweek),
                "discount": discount,
                "lineup": _compact_lineup(lineup),
                "value": {
                    "starter_points": round(starter_points, 6),
                    "captain_bonus": round(captain_bonus, 6),
                    "bench_value": round(bench_value, 6),
                    "autosub_value": round(autosub_value, 6),
                    "total": round(week_value, 6),
                    "discounted": round(discount * week_value, 6),
                },
            }
        )

    optionality_bonus = weights["optionality"] * sum(
        float(row["transfer_optionality"]) for row in squad
    )
    wildcard_risk_penalty = weights["wildcard_risk"] * sum(
        float(row["early_wildcard_risk"]) for row in squad
    )
    objective = discounted_week_value + optionality_bonus - wildcard_risk_penalty
    squad_rows = [
        {
            "player_id": str(row["player_id"]),
            "position": str(row["position"]),
            "club_id": str(row["club_id"]),
            "purchase_price": float(row["now_cost"]),
        }
        for row in squad
    ]
    squad_validation = validate_squad(squad_rows, rules=dict(rules))
    first = week_rows[0]["lineup"]
    by_id = {str(row["player_id"]): row for row in squad_rows}
    lineup_validation = validate_lineup(
        [by_id[player_id] for player_id in first["starting_xi"]],
        [by_id[player_id] for player_id in first["bench"]],
        captain_id=first["captain_id"],
        vice_captain_id=first["vice_captain_id"],
        rules=dict(rules),
    )
    if not squad_validation.ok or not lineup_validation.ok:
        raise InitialSquadError("Generated initial squad failed deterministic validation")
    result: dict[str, Any] = {
        "squad_player_ids": sorted(str(row["player_id"]) for row in squad),
        "squad": [
            {
                "player_id": str(row["player_id"]),
                "web_name": str(row["web_name"]),
                "position": str(row["position"]),
                "club_id": str(row["club_id"]),
                "now_cost": float(row["now_cost"]),
            }
            for row in sorted(squad, key=lambda item: (POSITIONS.index(item["position"]), str(item["player_id"])))
        ],
        "bank": round(
            float(get_rule(dict(rules), "squad.initial_budget")["value"])
            - sum(float(row["now_cost"]) for row in squad),
            1,
        ),
        "objective": round(objective, 6),
        "decomposition": {
            "discounted_lineup_captain_bench_autosub": round(
                discounted_week_value, 6
            ),
            "context_shrinkage_loss": round(total_context_loss, 6),
            "uncertainty_penalty": round(total_risk_penalty, 6),
            "transfer_optionality_bonus": round(optionality_bonus, 6),
            "early_wildcard_risk_penalty": round(wildcard_risk_penalty, 6),
        },
        "weekly_plans": week_rows,
        "validation": {
            "squad": squad_validation.as_dict(),
            "first_lineup": lineup_validation.as_dict(),
        },
    }
    result["proposal_sha256"] = initial_squad_hash(result)
    return result


def score_declared_initial_squad(
    packet: Mapping[str, Any],
    squad_player_ids: Sequence[str],
    *,
    policy: Mapping[str, Any],
    arm_mode: str,
    rules: Mapping[str, Any],
    ruleset_sha256: str,
) -> dict[str, Any]:
    """Validate and score a declared 15 against one frozen packet."""

    validated = validate_initial_squad_packet(
        packet, rules=rules, ruleset_sha256=ruleset_sha256
    )
    ids = [str(item) for item in squad_player_ids]
    if len(ids) != len(set(ids)):
        raise InitialSquadError("Declared squad player IDs must be unique")
    by_id = {str(row["player_id"]): row for row in validated["players"]}
    unknown = sorted(set(ids) - set(by_id))
    if unknown:
        raise InitialSquadError(
            f"Declared squad references unknown players: {', '.join(unknown)}"
        )
    return _evaluate_squad(
        [by_id[player_id] for player_id in ids],
        packet=validated,
        policy=policy,
        arm_mode=arm_mode,
        rules=rules,
    )


def optimise_initial_squad(
    packet: Mapping[str, Any],
    *,
    policy: Mapping[str, Any],
    arm_mode: str,
    rules: Mapping[str, Any],
    ruleset_sha256: str,
) -> dict[str, Any]:
    """Search a reproducible bounded candidate pool for a legal initial 15."""

    if arm_mode not in policy.get("arms", {}):
        raise InitialSquadError(f"Unknown initial-squad arm mode: {arm_mode}")
    validated = validate_initial_squad_packet(
        packet, rules=rules, ruleset_sha256=ruleset_sha256
    )
    configured_horizon = int(policy["horizon_gameweeks"])
    if configured_horizon != len(validated["horizon_gameweeks"]):
        raise InitialSquadError("Policy horizon differs from packet horizon")
    if [float(item) for item in policy["discount_factors"]] != validated["discount_factors"]:
        raise InitialSquadError("Policy discount factors differ from packet")

    search = policy["search"]
    beam_width = int(search["beam_width"])
    retained_squads = int(search["retained_squads"])
    candidate_limit = int(search["candidate_limit_per_position"])
    cheapest_limit = int(search["cheapest_per_position"])
    if min(beam_width, retained_squads, candidate_limit, cheapest_limit) < 1:
        raise InitialSquadError("Search budgets must be positive")

    weights = _arm_weights(policy, arm_mode)
    position_counts = {
        str(position): int(count)
        for position, count in get_rule(
            dict(rules), "squad.position_counts"
        )["value"].items()
    }
    max_per_club = int(get_rule(dict(rules), "squad.max_per_club")["value"])
    budget_tenths = int(
        round(float(get_rule(dict(rules), "squad.initial_budget")["value"]) * 10)
    )
    pools = {
        position: _shortlist(
            validated["players"],
            position=position,
            required=count,
            discounts=validated["discount_factors"],
            weights=weights,
            candidate_limit=candidate_limit,
            cheapest_limit=cheapest_limit,
        )
        for position, count in position_counts.items()
    }
    slots = [
        position
        for position in POSITIONS
        for _ in range(position_counts.get(position, 0))
    ]
    frontier: list[dict[str, Any]] = [
        {
            "chosen": [],
            "cost": 0,
            "clubs": {},
            "heuristic": 0.0,
            "last_indices": {},
            "position_selected": {},
        }
    ]
    expanded = generated = budget_pruned = club_pruned = 0
    for position in slots:
        next_states: list[dict[str, Any]] = []
        for state in frontier:
            expanded += 1
            last = int(state["last_indices"].get(position, -1))
            selected_here = int(state["position_selected"].get(position, 0))
            remaining_here = position_counts[position] - selected_here
            stop = len(pools[position]) - remaining_here + 1
            for index in range(last + 1, stop):
                row = pools[position][index]
                club_id = str(row["club_id"])
                club_count = int(state["clubs"].get(club_id, 0)) + 1
                if club_count > max_per_club:
                    club_pruned += 1
                    continue
                cost = int(state["cost"]) + int(round(float(row["now_cost"]) * 10))
                if cost > budget_tenths:
                    budget_pruned += 1
                    continue
                generated += 1
                clubs = dict(state["clubs"])
                clubs[club_id] = club_count
                last_indices = dict(state["last_indices"])
                last_indices[position] = index
                position_selected = dict(state["position_selected"])
                position_selected[position] = selected_here + 1
                remaining = {
                    item: position_counts[item]
                    - int(position_selected.get(item, 0))
                    for item in position_counts
                }
                minimum = _remaining_minimum_cost(pools, remaining, last_indices)
                if minimum is None or cost + minimum > budget_tenths:
                    budget_pruned += 1
                    continue
                next_states.append(
                    {
                        "chosen": [*state["chosen"], row],
                        "cost": cost,
                        "clubs": clubs,
                        "heuristic": round(
                            float(state["heuristic"]) + float(row["_search_value"]),
                            8,
                        ),
                        "last_indices": last_indices,
                        "position_selected": position_selected,
                    }
                )
        if not next_states:
            raise InitialSquadError(
                f"Bounded search found no feasible state while filling {position}"
            )
        next_states.sort(
            key=lambda state: (
                -float(state["heuristic"]),
                int(state["cost"]),
                tuple(str(row["player_id"]) for row in state["chosen"]),
            )
        )
        frontier = next_states[:beam_width]

    completed = sorted(
        (
            _evaluate_squad(
                state["chosen"],
                packet=validated,
                policy=policy,
                arm_mode=arm_mode,
                rules=rules,
            )
            for state in frontier
        ),
        key=lambda result: (
            -float(result["objective"]),
            tuple(result["squad_player_ids"]),
        ),
    )
    if not completed:
        raise InitialSquadError("Bounded search produced no completed squad")
    retained = completed[:retained_squads]
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "status": "complete",
        "arm_mode": arm_mode,
        "packet_sha256": validated["content_sha256"],
        "policy_id": str(policy["policy_id"]),
        "policy_version": str(policy["policy_version"]),
        "ruleset_id": str(validated["ruleset_id"]),
        "ruleset_sha256": ruleset_sha256,
        "selected": retained[0],
        "alternatives": retained[1:],
        "search": {
            "algorithm": "deterministic_bounded_beam",
            "global_optimality_guaranteed": False,
            "beam_width": beam_width,
            "retained_squads": retained_squads,
            "candidate_pool_sizes": {
                position: len(rows) for position, rows in pools.items()
            },
            "expanded_states": expanded,
            "generated_states": generated,
            "budget_pruned": budget_pruned,
            "club_pruned": club_pruned,
        },
    }
    result["content_sha256"] = initial_squad_hash(result)
    return result
