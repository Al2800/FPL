"""Build immutable, point-in-time set-piece role snapshots and ledgers."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from typing import Any, Iterable, Mapping


SOURCE_ID = "fpl-official-endpoints"
ROLE_FIELDS = {
    "penalty": ("penalties_order", "penalties_text"),
    "direct_free_kick": ("direct_freekicks_order", "direct_freekicks_text"),
    "corner_or_indirect_free_kick": (
        "corners_and_indirect_freekicks_order",
        "corners_and_indirect_freekicks_text",
    ),
}
RANK_CONFIDENCE = {
    1: 0.95,
    2: 0.80,
    3: 0.65,
    4: 0.50,
    5: 0.40,
    6: 0.32,
    7: 0.28,
    8: 0.24,
    9: 0.22,
    10: 0.20,
}


class SetPieceRoleError(ValueError):
    """Raised when role evidence is malformed, ambiguous, or temporally unsafe."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def artifact_hash(value: Mapping[str, Any]) -> str:
    """Hash a role artifact without its circular content hash."""

    return hashlib.sha256(
        _canonical_bytes(
            {
                key: deepcopy(item)
                for key, item in value.items()
                if key != "content_sha256"
            }
        )
    ).hexdigest()


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise SetPieceRoleError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise SetPieceRoleError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _positive_int(value: Any, field: str) -> int:
    if value is None or value == "":
        raise SetPieceRoleError(f"{field} is missing")
    if isinstance(value, bool):
        raise SetPieceRoleError(f"{field} must be a positive integer")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise SetPieceRoleError(f"{field} must be a positive integer") from exc
    if not math.isfinite(number) or number <= 0 or not number.is_integer():
        raise SetPieceRoleError(f"{field} must be a positive integer")
    return int(number)


