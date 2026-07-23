"""Build content-addressed, deadline-safe state from observed historical episodes."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping


MODEL_SPEC = {
    "model_version": "historical-rolling-v1",
    "history_unit": "player_gameweek",
    "rolling_window_gameweeks": 3,
    "start_probability": "0.6*prior_started+0.4*clip(mean_minutes/90,0.05,0.95)",
    "expected_minutes_per_fixture": "start_probability*75",
    "expected_points_per_fixture": "mean(last_3_completed_gameweek_points)",
    "blank_policy": "zero_fixture_points_retain_market",
    "double_policy": "forecast_each_fixture_then_sum",
}
FORBIDDEN_FIELDS = {
    "xP",
    "ep_this",
    "ep_next",
    "player_outcomes",
    "hidden_outcome",
    "hidden_outcome_ref",
}
SUM_FIELDS = (
    "minutes",
    "total_points",
    "goals_scored",
    "assists",
    "clean_sheets",
    "goals_conceded",
    "saves",
    "bonus",
    "bps",
    "yellow_cards",
    "red_cards",
    "expected_goals",
    "expected_assists",
    "expected_goal_involvements",
    "expected_goals_conceded",
    "influence",
    "creativity",
    "threat",
    "ict_index",
)
POSITION_MAP = {"GK": "GKP", "GKP": "GKP", "DEF": "DEF", "MID": "MID", "FWD": "FWD"}


class HistoricalFeatureStateError(ValueError):
    """Raised when observed history cannot safely form a replay feature state."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def feature_state_hash(state: Mapping[str, Any]) -> str:
    """Hash all decision-relevant state fields without circular identity fields."""

    projection = {
        key: deepcopy(value)
        for key, value in state.items()
        if key not in {"feature_state_id", "content_sha256"}
    }
    return _stable_hash(projection)


