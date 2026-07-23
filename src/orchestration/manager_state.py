"""Validate and normalise manually entered FPL manager state."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator, FormatChecker

from src.data.temporal import parse_aware_datetime
from src.scoring.rules_activation import assert_ruleset_activatable
from src.scoring.validator import selling_price, validate_squad


REPO_ROOT = Path(__file__).resolve().parents[2]
MANAGER_STATE_SCHEMA = REPO_ROOT / "control/schemas/benchmark/manager-state.json"
MANAGER_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,63}$")
MANUAL_FIELDS = {
    "$schema_note", "manager_id", "season", "gameweek", "observed_at",
    "available_at", "deadline", "decision_cutoff", "bank", "free_transfers",
    "chips_available", "chip_history", "squad", "notes",
}
MANUAL_PLAYER_FIELDS = {
    "player_id", "fpl_code", "web_name", "position", "club_id",
    "purchase_price", "selling_price", "now_cost",
}


class ManagerStateError(ValueError):
    """Raised when manual state cannot be trusted as a benchmark input."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _content_hash(value: Mapping[str, Any]) -> str:
    projection = {key: item for key, item in value.items() if key != "content_sha256"}
    return hashlib.sha256(_canonical_bytes(projection)).hexdigest()


def _timestamp(value: Any, field: str) -> str:
    try:
        parsed = parse_aware_datetime(str(value), field=field)
    except (TypeError, ValueError) as exc:
        raise ManagerStateError(str(exc)) from exc
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _price(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ManagerStateError(f"{field} must be a numeric price in millions")
    price = round(float(value), 1)
    if price < 0 or abs(float(value) * 10 - round(float(value) * 10)) > 1e-8:
        raise ManagerStateError(f"{field} must be non-negative in 0.1 increments")
    return price


def _bootstrap_catalogue(bootstrap: Mapping[str, Any]) -> tuple[dict[str, dict], dict[int, str]]:
    elements = bootstrap.get("elements")
    element_types = bootstrap.get("element_types")
    if not isinstance(elements, list) or not elements:
        raise ManagerStateError("bootstrap elements catalogue is missing or empty")
    if not isinstance(element_types, list) or not element_types:
        raise ManagerStateError("bootstrap position catalogue is missing or empty")
    positions: dict[int, str] = {}
    for row in element_types:
        try:
            position = str(row["singular_name_short"])
            type_id = int(row["id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ManagerStateError("bootstrap position catalogue is malformed") from exc
        if position not in {"GKP", "DEF", "MID", "FWD"}:
            raise ManagerStateError(f"unsupported bootstrap position {position!r}")
        positions[type_id] = position
    catalogue: dict[str, dict] = {}
    for row in elements:
        try:
            player_id = str(int(row["id"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ManagerStateError("bootstrap player id is malformed") from exc
        if player_id in catalogue:
            raise ManagerStateError(f"bootstrap player IDs must be unique: {player_id}")
        catalogue[player_id] = dict(row)
    return catalogue, positions


def _deadline_for_gameweek(bootstrap: Mapping[str, Any], gameweek: int) -> str:
    events = bootstrap.get("events")
    if not isinstance(events, list):
        raise ManagerStateError("bootstrap events catalogue is missing or malformed")
    try:
        matching = [row for row in events if isinstance(row, Mapping) and int(row.get("id", 0)) == gameweek]
    except (TypeError, ValueError) as exc:
        raise ManagerStateError("bootstrap event identity is malformed") from exc
    if len(matching) != 1 or not matching[0].get("deadline_time"):
        raise ManagerStateError(f"bootstrap has no unique deadline for Gameweek {gameweek}")
    return _timestamp(matching[0]["deadline_time"], "bootstrap.deadline_time")


def _normalise_chip_state(
    entry: Mapping[str, Any], profile: Mapping[str, Any], gameweek: int
) -> tuple[list[str], list[dict[str, Any]]]:
    chip_sets = list(profile["chip_sets"])
    all_chips = [str(chip) for chip_set in chip_sets for chip in chip_set["chips"]]
    history_value = entry.get("chip_history", [])
    if not isinstance(history_value, list):
        raise ManagerStateError("chip history must be an array")
    history: list[dict[str, Any]] = []
    used: set[str] = set()
    used_gameweeks: Counter[int] = Counter()
    windows = {
        str(chip): (int(chip_set["start_gameweek"]), int(chip_set["end_gameweek"]))
        for chip_set in chip_sets
        for chip in chip_set["chips"]
    }
    for row in history_value:
        if not isinstance(row, Mapping):
            raise ManagerStateError("chip history entries must be objects")
        chip = str(row.get("chip", ""))
        try:
            played = int(row.get("gameweek", 0))
        except (TypeError, ValueError) as exc:
            raise ManagerStateError("chip history gameweek must be an integer") from exc
        if chip not in windows:
            raise ManagerStateError(f"unknown chip in chip history: {chip}")
        if chip in used:
            raise ManagerStateError(f"chip history must use each chip at most once: {chip}")
        start, end = windows[chip]
        if played < start or played > end or played >= gameweek:
            raise ManagerStateError(f"chip {chip} has invalid chip history gameweek {played}")
        used.add(chip)
        used_gameweeks[played] += 1
        history.append({"chip": chip, "gameweek": played})
    if profile["one_chip_per_gameweek"] and any(count > 1 for count in used_gameweeks.values()):
        raise ManagerStateError("chip history contains more than one chip in a Gameweek")

    expired = {
        str(chip)
        for chip_set in chip_sets
        if int(chip_set["end_gameweek"]) < gameweek
        for chip in chip_set["chips"]
    }
    expected = set(all_chips) - used - expired
    supplied_value = entry.get("chips_available")
    if not isinstance(supplied_value, list) or any(not isinstance(chip, str) for chip in supplied_value):
        raise ManagerStateError("chips available must be an array of chip IDs")
    if len(supplied_value) != len(set(supplied_value)):
        raise ManagerStateError("chips available must be unique")
    supplied = set(supplied_value)
    unknown = sorted(supplied - set(all_chips))
    if unknown:
        raise ManagerStateError("unknown chip IDs: " + ", ".join(unknown))
    if supplied != expected:
        missing = sorted(expected - supplied)
        unexpected = sorted(supplied - expected)
        raise ManagerStateError(
            f"chip inventory does not match rules/history; missing={missing}, unexpected={unexpected}"
        )
    ordered = [chip for chip in all_chips if chip in supplied]
    history.sort(key=lambda row: (row["gameweek"], row["chip"]))
    return ordered, history


def normalise_manager_state(
    entry: Mapping[str, Any],
    *,
    bootstrap: Mapping[str, Any],
    rules: Mapping[str, Any],
    ruleset_sha256: str,
    compatibility_policy: Iterable[Mapping[str, Any]] = (),
    max_age_seconds: int = 21600,
) -> dict[str, Any]:
    """Return a strict, content-addressed state or fail without guessing."""

    unexpected_fields = sorted(set(entry) - MANUAL_FIELDS)
    if unexpected_fields:
        raise ManagerStateError(
            "manual manager state contains unsupported fields: " + ", ".join(unexpected_fields)
        )
    activation = assert_ruleset_activatable(
        rules,
        ruleset_sha256,
        mode="live",
        compatibility_policy=compatibility_policy,
    )
    profile = activation["transition_profile"]
    manager_id = str(entry.get("manager_id", ""))
    if not MANAGER_ID.fullmatch(manager_id) or manager_id.isdigit():
        raise ManagerStateError(
            "manager_id must be a non-numeric pseudonymous 3-64 character identifier"
        )
    season = str(entry.get("season", ""))
    if season != str(activation["season"]):
        raise ManagerStateError("manager-state season does not match active ruleset")
    raw_gameweek = entry.get("gameweek")
    if isinstance(raw_gameweek, bool) or not isinstance(raw_gameweek, int):
        raise ManagerStateError("gameweek must be an integer")
    gameweek = raw_gameweek
    if gameweek < 1 or gameweek > int(profile["regular_gameweeks"]):
        raise ManagerStateError("gameweek is outside the active season")

    observed_at = _timestamp(entry.get("observed_at"), "observed_at")
    available_at = _timestamp(entry.get("available_at"), "available_at")
    cutoff = _timestamp(entry.get("decision_cutoff"), "decision_cutoff")
    deadline = _timestamp(entry.get("deadline"), "deadline")
    observed_dt = parse_aware_datetime(observed_at, field="observed_at")
    available_dt = parse_aware_datetime(available_at, field="available_at")
    cutoff_dt = parse_aware_datetime(cutoff, field="decision_cutoff")
    deadline_dt = parse_aware_datetime(deadline, field="deadline")
    if not observed_dt <= available_dt <= cutoff_dt <= deadline_dt:
        raise ManagerStateError(
            "manager timestamps must satisfy observed_at <= available_at <= cutoff <= deadline"
        )
    if (cutoff_dt - observed_dt).total_seconds() > max_age_seconds:
        raise ManagerStateError(
            f"manager state is stale at cutoff (maximum {max_age_seconds} seconds)"
        )
    official_deadline = _deadline_for_gameweek(bootstrap, gameweek)
    if deadline != official_deadline:
        raise ManagerStateError(
            f"manager deadline {deadline} does not match bootstrap deadline {official_deadline}"
        )

    catalogue, positions = _bootstrap_catalogue(bootstrap)
    squad_value = entry.get("squad")
    if not isinstance(squad_value, list):
        raise ManagerStateError("squad must be an array")
    normalised_squad: list[dict[str, Any]] = []
    for manual in squad_value:
        if not isinstance(manual, Mapping):
            raise ManagerStateError("squad entries must be objects")
        unexpected_player_fields = sorted(set(manual) - MANUAL_PLAYER_FIELDS)
        if unexpected_player_fields:
            raise ManagerStateError(
                "manual squad entry contains unsupported fields: "
                + ", ".join(unexpected_player_fields)
            )
        player_id = str(manual.get("player_id", ""))
        source = catalogue.get(player_id)
        if source is None:
            raise ManagerStateError(f"player {player_id!r} is absent from bootstrap catalogue")
        try:
            source_code = int(source["code"])
            source_club = str(int(source["team"]))
            source_position = positions[int(source["element_type"])]
            raw_cost = source["now_cost"]
            if isinstance(raw_cost, bool) or not isinstance(raw_cost, int):
                raise TypeError
            current = round(raw_cost / 10, 1)
        except (KeyError, TypeError, ValueError) as exc:
            raise ManagerStateError(f"bootstrap player {player_id} is malformed") from exc
        try:
            manual_code = manual.get("fpl_code")
            if isinstance(manual_code, bool) or not isinstance(manual_code, int):
                raise TypeError
        except (TypeError, ValueError) as exc:
            raise ManagerStateError(f"player {player_id} code must be an integer") from exc
        if manual_code != source_code:
            raise ManagerStateError(f"player {player_id} code does not match bootstrap")
        if str(manual.get("web_name", "")) != str(source.get("web_name", "")):
            raise ManagerStateError(f"player {player_id} web name does not match bootstrap")
        if str(manual.get("position", "")) != source_position:
            raise ManagerStateError(f"player {player_id} position does not match bootstrap")
        if str(manual.get("club_id", "")) != source_club:
            raise ManagerStateError(f"player {player_id} club does not match bootstrap")
        if _price(manual.get("now_cost"), f"player {player_id} now cost") != current:
            raise ManagerStateError(f"player {player_id} current price does not match bootstrap")
        purchase = _price(manual.get("purchase_price"), f"player {player_id} purchase price")
        expected_selling = selling_price(purchase, current, dict(rules))
        supplied_selling = _price(
            manual.get("selling_price"), f"player {player_id} selling price"
        )
        if supplied_selling != expected_selling:
            raise ManagerStateError(
                f"player {player_id} selling price expected {expected_selling:.1f}, got {supplied_selling:.1f}"
            )
        normalised_squad.append(
            {
                "player_id": player_id,
                "fpl_code": source_code,
                "web_name": str(source["web_name"]),
                "position": source_position,
                "club_id": source_club,
                "purchase_price": purchase,
                "current_price": current,
                "selling_price": expected_selling,
            }
        )
    normalised_squad.sort(
        key=lambda player: (
            {"GKP": 0, "DEF": 1, "MID": 2, "FWD": 3}[player["position"]],
            int(player["player_id"]) if player["player_id"].isdigit() else player["player_id"],
        )
    )
    bank = _price(entry.get("bank"), "bank")
    squad_validation = validate_squad(normalised_squad, bank=bank, rules=dict(rules))
    if not squad_validation.ok:
        raise ManagerStateError("invalid squad: " + "; ".join(squad_validation.errors))
    raw_free_transfers = entry.get("free_transfers")
    if isinstance(raw_free_transfers, bool) or not isinstance(raw_free_transfers, int):
        raise ManagerStateError("free transfers must be an integer")
    free_transfers = raw_free_transfers
    if not 0 <= free_transfers <= int(profile["max_banked"]):
        raise ManagerStateError(
            f"free transfers must be between 0 and {profile['max_banked']}"
        )
    chips_available, chip_history = _normalise_chip_state(entry, profile, gameweek)

    purchase_total = round(sum(player["purchase_price"] for player in normalised_squad), 1)
    current_total = round(sum(player["current_price"] for player in normalised_squad), 1)
    selling_total = round(sum(player["selling_price"] for player in normalised_squad), 1)
    if gameweek == 1 and round(purchase_total + bank, 1) != round(float(profile["initial_budget"]), 1):
        raise ManagerStateError(
            "Gameweek 1 purchase prices plus bank must equal the ruleset initial budget"
        )
    identity = {
        "manager_id": manager_id,
        "season": season,
        "gameweek": gameweek,
        "available_at": available_at,
        "ruleset_sha256": ruleset_sha256,
        "player_ids": [player["player_id"] for player in normalised_squad],
    }
    identity_hash = hashlib.sha256(_canonical_bytes(identity)).hexdigest()
    state: dict[str, Any] = {
        "manager_state_version": "1.0",
        "manager_state_id": f"manager-state:{season}:gw{gameweek:02d}:{manager_id}:{identity_hash[:16]}",
        "manager_id": manager_id,
        "season": season,
        "gameweek": gameweek,
        "observed_at": observed_at,
        "available_at": available_at,
        "cutoff": cutoff,
        "deadline": deadline,
        "ruleset_id": str(activation["ruleset_id"]),
        "ruleset_sha256": ruleset_sha256,
        "bank": bank,
        "free_transfers": free_transfers,
        "chips_available": chips_available,
        "chip_history": chip_history,
        "squad": normalised_squad,
        "team_purchase_value": purchase_total,
        "team_current_value": current_total,
        "team_selling_value": selling_total,
        "funds_available": round(selling_total + bank, 1),
        "provenance": {
            "entry_method": "manual",
            "authentication": "none",
            "account_identifier_stored": False,
        },
    }
    state["content_sha256"] = _content_hash(state)
    schema = json.loads(MANAGER_STATE_SCHEMA.read_text(encoding="utf-8"))
    try:
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(state)
    except Exception as exc:
        raise ManagerStateError(f"normalised manager state is invalid: {exc}") from exc
    return state