def _stable_id(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def normalise_official_set_piece_snapshot(
    bootstrap: Mapping[str, Any],
    *,
    source_sha256: str,
    observed_at: str,
    available_at: str,
    expiry_hours: int = 192,
) -> dict[str, Any]:
    """Normalise one official bootstrap into complete club-role groups."""

    if len(source_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in source_sha256
    ):
        raise SetPieceRoleError("source_sha256 must be a lowercase SHA-256")
    observed_text, observed = _timestamp(observed_at, "observed_at")
    available_text, available = _timestamp(available_at, "available_at")
    if available < observed:
        raise SetPieceRoleError("available_at cannot be before observed_at")
    if isinstance(expiry_hours, bool) or int(expiry_hours) <= 0:
        raise SetPieceRoleError("expiry_hours must be positive")
    expires = available + timedelta(hours=int(expiry_hours))
    expires_text = expires.isoformat().replace("+00:00", "Z")

    raw_teams = list(bootstrap.get("teams", []))
    teams: dict[int, str] = {}
    for raw in raw_teams:
        team_id = _positive_int(raw.get("id"), "team.id")
        if team_id in teams:
            raise SetPieceRoleError(f"Duplicate official team id: {team_id}")
        teams[team_id] = str(raw.get("name", "")).strip()
    if not teams:
        raise SetPieceRoleError("Official bootstrap contains no teams")

    raw_players = list(bootstrap.get("elements", []))
    players: dict[int, dict[str, Any]] = {}
    for raw in raw_players:
        player_id = _positive_int(raw.get("id"), "element.id")
        team_id = _positive_int(raw.get("team"), "element.team")
        if team_id not in teams:
            raise SetPieceRoleError(
                f"Player {player_id} references unknown team {team_id}"
            )
        if player_id in players:
            raise SetPieceRoleError(f"Duplicate official player id: {player_id}")
        players[player_id] = deepcopy(dict(raw))

    groups: list[dict[str, Any]] = []
    for team_id in sorted(teams):
        for role, (order_field, text_field) in ROLE_FIELDS.items():
            assignments: list[dict[str, Any]] = []
            ranks: dict[int, list[int]] = {}
            for player_id, player in sorted(players.items()):
                if int(player["team"]) != team_id:
                    continue
                raw_rank = player.get(order_field)
                if raw_rank in (None, ""):
                    continue
                rank = _positive_int(raw_rank, f"{order_field}.{player_id}")
                confidence = RANK_CONFIDENCE.get(rank, 0.20)
                observation_key = {
                    "source_sha256": source_sha256,
                    "team_id": team_id,
                    "role": role,
                    "player_id": player_id,
                    "rank": rank,
                }
                assignments.append(
                    {
                        "observation_id": _stable_id(observation_key),
                        "official_player_id": player_id,
                        "player_name": str(player.get("web_name", "")),
                        "official_team_id": team_id,
                        "team_name": teams[team_id],
                        "role": role,
                        "rank": rank,
                        "confidence": confidence,
                        "source_text": (
                            str(player.get(text_field))
                            if player.get(text_field) not in (None, "")
                            else None
                        ),
                        "observed_at": observed_text,
                        "available_at": available_text,
                        "expires_at": expires_text,
                        "source_id": SOURCE_ID,
                        "source_sha256": source_sha256,
                    }
                )
                ranks.setdefault(rank, []).append(player_id)
            conflicts = [
                {
                    "type": "duplicate_rank",
                    "rank": rank,
                    "official_player_ids": sorted(player_ids),
                }
                for rank, player_ids in sorted(ranks.items())
                if len(player_ids) > 1
            ]
            assignments.sort(
                key=lambda row: (row["rank"], row["official_player_id"])
            )
            group_identity = {
                "source_sha256": source_sha256,
                "team_id": team_id,
                "role": role,
                "assignments": [
                    (row["official_player_id"], row["rank"]) for row in assignments
                ],
            }
            groups.append(
                {
                    "group_id": _stable_id(group_identity),
                    "official_team_id": team_id,
                    "team_name": teams[team_id],
                    "role": role,
                    "status": (
                        "conflicted"
                        if conflicts
                        else "active"
                        if assignments
                        else "unknown"
                    ),
                    "assignments": assignments,
                    "conflicts": conflicts,
                    "observed_at": observed_text,
                    "available_at": available_text,
                    "expires_at": expires_text,
                    "source_sha256": source_sha256,
                }
            )

    result: dict[str, Any] = {
        "schema_version": "1.0",
        "source_id": SOURCE_ID,
        "source_sha256": source_sha256,
        "observed_at": observed_text,
        "available_at": available_text,
        "expires_at": expires_text,
        "replacement_boundary": "whole_team_role_group",
        "team_count": len(teams),
        "player_count": len(players),
        "group_count": len(groups),
        "assignment_count": sum(len(group["assignments"]) for group in groups),
        "conflict_count": sum(len(group["conflicts"]) for group in groups),
        "unknown_group_count": sum(group["status"] == "unknown" for group in groups),
        "groups": groups,
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def build_set_piece_role_ledger(
    snapshots: Iterable[Mapping[str, Any]],
    *,
    as_of: str,
) -> dict[str, Any]:
    """Select the latest complete club-role group available at an as-of time."""

    as_of_text, as_of_time = _timestamp(as_of, "as_of")
    admissible: list[dict[str, Any]] = []
    excluded_future: list[str] = []
    for raw in snapshots:
        snapshot = deepcopy(dict(raw))
        snapshot_id = str(snapshot.get("content_sha256", ""))
        if snapshot_id != artifact_hash(snapshot):
            raise SetPieceRoleError("Set-piece snapshot content hash mismatch")
        _, available = _timestamp(snapshot.get("available_at"), "available_at")
        if available > as_of_time:
            excluded_future.append(snapshot_id)
        else:
            admissible.append(snapshot)
    admissible.sort(
        key=lambda value: (
            str(value["available_at"]),
            str(value["observed_at"]),
            str(value["content_sha256"]),
        )
    )

    histories: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for snapshot in admissible:
        for raw_group in snapshot.get("groups", []):
            group = deepcopy(dict(raw_group))
            key = (int(group["official_team_id"]), str(group["role"]))
            group["snapshot_content_sha256"] = snapshot["content_sha256"]
            histories.setdefault(key, []).append(group)

    resolved_groups: list[dict[str, Any]] = []
    active_roles: list[dict[str, Any]] = []
    unknowns: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    expired: list[dict[str, Any]] = []
    for key in sorted(histories):
        history = histories[key]
        latest = deepcopy(history[-1])
        latest["superseded_group_ids"] = [
            group["group_id"] for group in history[:-1]
        ]
        _, expiry = _timestamp(latest["expires_at"], "expires_at")
        if as_of_time >= expiry:
            latest["resolved_status"] = "expired"
            expired.append(
                {
                    "official_team_id": key[0],
                    "role": key[1],
                    "group_id": latest["group_id"],
                }
            )
        elif latest["status"] == "conflicted":
            latest["resolved_status"] = "conflicted"
            conflicts.append(
                {
                    "official_team_id": key[0],
                    "role": key[1],
                    "group_id": latest["group_id"],
                    "conflicts": deepcopy(latest["conflicts"]),
                }
            )
        elif latest["status"] == "unknown":
            latest["resolved_status"] = "unknown"
            unknowns.append(
                {
                    "official_team_id": key[0],
                    "role": key[1],
                    "group_id": latest["group_id"],
                }
            )
        else:
            latest["resolved_status"] = "active"
            active_roles.extend(deepcopy(latest["assignments"]))
        resolved_groups.append(latest)

    degraded = not resolved_groups or bool(
        excluded_future or conflicts or unknowns or expired
    )
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "as_of": as_of_text,
        "status": "degraded" if degraded else "complete",
        "admissible_snapshot_ids": [
            value["content_sha256"] for value in admissible
        ],
        "excluded_future_snapshot_ids": sorted(excluded_future),
        "resolved_groups": resolved_groups,
        "active_roles": sorted(
            active_roles,
            key=lambda row: (
                row["official_team_id"],
                row["role"],
                row["rank"],
                row["official_player_id"],
            ),
        ),
        "unknowns": unknowns,
        "conflicts": conflicts,
        "expired": expired,
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def build_set_piece_feature_payload(
    ledger: Mapping[str, Any],
) -> dict[str, Any]:
    """Expose role signals without inventing a forecast effect or silent fallback."""

    value = deepcopy(dict(ledger))
    if value.get("content_sha256") != artifact_hash(value):
        raise SetPieceRoleError("Set-piece ledger content hash mismatch")
    adjustments = [
        {
            "official_player_id": row["official_player_id"],
            "official_team_id": row["official_team_id"],
            "role": row["role"],
            "rank": row["rank"],
            "confidence": row["confidence"],
            "observation_id": row["observation_id"],
        }
        for row in value.get("active_roles", [])
    ]
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "family": "set_piece_role",
        "ledger_content_sha256": value["content_sha256"],
        "status": "shadow_ready" if adjustments else "degraded",
        "adjustments": adjustments,
        "effect_weights": None,
        "promotion_status": "shadow_only_pending_point_in_time_ablation",
        "fallback": (
            None if adjustments else "byte_identical_baseline"
        ),
    }
    result["content_sha256"] = artifact_hash(result)
    return result
