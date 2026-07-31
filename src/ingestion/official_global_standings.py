"""Prospective official Overall-league standings capture for rank calibration.

Downstream-only: never feeds pre-deadline forecasts, optimisation or policy.
Collection is disabled unless config.collection_enabled is true and a fetch
callback is supplied. Missing pages become explicit gaps.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from src.evaluation.rank_calibration import validate_row
from src.ingestion.registry import assert_collectable


class OfficialGlobalStandingsError(ValueError):
    """Raised when standings capture or transformation is unsafe."""


FetchPage = Callable[[int], Mapping[str, Any] | None]


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def artifact_hash(value: Mapping[str, Any]) -> str:
    body = {
        key: deepcopy(item)
        for key, item in value.items()
        if key != "content_sha256"
    }
    return hashlib.sha256(_canonical(body)).hexdigest()


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def _utc(value: Any, field: str) -> str:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise OfficialGlobalStandingsError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise OfficialGlobalStandingsError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def load_rank_thresholds_config(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise OfficialGlobalStandingsError("rank thresholds config must be an object")
    return data


def assert_capture_permitted(config: Mapping[str, Any]) -> None:
    """Fail closed unless owner-approved, registry-collectable and enabled."""

    if config.get("owner_approved") is not True:
        raise OfficialGlobalStandingsError("owner approval is required before capture")
    if config.get("collection_enabled") is not True:
        raise OfficialGlobalStandingsError(
            "collection_enabled is false; standings capture remains disabled"
        )
    if config.get("decision_path_use") != "forbidden":
        raise OfficialGlobalStandingsError(
            "decision_path_use must remain forbidden for standings capture"
        )
    source_id = str(config.get("source_id", ""))
    assert_collectable(source_id)


def build_standings_snapshot(
    *,
    config: Mapping[str, Any],
    gameweek: int,
    observed_at: str,
    available_at: str,
    finalised_at: str,
    fetch_page: FetchPage | None = None,
    pages: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Capture one post-finalisation Overall standings snapshot.

    ``fetch_page(page)`` returns a page payload or ``None`` for a missing page.
    When ``collection_enabled`` is false, this function fails closed without
    network access.
    """

    assert_capture_permitted(config)
    if fetch_page is None and pages is None:
        raise OfficialGlobalStandingsError(
            "no fetch callback or pages supplied; refusing network default"
        )

    observed = _utc(observed_at, "observed_at")
    available = _utc(available_at, "available_at")
    finalised = _utc(finalised_at, "finalised_at")
    if available > observed:
        raise OfficialGlobalStandingsError(
            "available_at must not be after observed_at"
        )

    max_pages = int(config.get("max_pages", 20))
    league_id = int(config["league_id"])
    endpoint_template = str(config["endpoint_template"])
    collected: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    field_size: int | None = None

    if pages is not None:
        page_source: Sequence[Mapping[str, Any] | None] = list(pages)
    else:
        page_source = []

    page_number = 0
    while page_number < max_pages:
        page_number += 1
        if pages is not None:
            if page_number > len(page_source):
                break
            payload = page_source[page_number - 1]
        else:
            payload = fetch_page(page_number) if fetch_page is not None else None

        endpoint = endpoint_template.format(page=page_number)
        if payload is None:
            gaps.append(
                {
                    "page": page_number,
                    "endpoint": endpoint,
                    "reason": "missing_page",
                }
            )
            # Injected page lists may intentionally include later pages after a
            # gap; live fetch stops so a later live response cannot fill an
            # earlier missing checkpoint.
            if pages is None:
                break
            continue
        if not isinstance(payload, Mapping):
            raise OfficialGlobalStandingsError("standings page must be an object")
        standings = payload.get("standings")
        if not isinstance(standings, Mapping):
            gaps.append(
                {
                    "page": page_number,
                    "endpoint": endpoint,
                    "reason": "malformed_standings",
                }
            )
            if pages is None:
                break
            continue
        results = standings.get("results")
        if not isinstance(results, list):
            gaps.append(
                {
                    "page": page_number,
                    "endpoint": endpoint,
                    "reason": "missing_results",
                }
            )
            if pages is None:
                break
            continue
        if field_size is None:
            league = payload.get("league")
            if isinstance(league, Mapping) and league.get("rank_count") is not None:
                field_size = int(league["rank_count"])
        rows: list[dict[str, Any]] = []
        for item in results:
            if not isinstance(item, Mapping):
                continue
            rows.append(
                {
                    "rank": int(item["rank"]),
                    "entry": int(item.get("entry", 0)),
                    "total_points": int(item["total"]),
                    "event_total": int(item.get("event_total", 0)),
                }
            )
        page_body = {
            "page": page_number,
            "endpoint": endpoint,
            "has_next": bool(standings.get("has_next")),
            "rows": rows,
        }
        page_body["page_sha256"] = hashlib.sha256(_canonical(page_body)).hexdigest()
        collected.append(page_body)
        if pages is None and not standings.get("has_next"):
            break

    snapshot = {
        "schema_version": "official-global-standings-v1",
        "season": str(config["season"]),
        "gameweek": int(gameweek),
        "league_id": league_id,
        "source_id": str(config["source_id"]),
        "endpoint_template": endpoint_template,
        "observed_at": observed,
        "available_at": available,
        "effective_at": finalised,
        "finalised_at": finalised,
        "finalisation_state": "post_finalisation",
        "auto_sub_finalised": True,
        "tie_rule": str(config.get("tie_rule", "shared_rank_as_published")),
        "field_size": field_size,
        "pages": collected,
        "gaps": gaps,
        "account_writes": False,
        "decision_path_use": "forbidden",
    }
    return _seal(snapshot)


