"""Build immutable player priors from a completed earlier season."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from typing import Any, Iterable, Mapping

from src.forecasting.live_faithful import artifact_hash


class PlayerPriorError(ValueError):
    """Raised when source history cannot form an unambiguous player prior."""


POSITION_MAP = {"GK": "GKP", "GKP": "GKP", "DEF": "DEF", "MID": "MID", "FWD": "FWD"}
EVENT_FIELDS = (
    "expected_goals",
    "expected_assists",
    "clean_sheets",
    "saves",
    "bonus",
    "yellow_cards",
    "red_cards",
)


def _number(value: Any, field: str) -> float:
    if value is None or isinstance(value, bool):
        raise PlayerPriorError(f"{field} must be numeric")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise PlayerPriorError(f"{field} must be numeric") from exc


def _position(value: Any) -> str:
    try:
        return POSITION_MAP[str(value).upper()]
    except KeyError as exc:
        raise PlayerPriorError(f"Unknown position: {value!r}") from exc


def _identity_codes(identity_map: Mapping[str, Any]) -> dict[int, int]:
    result: dict[int, int] = {}
    seen_codes: set[int] = set()
    for row in identity_map.get("players", []):
        element = int(row["fpl_player_id"])
        code = int(row["fpl_code"])
        if element in result:
            raise PlayerPriorError(f"Duplicate player identity for element {element}")
        if code in seen_codes:
            raise PlayerPriorError(f"Duplicate FPL code in identity map: {code}")
        result[element] = code
        seen_codes.add(code)
    return result


def price_band(price: float, bands: Iterable[Iterable[float]]) -> str:
    """Return one stable lower-inclusive, upper-exclusive band label."""

    parsed = [tuple(float(value) for value in band) for band in bands]
    for index, (lower, upper) in enumerate(parsed):
        if lower >= upper:
            raise PlayerPriorError("Price band lower bound must be below upper bound")
        is_last = index == len(parsed) - 1
        if lower <= price < upper or (is_last and price == upper):
            return f"{lower:g}-{upper:g}"
    raise PlayerPriorError(f"Price {price:g} is outside configured bands")


def _rate(group: list[dict[str, Any]]) -> dict[str, Any]:
    minutes = sum(row["minutes"] for row in group)
    points = sum(row["total_points"] for row in group)
    starts = sum(row["started"] for row in group)
    fixtures = len(group)
    start_minutes = sum(row["minutes"] for row in group if row["started"])
    result = {
        "points_per_90": round(90.0 * points / minutes, 4) if minutes else 0.0,
        "start_probability": round(starts / fixtures, 4) if fixtures else 0.0,
        "minutes_per_start": round(start_minutes / starts, 1) if starts else 0.0,
        "sample_minutes": int(round(minutes)),
        "sample_fixtures": fixtures,
    }
    for field in EVENT_FIELDS:
        total = sum(row[field] for row in group)
        result[f"{field}_per_90"] = (
            round(90.0 * total / minutes, 6) if minutes else 0.0
        )
    return result


def build_player_prior(
    *,
    season: str,
    as_of: str,
    rows: Iterable[Mapping[str, Any]],
    identity_map: Mapping[str, Any],
    price_bands: Iterable[Iterable[float]],
) -> dict[str, Any]:
    """Aggregate completed-season fixture rows by stable FPL code."""

    identities = _identity_codes(identity_map)
    bands = [list(band) for band in price_bands]
    normalised: list[dict[str, Any]] = []
    player_groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    player_positions: dict[int, str] = {}
    player_prices: dict[int, list[float]] = defaultdict(list)
    seen_fixtures: set[tuple[int, int]] = set()
    for source in rows:
        row = deepcopy(dict(source))
        element = int(row["element"])
        if element not in identities:
            raise PlayerPriorError(f"Missing identity for element {element}")
        fixture = int(row["fixture"])
        key = (element, fixture)
        if key in seen_fixtures:
            raise PlayerPriorError(
                f"Duplicate player-fixture row: element={element}, fixture={fixture}"
            )
        seen_fixtures.add(key)
        position = _position(row["position"])
        if element in player_positions and player_positions[element] != position:
            raise PlayerPriorError(f"Position changed within source season: {element}")
        player_positions[element] = position
        minutes = _number(row.get("minutes", 0), "minutes")
        points = _number(row.get("total_points", 0), "total_points")
        started = int(_number(row.get("starts", 0), "starts") > 0)
        price = _number(row["value"], "value") / 10.0
        item = {
            "element": element,
            "minutes": minutes,
            "total_points": points,
            "started": started,
            "position": position,
            "price": price,
            "expected_goals": _number(
                row.get("expected_goals", row.get("goals_scored", 0)),
                "expected_goals",
            ),
            "expected_assists": _number(
                row.get("expected_assists", row.get("assists", 0)),
                "expected_assists",
            ),
            "clean_sheets": _number(row.get("clean_sheets", 0), "clean_sheets"),
            "saves": _number(row.get("saves", 0), "saves"),
            "bonus": _number(row.get("bonus", 0), "bonus"),
            "yellow_cards": _number(row.get("yellow_cards", 0), "yellow_cards"),
            "red_cards": _number(row.get("red_cards", 0), "red_cards"),
        }
        normalised.append(item)
        player_groups[element].append(item)
        player_prices[element].append(price)

    players: list[dict[str, Any]] = []
    fallback_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    position_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for element, group in sorted(player_groups.items()):
        position = player_positions[element]
        launch_proxy = group[0]["price"]
        band = price_band(launch_proxy, bands)
        metrics = _rate(group)
        players.append(
            {
                "fpl_code": identities[element],
                "position": position,
                "price_band": band,
                "source_price": round(launch_proxy, 1),
                **metrics,
            }
        )
        fallback_groups[f"{position}:{band}"].extend(group)
        position_groups[position].extend(group)

    fallbacks = {
        key: _rate(group)
        for key, group in sorted(fallback_groups.items())
    }
    for position, group in sorted(position_groups.items()):
        fallbacks[position] = _rate(group)

    identity_bytes = json.dumps(
        identity_map,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    result = {
        "schema_version": "1.0",
        "season": str(season),
        "as_of": str(as_of),
        "source": {
            "row_count": len(normalised),
            "identity_map_sha256": hashlib.sha256(identity_bytes).hexdigest(),
            "aggregation": "completed_fixture_rows_by_fpl_code",
            "launch_price_policy": "first_source_fixture_price_proxy",
        },
        "price_bands": bands,
        "players": sorted(players, key=lambda row: int(row["fpl_code"])),
        "fallbacks": fallbacks,
    }
    result["content_sha256"] = artifact_hash(result)
    return result
