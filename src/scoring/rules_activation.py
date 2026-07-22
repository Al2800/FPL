"""Compile evidence-oriented FPL catalogues into safe operational profiles."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Iterable, Mapping



SHA256_CHARS = frozenset("0123456789abcdef")
TRANSITION_RULE_IDS = (
    "squad.initial_budget",
    "squad.size",
    "squad.position_counts",
    "squad.max_per_club",
    "transfers.free_per_gameweek",
    "transfers.max_banked",
    "transfers.hit_cost",
    "transfers.afcon_exceptional_topup",
    "transfers.wildcard_free_hit_retain_banked",
    "prices.selling_half_profit",
    "chips.sets_per_season",
    "chips.first_half_expiry",
    "chips.one_per_gameweek",
    "chips.boundary_restrictions",
)
RULE_ALIASES = {
    "chips.boundary_restrictions": (
        "chips.boundary_restrictions",
        "chips.gw1_and_boundary_restrictions",
    )
}


def _index_rules(rules: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for key, value in rules.items():
        if key in {"meta", "launch_verification_checklist"}:
            continue
        if isinstance(value, list):
            for rule in value:
                rule_id = rule["rule_id"]
                if rule_id in indexed:
                    raise ValueError(f"Duplicate rule_id: {rule_id}")
                indexed[rule_id] = rule
    return indexed


class RulesetActivationError(ValueError):
    """Raised before unsafe or unresolved rules can create longitudinal state."""


def _blocker(code: str, rule_id: str | None, message: str) -> dict[str, Any]:
    return {"code": code, "rule_id": rule_id, "message": message}


def _canonical_rule(
    indexed: Mapping[str, Mapping[str, Any]], rule_id: str
) -> Mapping[str, Any] | None:
    for candidate in RULE_ALIASES.get(rule_id, (rule_id,)):
        if candidate in indexed:
            return indexed[candidate]
    return None


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and not (set(value) - SHA256_CHARS)
    )


def _integer(value: Any, *, minimum: int = 0) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        return None
    return value


def _number(value: Any, *, positive: bool = False) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    if positive and result <= 0:
        return None
    return result


def _integer_list(value: Any) -> list[int] | None:
    if not isinstance(value, list):
        return None
    result = [_integer(item, minimum=1) for item in value]
    if any(item is None for item in result) or len(set(result)) != len(result):
        return None
    return [int(item) for item in result]


def _normalise_compatibility_policy(
    values: Iterable[Mapping[str, Any]], blockers: list[dict[str, Any]]
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    normalised: list[dict[str, str]] = []
    indexed: dict[str, dict[str, str]] = {}
    for raw in values:
        row = dict(raw)
        rule_id = str(row.get("rule_id", ""))
        status = str(row.get("status", ""))
        rationale = str(row.get("rationale", ""))
        approved_by = str(row.get("approved_by", ""))
        approved_at = str(row.get("approved_at", ""))
        valid_time = False
        try:
            valid_time = datetime.fromisoformat(
                approved_at.replace("Z", "+00:00")
            ).tzinfo is not None
        except ValueError:
            pass
        if (
            rule_id not in TRANSITION_RULE_IDS
            or status != "inherited"
            or len(rationale) < 10
            or not approved_by
            or not valid_time
            or rule_id in indexed
        ):
            blockers.append(
                _blocker(
                    "invalid_compatibility_policy",
                    rule_id or None,
                    "Compatibility approvals require a unique consumed rule, inherited "
                    "status, rationale, approver and timezone-aware approval time",
                )
            )
            continue
        clean = {
            "rule_id": rule_id,
            "status": "inherited",
            "rationale": rationale,
            "approved_by": approved_by,
            "approved_at": approved_at,
        }
        normalised.append(clean)
        indexed[rule_id] = clean
    normalised.sort(key=lambda item: item["rule_id"])
    return normalised, indexed


def _compile_profile(
    indexed: Mapping[str, Mapping[str, Any]], blockers: list[dict[str, Any]]
) -> dict[str, Any] | None:
    values = {
        rule_id: rule.get("value")
        for rule_id in TRANSITION_RULE_IDS
        if (rule := _canonical_rule(indexed, rule_id)) is not None
    }

    def malformed(rule_id: str, expectation: str) -> None:
        blockers.append(
            _blocker(
                "malformed_rule_value", rule_id, f"{rule_id} must be {expectation}"
            )
        )

    initial_budget = _number(values.get("squad.initial_budget"), positive=True)
    if initial_budget is None:
        malformed("squad.initial_budget", "a positive number")
    squad_size = _integer(values.get("squad.size"), minimum=1)
    if squad_size is None:
        malformed("squad.size", "a positive integer")
    position_counts = values.get("squad.position_counts")
    clean_counts = None
    if isinstance(position_counts, dict) and set(position_counts) == {
        "GKP",
        "DEF",
        "MID",
        "FWD",
    }:
        candidate = {
            key: _integer(position_counts[key], minimum=0)
            for key in ("GKP", "DEF", "MID", "FWD")
        }
        if all(value is not None for value in candidate.values()):
            clean_counts = {key: int(value) for key, value in candidate.items()}
    if clean_counts is None:
        malformed("squad.position_counts", "integer GKP/DEF/MID/FWD counts")
    max_per_club = _integer(values.get("squad.max_per_club"), minimum=1)
    if max_per_club is None:
        malformed("squad.max_per_club", "a positive integer")

    free_per = _integer(values.get("transfers.free_per_gameweek"), minimum=0)
    if free_per is None:
        malformed("transfers.free_per_gameweek", "a non-negative integer")
    max_banked = _integer(values.get("transfers.max_banked"), minimum=1)
    if max_banked is None:
        malformed("transfers.max_banked", "a positive integer")
    hit_cost = _integer(values.get("transfers.hit_cost"), minimum=0)
    if hit_cost is None:
        malformed("transfers.hit_cost", "a non-negative integer")
    retain = values.get("transfers.wildcard_free_hit_retain_banked")
    if not isinstance(retain, bool):
        malformed("transfers.wildcard_free_hit_retain_banked", "a Boolean")

    exceptional_events = []
    afcon = values.get("transfers.afcon_exceptional_topup")
    if afcon is False:
        pass
    elif isinstance(afcon, dict) and set(afcon) == {"gameweek", "top_up_to"}:
        event_gameweek = _integer(afcon.get("gameweek"), minimum=1)
        event_top_up = _integer(afcon.get("top_up_to"), minimum=1)
        if event_gameweek is None or event_top_up is None:
            exceptional_events = None
        else:
            exceptional_events = [
                {
                    "kind": "free_transfer_top_up",
                    "gameweek": event_gameweek,
                    "top_up_to": event_top_up,
                }
            ]
    else:
        exceptional_events = None
    if exceptional_events is None:
        malformed(
            "transfers.afcon_exceptional_topup",
            "false or an object containing positive gameweek and top_up_to integers",
        )

    selling = values.get("prices.selling_half_profit")
    rise_share = None
    round_down = None
    if isinstance(selling, dict):
        rise_share = _number(selling.get("rise_share_kept"))
        round_down = _number(selling.get("round_down_to"), positive=True)
        if rise_share is not None and not 0 <= rise_share <= 1:
            rise_share = None
    if rise_share is None or round_down is None:
        malformed(
            "prices.selling_half_profit",
            "rise_share_kept from zero to one and a positive round_down_to",
        )

    chip_rule = values.get("chips.sets_per_season")
    sets = None
    chip_bases = None
    if isinstance(chip_rule, dict):
        sets = _integer(chip_rule.get("sets"), minimum=1)
        raw_chips = chip_rule.get("chips_per_set")
        if (
            isinstance(raw_chips, list)
            and raw_chips
            and all(isinstance(item, str) and item for item in raw_chips)
            and len(set(raw_chips)) == len(raw_chips)
        ):
            chip_bases = list(raw_chips)
    if sets != 2 or chip_bases is None:
        malformed("chips.sets_per_season", "exactly two sets and unique chip names")

    expiry_rule = values.get("chips.first_half_expiry")
    expiry = None
    if isinstance(expiry_rule, dict):
        expiry = _integer(expiry_rule.get("expires_at_gameweek"), minimum=1)
    if expiry is None:
        malformed(
            "chips.first_half_expiry",
            "an object with a positive expires_at_gameweek integer",
        )
    one_chip = values.get("chips.one_per_gameweek")
    if not isinstance(one_chip, bool):
        malformed("chips.one_per_gameweek", "a Boolean")

    boundary = values.get("chips.boundary_restrictions")
    clean_boundary = None
    if isinstance(boundary, dict):
        wildcard = _integer_list(boundary.get("wildcard_unavailable_gameweeks"))
        free_hit = _integer_list(boundary.get("free_hit_unavailable_gameweeks"))
        adjacent = _integer_list(
            boundary.get("free_hit_cannot_span_adjacent_gameweeks")
        )
        if wildcard is not None and free_hit is not None and adjacent and len(adjacent) == 2:
            clean_boundary = {
                "wildcard_unavailable_gameweeks": wildcard,
                "free_hit_unavailable_gameweeks": free_hit,
                "free_hit_cannot_span_adjacent_gameweeks": adjacent,
            }
    if clean_boundary is None:
        malformed(
            "chips.boundary_restrictions",
            "structured Wildcard, Free Hit and two-Gameweek adjacency lists",
        )

    if clean_counts is not None and squad_size is not None:
        if sum(clean_counts.values()) != squad_size:
            blockers.append(
                _blocker(
                    "inconsistent_rules",
                    "squad.position_counts",
                    "Position counts must sum to squad.size",
                )
            )
    if exceptional_events and max_banked is not None:
        if any(event["top_up_to"] > max_banked for event in exceptional_events):
            blockers.append(
                _blocker(
                    "inconsistent_rules",
                    "transfers.afcon_exceptional_topup",
                    "Exceptional top-up cannot exceed transfers.max_banked",
                )
            )
    if clean_boundary is not None and expiry is not None:
        if clean_boundary["free_hit_cannot_span_adjacent_gameweeks"] != [
            expiry,
            expiry + 1,
        ]:
            blockers.append(
                _blocker(
                    "inconsistent_rules",
                    "chips.boundary_restrictions",
                    "Free Hit adjacency boundary must straddle first-half expiry",
                )
            )
    if any(
        row["code"] in {"malformed_rule_value", "inconsistent_rules"}
        for row in blockers
    ):
        return None
    regular_gameweeks = int(expiry) * int(sets)
    chip_sets = [
        {
            "index": 1,
            "suffix": "fh",
            "start_gameweek": 1,
            "end_gameweek": int(expiry),
            "chips": [f"{chip}_fh" for chip in chip_bases],
        },
        {
            "index": 2,
            "suffix": "sh",
            "start_gameweek": int(expiry) + 1,
            "end_gameweek": regular_gameweeks,
            "chips": [f"{chip}_sh" for chip in chip_bases],
        },
    ]
    return {
        "initial_budget": initial_budget,
        "squad_size": squad_size,
        "position_counts": clean_counts,
        "max_per_club": max_per_club,
        "free_transfers_per_gameweek": free_per,
        "max_banked": max_banked,
        "hit_cost": hit_cost,
        "retain_banked_on_wildcard_free_hit": retain,
        "selling_rise_share_kept": rise_share,
        "selling_round_down_to": round_down,
        "exceptional_transfer_events": exceptional_events,
        "one_chip_per_gameweek": one_chip,
        "chip_sets": chip_sets,
        "chip_boundary_restrictions": clean_boundary,
        "regular_gameweeks": regular_gameweeks,
        "terminal_state_gameweek": regular_gameweeks + 1,
    }


def build_ruleset_activation(
    rules: Mapping[str, Any],
    ruleset_sha256: str,
    *,
    mode: str = "live",
    compatibility_policy: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    source = deepcopy(dict(rules))
    blockers: list[dict[str, Any]] = []
    if mode not in {"historical_replay", "live"}:
        blockers.append(
            _blocker("invalid_ruleset_identity", None, f"Unsupported mode {mode!r}")
        )
        mode = "live"
    meta = source.get("meta") if isinstance(source.get("meta"), dict) else {}
    season = str(meta.get("season", "unknown"))
    ruleset_id = str(meta.get("ruleset_id", "unknown"))
    if len(season) < 3 or len(ruleset_id) < 3 or not _valid_sha256(ruleset_sha256):
        blockers.append(
            _blocker(
                "invalid_ruleset_identity",
                None,
                "Ruleset requires season, ruleset_id and lower-case SHA-256 identity",
            )
        )
    digest = ruleset_sha256 if _valid_sha256(ruleset_sha256) else "0" * 64
    approvals, approvals_by_rule = _normalise_compatibility_policy(
        compatibility_policy, blockers
    )
    try:
        indexed = _index_rules(source)
    except (KeyError, TypeError, ValueError) as exc:
        blockers.append(_blocker("malformed_rule_value", None, str(exc)))
        indexed = {}
    for rule_id in TRANSITION_RULE_IDS:
        rule = _canonical_rule(indexed, rule_id)
        if rule is None:
            blockers.append(_blocker("missing_rule", rule_id, f"Missing rule {rule_id}"))
            continue
        status = str(rule.get("status", ""))
        approval = approvals_by_rule.get(rule_id)
        if status == "confirmed":
            if approval:
                blockers.append(
                    _blocker(
                        "invalid_compatibility_policy",
                        rule_id,
                        "Confirmed rules must not carry compatibility approvals",
                    )
                )
        elif status == "inherited" and approval:
            pass
        else:
            blockers.append(
                _blocker(
                    "unconfirmed_rule",
                    rule_id,
                    f"Consumed rule {rule_id} has unapproved status {status!r}",
                )
            )
            if approval and status != "inherited":
                blockers.append(
                    _blocker(
                        "invalid_compatibility_policy",
                        rule_id,
                        f"Compatibility cannot approve {status!r} rules",
                    )
                )
    profile = _compile_profile(indexed, blockers)
    blockers.sort(key=lambda item: (item["code"], item["rule_id"] or "", item["message"]))
    activatable = not blockers and profile is not None
    return {
        "schema_version": "1.0",
        "mode": mode,
        "activatable": activatable,
        "season": season,
        "ruleset_id": ruleset_id,
        "ruleset_sha256": digest,
        "compatibility_policy": approvals,
        "blockers": blockers,
        "transition_profile": profile if activatable else None,
    }


def assert_ruleset_activatable(
    rules: Mapping[str, Any],
    ruleset_sha256: str,
    *,
    mode: str = "live",
    compatibility_policy: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    report = build_ruleset_activation(
        rules,
        ruleset_sha256,
        mode=mode,
        compatibility_policy=compatibility_policy,
    )
    if not report["activatable"]:
        details = "; ".join(
            f"{row['rule_id'] or 'ruleset'}: {row['message']}"
            for row in report["blockers"]
        )
        raise RulesetActivationError(
            f"Ruleset {report['ruleset_id']} is not activatable: {details}"
        )
    return report


def ruleset_semantic_diff(
    left_rules: Mapping[str, Any],
    left_sha256: str,
    right_rules: Mapping[str, Any],
    right_sha256: str,
) -> dict[str, Any]:
    left = _index_rules(deepcopy(dict(left_rules)))
    right = _index_rules(deepcopy(dict(right_rules)))
    changes = []
    for rule_id in TRANSITION_RULE_IDS:
        left_rule = _canonical_rule(left, rule_id)
        right_rule = _canonical_rule(right, rule_id)
        left_value = deepcopy(left_rule.get("value")) if left_rule else None
        right_value = deepcopy(right_rule.get("value")) if right_rule else None
        if left_value != right_value:
            changes.append(
                {
                    "rule_id": rule_id,
                    "classification": "behavioral",
                    "left": left_value,
                    "right": right_value,
                }
            )
    return {
        "left_ruleset_id": str(left_rules.get("meta", {}).get("ruleset_id", "unknown")),
        "left_ruleset_sha256": left_sha256,
        "right_ruleset_id": str(right_rules.get("meta", {}).get("ruleset_id", "unknown")),
        "right_ruleset_sha256": right_sha256,
        "changes": changes,
    }
