"""Pure, fail-closed construction of canonical Gameweek action plans."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator, FormatChecker

from src.optimisation.io import fingerprint
from src.scoring.validator import (
    club_limit_exceptions,
    selling_price,
    transfer_hit_cost,
    validate_chips,
    validate_lineup,
    validate_squad,
)


ROOT = Path(__file__).resolve().parents[2]
PLAN_SCHEMA = ROOT / "control/schemas/benchmark/validated-plan.json"
_VALIDATION_CHECKS = [
    "predecessor_and_rules_bound",
    "transfer_finance_recomputed",
    "squad_legal",
    "lineup_legal_and_ordered",
    "chip_legal",
]


class ValidatedPlanError(ValueError):
    """Raised when a proposed or frozen Gameweek plan fails validation."""


def _price(value: Any) -> float:
    if isinstance(value, bool):
        raise ValidatedPlanError("Price must be numeric")
    return round(float(value) + 1e-9, 1)


def _iso_datetime(value: Any, field: str) -> str:
    text = str(value)
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidatedPlanError(f"{field} must be an ISO-8601 timestamp") from exc
    return text


def _market_by_id(
    market: Mapping[str, Any] | Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    rows = market.values() if isinstance(market, Mapping) else market
    result: dict[str, dict[str, Any]] = {}
    for source in rows:
        row = dict(source)
        player_id = str(row.get("player_id"))
        if not player_id or player_id == "None" or player_id in result:
            raise ValidatedPlanError("Decision market player IDs must be present and unique")
        result[player_id] = row
    return result


def _validation_payload(plan: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "episode_id": plan["episode_id"],
        "policy_arm": plan["policy_arm"],
        "season": plan["season"],
        "gameweek": plan["gameweek"],
        "previous_state_sha256": plan["previous_state_sha256"],
        "ruleset": plan["ruleset"],
        "transfers": plan["transfers"],
        "squad_after": plan["squad_after"],
        "lineup": plan["lineup"],
        "active_chip": plan["active_chip"],
        "finance": plan["finance"],
        "checks": plan["validation"]["checks"],
    }


def validated_plan_hash(plan: Mapping[str, Any]) -> str:
    """Return the canonical hash of a plan, excluding its hash field."""
    body = deepcopy(dict(plan))
    body.pop("content_sha256", None)
    return fingerprint(body)


def _schema_errors(plan: Mapping[str, Any]) -> list[str]:
    schema = json.loads(PLAN_SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(plan), key=lambda err: list(err.absolute_path))
    ]


def validate_plan_integrity(
    plan: Mapping[str, Any],
    *,
    expected_state: Mapping[str, Any] | None = None,
    rules: Mapping[str, Any] | None = None,
    ruleset_sha256: str | None = None,
) -> None:
    """Validate the closed shape, hashes, and optional predecessor/rules bindings."""
    errors = _schema_errors(plan)
    if errors:
        raise ValidatedPlanError("Validated plan schema failed: " + "; ".join(errors))
    if plan["validation"]["content_sha256"] != fingerprint(_validation_payload(plan)):
        raise ValidatedPlanError("Validated plan validation hash mismatch")
    if plan["content_sha256"] != validated_plan_hash(plan):
        raise ValidatedPlanError("Validated plan content hash mismatch")
    if expected_state is not None:
        expected = {
            "policy_arm": str(expected_state["policy_arm"]),
            "season": str(expected_state["season"]),
            "gameweek": int(expected_state["gameweek"]),
            "previous_state_sha256": str(expected_state["content_sha256"]),
            "ruleset_id": str(expected_state["ruleset_id"]),
            "ruleset_sha256": str(expected_state["ruleset_sha256"]),
        }
        actual = {
            "policy_arm": plan["policy_arm"],
            "season": plan["season"],
            "gameweek": plan["gameweek"],
            "previous_state_sha256": plan["previous_state_sha256"],
            "ruleset_id": plan["ruleset"]["ruleset_id"],
            "ruleset_sha256": plan["ruleset"]["content_sha256"],
        }
        if actual != expected:
            raise ValidatedPlanError("Validated plan predecessor or rules binding mismatch")
    if rules is not None and plan["ruleset"]["ruleset_id"] != rules["meta"]["ruleset_id"]:
        raise ValidatedPlanError("Validated plan ruleset_id mismatch")
    if ruleset_sha256 is not None and plan["ruleset"]["content_sha256"] != ruleset_sha256:
        raise ValidatedPlanError("Validated plan ruleset hash mismatch")


def validate_and_freeze_plan(
    *,
    episode_id: str,
    policy_arm: str,
    state: Mapping[str, Any],
    candidate: Mapping[str, Any],
    decision_market: Mapping[str, Any] | Iterable[Mapping[str, Any]],
    active_chip: str | None,
    frozen_at: str,
    rules: Mapping[str, Any],
    ruleset_sha256: str,
) -> dict[str, Any]:
    """Recompute and freeze one candidate into the only action representation."""
    rules_dict = dict(rules)
    ruleset_id = str(rules_dict["meta"]["ruleset_id"])
    if str(state["policy_arm"]) != str(policy_arm):
        raise ValidatedPlanError("Policy arm does not match predecessor state")
    if str(state["ruleset_id"]) != ruleset_id or str(state["ruleset_sha256"]) != ruleset_sha256:
        raise ValidatedPlanError("Rules do not match predecessor state")
    freeze_time = _iso_datetime(frozen_at, "frozen_at")
    market = _market_by_id(decision_market)

    current_rows = [dict(row) for row in state["squad"]]
    owned: dict[str, dict[str, Any]] = {}
    for row in current_rows:
        player_id = str(row["player_id"])
        if player_id in owned:
            raise ValidatedPlanError("Predecessor squad player IDs must be unique")
        if player_id not in market:
            raise ValidatedPlanError(f"Owned player {player_id} missing from decision market")
        observed = market[player_id]
        if str(observed["position"]) != str(row["position"]):
            raise ValidatedPlanError(f"Owned player {player_id} position mismatch")
        row["player_id"] = player_id
        row["club_id"] = str(observed["club_id"])
        row["current_price"] = _price(observed["now_cost"])
        row["selling_price"] = selling_price(
            _price(row["purchase_price"]), row["current_price"], rules_dict
        )
        owned[player_id] = row

    raw_transfers = list(candidate.get("transfers", []))
    out_ids = [str(move["player_out_id"]) for move in raw_transfers]
    in_ids = [str(move["player_in_id"]) for move in raw_transfers]
    if len(out_ids) != len(set(out_ids)) or len(in_ids) != len(set(in_ids)):
        raise ValidatedPlanError("Transfer player IDs must be unique")
    bank = _price(state["bank"])
    audited: list[dict[str, Any]] = []
    for move, out_id, in_id in zip(raw_transfers, out_ids, in_ids):
        if out_id not in owned:
            raise ValidatedPlanError(f"Transfer-out player {out_id} is not owned")
        if in_id not in market:
            raise ValidatedPlanError(f"Transfer-in player {in_id} missing from decision market")
        if in_id in owned and in_id not in out_ids:
            raise ValidatedPlanError(f"Transfer-in player {in_id} is already owned")
        outgoing = owned[out_id]
        incoming = market[in_id]
        if str(outgoing["position"]) != str(incoming["position"]):
            raise ValidatedPlanError("Transfers must preserve player position")
        sale = _price(outgoing["selling_price"])
        purchase = _price(incoming["now_cost"])
        bank = _price(bank + sale - purchase)
        if bank < 0:
            raise ValidatedPlanError("Transfers exceed available bank")
        del owned[out_id]
        owned[in_id] = {
            "player_id": in_id,
            "position": str(incoming["position"]),
            "club_id": str(incoming["club_id"]),
            "purchase_price": purchase,
            "current_price": purchase,
            "selling_price": purchase,
        }
        audited.append(
            {
                "player_out_id": out_id,
                "player_in_id": in_id,
                "position": str(incoming["position"]),
                "selling_price": sale,
                "purchase_price": purchase,
            }
        )

    free_before = int(state["free_transfers"])
    hit = transfer_hit_cost(len(audited), free_before, rules_dict)
    if active_chip in {"wildcard_fh", "wildcard_sh", "free_hit_fh", "free_hit_sh"}:
        hit = 0
    if "bank_after" in candidate and _price(candidate["bank_after"]) != bank:
        raise ValidatedPlanError("Candidate bank_after does not match recomputed finance")
    if "hit_cost" in candidate and int(candidate["hit_cost"]) != hit:
        raise ValidatedPlanError("Candidate hit_cost does not match recomputed finance")

    squad_rows = list(owned.values())
    squad_validation = validate_squad(squad_rows, bank=bank, rules=rules_dict)
    squad_errors = list(squad_validation.errors)
    declared_exceptions = list(state.get("club_limit_exceptions", []))
    may_carry_exception = (
        not audited
        and bool(declared_exceptions)
        and declared_exceptions == club_limit_exceptions(squad_rows, rules_dict)
    )
    if may_carry_exception:
        squad_errors = [
            error
            for error in squad_errors
            if not error.startswith("squad.max_per_club")
        ]
    if squad_errors:
        raise ValidatedPlanError(
            "Illegal post-transfer squad: " + "; ".join(squad_errors)
        )
    squad_after = [
        {
            "player_id": str(row["player_id"]),
            "position": str(row["position"]),
            "club_id": str(row["club_id"]),
        }
        for row in sorted(squad_rows, key=lambda item: str(item["player_id"]))
    ]
    refs = {row["player_id"]: row for row in squad_after}

    lineup = dict(candidate.get("lineup", {}))
    xi_ids = [str(value) for value in lineup.get("starting_xi_ids", [])]
    bench_ids = [str(value) for value in lineup.get("bench_ids", [])]
    if set(xi_ids + bench_ids) != set(refs) or len(xi_ids + bench_ids) != len(refs):
        raise ValidatedPlanError("Illegal line-up: XI and bench must partition the squad")
    captain_id = str(lineup.get("captain_id", ""))
    vice_id = str(lineup.get("vice_captain_id", ""))
    lineup_validation = validate_lineup(
        [refs[player_id] for player_id in xi_ids],
        [refs[player_id] for player_id in bench_ids],
        captain_id=captain_id,
        vice_captain_id=vice_id,
        rules=rules_dict,
    )
    if not lineup_validation.ok:
        raise ValidatedPlanError("Illegal line-up: " + "; ".join(lineup_validation.errors))
    actual_formation = dict(Counter(refs[player_id]["position"] for player_id in xi_ids))
    formation = {position: int(lineup.get("formation", {}).get(position, -1)) for position in ("DEF", "MID", "FWD")}
    if formation != {position: actual_formation.get(position, 0) for position in formation}:
        raise ValidatedPlanError("Illegal line-up: formation does not match starting XI")

    chips = [] if active_chip is None else [str(active_chip)]
    chip_validation = validate_chips(chips, gameweek=int(state["gameweek"]), rules=rules_dict)
    if not chip_validation.ok:
        raise ValidatedPlanError("Illegal chip: " + "; ".join(chip_validation.errors))
    if active_chip is not None and str(active_chip) not in {str(chip) for chip in state["chips_available"]}:
        raise ValidatedPlanError("Illegal chip: chip is not available in predecessor state")

    plan: dict[str, Any] = {
        "schema_version": "1.0",
        "plan_id": f"validated-plan:{episode_id}:{policy_arm}",
        "episode_id": str(episode_id),
        "policy_arm": str(policy_arm),
        "season": str(state["season"]),
        "gameweek": int(state["gameweek"]),
        "previous_state_sha256": str(state["content_sha256"]),
        "ruleset": {"ruleset_id": ruleset_id, "content_sha256": str(ruleset_sha256)},
        "transfers": audited,
        "squad_after": squad_after,
        "lineup": {
            "formation": formation,
            "starting_xi_ids": xi_ids,
            "bench_ids": bench_ids,
            "captain_id": captain_id,
            "vice_captain_id": vice_id,
        },
        "active_chip": active_chip,
        "finance": {
            "bank_before": _price(state["bank"]),
            "bank_after": bank,
            "free_transfers_before": free_before,
            "transfer_count": len(audited),
            "hit_cost": hit,
        },
        "validation": {
            "status": "passed",
            "checks": list(_VALIDATION_CHECKS),
            "content_sha256": "",
        },
        "frozen_at": freeze_time,
    }
    plan["validation"]["content_sha256"] = fingerprint(_validation_payload(plan))
    plan["content_sha256"] = validated_plan_hash(plan)
    validate_plan_integrity(
        plan,
        expected_state=state,
        rules=rules_dict,
        ruleset_sha256=ruleset_sha256,
    )
    return plan
