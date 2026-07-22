"""Build deterministic, outcome-isolated historical benchmark episodes."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import pandas as pd
from jsonschema import Draft202012Validator, FormatChecker

from src.scoring.rules_loader import index_rules, load_rules


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET_MANIFEST = (
    REPO_ROOT / "control" / "manifests" / "datasets" / "benchmark-v0.json"
)
DEFAULT_RULES = REPO_ROOT / "control" / "rules" / "2025-26.yaml"
EPISODE_SCHEMA = REPO_ROOT / "control" / "schemas" / "benchmark" / "episode-manifest.json"
POLICY_ARMS = [
    "naive_baseline",
    "forecast_optimizer",
    "evidence_agent",
    "evidence_challenger",
    "human_decision",
]
FOOTBALL_DATA_TEAM_ALIASES = {
    "manunited": "manutd",
    "tottenham": "spurs",
}
OBSERVED_FIXTURE_FIELDS = [
    "id",
    "event",
    "kickoff_time",
    "team_h",
    "team_a",
    "team_h_difficulty",
    "team_a_difficulty",
    "provisional_start_time",
]
LAGGED_PLAYER_FIELDS = [
    "GW",
    "element",
    "fixture",
    "name",
    "position",
    "team",
    "opponent_team",
    "kickoff_time",
    "minutes",
    "starts",
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
    "value",
    "selected",
    "transfers_balance",
    "transfers_in",
    "transfers_out",
]


class HistoricalEpisodeError(ValueError):
    """Raised when a historical episode cannot be built without guessing."""


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


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_records(frame: pd.DataFrame, fields: list[str] | None = None) -> list[dict[str, Any]]:
    selected = frame if fields is None else frame[[field for field in fields if field in frame.columns]]
    if selected.empty:
        return []
    return json.loads(selected.to_json(orient="records", date_format="iso"))


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin-1", low_memory=False)


def _sort_records(records: list[dict[str, Any]], *keys: str) -> list[dict[str, Any]]:
    return sorted(records, key=lambda row: tuple(str(row.get(key, "")) for key in keys))


def _write_immutable(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise FileExistsError(
                f"Refusing to replace immutable artefact with invalid JSON: {path}"
            ) from exc
        if existing != value:
            raise FileExistsError(f"Refusing to replace immutable artefact: {path}")
        return
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def _write_immutable_bytes(path: Path, payload: bytes) -> None:
    """Write exact evidence bytes once, accepting only identical reruns."""

    if path.exists():
        if path.read_bytes() != payload:
            raise FileExistsError(f"Refusing to replace immutable artefact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _validated_ruleset(path: Path, season: str) -> tuple[dict[str, Any], str, bytes]:
    """Load a fully resolved catalogue for the season and return its exact digest."""

    payload = path.read_bytes()
    rules = load_rules(path)
    meta = rules.get("meta", {})
    if meta.get("season") != season:
        raise HistoricalEpisodeError(
            f"Rules season {meta.get('season')!r} does not match dataset season {season!r}"
        )
    if meta.get("replay_status") != "validated":
        raise HistoricalEpisodeError("Historical replay requires replay_status=validated")
    unresolved = sorted(
        rule_id
        for rule_id, rule in index_rules(rules).items()
        if rule.get("status") != "confirmed"
    )
    if unresolved:
        raise HistoricalEpisodeError(
            f"Historical rules contain unresolved entries: {unresolved}"
        )
    return rules, hashlib.sha256(payload).hexdigest(), payload


def _normalise_name(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _utc_string(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_kickoff(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise HistoricalEpisodeError(f"Kickoff timestamp is not timezone-aware: {value}")
    return parsed.astimezone(timezone.utc)


def _football_result_kickoff(row: pd.Series) -> datetime:
    date_value = datetime.strptime(str(row["Date"]), "%d/%m/%Y").date()
    time_text = str(row.get("Time", "15:00"))
    if not time_text or time_text.casefold() == "nan":
        time_text = "15:00"
    time_value = datetime.strptime(time_text, "%H:%M").time()
    return datetime.combine(date_value, time_value, ZoneInfo("Europe/London")).astimezone(
        timezone.utc
    )


def _git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _load_sources(
    manifest: dict[str, Any], data_root: Path
) -> tuple[dict[str, pd.DataFrame], dict[str, dict[str, Any]]]:
    entries = {str(entry["dataset_role"]): entry for entry in manifest["sources"]}
    required = {
        "fpl_gameweeks",
        "fpl_fixtures",
        "fpl_players",
        "fpl_teams",
        "match_results",
    }
    missing = sorted(required - set(entries))
    if missing:
        raise HistoricalEpisodeError(f"Dataset manifest is missing source roles: {missing}")
    frames: dict[str, pd.DataFrame] = {}
    for role in sorted(required):
        entry = entries[role]
        path = data_root / Path(str(entry["local_artifact"]))
        if not path.exists():
            raise HistoricalEpisodeError(f"Local benchmark source is missing: {path}")
        actual_hash = _file_hash(path)
        expected_hash = str(entry["content_hash_sha256"])
        if actual_hash != expected_hash:
            raise HistoricalEpisodeError(
                f"Source hash mismatch for {role}: expected={expected_hash}, actual={actual_hash}"
            )
        frames[role] = _read_csv(path)
    return frames, entries


def _deduplicate_gameweeks(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"GW", "element", "fixture", "kickoff_time", "total_points", "minutes"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise HistoricalEpisodeError(f"merged_gw missing required columns: {missing}")
    key = ["element", "GW", "fixture"]
    duplicates = frame.loc[frame.duplicated(subset=key, keep=False)]
    conflicts = [
        values
        for values, group in duplicates.groupby(key, dropna=False)
        if len(group.drop_duplicates()) > 1
    ]
    if conflicts:
        raise HistoricalEpisodeError(
            f"Conflicting merged_gw natural keys: {conflicts[:5]}"
        )
    return frame.drop_duplicates().reset_index(drop=True)


def _team_identity_map(
    *, season: str, teams: pd.DataFrame, players: pd.DataFrame, results: pd.DataFrame
) -> dict[str, Any]:
    if not {"id", "name"}.issubset(teams.columns):
        raise HistoricalEpisodeError("FPL team catalogue requires id and name")
    fpl_by_normalised: dict[str, dict[str, Any]] = {}
    team_records: list[dict[str, Any]] = []
    for row in teams[["id", "name"]].drop_duplicates().to_dict("records"):
        normalised = _normalise_name(str(row["name"]))
        canonical_id = f"team:{season}:{int(row['id'])}"
        record = {
            "canonical_id": canonical_id,
            "fpl_team_id": int(row["id"]),
            "fpl_name": str(row["name"]),
        }
        if normalised in fpl_by_normalised:
            raise HistoricalEpisodeError(f"Ambiguous normalised FPL team name: {row['name']}")
        fpl_by_normalised[normalised] = record
        team_records.append(record)

    result_names = sorted(
        {str(value) for value in results["HomeTeam"].dropna()}
        | {str(value) for value in results["AwayTeam"].dropna()}
    )
    result_mappings: list[dict[str, Any]] = []
    unresolved: list[str] = []
    for name in result_names:
        normalised = _normalise_name(name)
        target = FOOTBALL_DATA_TEAM_ALIASES.get(normalised, normalised)
        match = fpl_by_normalised.get(target)
        if match is None:
            unresolved.append(name)
            continue
        result_mappings.append(
            {
                "source_name": name,
                "canonical_id": match["canonical_id"],
                "resolution_method": "explicit_alias" if target != normalised else "exact_name",
            }
        )
    if unresolved:
        raise HistoricalEpisodeError(
            f"Unresolved football-data team identities: {unresolved}"
        )

    player_records = []
    required_player = {"id", "code", "team"}
    if not required_player.issubset(players.columns):
        raise HistoricalEpisodeError("FPL player catalogue requires id, code and team")
    valid_team_ids = {int(record["fpl_team_id"]) for record in team_records}
    for row in players[["id", "code", "team"]].drop_duplicates().to_dict("records"):
        if int(row["team"]) not in valid_team_ids:
            raise HistoricalEpisodeError(f"Player {row['id']} has unresolved team {row['team']}")
        player_records.append(
            {
                "canonical_id": f"player:{season}:{int(row['id'])}",
                "fpl_player_id": int(row["id"]),
                "fpl_code": int(row["code"]),
                "team_canonical_id": f"team:{season}:{int(row['team'])}",
            }
        )
    payload = {
        "identity_map_version": "1.0",
        "season": season,
        "teams": sorted(team_records, key=lambda row: row["fpl_team_id"]),
        "football_data_team_mappings": sorted(
            result_mappings, key=lambda row: row["source_name"]
        ),
        "players": sorted(player_records, key=lambda row: row["fpl_player_id"]),
        "metrics": {
            "teams": len(team_records),
            "football_data_teams_resolved": len(result_mappings),
            "football_data_teams_unresolved": 0,
            "players": len(player_records),
        },
    }
    payload["identity_map_id"] = _stable_hash(payload)
    return payload


def _result_records(
    frame: pd.DataFrame,
    identity_map: dict[str, Any],
) -> list[dict[str, Any]]:
    by_name = {
        row["source_name"]: row["canonical_id"]
        for row in identity_map["football_data_team_mappings"]
    }
    records: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        kickoff = _football_result_kickoff(row)
        records.append(
            {
                "kickoff_time": _utc_string(kickoff),
                "home_team_id": by_name[str(row["HomeTeam"])],
                "away_team_id": by_name[str(row["AwayTeam"])],
                "home_team_name": str(row["HomeTeam"]),
                "away_team_name": str(row["AwayTeam"]),
                "home_goals": int(row["FTHG"]),
                "away_goals": int(row["FTAG"]),
                "result": str(row.get("FTR", "")),
            }
        )
    return _sort_records(records, "kickoff_time", "home_team_id", "away_team_id")


def _source_artifact(
    *, source_id: str, role: str, gameweek: int, payload: Any, available_at: str
) -> dict[str, Any]:
    content_hash = _stable_hash(payload)
    return {
        "source_id": source_id,
        "artifact_id": f"historical:{role}:gw{gameweek:02d}:{content_hash[:16]}",
        "content_sha256": content_hash,
        "available_at": available_at,
    }


def _observed_hash(manifest: dict[str, Any]) -> str:
    projection = {
        key: value
        for key, value in manifest.items()
        if key not in {"created_at", "hidden_outcome_ref"}
    }
    return _stable_hash(projection)


def _validate_episode(manifest: dict[str, Any]) -> None:
    schema = json.loads(EPISODE_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(manifest)


def build_historical_episodes(
    *,
    dataset_manifest_path: Path = DEFAULT_DATASET_MANIFEST,
    out_dir: Path,
    data_root: Path | None = None,
    gameweeks: Iterable[int] | None = None,
    code_commit: str | None = None,
    rules_path: Path = DEFAULT_RULES,
) -> dict[str, Any]:
    """Build immutable local episode partitions and return a safe public index."""

    dataset_manifest = json.loads(dataset_manifest_path.read_text(encoding="utf-8"))
    if dataset_manifest.get("status") != "frozen":
        raise HistoricalEpisodeError("Historical episodes require a frozen dataset manifest")
    season = str(dataset_manifest["season"])
    rules, rules_hash, rules_payload = _validated_ruleset(rules_path, season)
    root = data_root or REPO_ROOT / "data" / "benchmark-v0" / season
    frames, source_entries = _load_sources(dataset_manifest, root)
    merged = _deduplicate_gameweeks(frames["fpl_gameweeks"])
    fixtures = frames["fpl_fixtures"]
    identity_map = _team_identity_map(
        season=season,
        teams=frames["fpl_teams"],
        players=frames["fpl_players"],
        results=frames["match_results"],
    )
    identity_hash = _stable_hash(identity_map)
    results = _result_records(frames["match_results"], identity_map)
    result_by_pair = {
        (row["home_team_id"], row["away_team_id"]): row for row in results
    }
    fpl_team_ids = {
        int(row["fpl_team_id"]): row["canonical_id"] for row in identity_map["teams"]
    }
    requested = sorted(
        {int(value) for value in (gameweeks or dataset_manifest["gameweeks"])}
    )
    available = {int(value) for value in dataset_manifest["gameweeks"]}
    unknown = sorted(set(requested) - available)
    if unknown:
        raise HistoricalEpisodeError(f"Gameweeks absent from frozen dataset: {unknown}")
    commit = code_commit or _git_commit()
    if len(commit) not in {40, 64} or any(char not in "0123456789abcdef" for char in commit):
        raise HistoricalEpisodeError(f"Invalid code commit: {commit}")

    ruleset_id = str(rules["meta"]["ruleset_id"])
    episodes: list[dict[str, Any]] = []
    for gameweek in requested:
        episode_id = f"benchmark-v0:{season}:gw{gameweek:02d}:manager-neutral"
        current_fixtures = fixtures.loc[fixtures["event"] == gameweek].copy()
        if current_fixtures.empty:
            raise HistoricalEpisodeError(f"No fixtures for Gameweek {gameweek}")
        kickoff_values = [_parse_kickoff(value) for value in current_fixtures["kickoff_time"]]
        deadline_at = min(kickoff_values) - timedelta(minutes=90)
        deadline = _utc_string(deadline_at)
        cutoff = deadline

        prior_gameweek = gameweek - 1
        lagged = merged.loc[merged["GW"] == prior_gameweek].copy()
        if not lagged.empty:
            lagged = lagged.loc[
                lagged["kickoff_time"].map(_parse_kickoff) < deadline_at
            ]
        lagged_records = _sort_records(
            _json_records(lagged, LAGGED_PLAYER_FIELDS), "element", "fixture"
        )
        fixture_records = _sort_records(
            _json_records(current_fixtures, OBSERVED_FIXTURE_FIELDS), "id"
        )
        prior_results = [
            row for row in results if _parse_kickoff(row["kickoff_time"]) < deadline_at
        ]
        limitations = [
            "historical_news_unavailable",
            "historical_manager_state_unavailable",
            "final_export_fixture_revision_not_archived",
            "fixture_deadline_derived_as_first_kickoff_minus_90_minutes",
            "untimestamped_market_odds_excluded",
            "unshifted_vaastav_xP_excluded",
        ]
        if gameweek == 1:
            limitations.append("cold_start_no_prior_gameweek")
        observed = {
            "observed_partition_version": "1.0",
            "episode_id": episode_id,
            "season": season,
            "gameweek": gameweek,
            "cutoff": cutoff,
            "deadline": deadline,
            "dataset_id": str(dataset_manifest["dataset_id"]),
            "dataset_hash": str(dataset_manifest["dataset_hash"]),
            "lagged_from_gameweek": prior_gameweek if gameweek > 1 else None,
            "lagged_player_features": lagged_records,
            "fixtures": fixture_records,
            "prior_match_results": prior_results,
            "identity_map_ref": {
                "artifact_id": identity_map["identity_map_id"],
                "content_sha256": identity_hash,
            },
            "limitations": sorted(limitations),
        }
        current_outcomes = _sort_records(
            _json_records(merged.loc[merged["GW"] == gameweek]), "element", "fixture"
        )
        hidden_fixtures = _sort_records(_json_records(current_fixtures), "id")
        current_pairs = {
            (fpl_team_ids[int(row["team_h"])], fpl_team_ids[int(row["team_a"])])
            for row in current_fixtures.to_dict("records")
        }
        hidden_results = [result_by_pair[pair] for pair in sorted(current_pairs) if pair in result_by_pair]
        hidden = {
            "hidden_outcome_version": "1.0",
            "episode_id": episode_id,
            "season": season,
            "gameweek": gameweek,
            "reveal_after": "proposal_frozen",
            "player_outcomes": current_outcomes,
            "fixtures": hidden_fixtures,
            "match_results": hidden_results,
        }
        manager_state = {
            "manager_state_placeholder_version": "1.0",
            "episode_id": episode_id,
            "status": "unavailable_requires_policy_state",
            "owner_bead": "FPL-bsw.12",
        }
        uncertainty = {
            "forecast_uncertainty_version": "1.0",
            "episode_id": episode_id,
            "status": "not_yet_forecast",
            "limitations": sorted(limitations),
            "lagged_player_rows": len(lagged_records),
            "fixture_rows": len(fixture_records),
        }
        observed_hash = _stable_hash(observed)
        hidden_hash = _stable_hash(hidden)
        manager_hash = _stable_hash(manager_state)
        uncertainty_hash = _stable_hash(uncertainty)
        source_artifacts = [
            _source_artifact(
                source_id="vaastav-fpl",
                role="lagged-player-features",
                gameweek=gameweek,
                payload=lagged_records,
                available_at=cutoff,
            ),
            _source_artifact(
                source_id="vaastav-fpl",
                role="fixture-schedule",
                gameweek=gameweek,
                payload=fixture_records,
                available_at=cutoff,
            ),
            _source_artifact(
                source_id="football-data-co-uk",
                role="prior-match-results",
                gameweek=gameweek,
                payload=prior_results,
                available_at=cutoff,
            ),
            _source_artifact(
                source_id="benchmark-v0-identity-map",
                role="identity-map",
                gameweek=gameweek,
                payload=identity_map,
                available_at=cutoff,
            ),
        ]
        manifest = {
            "schema_version": "1.0",
            "episode_id": episode_id,
            "season": season,
            "gameweek": gameweek,
            "mode": "historical_structured",
            "cutoff": cutoff,
            "deadline": deadline,
            "created_at": str(dataset_manifest["created_at"]),
            "code_commit": commit,
            "ruleset": {
                "ruleset_id": ruleset_id,
                "content_sha256": rules_hash,
            },
            "observed": {
                "snapshot_ids": sorted(
                    {str(entry["content_identity"]) for entry in source_entries.values()}
                ),
                "source_artifacts": source_artifacts,
                "manager_state_ref": {
                    "artifact_id": f"manager-state:{episode_id}",
                    "content_sha256": manager_hash,
                },
                "feature_snapshot_ref": {
                    "artifact_id": f"observed:{episode_id}",
                    "content_sha256": observed_hash,
                },
                "forecast_uncertainty_ref": {
                    "artifact_id": f"uncertainty:{episode_id}",
                    "content_sha256": uncertainty_hash,
                },
            },
            "allowed_tools": [
                {
                    "tool_id": "historical-structured-feature-query",
                    "version": "1.0",
                    "access": "read_only",
                }
            ],
            "resource_budget": {
                "wall_clock_seconds": 120,
                "tool_calls": 0,
                "tokens": 0,
                "cost_currency": "GBP",
                "cost_cap": 0,
            },
            "policy_arms": list(POLICY_ARMS),
            "hidden_outcome_ref": {
                "outcome_id": f"hidden:{episode_id}",
                "content_sha256": hidden_hash,
                "reveal_after": "proposal_frozen",
            },
        }
        _validate_episode(manifest)
        pairing_hash = _observed_hash(manifest)
        episode_dir = out_dir / f"gw-{gameweek:02d}"
        _write_immutable(episode_dir / "identity-map.json", identity_map)
        _write_immutable_bytes(episode_dir / "ruleset.yaml", rules_payload)
        _write_immutable(episode_dir / "manager-state.json", manager_state)
        _write_immutable(episode_dir / "forecast-uncertainty.json", uncertainty)
        _write_immutable(episode_dir / "observed.json", observed)
        _write_immutable(episode_dir / "hidden-outcome.json", hidden)
        _write_immutable(episode_dir / "episode-manifest.json", manifest)
        episodes.append(
            {
                "episode_id": episode_id,
                "season": season,
                "gameweek": gameweek,
                "cutoff": cutoff,
                "deadline": deadline,
                "observed_episode_sha256": pairing_hash,
                "observed_partition_sha256": observed_hash,
                "hidden_outcome_sha256": hidden_hash,
                "identity_map_sha256": identity_hash,
                "ruleset_id": ruleset_id,
                "ruleset_sha256": rules_hash,
                "observed_rows": len(lagged_records) + len(fixture_records) + len(prior_results),
                "lagged_player_rows": len(lagged_records),
                "fixture_rows": len(fixture_records),
                "prior_match_result_rows": len(prior_results),
                "hidden_player_rows": len(current_outcomes),
                "hidden_fixture_rows": len(hidden_fixtures),
                "limitations": sorted(limitations),
            }
        )
    index = {
        "index_version": "1.0",
        "dataset_id": str(dataset_manifest["dataset_id"]),
        "dataset_hash": str(dataset_manifest["dataset_hash"]),
        "season": season,
        "episode_count": len(episodes),
        "episodes": episodes,
    }
    if len({_stable_hash(row) for row in episodes}) != len(episodes):
        raise HistoricalEpisodeError("Historical episode index contains duplicate entries")
    return index


def write_episode_index(index: dict[str, Any], path: Path) -> None:
    """Persist a safe, row-free episode index without replacing different content."""

    _write_immutable(path, index)
