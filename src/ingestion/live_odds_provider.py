"""Cutoff-safe, secret-free acquisition adapter for The Odds API."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping

import httpx

from src.ingestion.acquisition import AcquisitionMode, record_acquisition


class LiveOddsProviderError(ValueError):
    """Raised when an odds capture cannot safely be attempted."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def artifact_hash(value: Mapping[str, Any]) -> str:
    """Hash an artifact while excluding its self-referential hash field."""

    content = {key: item for key, item in value.items() if key != "content_sha256"}
    return hashlib.sha256(_canonical_bytes(content)).hexdigest()


def write_immutable_json(path: Path, value: Mapping[str, Any]) -> str:
    """Write canonical JSON once, allowing only byte-identical reruns."""

    encoded = (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise FileExistsError(f"Refusing to overwrite immutable artifact: {path}")
        return "unchanged"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
    return "written"


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise LiveOddsProviderError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise LiveOddsProviderError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _integer_header(headers: Mapping[str, str], name: str) -> int | None:
    value = headers.get(name)
    if value in {None, ""}:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _quota(
    headers: Mapping[str, str],
    config: Mapping[str, Any],
) -> dict[str, int | None]:
    names = config["quota"]["response_headers"]
    return {
        "last": _integer_header(headers, str(names["last"])),
        "remaining": _integer_header(headers, str(names["remaining"])),
        "used": _integer_header(headers, str(names["used"])),
    }


def _safe_float(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise LiveOddsProviderError(f"{field} must be numeric") from exc
    if not math.isfinite(number):
        raise LiveOddsProviderError(f"{field} must be finite")
    return number


def _normalize_payload(
    raw: Any,
    *,
    sport_key: str,
    requested_markets: set[str],
    required_markets: set[str],
) -> tuple[dict[str, Any], list[str]]:
    if not isinstance(raw, list):
        raise LiveOddsProviderError("Provider response must be an array")

    seen_events: set[str] = set()
    markets: list[dict[str, Any]] = []
    gaps: list[str] = []
    fixtures: list[dict[str, str]] = []

    for event_index, event in enumerate(raw):
        if not isinstance(event, Mapping):
            raise LiveOddsProviderError(
                f"Provider event {event_index} must be an object"
            )
        event_id = str(event.get("id", "")).strip()
        if not event_id:
            raise LiveOddsProviderError(f"Provider event {event_index} has no id")
        if event_id in seen_events:
            raise LiveOddsProviderError(f"Duplicate provider event id: {event_id}")
        seen_events.add(event_id)
        if str(event.get("sport_key", "")) != sport_key:
            raise LiveOddsProviderError(
                f"Provider event {event_id} has the wrong sport key"
            )

        commence_time, _ = _timestamp(
            event.get("commence_time"), f"event:{event_id}.commence_time"
        )
        home_team = str(event.get("home_team", "")).strip()
        away_team = str(event.get("away_team", "")).strip()
        if not home_team or not away_team or home_team == away_team:
            raise LiveOddsProviderError(
                f"Provider event {event_id} has invalid teams"
            )
        fixtures.append(
            {
                "event_id": event_id,
                "commence_time": commence_time,
                "home_team": home_team,
                "away_team": away_team,
            }
        )

        found_required: set[str] = set()
        bookmakers = event.get("bookmakers", [])
        if not isinstance(bookmakers, list):
            raise LiveOddsProviderError(
                f"Provider event {event_id} bookmakers must be an array"
            )
        for bookmaker in bookmakers:
            if not isinstance(bookmaker, Mapping):
                continue
            bookmaker_key = str(bookmaker.get("key", "")).strip()
            bookmaker_title = str(bookmaker.get("title", "")).strip()
            if not bookmaker_key:
                continue
            bookmaker_markets = bookmaker.get("markets", [])
            if not isinstance(bookmaker_markets, list):
                continue
            for market in bookmaker_markets:
                if not isinstance(market, Mapping):
                    continue
                market_key = str(market.get("key", "")).strip()
                if market_key not in requested_markets:
                    continue
                outcomes = market.get("outcomes", [])
                if not isinstance(outcomes, list) or not outcomes:
                    continue
                normalized_outcomes: list[dict[str, Any]] = []
                for outcome in outcomes:
                    if not isinstance(outcome, Mapping):
                        continue
                    name = str(outcome.get("name", "")).strip()
                    if not name:
                        continue
                    price = _safe_float(
                        outcome.get("price"),
                        f"event:{event_id}.{market_key}.{name}.price",
                    )
                    if price <= 1.0:
                        raise LiveOddsProviderError(
                            f"event:{event_id}.{market_key}.{name}.price "
                            "must be greater than 1"
                        )
                    item: dict[str, Any] = {"name": name, "price": price}
                    if outcome.get("point") is not None:
                        item["point"] = _safe_float(
                            outcome["point"],
                            f"event:{event_id}.{market_key}.{name}.point",
                        )
                    normalized_outcomes.append(item)
                if not normalized_outcomes:
                    continue
                market_updated, _ = _timestamp(
                    market.get("last_update")
                    or bookmaker.get("last_update")
                    or event.get("commence_time"),
                    f"event:{event_id}.{market_key}.last_update",
                )
                markets.append(
                    {
                        "event_id": event_id,
                        "commence_time": commence_time,
                        "home_team": home_team,
                        "away_team": away_team,
                        "bookmaker_key": bookmaker_key,
                        "bookmaker_title": bookmaker_title,
                        "market_key": market_key,
                        "last_update": market_updated,
                        "outcomes": sorted(
                            normalized_outcomes,
                            key=lambda item: (
                                str(item["name"]),
                                float(item.get("point", 0)),
                            ),
                        ),
                    }
                )
                if market_key in required_markets:
                    found_required.add(market_key)

        for market_key in sorted(required_markets - found_required):
            gaps.append(f"event:{event_id}:missing_required_market:{market_key}")

    return {
        "sport_key": sport_key,
        "fixtures": sorted(fixtures, key=lambda item: item["event_id"]),
        "markets": sorted(
            markets,
            key=lambda item: (
                item["event_id"],
                item["bookmaker_key"],
                item["market_key"],
            ),
        ),
    }, gaps


def _capture_artifact(
    *,
    status: str,
    degraded_reasons: list[str],
    quota: Mapping[str, Any],
    retry_after_seconds: int | None,
    acquisition: Mapping[str, Any],
    snapshot: Mapping[str, Any] | None,
) -> dict[str, Any]:
    artifact: dict[str, Any] = {
        "schema_version": "1.0",
        "provider": "the-odds-api",
        "status": status,
        "degraded_reasons": degraded_reasons,
        "quota": dict(quota),
        "retry_after_seconds": retry_after_seconds,
        "acquisition": deepcopy(dict(acquisition)),
        "snapshot": deepcopy(dict(snapshot)) if snapshot is not None else None,
        "account_writes": False,
        "authentication": "api_key_environment",
    }
    artifact["content_sha256"] = artifact_hash(artifact)
    return artifact


def capture_the_odds_api(
    client: httpx.Client,
    *,
    season: str,
    slot: str,
    observed_at: str,
    decision_cutoff: str,
    raw_out_dir: Path,
    config: Mapping[str, Any],
    api_key: str | None = None,
    mode: AcquisitionMode = "live",
    registry_path: Path | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Capture one immutable pre-deadline odds observation."""

    provider = config.get("provider")
    request = config.get("request")
    slots = config.get("slots")
    if not isinstance(provider, Mapping) or not isinstance(request, Mapping):
        raise LiveOddsProviderError("Odds provider config is incomplete")
    if not isinstance(slots, Mapping) or slot not in slots:
        raise LiveOddsProviderError(f"Unknown odds capture slot: {slot}")
    if str(provider.get("source_id")) != "the-odds-api":
        raise LiveOddsProviderError("Odds provider source_id is not the-odds-api")

    observed_text, observed = _timestamp(observed_at, "observed_at")
    cutoff_text, cutoff = _timestamp(decision_cutoff, "decision_cutoff")
    if observed >= cutoff:
        raise LiveOddsProviderError(
            "observed_at must be strictly before decision_cutoff"
        )
    lead_hours = (cutoff - observed).total_seconds() / 3600
    window = slots[slot]
    minimum = float(window["exclusive_minimum_lead_hours"])
    maximum = float(window["inclusive_maximum_lead_hours"])
    if not minimum < lead_hours <= maximum:
        raise LiveOddsProviderError(
            f"Capture is outside the configured {slot} lead-time window"
        )

    secret_name = str(request.get("secret_environment_variable", ""))
    secret = api_key if api_key is not None else os.environ.get(secret_name)
    if not secret:
        raise LiveOddsProviderError(
            f"Missing required API credential in {secret_name}"
        )

    sport_key = str(request["sport_key"])
    regions = ",".join(str(value) for value in request["regions"])
    requested = [str(value) for value in request["requested_markets"]]
    required = {str(value) for value in request["required_markets"]}
    root = str(base_url or provider["base_url"]).rstrip("/")
    endpoint = f"{root}/v4/sports/{sport_key}/odds"
    artifact_name = f"{sport_key}-{regions}-{'-'.join(requested)}.json"
    params = {
        "apiKey": secret,
        "regions": regions,
        "markets": ",".join(requested),
        "oddsFormat": str(request["odds_format"]),
        "dateFormat": str(request["date_format"]),
    }

    try:
        response = client.get(
            endpoint,
            params=params,
            timeout=float(request.get("timeout_seconds", 30)),
        )
        body = response.content
        status_code = response.status_code
        headers = response.headers
    except httpx.HTTPError as exc:
        acquisition = record_acquisition(
            source_id="the-odds-api",
            mode=mode,
            origin=endpoint,
            body=b"",
            out_dir=raw_out_dir,
            artifact_name=artifact_name,
            status="transport_error",
            observed_at=observed_text,
            http_status=0,
            request_url=endpoint,
            failure={
                "category": "transport",
                "type": type(exc).__name__,
                "message": "Transport request failed; credentials suppressed",
            },
            registry_path=registry_path,
        )
        return _capture_artifact(
            status="degraded",
            degraded_reasons=["provider_transport_error"],
            quota={"last": None, "remaining": None, "used": None},
            retry_after_seconds=None,
            acquisition=acquisition,
            snapshot=None,
        )

    quota = _quota(headers, config)
    retry_after = _integer_header(headers, "retry-after")
    acquisition_status = "success" if status_code == 200 else "http_error"
    acquisition = record_acquisition(
        source_id="the-odds-api",
        mode=mode,
        origin=endpoint,
        body=body,
        out_dir=raw_out_dir,
        artifact_name=artifact_name,
        status=acquisition_status,
        observed_at=observed_text,
        http_status=status_code,
        request_url=endpoint,
        failure=(
            None
            if status_code == 200
            else {
                "category": "http",
                "type": "HTTPStatus",
                "message": f"HTTP {status_code}",
            }
        ),
        registry_path=registry_path,
    )
    if status_code != 200:
        return _capture_artifact(
            status="degraded",
            degraded_reasons=[f"provider_http_{status_code}"],
            quota=quota,
            retry_after_seconds=retry_after,
            acquisition=acquisition,
            snapshot=None,
        )

    try:
        raw = json.loads(body)
        payload, gaps = _normalize_payload(
            raw,
            sport_key=sport_key,
            requested_markets=set(requested),
            required_markets=required,
        )
    except (json.JSONDecodeError, LiveOddsProviderError) as exc:
        reason = (
            "provider_invalid_json"
            if isinstance(exc, json.JSONDecodeError)
            else "provider_schema_invalid"
        )
        return _capture_artifact(
            status="degraded",
            degraded_reasons=[reason],
            quota=quota,
            retry_after_seconds=retry_after,
            acquisition=acquisition,
            snapshot=None,
        )


    payload["season"] = season
    payload["regions"] = list(request["regions"])
    payload["requested_markets"] = requested
    payload["odds_format"] = str(request["odds_format"])
    source_sha256 = hashlib.sha256(_canonical_bytes(payload)).hexdigest()
    snapshot = {
        "source_id": "the-odds-api",
        "slot": slot,
        "observed_at": observed_text,
        "available_at": observed_text,
        "decision_cutoff": cutoff_text,
        "lead_time_hours": round(lead_hours, 6),
        "payload": payload,
        "source_sha256": source_sha256,
    }
    return _capture_artifact(
        status="degraded" if gaps else "complete",
        degraded_reasons=gaps,
        quota=quota,
        retry_after_seconds=retry_after,
        acquisition=acquisition,
        snapshot=snapshot,
    )
