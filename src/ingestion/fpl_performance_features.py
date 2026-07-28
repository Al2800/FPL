"""Point-in-time FPL-native player performance feature snapshots."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class FplPerformanceError(ValueError):
    """Raised when official FPL inputs cannot form a safe weekly snapshot."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def payload_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def artifact_hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        _canonical_bytes(
            {
                key: deepcopy(item)
                for key, item in value.items()
                if key != "content_sha256"
            }
        )
    ).hexdigest()


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    if not isinstance(value, str) or not value:
        raise FplPerformanceError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FplPerformanceError(
            f"{field} must be an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise FplPerformanceError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise FplPerformanceError(f"{field} must be a positive integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise FplPerformanceError(
            f"{field} must be a positive integer"
        ) from exc
    if parsed < 1:
        raise FplPerformanceError(f"{field} must be a positive integer")
    return parsed


def _metric_number(value: Any, *, kind: str) -> int | float:
    if value is None or isinstance(value, bool):
        raise ValueError("metric is not numeric")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("metric is not numeric") from exc
    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError("metric must be finite and non-negative")
    if kind == "integer":
        if not parsed.is_integer():
            raise ValueError("integer metric is not whole")
        return int(parsed)
    if kind == "decimal":
        return round(parsed, 6)
    raise FplPerformanceError(f"Unsupported metric kind: {kind}")


def _field_value(
    row: Mapping[str, Any],
    metric: Mapping[str, Any],
) -> tuple[int | float | None, str | None]:
    for field in metric["source_fields"]:
        if field in row:
            try:
                return (
                    _metric_number(row[field], kind=str(metric["kind"])),
                    str(field),
                )
            except ValueError:
                return None, str(field)
    return None, None


def _validate_envelope(
    source: Mapping[str, Any],
    *,
    label: str,
    cutoff: datetime,
) -> tuple[dict[str, Any], dict[str, str]]:
    required = {
        "manifest_id",
        "source_sha256",
        "payload_sha256",
        "observed_at",
        "available_at",
        "payload",
    }
    missing = sorted(required - set(source))
    if missing:
        raise FplPerformanceError(
            f"{label} envelope missing: " + ", ".join(missing)
        )
    manifest_id = str(source["manifest_id"])
    if not manifest_id:
        raise FplPerformanceError(f"{label} manifest_id must be non-empty")
    for field in ("source_sha256", "payload_sha256"):
        if not _SHA256.fullmatch(str(source[field])):
            raise FplPerformanceError(
                f"{label} {field} must be a lowercase SHA-256"
            )
    observed_text, observed = _timestamp(
        source["observed_at"], f"{label}.observed_at"
    )
    available_text, available = _timestamp(
        source["available_at"], f"{label}.available_at"
    )
    if observed > available:
        raise FplPerformanceError(
            f"{label} observed_at cannot follow available_at"
        )
    if available > cutoff:
        raise FplPerformanceError(f"{label} is after cutoff")
    payload = deepcopy(source["payload"])
    if str(source["payload_sha256"]) != payload_hash(payload):
        raise FplPerformanceError(f"{label} payload hash mismatch")
    if not isinstance(payload, Mapping):
        raise FplPerformanceError(f"{label} payload must be an object")
    return deepcopy(dict(payload)), {
        "label": label,
        "manifest_id": manifest_id,
        "source_sha256": str(source["source_sha256"]),
        "payload_sha256": str(source["payload_sha256"]),
        "observed_at": observed_text,
        "available_at": available_text,
    }


def _element_index(
    payload: Mapping[str, Any],
    *,
    label: str,
) -> tuple[dict[int, dict[str, Any]], dict[int, dict[str, Any]]]:
    rows = payload.get("elements")
    if not isinstance(rows, list):
        raise FplPerformanceError(f"{label}.elements must be a list")
    by_id: dict[int, dict[str, Any]] = {}
    by_code: dict[int, dict[str, Any]] = {}
    for index, source in enumerate(rows):
        if not isinstance(source, Mapping):
            raise FplPerformanceError(
                f"{label}.elements[{index}] must be an object"
            )
        row = deepcopy(dict(source))
        player_id = _positive_int(row.get("id"), f"{label}.elements.id")
        code = _positive_int(row.get("code"), f"{label}.elements.code")
        if player_id in by_id or code in by_code:
            raise FplPerformanceError(
                f"{label} has duplicate player ID or stable code"
            )
        by_id[player_id] = row
        by_code[code] = row
    return by_id, by_code


def _event_index(payload: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    rows = payload.get("elements")
    if not isinstance(rows, list):
        raise FplPerformanceError("event_live.elements must be a list")
    result: dict[int, dict[str, Any]] = {}
    for index, source in enumerate(rows):
        if not isinstance(source, Mapping):
            raise FplPerformanceError(
                f"event_live.elements[{index}] must be an object"
            )
        row = deepcopy(dict(source))
        player_id = _positive_int(
            row.get("id"), f"event_live.elements[{index}].id"
        )
        if player_id in result:
            raise FplPerformanceError(
                f"event_live has duplicate player ID: {player_id}"
            )
        if not isinstance(row.get("stats"), Mapping):
            raise FplPerformanceError(
                f"event_live player {player_id} stats must be an object"
            )
        result[player_id] = row
    return result


def _summary_rows(
    source: Mapping[str, Any] | None,
    *,
    gameweek: int,
) -> tuple[list[dict[str, Any]] | None, list[int]]:
    if source is None:
        return None, []
    payload = source["payload"]
    history = payload.get("history")
    if not isinstance(history, list):
        raise FplPerformanceError("element-summary history must be a list")
    rows: list[dict[str, Any]] = []
    fixture_ids: list[int] = []
    for index, value in enumerate(history):
        if not isinstance(value, Mapping):
            raise FplPerformanceError(
                f"element-summary history[{index}] must be an object"
            )
        if int(value.get("round", -1)) != gameweek:
            continue
        row = deepcopy(dict(value))
        fixture = _positive_int(
            row.get("fixture"), "element-summary history.fixture"
        )
        if fixture in fixture_ids:
            raise FplPerformanceError(
                "element-summary has duplicate fixture row"
            )
        fixture_ids.append(fixture)
        rows.append(row)
    rows.sort(key=lambda row: int(row["fixture"]))
    return rows, sorted(fixture_ids)


def _summed_metric(
    rows: list[dict[str, Any]] | None,
    metric: Mapping[str, Any],
) -> tuple[int | float | None, str]:
    if rows is None:
        return None, "not_captured"
    if not rows:
        return 0 if metric["kind"] == "integer" else 0.0, "blank"
    values: list[int | float] = []
    for row in rows:
        value, field = _field_value(row, metric)
        if field is None:
            return None, "field_missing"
        if value is None:
            return None, "schema_invalid"
        values.append(value)
    total = sum(float(value) for value in values)
    if metric["kind"] == "integer":
        return int(total), "captured"
    return round(total, 6), "captured"


def _cumulative_delta(
    before: Mapping[str, Any] | None,
    after: Mapping[str, Any],
    metric: Mapping[str, Any],
) -> tuple[int | float | None, str]:
    if before is None:
        return None, "no_prior_player"
    prior, prior_field = _field_value(before, metric)
    current, current_field = _field_value(after, metric)
    if prior_field is None or current_field is None:
        return None, "field_missing"
    if prior is None or current is None:
        return None, "schema_invalid"
    delta = float(current) - float(prior)
    if delta < -1e-9:
        return None, "cumulative_decrease"
    if metric["kind"] == "integer":
        return int(round(delta)), "captured"
    return round(delta, 6), "captured"


def _metric_record(
    *,
    metric: Mapping[str, Any],
    event_stats: Mapping[str, Any] | None,
    summary_rows: list[dict[str, Any]] | None,
    before: Mapping[str, Any] | None,
    after: Mapping[str, Any],
) -> dict[str, Any]:
    event_value: int | float | None = None
    event_state = "player_missing"
    if event_stats is not None:
        event_value, event_field = _field_value(event_stats, metric)
        if event_field is None:
            event_state = "field_missing"
        elif event_value is None:
            event_state = "schema_invalid"
        else:
            event_state = "captured"
    summary_value, summary_state = _summed_metric(summary_rows, metric)
    delta_value, delta_state = _cumulative_delta(before, after, metric)

    reasons: list[str] = []
    required = bool(metric["required"])
    if event_state != "captured":
        reasons.append(f"event_live:{event_state}")
    tolerance = float(metric["tolerance"])
    comparisons = {
        "event_live": {
            "value": event_value,
            "status": event_state,
        },
        "element_summary_sum": {
            "value": summary_value,
            "status": summary_state,
        },
        "bootstrap_delta": {
            "value": delta_value,
            "status": delta_state,
        },
    }
    if event_value is not None:
        for label, candidate, state in (
            ("element_summary", summary_value, summary_state),
            ("bootstrap_delta", delta_value, delta_state),
        ):
            if candidate is not None and state in {"captured", "blank"}:
                if abs(float(event_value) - float(candidate)) > tolerance:
                    reasons.append(f"{label}:disagreement")
    if delta_state == "cumulative_decrease":
        reasons.append("bootstrap_delta:cumulative_decrease")

    if reasons:
        invalid = any(
            reason.endswith("schema_invalid")
            or reason.endswith("disagreement")
            or reason.endswith("cumulative_decrease")
            for reason in reasons
        )
        status = "quarantined" if invalid or required else "unavailable"
        value = None
    else:
        status = "admitted"
        value = event_value
    return {
        "value": value,
        "status": status,
        "required": required,
        "reasons": sorted(set(reasons)),
        "comparisons": comparisons,
    }


def build_fpl_performance_snapshot(
    bundle: Mapping[str, Any],
    *,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one immutable player-gameweek snapshot from official sources."""

    if config.get("schema_version") != "1.0":
        raise FplPerformanceError("Unsupported performance config schema")
    season = str(bundle.get("season", ""))
    if season != str(config.get("season", "")):
        raise FplPerformanceError("Bundle season does not match config")
    gameweek = _positive_int(bundle.get("gameweek"), "gameweek")
    cutoff_text, cutoff = _timestamp(bundle.get("cutoff"), "cutoff")
    metrics = config.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        raise FplPerformanceError("Performance config requires metrics")

    before_payload, before_binding = _validate_envelope(
        bundle.get("bootstrap_before", {}),
        label="bootstrap_before",
        cutoff=cutoff,
    )
    after_payload, after_binding = _validate_envelope(
        bundle.get("bootstrap_after", {}),
        label="bootstrap_after",
        cutoff=cutoff,
    )
    event_payload, event_binding = _validate_envelope(
        bundle.get("event_live", {}),
        label="event_live",
        cutoff=cutoff,
    )
    _, before_by_code = _element_index(
        before_payload, label="bootstrap_before"
    )
    after_by_id, after_by_code = _element_index(
        after_payload, label="bootstrap_after"
    )
    event_by_id = _event_index(event_payload)

    summary_inputs = bundle.get("element_summaries", [])
    if not isinstance(summary_inputs, list):
        raise FplPerformanceError("element_summaries must be a list")
    summaries: dict[int, dict[str, Any]] = {}
    summary_bindings: list[dict[str, str]] = []
    for index, source in enumerate(summary_inputs):
        if not isinstance(source, Mapping):
            raise FplPerformanceError(
                f"element_summaries[{index}] must be an object"
            )
        player_id = _positive_int(
            source.get("fpl_player_id"),
            f"element_summaries[{index}].fpl_player_id",
        )
        if player_id in summaries:
            raise FplPerformanceError(
                f"Duplicate element-summary player: {player_id}"
            )
        payload, binding = _validate_envelope(
            source,
            label=f"element_summary:{player_id}",
            cutoff=cutoff,
        )
        summaries[player_id] = {"payload": payload}
        summary_bindings.append(binding)

    players: list[dict[str, Any]] = []
    gaps: list[str] = []
    quarantined_metrics = 0
    total_metrics = 0
    for code, after in sorted(after_by_code.items()):
        player_id = _positive_int(
            after.get("id"), "bootstrap_after player.id"
        )
        before = before_by_code.get(code)
        prior_id = (
            _positive_int(before.get("id"), "bootstrap_before player.id")
            if before is not None
            else None
        )
        event = event_by_id.get(player_id)
        event_stats = (
            deepcopy(dict(event["stats"])) if event is not None else None
        )
        rows, fixture_ids = _summary_rows(
            summaries.get(player_id), gameweek=gameweek
        )
        if rows is None and event is not None:
            explain = event.get("explain", [])
            if isinstance(explain, list):
                fixture_ids = sorted(
                    {
                        int(row["fixture"])
                        for row in explain
                        if isinstance(row, Mapping)
                        and isinstance(row.get("fixture"), int)
                        and int(row["fixture"]) > 0
                    }
                )
        metric_rows: dict[str, dict[str, Any]] = {}
        for metric in metrics:
            if not isinstance(metric, Mapping):
                raise FplPerformanceError("Metric config rows must be objects")
            name = str(metric.get("output", ""))
            if not name or name in metric_rows:
                raise FplPerformanceError(
                    "Metric outputs must be non-empty and unique"
                )
            record = _metric_record(
                metric=metric,
                event_stats=event_stats,
                summary_rows=rows,
                before=before,
                after=after,
            )
            metric_rows[name] = record
            total_metrics += 1
            if record["status"] != "admitted":
                gaps.extend(
                    f"player:{code}:metric:{name}:{reason}"
                    for reason in (record["reasons"] or [record["status"]])
                )
            if record["status"] == "quarantined":
                quarantined_metrics += 1
        status = (
            "complete"
            if all(
                row["status"] == "admitted"
                for row in metric_rows.values()
            )
            else "degraded"
        )
        players.append(
            {
                "fpl_code": code,
                "fpl_player_id": player_id,
                "prior_fpl_player_id": prior_id,
                "gameweek": gameweek,
                "fixture_count": len(fixture_ids),
                "fixture_ids": fixture_ids,
                "blank": len(fixture_ids) == 0,
                "status": status,
                "metrics": metric_rows,
            }
        )

    missing_event_ids = sorted(set(event_by_id) - set(after_by_id))
    if missing_event_ids:
        gaps.append(
            "event_live_players_missing_from_bootstrap_after:"
            + ",".join(str(value) for value in missing_event_ids)
        )
    status = (
        "complete"
        if players and not gaps and quarantined_metrics == 0
        else "degraded"
    )
    return _seal(
        {
            "schema_version": "1.0",
            "snapshot_id": f"fpl-performance:{season}:gw{gameweek:02d}",
            "season": season,
            "gameweek": gameweek,
            "cutoff": cutoff_text,
            "source_id": str(config["source_id"]),
            "status": status,
            "source_bindings": [
                before_binding,
                after_binding,
                event_binding,
                *sorted(
                    summary_bindings,
                    key=lambda row: str(row["label"]),
                ),
            ],
            "players": players,
            "quality": {
                "player_count": len(players),
                "metric_count": total_metrics,
                "quarantined_metric_count": quarantined_metrics,
                "quarantine_rate": (
                    round(quarantined_metrics / total_metrics, 6)
                    if total_metrics
                    else 0.0
                ),
                "gaps": sorted(set(gaps)),
            },
            "feature_family": {
                "family_id": "fpl_native_performance",
                "external_match_ratings_are_distinct": True,
                "promotion_status": str(
                    config["ablation"]["promotion_status"]
                ),
            },
            "account_writes": False,
        }
    )


def apply_fpl_performance_ablation(
    baseline: Mapping[str, Any],
    *,
    snapshot: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Attach the isolated family or preserve the exact shared baseline."""

    if snapshot is None:
        return deepcopy(dict(baseline))
    if snapshot.get("content_sha256") != artifact_hash(snapshot):
        raise FplPerformanceError("Performance snapshot hash mismatch")
    admitted = any(
        metric.get("status") == "admitted"
        for player in snapshot.get("players", [])
        for metric in player.get("metrics", {}).values()
    )
    if not admitted:
        return deepcopy(dict(baseline))
    result = deepcopy(dict(baseline))
    families = result.setdefault("feature_families", {})
    if not isinstance(families, dict):
        raise FplPerformanceError("feature_families must be an object")
    families["fpl_native_performance"] = {
        "snapshot_sha256": snapshot["content_sha256"],
        "season": snapshot["season"],
        "gameweek": snapshot["gameweek"],
        "status": snapshot["status"],
        "players": deepcopy(snapshot["players"]),
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def write_immutable_json(
    path: Path,
    value: Mapping[str, Any],
) -> str:
    encoded = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise FileExistsError(
                f"Refusing to overwrite FPL performance artifact: {path}"
            )
        return "identical"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(encoded)
    return "created"