def thresholds_from_standings_snapshot(
    snapshot: Mapping[str, Any],
    *,
    cumulative_points_targets: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Map a sealed standings snapshot to validated per-score threshold rows.

    Returns a Gameweek pack (not a full GW1–GW38 season artifact). Missing
    pages never invent ranks; they only reduce observed support or yield
    unavailable rows for requested scores outside capture.
    """

    if artifact_hash(snapshot) != snapshot.get("content_sha256"):
        raise OfficialGlobalStandingsError("standings snapshot hash mismatch")

    observed_pairs: list[tuple[int, int]] = []
    for page in snapshot.get("pages", []):
        if not isinstance(page, Mapping):
            continue
        for row in page.get("rows", []):
            if not isinstance(row, Mapping):
                continue
            observed_pairs.append((int(row["total_points"]), int(row["rank"])))
    observed_pairs.sort(key=lambda item: (-item[0], item[1]))

    field_size = snapshot.get("field_size")
    if field_size is None and observed_pairs:
        field_size = max(rank for _points, rank in observed_pairs)

    points_to_ranks: dict[int, list[int]] = {}
    for points, rank in observed_pairs:
        points_to_ranks.setdefault(points, []).append(rank)

    targets = (
        list(cumulative_points_targets)
        if cumulative_points_targets is not None
        else sorted(points_to_ranks, reverse=True)
    )

    rows: list[dict[str, Any]] = []
    source_hash = str(snapshot["content_sha256"])
    for points in targets:
        ranks = points_to_ranks.get(int(points))
        if not ranks:
            mode = "unavailable"
            rank_lower = None
            rank_upper = None
            exact = False
            derivation = "gap_outside_captured_pages"
            row_field_size = None
        elif min(ranks) == max(ranks):
            mode = "exact"
            rank_lower = min(ranks)
            rank_upper = max(ranks)
            exact = True
            derivation = "official_overall_standings_page"
            row_field_size = field_size
        else:
            mode = "bounded"
            rank_lower = min(ranks)
            rank_upper = max(ranks)
            exact = False
            derivation = "official_overall_standings_shared_or_sampled"
            row_field_size = field_size

        rows.append(
            validate_row(
                {
                    "season": snapshot["season"],
                    "gameweek": snapshot["gameweek"],
                    "cumulative_points": int(points),
                    "rank_lower": rank_lower,
                    "rank_upper": rank_upper,
                    "exact": exact,
                    "field_size": row_field_size,
                    "snapshot_at": snapshot["observed_at"],
                    "finalised": True,
                    "auto_sub_finalised": True,
                    "tie_rule": snapshot["tie_rule"],
                    "source_id": snapshot["source_id"],
                    "source_artifact_hash": source_hash,
                    "derivation_method": derivation,
                    "mode": mode,
                },
                season=str(snapshot["season"]),
            )
        )

    if snapshot.get("gaps") and not rows:
        rows.append(
            validate_row(
                {
                    "season": snapshot["season"],
                    "gameweek": snapshot["gameweek"],
                    "cumulative_points": 0,
                    "rank_lower": None,
                    "rank_upper": None,
                    "exact": False,
                    "field_size": None,
                    "snapshot_at": snapshot["observed_at"],
                    "finalised": True,
                    "auto_sub_finalised": True,
                    "tie_rule": snapshot["tie_rule"],
                    "source_id": snapshot["source_id"],
                    "source_artifact_hash": source_hash,
                    "derivation_method": "missing_standings_pages",
                    "mode": "unavailable",
                },
                season=str(snapshot["season"]),
            )
        )

    pack = {
        "schema_version": "rank-threshold-gameweek-pack-v1",
        "season": snapshot["season"],
        "gameweek": snapshot["gameweek"],
        "source_id": snapshot["source_id"],
        "source_artifact_hash": source_hash,
        "gaps": deepcopy(list(snapshot.get("gaps", []))),
        "rows": rows,
        "decision_path_use": "forbidden",
    }
    return _seal(pack)
