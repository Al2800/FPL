"""Deterministic, isolated longitudinal state for benchmark policy arms."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator, FormatChecker

from src.orchestration.validated_plan import (
    ValidatedPlanError,
    validate_plan_integrity,
)
from src.scoring.rules_loader import assert_ruleset_activatable
from src.scoring.validator import (
    club_limit_exceptions,
    selling_price,
    validate_squad,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_SCHEMA_PATH = REPO_ROOT / "control/schemas/benchmark/policy-state.json"
TRANSITION_SCHEMA_PATH = (
    REPO_ROOT / "control/schemas/benchmark/state-transition.json"
)
POLICY_ARMS = (
    "naive_baseline",
    "forecast_optimizer",
    "evidence_agent",
    "evidence_challenger",
    "human_decision",
)


class PolicyStateError(ValueError):
    """Raised when a policy-state boundary cannot be advanced safely."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _content_hash(value: Any, *, omit: str = "content_sha256") -> str:
    projection = {key: item for key, item in value.items() if key != omit}
    return hashlib.sha256(_canonical_bytes(projection)).hexdigest()


def state_hash(state: Mapping[str, Any]) -> str:
    """Hash every state field except its self-referential content hash."""

    return _content_hash(dict(state))


def transition_hash(transition: Mapping[str, Any]) -> str:
    """Hash every transition field except its self-referential content hash."""

    return _content_hash(dict(transition))


def _schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_schema(value: dict[str, Any], path: Path, label: str) -> None:
    try:
        Draft202012Validator(
            _schema(path), format_checker=FormatChecker()
        ).validate(value)
    except Exception as exc:  # jsonschema emits several concrete subclasses
        raise PolicyStateError(f"Invalid {label} contract: {exc}") from exc


def _player_key(player: Mapping[str, Any]) -> tuple[int, int | str]:
    player_id = str(player["player_id"])
    try:
        return (0, int(player_id))
    except ValueError:
        return (1, player_id)


def _round_price(value: float) -> float:
    return round(float(value) + 1e-9, 1)

def _require_price_step(value: Any, label: str) -> float:
    parsed = float(value)
    rounded = _round_price(parsed)
    if abs(parsed - rounded) > 1e-9:
        raise PolicyStateError(f"{label} must use £0.1m increments")
    return rounded



def _chip_order(profile: Mapping[str, Any]) -> list[str]:
    return [chip for chip_set in profile["chip_sets"] for chip in chip_set["chips"]]


def _ordered_chips(
    chips: Iterable[str], profile: Mapping[str, Any]
) -> list[str]:
    values = [str(chip) for chip in chips]
    if len(set(values)) != len(values):
        raise PolicyStateError("chips_available contains duplicates")
    configured = _chip_order(profile)
    unknown = sorted(set(values) - set(configured))
    if unknown:
        raise PolicyStateError(f"Unknown chips: {unknown}")
    return [chip for chip in configured if chip in values]


def _rules_identity(rules: Mapping[str, Any], ruleset_sha256: str) -> tuple[str, str]:
    meta = rules.get("meta", {})
    ruleset_id = str(meta.get("ruleset_id", ""))
    if not ruleset_id:
        raise PolicyStateError("Active ruleset has no ruleset_id")
    if len(ruleset_sha256) != 64 or any(
        char not in "0123456789abcdef" for char in ruleset_sha256
    ):
        raise PolicyStateError("ruleset_sha256 must be a lower-case SHA-256")
    return ruleset_id, ruleset_sha256



