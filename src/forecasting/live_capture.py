"""Build immutable, cutoff-safe inputs for the live forecast pipeline."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping, Sequence


class LiveForecastCaptureError(ValueError):
    """Raised when live forecast evidence is ambiguous, late, or unapproved."""


MARKET_SLOTS = ("T-24h", "T-8h", "T-2h", "final")
POSITIONS = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def artifact_hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        _canonical_bytes(
            {key: item for key, item in value.items() if key != "content_sha256"}
        )
    ).hexdigest()


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise LiveForecastCaptureError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise LiveForecastCaptureError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _source(registry: Mapping[str, Any], source_id: str) -> dict[str, Any]:
    for value in registry.get("sources", []):
        if value.get("source_id") == source_id:
            return deepcopy(dict(value))
    raise LiveForecastCaptureError(f"Market source is not registered: {source_id}")


def _approved_market_source(registry: Mapping[str, Any], source_id: str) -> dict[str, Any]:
    source = _source(registry, source_id)
    if not source.get("enabled"):
        raise LiveForecastCaptureError(f"Market source is disabled: {source_id}")
    approval = source.get("activation_approval")
    if not isinstance(approval, Mapping):
        raise LiveForecastCaptureError(
            f"Market source has no explicit activation approval: {source_id}"
        )
    if approval.get("terms") != "approved" or approval.get("cost") != "approved":
        raise LiveForecastCaptureError(
            f"Market source terms and cost are not approved: {source_id}"
        )
    return source


def _launch_context(
    value: Mapping[str, Any] | None,
    *,
    teams: set[int],
    player_codes: set[int],
) -> tuple[set[int], set[int], dict[str, Any]]:
    context = deepcopy(dict(value or {}))
    promoted = {int(item) for item in context.get("promoted_team_ids", [])}
    transferred = {int(item) for item in context.get("transferred_player_codes", [])}
    if not promoted <= teams:
        raise LiveForecastCaptureError("Launch context contains an unknown promoted team")
    if not transferred <= player_codes:
        raise LiveForecastCaptureError(
            "Launch context contains an unknown transferred player"
        )
    return promoted, transferred, {
        "promoted_team_ids": sorted(promoted),
        "transferred_player_codes": sorted(transferred),
        "classification_policy": (
            "promoted_team_then_transferred_player_then_established"
        ),
        "fallback_policy": {
            "promoted_team": "position_price_prior_with_promoted_team_shrinkage",
            "transferred_player": "stable_code_prior_with_new_club_minutes_shrinkage",
            "established": "stable_code_prior_then_position_price_fallback",
        },
    }


def _market_snapshot(
    value: Mapping[str, Any],
    *,
    cutoff: datetime,
    registry: Mapping[str, Any],
) -> dict[str, Any]:
    snapshot = deepcopy(dict(value))
    source_id = str(snapshot.get("source_id", ""))
    _approved_market_source(registry, source_id)
    slot = str(snapshot.get("slot", ""))
    if slot not in MARKET_SLOTS:
        raise LiveForecastCaptureError(f"Unknown market capture slot: {slot}")
    observed_at, observed = _timestamp(
        snapshot.get("observed_at"), "market_snapshot.observed_at"
    )
    available_at, available = _timestamp(
        snapshot.get("available_at"), "market_snapshot.available_at"
    )
    if observed >= cutoff or available >= cutoff:
        raise LiveForecastCaptureError(
            "Market snapshot observed_at and available_at must be strictly before cutoff"
        )
    payload = snapshot.get("payload")
    if not isinstance(payload, Mapping):
        raise LiveForecastCaptureError("Market snapshot payload must be an object")
    source_sha256 = str(snapshot.get("source_sha256", ""))
    expected_hash = hashlib.sha256(_canonical_bytes(payload)).hexdigest()
    if source_sha256 != expected_hash:
        raise LiveForecastCaptureError("Market snapshot source hash mismatch")
    return {
        "slot": slot,
        "source_id": source_id,
        "observed_at": observed_at,
        "available_at": available_at,
        "source_sha256": source_sha256,
        "market_count": len(payload.get("markets", [])),
    }


def build_live_forecast_capture(
    *,
    bootstrap: Mapping[str, Any],
    bootstrap_manifest: Mapping[str, Any],
    observed_at: str,
    decision_cutoff: str,
    launch_context: Mapping[str, Any] | None,
    market_snapshots: Sequence[Mapping[str, Any]],
    source_registry: Mapping[str, Any],
    freeze_launch: bool,
) -> dict[str, Any]:
    """Return a self-hashed launch and market evidence contract."""

    observed_text, observed = _timestamp(observed_at, "observed_at")
    cutoff_text, cutoff = _timestamp(decision_cutoff, "decision_cutoff")
    if observed >= cutoff:
        raise LiveForecastCaptureError("Official capture must be before decision cutoff")
    source_hash = str(bootstrap_manifest.get("content_hash_sha256", ""))
    if len(source_hash) != 64:
        raise LiveForecastCaptureError("Bootstrap manifest has no valid source hash")

    events = list(bootstrap.get("events", []))
    gw1 = next((item for item in events if int(item.get("id", 0)) == 1), None)
    if gw1 is None:
        raise LiveForecastCaptureError("Official bootstrap has no GW1 deadline")
    gw1_text, gw1_deadline = _timestamp(gw1.get("deadline_time"), "GW1 deadline")
    if freeze_launch and observed >= gw1_deadline:
        raise LiveForecastCaptureError("Launch state must be frozen before the GW1 deadline")

    teams: list[dict[str, Any]] = []
    team_ids: set[int] = set()
    for source in bootstrap.get("teams", []):
        team_id = int(source["id"])
        if team_id in team_ids:
            raise LiveForecastCaptureError(f"Duplicate official team: {team_id}")
        team_ids.add(team_id)
        teams.append(
            {
                "team_id": team_id,
                "name": str(source["name"]),
                "strength": source.get("strength"),
                "strength_attack_home": source.get("strength_attack_home"),
                "strength_attack_away": source.get("strength_attack_away"),
                "strength_defence_home": source.get("strength_defence_home"),
                "strength_defence_away": source.get("strength_defence_away"),
                "observed_at": observed_text,
                "available_at": observed_text,
                "source_sha256": source_hash,
            }
        )

    raw_players = list(bootstrap.get("elements", []))
    player_codes = {int(source["code"]) for source in raw_players}
    promoted, transferred, context = _launch_context(
        launch_context, teams=team_ids, player_codes=player_codes
    )
    players: list[dict[str, Any]] = []
    seen_players: set[int] = set()
    for source in raw_players:
        player_id = int(source["id"])
        if player_id in seen_players:
            raise LiveForecastCaptureError(f"Duplicate official player: {player_id}")
        seen_players.add(player_id)
        team_id = int(source["team"])
        code = int(source["code"])
        try:
            position = POSITIONS[int(source["element_type"])]
        except KeyError as exc:
            raise LiveForecastCaptureError(
                f"Unknown official position for player {player_id}"
            ) from exc
        prior_class = (
            "promoted_team"
            if team_id in promoted
            else "transferred_player"
            if code in transferred
            else "established"
        )
        players.append(
            {
                "player_id": player_id,
                "fpl_code": code,
                "web_name": str(source["web_name"]),
                "team_id": team_id,
                "position": position,
                "launch_price": round(float(source["now_cost"]) / 10.0, 1),
                "availability": {
                    "status": source.get("status"),
                    "news": source.get("news"),
                    "news_added": source.get("news_added"),
                    "chance_of_playing_this_round": source.get(
                        "chance_of_playing_this_round"
                    ),
                    "chance_of_playing_next_round": source.get(
                        "chance_of_playing_next_round"
                    ),
                },
                "cold_start_class": prior_class,
                "observed_at": observed_text,
                "available_at": observed_text,
                "source_sha256": source_hash,
            }
        )

    admitted_market: list[dict[str, Any]] = []
    rejected_market: list[dict[str, str]] = []
    for snapshot in market_snapshots:
        try:
            admitted_market.append(
                _market_snapshot(snapshot, cutoff=cutoff, registry=source_registry)
            )
        except LiveForecastCaptureError as exc:
            rejected_market.append(
                {
                    "source_id": str(snapshot.get("source_id", "unknown")),
                    "slot": str(snapshot.get("slot", "unknown")),
                    "reason": str(exc),
                }
            )
    by_slot: dict[str, dict[str, Any]] = {}
    for snapshot in admitted_market:
        slot = snapshot["slot"]
        if slot in by_slot:
            raise LiveForecastCaptureError(f"Duplicate admitted market slot: {slot}")
        by_slot[slot] = snapshot
    missing_slots = [slot for slot in MARKET_SLOTS if slot not in by_slot]
    degraded = [
        {
            "feature": "timestamped_odds",
            "slot": slot,
            "reason": "no_approved_pre_cutoff_snapshot",
        }
        for slot in missing_slots
    ]
    degraded.extend(
        {
            "feature": "timestamped_odds",
            "slot": value["slot"],
            "reason": value["reason"],
        }
        for value in rejected_market
    )

    result: dict[str, Any] = {
        "schema_version": "1.0",
        "observed_at": observed_text,
        "decision_cutoff": cutoff_text,
        "official_launch": {
            "status": "frozen" if freeze_launch else "observed_not_frozen",
            "gw1_deadline": gw1_text,
            "source_id": "fpl-official-endpoints",
            "source_sha256": source_hash,
            "players": sorted(players, key=lambda row: row["player_id"]),
            "teams": sorted(teams, key=lambda row: row["team_id"]),
        },
        "cold_start_priors": context,
        "market_evidence": {
            "required_slots": list(MARKET_SLOTS),
            "snapshots": [by_slot[slot] for slot in MARKET_SLOTS if slot in by_slot],
            "rejected": rejected_market,
        },
        "degraded_features": degraded,
        "feature_contract": {
            "player_identity": "fpl_code",
            "player_prior_join": "stable_fpl_code_then_position_price_fallback",
            "team_prior_join": "official_team_id_to_canonical_team",
            "availability_fields": [
                "status",
                "news",
                "news_added",
                "chance_of_playing_this_round",
                "chance_of_playing_next_round",
            ],
            "forecast_interface": "live-faithful-v1",
        },
    }
    result["content_sha256"] = artifact_hash(result)
    return result