def _normalise_name(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _normalise_position(value: Any) -> str:
    position = str(value).upper()
    try:
        return POSITION_MAP[position]
    except KeyError as exc:
        raise HistoricalFeatureStateError(f"Unknown historical position: {value!r}") from exc


def _number(value: Any, field: str) -> float:
    if value is None or isinstance(value, bool):
        raise HistoricalFeatureStateError(f"{field} must be numeric")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise HistoricalFeatureStateError(f"{field} must be numeric") from exc


def _int_if_whole(value: float) -> int | float:
    return int(value) if value.is_integer() else round(value, 6)


def _validate_inputs(
    manifest: Mapping[str, Any],
    observed: Mapping[str, Any],
    identity_map: Mapping[str, Any],
    previous_state: Mapping[str, Any] | None,
) -> tuple[int, str, str]:
    episode_id = str(manifest.get("episode_id", ""))
    season = str(manifest.get("season", ""))
    gameweek = int(manifest.get("gameweek", 0))
    if manifest.get("mode") != "historical_structured":
        raise HistoricalFeatureStateError("Feature state requires historical_structured mode")
    for field, expected in (
        ("episode_id", episode_id),
        ("season", season),
        ("gameweek", gameweek),
        ("cutoff", manifest.get("cutoff")),
        ("deadline", manifest.get("deadline")),
    ):
        if observed.get(field) != expected:
            raise HistoricalFeatureStateError(f"Observed {field} does not match manifest")
    observed_hash = _stable_hash(observed)
    expected_observed_hash = (
        manifest.get("observed", {})
        .get("feature_snapshot_ref", {})
        .get("content_sha256")
    )
    if expected_observed_hash != observed_hash:
        raise HistoricalFeatureStateError("Observed partition content hash mismatch")
    identity_hash = _stable_hash(identity_map)
    if observed.get("identity_map_ref", {}).get("content_sha256") != identity_hash:
        raise HistoricalFeatureStateError("Identity map content hash mismatch")
    if str(identity_map.get("season")) != season:
        raise HistoricalFeatureStateError("Identity map season does not match episode")

    if previous_state is not None:
        if previous_state.get("content_sha256") != feature_state_hash(previous_state):
            raise HistoricalFeatureStateError("Previous feature state hash mismatch")
        if str(previous_state.get("season")) != season:
            raise HistoricalFeatureStateError("Previous feature state season mismatch")
        if int(previous_state.get("gameweek", 0)) + 1 != gameweek:
            raise HistoricalFeatureStateError(
                "Feature state must advance exactly one Gameweek"
            )
    return gameweek, observed_hash, identity_hash


def _identity_indexes(
    identity_map: Mapping[str, Any],
) -> tuple[dict[int, str], dict[str, str], dict[int, str]]:
    players: dict[int, str] = {}
    for row in identity_map.get("players", []):
        element = int(row["fpl_player_id"])
        if element in players:
            raise HistoricalFeatureStateError(f"Duplicate player identity: {element}")
        players[element] = str(row["canonical_id"])

    teams_by_name: dict[str, str] = {}
    teams_by_fpl_id: dict[int, str] = {}
    for row in identity_map.get("teams", []):
        canonical = str(row["canonical_id"])
        normalised = _normalise_name(str(row["fpl_name"]))
        if normalised in teams_by_name:
            raise HistoricalFeatureStateError(
                f"Duplicate normalised team identity: {row['fpl_name']}"
            )
        teams_by_name[normalised] = canonical
        teams_by_fpl_id[int(row["fpl_team_id"])] = canonical
    return players, teams_by_name, teams_by_fpl_id


def _consistent(group: list[dict[str, Any]], field: str) -> Any:
    values = {json.dumps(row.get(field), sort_keys=True) for row in group}
    if len(values) != 1:
        raise HistoricalFeatureStateError(
            f"Player-Gameweek has conflicting {field}: element={group[0].get('element')}"
        )
    return group[0].get(field)


def _aggregate_rows(
    rows: list[dict[str, Any]],
    *,
    gameweek: int,
    player_ids: Mapping[int, str],
    team_ids: Mapping[str, str],
) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    expected_prior = gameweek - 1
    for source in rows:
        row = deepcopy(source)
        forbidden = sorted(FORBIDDEN_FIELDS & set(row))
        if forbidden:
            raise HistoricalFeatureStateError(
                f"Observed lag row contains forbidden fields: {forbidden}"
            )
        if int(row.get("GW", -1)) != expected_prior:
            raise HistoricalFeatureStateError(
                f"Lag rows must come from the exact prior Gameweek {expected_prior}"
            )
        element = int(row.get("element", -1))
        if element not in player_ids:
            raise HistoricalFeatureStateError(f"Unresolved player identity: {element}")
        grouped.setdefault(element, []).append(row)

    aggregates: list[dict[str, Any]] = []
    for element, group in sorted(grouped.items()):
        group.sort(key=lambda row: (int(row.get("fixture", 0)), str(row.get("kickoff_time", ""))))
        position = _normalise_position(_consistent(group, "position"))
        team_name = str(_consistent(group, "team"))
        team_key = _normalise_name(team_name)
        if team_key not in team_ids:
            raise HistoricalFeatureStateError(f"Unresolved team identity: {team_name}")
        price_tenths = _number(_consistent(group, "value"), "value")
        aggregate: dict[str, Any] = {
            "gameweek": expected_prior,
            "fixture_count": len(group),
            "fixture_ids": sorted(int(row["fixture"]) for row in group),
            "name": str(_consistent(group, "name")),
            "position": position,
            "club_id": team_ids[team_key],
            "started": int(any(_number(row.get("starts", 0), "starts") > 0 for row in group)),
            "price": round(price_tenths / 10.0, 1),
        }
        for field in SUM_FIELDS:
            total = sum(_number(row.get(field, 0), field) for row in group)
            aggregate[field] = _int_if_whole(total)
        aggregates.append(
            {
                "player_id": player_ids[element],
                "record": aggregate,
            }
        )
    return aggregates


def _seed_players(seed: Mapping[str, Any], gameweek: int) -> list[dict[str, Any]]:
    if gameweek != 1:
        raise HistoricalFeatureStateError("Controlled seed may only initialise Gameweek 1")
    if str(seed.get("season")) == "" or int(seed.get("gameweek", 0)) != 1:
        raise HistoricalFeatureStateError("Controlled seed identity is invalid")
    result = []
    for row in seed.get("squad", []):
        price = round(_number(row["current_price"], "current_price"), 1)
        result.append(
            {
                "player_id": str(row["player_id"]),
                "name": str(row["web_name"]),
                "position": _normalise_position(row["position"]),
                "club_id": str(row["club_id"]),
                "quote": {
                    "now_cost": price,
                    "source_gameweek": 0,
                    "age_gameweeks": 0,
                    "price_confidence": "official_published_scout_price",
                },
                "history": [],
                "projection": {},
                "limitations": ["controlled_gw1_seed_no_historical_forecast"],
            }
        )
    return sorted(result, key=lambda row: row["player_id"])


def _fixture_components(
    player: Mapping[str, Any],
    fixtures: list[dict[str, Any]],
    teams_by_fpl_id: Mapping[int, str],
) -> list[dict[str, Any]]:
    club_id = str(player["club_id"])
    components: list[dict[str, Any]] = []
    for fixture in fixtures:
        home = teams_by_fpl_id.get(int(fixture["team_h"]))
        away = teams_by_fpl_id.get(int(fixture["team_a"]))
        if club_id == home:
            opponent = away
            was_home = True
            difficulty = int(fixture["team_h_difficulty"])
        elif club_id == away:
            opponent = home
            was_home = False
            difficulty = int(fixture["team_a_difficulty"])
        else:
            continue
        if opponent is None:
            raise HistoricalFeatureStateError("Fixture contains unresolved team identity")
        components.append(
            {
                "fixture_id": int(fixture["id"]),
                "opponent_club_id": opponent,
                "was_home": was_home,
                "difficulty": difficulty,
            }
        )
    return sorted(components, key=lambda row: row["fixture_id"])


def _project_player(
    player: dict[str, Any],
    fixtures: list[dict[str, Any]],
    teams_by_fpl_id: Mapping[int, str],
) -> None:
    history = list(player["history"])
    components = _fixture_components(player, fixtures, teams_by_fpl_id)
    if not history:
        player["projection"] = {
            "model_version": MODEL_SPEC["model_version"],
            "status": "controlled_seed_no_forecast",
            "rolling_gameweeks": [],
            "start_probability": 0.5,
            "expected_minutes": 0.0,
            "expected_points": 0.0,
            "fixture_count": len(components),
            "fixture_components": [
                {**component, "expected_minutes": 0.0, "expected_points": 0.0}
                for component in components
            ],
        }
        return

    rolling = history[-3:]
    mean_minutes = sum(float(row["minutes"]) for row in rolling) / len(rolling)
    soft = min(0.95, max(0.05, mean_minutes / 90.0))
    start_probability = min(
        0.95,
        max(0.05, 0.6 * float(history[-1]["started"]) + 0.4 * soft),
    )
    expected_minutes_per_fixture = round(start_probability * 75.0, 1)
    expected_points_per_fixture = round(
        sum(float(row["total_points"]) for row in rolling) / len(rolling), 2
    )
    projected_components = [
        {
            **component,
            "expected_minutes": expected_minutes_per_fixture,
            "expected_points": expected_points_per_fixture,
        }
        for component in components
    ]
    player["projection"] = {
        "model_version": MODEL_SPEC["model_version"],
        "status": "rolling_prior_gameweeks",
        "rolling_gameweeks": [int(row["gameweek"]) for row in rolling],
        "start_probability": round(start_probability, 4),
        "expected_minutes": round(
            expected_minutes_per_fixture * len(projected_components), 1
        ),
        "expected_points": round(
            expected_points_per_fixture * len(projected_components), 2
        ),
        "fixture_count": len(projected_components),
        "fixture_components": projected_components,
    }


def build_feature_state(
    *,
    episode_manifest: Mapping[str, Any],
    observed: Mapping[str, Any],
    identity_map: Mapping[str, Any],
    previous_state: Mapping[str, Any] | None = None,
    seed: Mapping[str, Any] | None = None,
    model_version: str = "historical-rolling-v1",
) -> dict[str, Any]:
    """Advance one historical episode without accepting any hidden-outcome input."""

    manifest = deepcopy(dict(episode_manifest))
    observed_copy = deepcopy(dict(observed))
    identity_copy = deepcopy(dict(identity_map))
    previous = deepcopy(dict(previous_state)) if previous_state is not None else None
    if model_version != MODEL_SPEC["model_version"]:
        raise HistoricalFeatureStateError(
            f"Unsupported historical model version: {model_version}"
        )
    gameweek, observed_hash, identity_hash = _validate_inputs(
        manifest, observed_copy, identity_copy, previous
    )
    player_ids, teams_by_name, teams_by_fpl_id = _identity_indexes(identity_copy)

    if gameweek == 1:
        if observed_copy.get("lagged_player_features"):
            raise HistoricalFeatureStateError("Gameweek 1 cannot contain lagged player rows")
        players = _seed_players(seed, gameweek) if seed is not None else []
    else:
        if observed_copy.get("lagged_from_gameweek") != gameweek - 1:
            raise HistoricalFeatureStateError(
                "Observed lagged_from_gameweek is not the exact prior Gameweek"
            )
        players = deepcopy(previous.get("players", [])) if previous else []

    indexed = {str(row["player_id"]): row for row in players}
    aggregates = _aggregate_rows(
        list(observed_copy.get("lagged_player_features", [])),
        gameweek=gameweek,
        player_ids=player_ids,
        team_ids=teams_by_name,
    )
    updated_ids: set[str] = set()
    for aggregate in aggregates:
        player_id = str(aggregate["player_id"])
        record = aggregate["record"]
        updated_ids.add(player_id)
        if player_id not in indexed:
            indexed[player_id] = {
                "player_id": player_id,
                "name": record["name"],
                "position": record["position"],
                "club_id": record["club_id"],
                "quote": {},
                "history": [],
                "projection": {},
                "limitations": [],
            }
        player = indexed[player_id]
        if player["history"] and player["position"] != record["position"]:
            raise HistoricalFeatureStateError(
                f"Position changed within season for {player_id}"
            )
        if any(
            int(item["gameweek"]) == int(record["gameweek"])
            for item in player["history"]
        ):
            raise HistoricalFeatureStateError(
                f"Duplicate player-Gameweek history for {player_id}"
            )
        player["name"] = record["name"]
        player["position"] = record["position"]
        player["club_id"] = record["club_id"]
        player["history"].append(record)
        player["history"].sort(key=lambda row: int(row["gameweek"]))
        player["quote"] = {
            "now_cost": record["price"],
            "source_gameweek": int(record["gameweek"]),
            "age_gameweeks": gameweek - int(record["gameweek"]),
            "price_confidence": "historical_post_gameweek_export",
        }
        player["limitations"] = [
            limitation
            for limitation in player.get("limitations", [])
            if limitation != "market_quote_carried_forward"
        ]

    for player_id, player in indexed.items():
        if player_id not in updated_ids and player.get("quote"):
            source_gameweek = int(player["quote"]["source_gameweek"])
            if player["quote"]["price_confidence"] == "official_published_scout_price":
                age = max(0, gameweek - 1)
            else:
                age = gameweek - source_gameweek
            player["quote"]["age_gameweeks"] = age
            if gameweek > 1 and "market_quote_carried_forward" not in player["limitations"]:
                player["limitations"].append("market_quote_carried_forward")
        player["limitations"] = sorted(set(player.get("limitations", [])))
        _project_player(
            player,
            list(observed_copy.get("fixtures", [])),
            teams_by_fpl_id,
        )

    previous_hash = previous.get("content_sha256") if previous else None
    previous_chain = (
        previous.get("lineage", {}).get("history_chain_sha256")
        if previous
        else "genesis"
    )
    seed_hash = _stable_hash(seed) if seed is not None else None
    limitations = sorted(
        set(observed_copy.get("limitations", []))
        | {"historical_prices_not_deadline_snapshots"}
        | (
            {"controlled_gw1_seed_no_historical_forecast"}
            if gameweek == 1
            else set()
        )
    )
    state: dict[str, Any] = {
        "schema_version": "1.0",
        "feature_state_id": "",
        "content_sha256": "",
        "episode_id": str(manifest["episode_id"]),
        "season": str(manifest["season"]),
        "gameweek": gameweek,
        "cutoff": str(manifest["cutoff"]),
        "status": "degraded" if limitations else "complete",
        "limitations": limitations,
        "lineage": {
            "dataset_id": str(observed_copy["dataset_id"]),
            "dataset_sha256": str(observed_copy["dataset_hash"]),
            "observed_sha256": observed_hash,
            "identity_map_sha256": identity_hash,
            "ruleset_id": str(manifest["ruleset"]["ruleset_id"]),
            "ruleset_sha256": str(manifest["ruleset"]["content_sha256"]),
            "previous_feature_state_sha256": previous_hash,
            "history_chain_sha256": _stable_hash(
                {
                    "previous": previous_chain,
                    "observed": observed_hash,
                    "gameweek": gameweek,
                }
            ),
            "model_version": model_version,
            "model_sha256": _stable_hash(MODEL_SPEC),
            "seed_sha256": seed_hash,
        },
        "fixtures": sorted(
            deepcopy(list(observed_copy.get("fixtures", []))),
            key=lambda row: int(row["id"]),
        ),
        "players": sorted(indexed.values(), key=lambda row: str(row["player_id"])),
    }
    content_hash = feature_state_hash(state)
    state["content_sha256"] = content_hash
    state["feature_state_id"] = (
        f"feature-state:{state['episode_id']}:{content_hash[:16]}"
    )
    return state