def _activation_profile(
    rules: Mapping[str, Any],
    ruleset_sha256: str,
    compatibility_policy: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    mode = (
        "historical_replay"
        if rules.get("meta", {}).get("replay_status") == "validated"
        else "live"
    )
    return assert_ruleset_activatable(
        rules,
        ruleset_sha256,
        mode=mode,
        compatibility_policy=compatibility_policy,
    )["transition_profile"]

def _hard_squad_errors(squad: list[dict[str, Any]], rules: Mapping[str, Any]) -> list[str]:
    result = validate_squad(squad, rules=dict(rules))
    return [
        error
        for error in result.errors
        if error.startswith("squad.size")
        or error.startswith("squad.player_unique")
        or error.startswith("squad.position_counts")
        or error.startswith("squad.max_per_club")
    ]


def _normalise_squad(
    rows: Iterable[Mapping[str, Any]],
    rules: Mapping[str, Any],
    *,
    allow_club_limit_exception: bool = False,
) -> list[dict[str, Any]]:
    squad: list[dict[str, Any]] = []
    for source in rows:
        purchase = _require_price_step(source["purchase_price"], "purchase_price")
        current = _require_price_step(source["current_price"], "current_price")
        expected_selling = selling_price(purchase, current, dict(rules))
        supplied_selling = _require_price_step(source["selling_price"], "selling_price")
        if supplied_selling != expected_selling:
            raise PolicyStateError(
                "selling price does not match this arm's purchase history for "
                f"player {source['player_id']}"
            )
        squad.append(
            {
                "player_id": str(source["player_id"]),
                "position": str(source["position"]),
                "club_id": str(source["club_id"]),
                "purchase_price": purchase,
                "current_price": current,
                "selling_price": supplied_selling,
            }
        )
    squad.sort(key=_player_key)
    errors = _hard_squad_errors(squad, rules)
    if allow_club_limit_exception:
        errors = [
            error
            for error in errors
            if not error.startswith("squad.max_per_club")
        ]
    if errors:
        raise PolicyStateError(f"Invalid squad: {errors}")
    return squad


def _validate_state(
    state: dict[str, Any],
    rules: Mapping[str, Any] | None = None,
    profile: Mapping[str, Any] | None = None,
) -> None:
    _validate_schema(state, STATE_SCHEMA_PATH, "policy state")
    if state_hash(state) != state["content_sha256"]:
        raise PolicyStateError("Policy state content hash mismatch")
    ids = [player["player_id"] for player in state["squad"]]
    if len(set(ids)) != len(ids):
        raise PolicyStateError("Policy state squad player IDs must be unique")
    if rules is not None:
        declared_exceptions = list(state.get("club_limit_exceptions", []))
        normalised = _normalise_squad(
            state["squad"],
            rules,
            allow_club_limit_exception=bool(declared_exceptions),
        )
        actual_exceptions = club_limit_exceptions(normalised, dict(rules))
        if declared_exceptions != actual_exceptions:
            raise PolicyStateError(
                "Policy state club-limit exception does not match its squad"
            )
    if profile is not None:
        terminal = int(profile["terminal_state_gameweek"])
        regular = int(profile["regular_gameweeks"])
        gameweek = int(state["gameweek"])
        if state["status"] == "season_complete" and gameweek != terminal:
            raise PolicyStateError("Season-complete state is not at the configured terminal")
        if state["status"] == "active" and not 1 <= gameweek <= regular:
            raise PolicyStateError("Active state is outside configured regular Gameweeks")
        if int(state["free_transfers"]) > int(profile["max_banked"]):
            raise PolicyStateError("Policy state exceeds configured transfer bank")
        configured_chips = set(_chip_order(profile))
        recorded_chips = set(state["chips_available"]) | {
            item["chip"] for item in state["chip_history"]
        }
        unknown_chips = sorted(recorded_chips - configured_chips)
        if unknown_chips:
            raise PolicyStateError(f"Policy state contains unknown chips: {unknown_chips}")


def _validate_transition(transition: dict[str, Any]) -> None:
    _validate_schema(transition, TRANSITION_SCHEMA_PATH, "state transition")
    if transition_hash(transition) != transition["content_sha256"]:
        raise PolicyStateError("State transition content hash mismatch")


def initialise_policy_states(
    seed: Mapping[str, Any],
    *,
    policy_arms: Iterable[str] = POLICY_ARMS,
    rules: Mapping[str, Any],
    ruleset_sha256: str,
    compatibility_policy: Iterable[Mapping[str, Any]] = (),
) -> dict[str, dict[str, Any]]:
    """Clone one controlled Gameweek-1 seed into independent arm states."""

    ruleset_id, ruleset_hash = _rules_identity(rules, ruleset_sha256)
    profile = _activation_profile(rules, ruleset_hash, compatibility_policy)
    if str(seed.get("season")) != str(rules["meta"].get("season")):
        raise PolicyStateError("Seed season does not match active ruleset")
    if int(seed.get("gameweek", 0)) != 1:
        raise PolicyStateError("Controlled initial state must begin at Gameweek 1")
    arms = [str(arm) for arm in policy_arms]
    if len(set(arms)) != len(arms) or not arms:
        raise PolicyStateError("Policy arms must be non-empty and unique")
    unknown_arms = sorted(set(arms) - set(POLICY_ARMS))
    if unknown_arms:
        raise PolicyStateError(f"Unknown policy arms: {unknown_arms}")
    if set(arms) != set(POLICY_ARMS):
        raise PolicyStateError("Benchmark initialization requires every policy arm")

    squad = _normalise_squad(seed["squad"], rules)
    if any(player["purchase_price"] != player["current_price"] for player in squad):
        raise PolicyStateError("Gameweek 1 seed prices must equal purchase prices")
    bank = _require_price_step(seed["bank"], "bank")
    if bank < 0:
        raise PolicyStateError("Initial bank cannot be negative")
    free_transfers = int(seed["free_transfers"])
    max_banked = int(profile["max_banked"])
    if free_transfers < 0 or free_transfers > max_banked:
        raise PolicyStateError("Initial free transfers outside active rules")
    chips = _ordered_chips(seed["chips_available"], profile)
    if chips != _chip_order(profile):
        raise PolicyStateError("Gameweek 1 seed must contain every configured chip")
    initial_budget = float(profile["initial_budget"])
    initial_value = sum(player["purchase_price"] for player in squad) + bank
    if abs(initial_value - initial_budget) > 1e-9:
        raise PolicyStateError(
            "Gameweek 1 squad purchase prices plus bank must equal the initial budget"
        )
    seed_projection = {
        "seed_id": str(seed["seed_id"]),
        "season": str(seed["season"]),
        "gameweek": 1,
        "bank": bank,
        "free_transfers": free_transfers,
        "chips_available": chips,
        "squad": squad,
        "ruleset_id": ruleset_id,
        "ruleset_sha256": ruleset_hash,
    }
    seed_hash = hashlib.sha256(_canonical_bytes(seed_projection)).hexdigest()

    states: dict[str, dict[str, Any]] = {}
    for arm in arms:
        state = {
            "schema_version": "1.0",
            "state_id": f"policy-state:{seed['seed_id']}:{arm}:gw01:{seed_hash[:12]}",
            "status": "active",
            "origin": {
                "type": "controlled_shared_seed",
                "seed_id": str(seed["seed_id"]),
                "seed_sha256": seed_hash,
            },
            "policy_arm": arm,
            "season": str(seed["season"]),
            "gameweek": 1,
            "ruleset_id": ruleset_id,
            "ruleset_sha256": ruleset_hash,
            "previous_state_sha256": None,
            "transition_id": None,
            "squad": deepcopy(squad),
            "bank": bank,
            "free_transfers": free_transfers,
            "chips_available": list(chips),
            "chip_history": [],
            "cumulative_points": 0,
        }
        state["content_sha256"] = state_hash(state)
        _validate_state(state, rules, profile)
        states[arm] = state
    return states


def _parse_timestamp(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise PolicyStateError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise PolicyStateError(f"{field} must be timezone-aware")
    return parsed


def _market_index(market: Mapping[str, Any] | Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    values = market.values() if isinstance(market, Mapping) else market
    indexed: dict[str, dict[str, Any]] = {}
    for source in values:
        row = dict(source)
        player_id = str(row["player_id"])
        if player_id in indexed:
            raise PolicyStateError(f"Duplicate market player: {player_id}")
        indexed[player_id] = row
    return indexed


def _validate_chip(
    chip: str | None,
    gameweek: int,
    state: Mapping[str, Any],
    profile: Mapping[str, Any],
) -> str | None:
    if chip is None:
        return None
    chip = str(chip)
    if chip not in state["chips_available"]:
        raise PolicyStateError(f"Chip {chip!r} is not available to this policy arm")
    active_set = next(
        (row for row in profile["chip_sets"] if chip in row["chips"]), None
    )
    if active_set is None or not (
        active_set["start_gameweek"] <= gameweek <= active_set["end_gameweek"]
    ):
        raise PolicyStateError(f"Chip {chip!r} is unavailable in Gameweek {gameweek}")
    base = chip.rsplit("_", 1)[0]
    boundaries = profile["chip_boundary_restrictions"]
    if base == "wildcard" and gameweek in boundaries["wildcard_unavailable_gameweeks"]:
        raise PolicyStateError(f"{base} cannot be played in Gameweek {gameweek}")
    if base == "free_hit" and gameweek in boundaries["free_hit_unavailable_gameweeks"]:
        raise PolicyStateError(f"{base} cannot be played in Gameweek {gameweek}")
    adjacent = boundaries["free_hit_cannot_span_adjacent_gameweeks"]
    if base == "free_hit" and gameweek == adjacent[1]:
        if any(
            item["chip"].startswith("free_hit_")
            and item["gameweek"] == adjacent[0]
            for item in state["chip_history"]
        ):
            raise PolicyStateError(
                f"Free Hit cannot be played in both Gameweek {adjacent[0]} and {adjacent[1]}"
            )
    return chip


def _next_free_transfers(
    *,
    available: int,
    used: int,
    chip_base: str | None,
    next_gameweek: int,
    profile: Mapping[str, Any],
) -> int:
    unlimited = chip_base in {"wildcard", "free_hit"}
    if unlimited and profile["retain_banked_on_wildcard_free_hit"]:
        result = available
    else:
        result = min(
            int(profile["max_banked"]),
            max(0, available - used)
            + int(profile["free_transfers_per_gameweek"]),
        )
    for event in profile["exceptional_transfer_events"]:
        if (
            event["kind"] == "free_transfer_top_up"
            and next_gameweek == event["gameweek"]
        ):
            result = int(event["top_up_to"])
    return result


def _refresh_squad(
    squad: Iterable[Mapping[str, Any]],
    market: Mapping[str, dict[str, Any]],
    rules: Mapping[str, Any],
) -> list[dict[str, Any]]:
    refreshed: list[dict[str, Any]] = []
    for player in squad:
        player_id = str(player["player_id"])
        if player_id not in market:
            raise PolicyStateError(f"Next market missing owned player {player_id}")
        quote = market[player_id]
        if str(quote["position"]) != player["position"]:
            raise PolicyStateError(f"Position changed for owned player {player_id}")
        purchase = _require_price_step(player["purchase_price"], "purchase_price")
        current = _require_price_step(quote["now_cost"], "now_cost")
        refreshed.append(
            {
                "player_id": player_id,
                "position": player["position"],
                "club_id": str(quote["club_id"]),
                "purchase_price": purchase,
                "current_price": current,
                "selling_price": selling_price(purchase, current, dict(rules)),
            }
        )
    return _normalise_squad(
        refreshed,
        rules,
        allow_club_limit_exception=True,
    )


def transition_policy_state(
    state: Mapping[str, Any],
    plan: Mapping[str, Any],
    outcome: Mapping[str, Any],
    *,
    decision_market: Mapping[str, Any] | Iterable[Mapping[str, Any]],
    next_market: Mapping[str, Any] | Iterable[Mapping[str, Any]],
    rules: Mapping[str, Any],
    ruleset_sha256: str,
    compatibility_policy: Iterable[Mapping[str, Any]] = (),
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return an audited successor without mutating any supplied value."""

    ruleset_id, ruleset_hash = _rules_identity(rules, ruleset_sha256)
    profile = _activation_profile(rules, ruleset_hash, compatibility_policy)
    current = deepcopy(dict(state))
    _validate_state(current, rules, profile)
    if current["status"] == "season_complete":
        raise PolicyStateError("Cannot transition a season-complete policy state")
    try:
        validate_plan_integrity(
            plan,
            expected_state=current,
            rules=rules,
            ruleset_sha256=ruleset_hash,
        )
    except ValidatedPlanError as exc:
        raise PolicyStateError(f"Validated plan integrity failed: {exc}") from exc
    if current["ruleset_id"] != ruleset_id or current["ruleset_sha256"] != ruleset_hash:
        raise PolicyStateError("Policy state ruleset does not match active rules")
    if str(plan.get("policy_arm")) != current["policy_arm"]:
        raise PolicyStateError("Plan policy arm does not own this state")
    if int(plan.get("gameweek", 0)) != current["gameweek"]:
        raise PolicyStateError("Plan Gameweek does not match policy state")
    if plan.get("previous_state_sha256") != current["content_sha256"]:
        raise PolicyStateError("Plan predecessor does not match current state")
    episode_id = str(plan.get("episode_id", ""))
    if len(episode_id) < 3:
        raise PolicyStateError("Decision requires an episode_id")
    outcome_id = str(outcome.get("outcome_id", ""))
    if len(outcome_id) < 3:
        raise PolicyStateError("Revealed outcome requires an outcome_id")
    proposal_hash = str(plan["content_sha256"])
    frozen_at = _parse_timestamp(plan.get("frozen_at"), "frozen_at")
    revealed_at = _parse_timestamp(outcome.get("revealed_at"), "revealed_at")
    if revealed_at <= frozen_at:
        raise PolicyStateError("Outcome must be revealed after proposal freeze")
    if isinstance(outcome.get("gross_points"), bool) or not isinstance(
        outcome.get("gross_points"), int
    ):
        raise PolicyStateError("gross_points must be an integer")
    if outcome.get("plan_sha256") not in (None, proposal_hash):
        raise PolicyStateError("Outcome does not belong to validated plan")

    gameweek = int(current["gameweek"])
    active_chip = _validate_chip(plan.get("active_chip"), gameweek, current, profile)
    chip_base = active_chip.rsplit("_", 1)[0] if active_chip else None
    decision_prices = _market_index(decision_market)
    future_prices = _market_index(next_market)
    owned = {player["player_id"]: deepcopy(player) for player in current["squad"]}
    for player_id, player in owned.items():
        if player_id not in decision_prices:
            raise PolicyStateError(f"Decision market missing owned player {player_id}")
        quote = decision_prices[player_id]
        if str(quote["position"]) != player["position"]:
            raise PolicyStateError(f"Decision market position mismatch for {player_id}")
        if str(quote["club_id"]) != player["club_id"]:
            raise PolicyStateError(f"Decision market club mismatch for {player_id}")
        if _require_price_step(quote["now_cost"], "now_cost") != player["current_price"]:
            raise PolicyStateError(f"Decision market is stale for owned player {player_id}")

    raw_moves = [dict(move) for move in plan.get("transfers", [])]
    out_ids = [str(move.get("player_out_id")) for move in raw_moves]
    in_ids = [str(move.get("player_in_id")) for move in raw_moves]
    if len(set(out_ids)) != len(out_ids) or len(set(in_ids)) != len(in_ids):
        raise PolicyStateError("Transfer player IDs must be unique")
    if set(in_ids) & set(owned):
        raise PolicyStateError("Incoming player is already owned")

    working = deepcopy(owned)
    bank = float(current["bank"])
    audited_moves: list[dict[str, Any]] = []
    for out_id, in_id in zip(out_ids, in_ids, strict=True):
        if out_id not in owned:
            raise PolicyStateError(f"Outgoing player {out_id} is not owned")
        if in_id not in decision_prices:
            raise PolicyStateError(f"Decision market missing incoming player {in_id}")
        outgoing = owned[out_id]
        incoming = decision_prices[in_id]
        if outgoing["position"] != str(incoming["position"]):
            raise PolicyStateError("Transfers must exchange players in the same position")
        sale = selling_price(
            float(outgoing["purchase_price"]),
            float(outgoing["current_price"]),
            dict(rules),
        )
        purchase = _require_price_step(incoming["now_cost"], "now_cost")
        bank += sale - purchase
        del working[out_id]
        working[in_id] = {
            "player_id": in_id,
            "position": outgoing["position"],
            "club_id": str(incoming["club_id"]),
            "purchase_price": purchase,
            "current_price": purchase,
            "selling_price": purchase,
        }
        audited_moves.append(
            {
                "player_out_id": out_id,
                "player_in_id": in_id,
                "position": outgoing["position"],
                "selling_price": sale,
                "purchase_price": purchase,
            }
        )
    bank = _round_price(bank)
    if bank < 0:
        raise PolicyStateError("Transfer set has insufficient bank")
    candidate_squad = _normalise_squad(
        working.values(),
        rules,
        allow_club_limit_exception=(
            not raw_moves and bool(current.get("club_limit_exceptions"))
        ),
    )

    transfer_count = len(audited_moves)
    hit_per_transfer = int(profile["hit_cost"])
    unlimited = chip_base in {"wildcard", "free_hit"}
    hit_cost = 0 if unlimited else max(
        0, transfer_count - int(current["free_transfers"])
    ) * hit_per_transfer
    if audited_moves != list(plan["transfers"]):
        raise PolicyStateError("Plan transfer audit differs from transition recomputation")
    expected_finance = {
        "bank_before": _round_price(float(current["bank"])),
        "bank_after": bank,
        "free_transfers_before": int(current["free_transfers"]),
        "transfer_count": transfer_count,
        "hit_cost": hit_cost,
    }
    if dict(plan["finance"]) != expected_finance:
        raise PolicyStateError("Plan finance differs from transition recomputation")

    next_gameweek = gameweek + 1
    next_free_transfers = _next_free_transfers(
        available=int(current["free_transfers"]),
        used=transfer_count,
        chip_base=chip_base,
        next_gameweek=next_gameweek,
        profile=profile,
    )

    temporary_hash = None
    if chip_base == "free_hit":
        temporary_hash = hashlib.sha256(_canonical_bytes(candidate_squad)).hexdigest()
        persistent_squad = list(owned.values())
        next_bank = float(current["bank"])
    else:
        persistent_squad = candidate_squad
        next_bank = bank
    refreshed_squad = _refresh_squad(persistent_squad, future_prices, rules)
    next_club_limit_exceptions = club_limit_exceptions(
        refreshed_squad, dict(rules)
    )

    chips = list(current["chips_available"])
    history = deepcopy(current["chip_history"])
    if active_chip is not None:
        chips.remove(active_chip)
        history.append({"chip": active_chip, "gameweek": gameweek})
    expired = {
        chip
        for chip_set in profile["chip_sets"]
        if next_gameweek > chip_set["end_gameweek"]
        for chip in chip_set["chips"]
    }
    chips = _ordered_chips(
        (chip for chip in chips if chip not in expired), profile
    )

    transition_id = (
        f"state-transition:{current['season']}:gw{gameweek:02d}:"
        f"{current['policy_arm']}:{proposal_hash[:12]}"
    )
    gross_points = int(outcome["gross_points"])
    net_points = gross_points - hit_cost
    successor = {
        "schema_version": "1.0",
        "state_id": (
            f"policy-state:{current['origin']['seed_id']}:{current['policy_arm']}:"
            f"gw{next_gameweek:02d}:{proposal_hash[:12]}"
        ),
        "status": (
            "season_complete"
            if next_gameweek == profile["terminal_state_gameweek"]
            else "active"
        ),
        "origin": deepcopy(current["origin"]),
        "policy_arm": current["policy_arm"],
        "season": current["season"],
        "gameweek": next_gameweek,
        "ruleset_id": ruleset_id,
        "ruleset_sha256": ruleset_hash,
        "previous_state_sha256": current["content_sha256"],
        "transition_id": transition_id,
        "squad": refreshed_squad,
        "bank": _round_price(next_bank),
        "free_transfers": next_free_transfers,
        "chips_available": chips,
        "chip_history": history,
        "cumulative_points": int(current["cumulative_points"]) + net_points,
    }
    if next_club_limit_exceptions:
        successor["club_limit_exceptions"] = next_club_limit_exceptions
    successor["content_sha256"] = state_hash(successor)
    _validate_state(successor, rules, profile)

    transition = {
        "schema_version": "1.0",
        "transition_id": transition_id,
        "policy_arm": current["policy_arm"],
        "season": current["season"],
        "gameweek_from": gameweek,
        "gameweek_to": next_gameweek,
        "episode_id": episode_id,
        "ruleset_id": ruleset_id,
        "ruleset_sha256": ruleset_hash,
        "previous_state_sha256": current["content_sha256"],
        "proposal_sha256": proposal_hash,
        "proposal_frozen_at": str(plan["frozen_at"]),
        "outcome_id": outcome_id,
        "outcome_revealed_at": str(outcome["revealed_at"]),
        "moves": audited_moves,
        "active_chip": active_chip,
        "temporary_squad_sha256": temporary_hash,
        "hit_cost": hit_cost,
        "gross_points": gross_points,
        "net_points": net_points,
        "next_state_sha256": successor["content_sha256"],
    }
    if next_club_limit_exceptions:
        transition["next_club_limit_exceptions"] = next_club_limit_exceptions
    transition["content_sha256"] = transition_hash(transition)
    _validate_transition(transition)
    return successor, transition


class PolicyStateLedger:
    """In-memory immutable histories with strict predecessor and arm isolation."""

    def __init__(self, initial_states: Mapping[str, Mapping[str, Any]]) -> None:
        if not initial_states:
            raise PolicyStateError("PolicyStateLedger requires initial states")
        self._histories: dict[str, list[dict[str, Any]]] = {}
        for arm, source in initial_states.items():
            state = deepcopy(dict(source))
            if str(arm) != state.get("policy_arm"):
                raise PolicyStateError("Initial-state policy arm key mismatch")
            _validate_state(state)
            if state["gameweek"] != 1 or state["previous_state_sha256"] is not None:
                raise PolicyStateError("Ledger histories must start from an initial state")
            self._histories[str(arm)] = [state]

    def current(self, policy_arm: str) -> dict[str, Any]:
        if policy_arm not in self._histories:
            raise PolicyStateError(f"Unknown policy arm: {policy_arm}")
        return deepcopy(self._histories[policy_arm][-1])

    def history(self, policy_arm: str) -> list[dict[str, Any]]:
        if policy_arm not in self._histories:
            raise PolicyStateError(f"Unknown policy arm: {policy_arm}")
        return deepcopy(self._histories[policy_arm])

    def append(
        self, transition: Mapping[str, Any], next_state: Mapping[str, Any]
    ) -> None:
        record = deepcopy(dict(transition))
        successor = deepcopy(dict(next_state))
        arm = str(record.get("policy_arm"))
        if arm not in self._histories:
            raise PolicyStateError(f"Unknown policy arm: {arm}")
        if successor.get("policy_arm") != arm:
            raise PolicyStateError("Next-state policy arm differs from transition policy arm")
        current = self._histories[arm][-1]
        if record.get("previous_state_sha256") != current["content_sha256"]:
            raise PolicyStateError("Transition predecessor is not the arm's current state")
        if successor.get("previous_state_sha256") != current["content_sha256"]:
            raise PolicyStateError("Next-state predecessor is not the arm's current state")
        if successor.get("gameweek") != current["gameweek"] + 1:
            raise PolicyStateError("Policy state history must advance one Gameweek")
        if successor.get("transition_id") != record.get("transition_id"):
            raise PolicyStateError("Next state references a different transition")
        if record.get("next_state_sha256") != successor.get("content_sha256"):
            raise PolicyStateError("Transition successor hash mismatch")
        _validate_transition(record)
        _validate_state(successor)
        self._histories[arm].append(successor)
