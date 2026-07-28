"""Governed automated collection of official FPL availability evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Literal, Protocol

import httpx

from src.evidence.live_evidence_ledger import (
    append_live_evidence_claim,
    live_evidence_hash,
    new_live_evidence_ledger,
    validate_live_evidence_ledger,
)
from src.ingestion.acquisition import (
    assert_acquisition_allowed,
    record_acquisition,
)
from src.ingestion.registry import load_registry
from src.ingestion.fpl_endpoint_plan import (
    FplEndpointPlanError,
    build_endpoint_capture_plan,
    validate_endpoint_payload,
)


SOURCE_ID = "fpl-official-endpoints"
BOOTSTRAP_PATH = "/api/bootstrap-static/"


class LiveEvidenceCollectionError(ValueError):
    """Raised when governed automated evidence collection cannot proceed."""


class HttpClient(Protocol):
    def get(self, url: str, *, timeout: float) -> httpx.Response: ...


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = live_evidence_hash(result)
    return result


def _timestamp(value: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LiveEvidenceCollectionError(
            "observed_at must be an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise LiveEvidenceCollectionError("observed_at must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _claim_id(
    *,
    season: str,
    player_id: str,
    news_added: str,
    claim_value: Mapping[str, Any],
) -> str:
    digest = hashlib.sha256(
        _canonical_bytes(
            {
                "season": season,
                "player_id": player_id,
                "news_added": news_added,
                "claim_value": claim_value,
            }
        )
    ).hexdigest()
    return f"official-fpl-news:{digest[:24]}"


def _published_at(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _player_claim(
    player: Mapping[str, Any],
    *,
    season: str,
    observed_at: str,
    observed: datetime,
    source_hash: str,
    source_url: str,
    expiry_hours: int,
    default_impact_points: float,
) -> tuple[dict[str, Any] | None, str | None]:
    player_id = str(player.get("id", ""))
    if not player_id:
        return None, "player_missing_id"
    news = str(player.get("news") or "").strip()
    if not news:
        return None, None
    published_at = _published_at(player.get("news_added"))
    if published_at is None:
        return None, f"player:{player_id}:news_missing_exact_publication_time"
    player_uid = f"player:{season}:{player_id}"
    bindings = [
        {
            "entity_type": "player_uid",
            "stable_id": player_uid,
            "source_label": str(player.get("web_name") or player_id),
            "match_status": "exact",
        }
    ]
    code = player.get("code")
    if code is not None and str(code):
        bindings.append(
            {
                "entity_type": "fpl_code",
                "stable_id": str(code),
                "source_label": str(player.get("web_name") or player_id),
                "match_status": "exact",
            }
        )
    expires_at = (observed + timedelta(hours=expiry_hours)).isoformat().replace(
        "+00:00", "Z"
    )
    status = str(player.get("status") or "unknown")
    claim_value = {
        "status": status,
        "chance_of_playing_this_round": player.get(
            "chance_of_playing_this_round"
        ),
        "chance_of_playing_next_round": player.get(
            "chance_of_playing_next_round"
        ),
        "news": news,
    }
    claim = {
        "claim_id": _claim_id(
            season=season,
            player_id=player_id,
            news_added=published_at,
            claim_value=claim_value,
        ),
        "source_id": SOURCE_ID,
        "document_id": f"bootstrap-static:{source_hash}",
        "source_url": source_url,
        "source_hash_sha256": source_hash,
        "claim_text": (
            f"Official FPL availability for {player.get('web_name') or player_id}: "
            f"status {status}; {news}"
        ),
        "claim_precision": "official_structured_field_and_derived_summary",
        "claim_type": "player_availability",
        "value": claim_value,
        "confidence": 0.98,
        "published_at": published_at,
        "observed_at": observed_at,
        "available_at": observed_at,
        "expires_at": expires_at,
        "identity_bindings": bindings,
        "decision_boundary_ids": [f"availability:{player_uid}"],
        "estimated_impact_points": default_impact_points,
        "supersedes_claim_ids": [],
    }
    return claim, None


def _retry_after_seconds(headers: Mapping[str, Any]) -> int | None:
    value = headers.get("retry-after")
    if value in {None, ""}:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _endpoint_failure_reason(
    endpoint_id: str,
    status: str,
    *,
    checkpoint_id: str,
) -> str:
    if endpoint_id == "bootstrap-static" and checkpoint_id == "availability_only":
        return f"official_fpl_{status}"
    safe_endpoint = endpoint_id.replace("-", "_")
    return f"official_fpl_{safe_endpoint}_{status}"


def capture_official_fpl_evidence(
    client: HttpClient,
    *,
    season: str,
    observed_at: str,
    raw_out_dir: Path,
    config: Mapping[str, Any],
    base_url: str = "https://fantasy.premierleague.com",
    timeout: float = 30.0,
    mode: Literal["live", "fixture"] = "live",
    previous_ledger: Mapping[str, Any] | None = None,
    registry_path: Path | None = None,
    checkpoint_id: str = "availability_only",
    player_ids: Sequence[int] | None = None,
    gameweek: int | None = None,
) -> dict[str, Any]:
    """Capture a bounded official-FPL endpoint plan and availability claims."""

    observed_text, observed = _timestamp(observed_at)
    source = assert_acquisition_allowed(
        SOURCE_ID, mode, registry_path=registry_path
    )
    registry = load_registry(registry_path)
    registry_version = str(registry.get("registry_version", "unknown"))
    try:
        plan = build_endpoint_capture_plan(
            config=config,
            checkpoint_id=checkpoint_id,
            player_ids=player_ids,
            gameweek=gameweek,
        )
    except FplEndpointPlanError as exc:
        raise LiveEvidenceCollectionError(str(exc)) from exc

    if previous_ledger is None:
        ledger = new_live_evidence_ledger(
            season=season, created_at=observed_text
        )
    else:
        ledger = deepcopy(dict(previous_ledger))
        validate_live_evidence_ledger(ledger)
        if ledger["season"] != season:
            raise LiveEvidenceCollectionError(
                "Previous ledger season differs from collection season"
            )

    endpoint_captures: list[dict[str, Any]] = []
    bootstrap_payload: Mapping[str, Any] | None = None
    bootstrap_acquisition: dict[str, Any] | None = None
    attempted = 0
    retry_after_seconds: int | None = None
    rate_limit_stop = False

    for request in plan:
        endpoint_id = str(request["endpoint_id"])
        if rate_limit_stop:
            endpoint_captures.append(
                {
                    "endpoint_id": endpoint_id,
                    "path": request["path"],
                    "entity_id": request["entity_id"],
                    "status": "not_attempted",
                    "degraded_reasons": ["rate_limit_stop"],
                    "retry_after_seconds": retry_after_seconds,
                    "acquisition": None,
                }
            )
            continue

        url = base_url.rstrip("/") + str(request["path"])
        failure: dict[str, str] | None = None
        headers: Mapping[str, Any] = {}
        attempted += 1
        try:
            response = client.get(url, timeout=timeout)
            body = response.content
            http_status = int(response.status_code)
            headers = response.headers
            acquisition_status = (
                "success" if http_status == 200 else "http_error"
            )
            if acquisition_status != "success":
                failure = {
                    "category": "http",
                    "type": "HTTPStatus",
                    "message": f"HTTP {http_status}",
                }
        except httpx.HTTPError as exc:
            body = b""
            http_status = 0
            acquisition_status = "transport_error"
            failure = {
                "category": "transport",
                "type": type(exc).__name__,
                "message": str(exc),
            }

        acquisition = record_acquisition(
            source_id=SOURCE_ID,
            mode=mode,
            origin=url,
            body=body,
            out_dir=raw_out_dir,
            artifact_name=str(request["artifact_name"]),
            status=acquisition_status,
            registry_version=registry_version,
            observed_at=observed_text,
            http_status=http_status,
            request_url=url,
            failure=failure,
            registry_path=registry_path,
        )

        reasons: list[str] = []
        payload: Any = None
        if acquisition_status == "success":
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                reasons.append("schema_drift:invalid_json")
            else:
                reasons.extend(
                    validate_endpoint_payload(
                        payload,
                        schema=request["schema"],
                    )
                )
        else:
            reasons.append(
                _endpoint_failure_reason(
                    endpoint_id,
                    acquisition_status,
                    checkpoint_id=checkpoint_id,
                )
            )

        endpoint_retry = _retry_after_seconds(headers)
        if http_status == 429:
            rate_limit_stop = True
            retry_after_seconds = endpoint_retry
        row_status = "complete" if not reasons else "degraded"
        row = {
            "endpoint_id": endpoint_id,
            "path": request["path"],
            "entity_id": request["entity_id"],
            "status": row_status,
            "degraded_reasons": reasons,
            "retry_after_seconds": endpoint_retry,
            "acquisition": acquisition,
        }
        endpoint_captures.append(row)

        if endpoint_id == "bootstrap-static":
            bootstrap_acquisition = acquisition
            if row_status == "complete" and isinstance(payload, Mapping):
                bootstrap_payload = payload

    automated = config["automated_collection"]
    expiry_hours = int(automated["official_fpl_news_expiry_hours"])
    impact = float(automated["default_availability_impact_points"])
    existing = {str(row["claim_id"]) for row in ledger["claims"]}
    claim_gaps: list[str] = []
    added = 0
    raw_claim_count = 0
    observed_player_ids: list[str] = []

    if bootstrap_payload is not None and bootstrap_acquisition is not None:
        source_hash = str(bootstrap_acquisition["content_hash_sha256"])
        source_url = base_url.rstrip("/") + BOOTSTRAP_PATH
        for player in bootstrap_payload["elements"]:
            if not isinstance(player, Mapping):
                claim_gaps.append("non_object_player_record")
                continue
            player_id = str(player.get("id", ""))
            if player_id:
                observed_player_ids.append(player_id)
            if str(player.get("news") or "").strip():
                raw_claim_count += 1
            claim, gap = _player_claim(
                player,
                season=season,
                observed_at=observed_text,
                observed=observed,
                source_hash=source_hash,
                source_url=source_url,
                expiry_hours=expiry_hours,
                default_impact_points=impact,
            )
            if gap:
                claim_gaps.append(gap)
            if claim is None or claim["claim_id"] in existing:
                continue
            ledger = append_live_evidence_claim(
                ledger,
                claim,
                source_registry=registry,
                config=config,
            )
            existing.add(claim["claim_id"])
            added += 1

    endpoint_reasons = sorted(
        {
            str(reason)
            for row in endpoint_captures
            for reason in row["degraded_reasons"]
        }
    )
    endpoint_gaps = [
        f"endpoint:{row['endpoint_id']}:{reason}"
        for row in endpoint_captures
        for reason in row["degraded_reasons"]
    ]
    complete = all(row["status"] == "complete" for row in endpoint_captures)
    document_count = sum(
        1
        for row in endpoint_captures
        if row["acquisition"] is not None
        and row["acquisition"]["acquisition_status"] == "success"
    )

    return _seal(
        {
            "schema_version": "1.1",
            "capture_id": (
                f"live-evidence-capture:{season}:{checkpoint_id}:{observed_text}"
            ),
            "season": season,
            "checkpoint_id": checkpoint_id,
            "observed_at": observed_text,
            "status": "complete" if complete else "degraded",
            "degraded_reasons": endpoint_reasons,
            "source": {
                "source_id": SOURCE_ID,
                "registry_version": registry_version,
                "authority": source["authority"],
            },
            "acquisition": bootstrap_acquisition,
            "endpoint_captures": endpoint_captures,
            "request_count_planned": len(plan),
            "request_count_attempted": attempted,
            "retry_after_seconds": retry_after_seconds,
            "document_count": document_count,
            "raw_claim_count": raw_claim_count,
            "observed_player_ids": sorted(set(observed_player_ids)),
            "ledger": ledger,
            "claim_count_added": added,
            "gaps": sorted(set(claim_gaps + endpoint_gaps)),
            "frozen_no_evidence_control_preserved": True,
            "account_writes": False,
            "authentication": "none",
        }
    )
