"""Build immutable live-shadow benchmark episodes from governed local inputs."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker

from src.data.quality import evaluate_quality
from src.data.temporal import normalise_observation, parse_aware_datetime
from src.features.deadline_view import materialise_deadline_view
from src.ingestion.acquisition import detect_schema
from src.orchestration.manager_state import normalise_manager_state
from src.orchestration.policy_state import POLICY_ARMS
from src.scoring.rules_loader import (
    DEFAULT_RULES_PATH,
    load_rules,
    ruleset_bytes,
    ruleset_sha256,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
EPISODE_SCHEMA = REPO_ROOT / "control/schemas/benchmark/episode-manifest.json"
PENDING_SCHEMA = REPO_ROOT / "control/schemas/benchmark/pending-outcome.json"
SOURCE_MANIFEST_SCHEMA = REPO_ROOT / "control/schemas/data/source-snapshot-manifest.json"
SOURCE_ID = "fpl-official-endpoints"
OFFICIAL_HOST = "fantasy.premierleague.com"
REQUIRED_ENDPOINTS = {"/api/bootstrap-static/", "/api/fixtures/"}
OBSERVED_FIXTURE_FIELDS = (
    "id",
    "event",
    "kickoff_time",
    "team_h",
    "team_a",
    "team_h_difficulty",
    "team_a_difficulty",
    "provisional_start_time",
)


class LiveEpisodeError(ValueError):
    """Raised when a live episode cannot be built without guessing or leakage."""


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


def _content_hash(value: Mapping[str, Any]) -> str:
    return _stable_hash(
        {key: item for key, item in value.items() if key != "content_sha256"}
    )


def _timestamp(value: Any, field: str) -> str:
    try:
        parsed = parse_aware_datetime(str(value), field=field)
    except (TypeError, ValueError) as exc:
        raise LiveEpisodeError(str(exc)) from exc
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LiveEpisodeError(f"Unable to read {label}: {path}: {exc}") from exc


def _validate(schema_path: Path, value: dict[str, Any], label: str) -> None:
    schema = _load_json(schema_path, f"{label} schema")
    try:
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)
    except Exception as exc:
        raise LiveEpisodeError(f"{label} is invalid: {exc}") from exc


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise LiveEpisodeError("unable to resolve the repository code commit") from exc
    return result.stdout.strip()


def _write_immutable_json(path: Path, value: Any) -> None:
    encoded = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise FileExistsError(f"Refusing to replace immutable artefact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)


def _write_immutable_bytes(path: Path, value: bytes) -> None:
    if path.exists():
        if path.read_bytes() != value:
            raise FileExistsError(f"Refusing to replace immutable artefact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def _verify_capture(summary_path: Path) -> tuple[dict[str, Any], dict, list, list[dict]]:
    summary = _load_json(summary_path, "capture summary")
    if not isinstance(summary, dict):
        raise LiveEpisodeError("capture summary must be an object")
    if (
        summary.get("capture_version") != "1.0"
        or summary.get("status") != "complete"
        or summary.get("failure_count") != 0
        or summary.get("failures") != []
    ):
        raise LiveEpisodeError("capture must be version 1.0 and complete with zero endpoint failures")
    if summary.get("source_id") != SOURCE_ID:
        raise LiveEpisodeError(f"capture source must be {SOURCE_ID}")
    if summary.get("authentication") != "none":
        raise LiveEpisodeError("capture authentication must be none")
    if summary.get("execution_mode") != "no_execution":
        raise LiveEpisodeError("capture execution mode must be no_execution")
    if summary.get("browser_actions") is not False or summary.get("account_writes") is not False:
        raise LiveEpisodeError("capture must not contain browser actions or account writes")
    observed_at = _timestamp(summary.get("observed_at"), "capture.observed_at")
    endpoints = summary.get("endpoints")
    if (
        not isinstance(endpoints, list)
        or len(endpoints) != 2
        or summary.get("endpoint_count") != 2
    ):
        raise LiveEpisodeError("capture must contain exactly bootstrap and fixtures endpoints")

    by_path: dict[str, tuple[dict[str, Any], Any]] = {}
    verified: list[dict[str, Any]] = []
    for endpoint in endpoints:
        if not isinstance(endpoint, dict):
            raise LiveEpisodeError("capture endpoint metadata must be objects")
        _validate(SOURCE_MANIFEST_SCHEMA, endpoint, "capture endpoint manifest")
        request_url = str(endpoint.get("request_url", ""))
        parsed_url = urlparse(request_url)
        path = parsed_url.path
        if parsed_url.scheme != "https" or parsed_url.netloc != OFFICIAL_HOST:
            raise LiveEpisodeError(f"endpoint {path!r} is not on the official FPL HTTPS host")
        if path not in REQUIRED_ENDPOINTS or path in by_path:
            raise LiveEpisodeError(f"unexpected or duplicate capture endpoint: {path!r}")
        if endpoint.get("origin") != request_url:
            raise LiveEpisodeError(f"endpoint {path} origin differs from request URL")
        if endpoint.get("acquisition_mode") != "live":
            raise LiveEpisodeError(f"endpoint {path} was not acquired in live mode")
        if endpoint.get("source_id") != SOURCE_ID:
            raise LiveEpisodeError(f"endpoint {path} has wrong source identity")
        if endpoint.get("acquisition_status") != "success" or endpoint.get("http_status") != 200:
            raise LiveEpisodeError(f"endpoint {path} was not acquired successfully")
        if _timestamp(endpoint.get("observed_at"), f"endpoint {path} observed_at") != observed_at:
            raise LiveEpisodeError(f"endpoint {path} timestamp differs from capture summary")
        body_file = str(endpoint.get("body_file", ""))
        if not body_file or Path(body_file).name != body_file:
            raise LiveEpisodeError(f"endpoint {path} body_file is unsafe")
        body_path = summary_path.parent / body_file
        try:
            body = body_path.read_bytes()
        except OSError as exc:
            raise LiveEpisodeError(f"endpoint body is missing: {body_path}") from exc
        digest = hashlib.sha256(body).hexdigest()
        if digest != endpoint.get("content_hash_sha256"):
            raise LiveEpisodeError(f"endpoint {path} body hash does not match manifest")
        expected_schema = detect_schema(body, available=True, http_status=200)
        if endpoint.get("schema_detection") != expected_schema:
            raise LiveEpisodeError(f"endpoint {path} schema fingerprint does not match body")
        manifest_identity = {
            "source_id": SOURCE_ID,
            "origin": request_url,
            "content_hash_sha256": digest,
            "acquisition_status": "success",
            "schema_detection": expected_schema,
        }
        if _stable_hash(manifest_identity) != endpoint.get("manifest_id"):
            raise LiveEpisodeError(f"endpoint {path} manifest identity does not match evidence")
        if endpoint.get("content_identity") != f"sha256:{digest}":
            raise LiveEpisodeError(f"endpoint {path} content identity does not match body hash")
        if endpoint.get("bytes") != len(body):
            raise LiveEpisodeError(f"endpoint {path} byte count does not match body")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise LiveEpisodeError(f"endpoint {path} body is not valid JSON") from exc
        by_path[path] = (endpoint, payload)
        verified.append(endpoint)

    if set(by_path) != REQUIRED_ENDPOINTS:
        raise LiveEpisodeError("capture is missing bootstrap or fixtures endpoint")
    stable_identity = {
        "source_id": SOURCE_ID,
        "observed_at": observed_at,
        "endpoint_manifest_ids": [endpoint["manifest_id"] for endpoint in endpoints],
    }
    if _stable_hash(stable_identity) != summary.get("capture_id"):
        raise LiveEpisodeError("capture identity does not match endpoint manifests")
    bootstrap = by_path["/api/bootstrap-static/"][1]
    fixtures = by_path["/api/fixtures/"][1]
    if not isinstance(bootstrap, dict):
        raise LiveEpisodeError("bootstrap body must be an object")
    if not isinstance(fixtures, list):
        raise LiveEpisodeError("fixtures body must be an array")
    return summary, bootstrap, fixtures, verified


def _observations(
    *,
    bootstrap: Mapping[str, Any],
    fixtures: list[dict[str, Any]],
    gameweek: int,
    observed_at: str,
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    elements = bootstrap.get("elements")
    if not isinstance(elements, list) or not elements:
        raise LiveEpisodeError("bootstrap elements catalogue is missing or empty")
    records: list[dict[str, Any]] = []
    player_ids: list[str] = []
    for element in elements:
        try:
            raw_id = int(element["id"])
            player_id = f"player:{raw_id}"
            ownership = float(element["selected_by_percent"])
        except (KeyError, TypeError, ValueError) as exc:
            raise LiveEpisodeError("bootstrap player feature fields are malformed") from exc
        player_ids.append(player_id)
        records.append(
            normalise_observation(
                {
                    "source_id": SOURCE_ID,
                    "field_name": "selected_by_percent",
                    "entity_id": player_id,
                    "source_record_id": f"element:{raw_id}",
                    "observed_at": observed_at,
                    "ingested_at": observed_at,
                    "value": ownership,
                }
            )
        )
        records.append(
            normalise_observation(
                {
                    "source_id": SOURCE_ID,
                    "field_name": "player_status",
                    "entity_id": player_id,
                    "source_record_id": f"element:{raw_id}",
                    "published_at": element.get("news_added"),
                    "observed_at": observed_at,
                    "ingested_at": observed_at,
                    "value": {
                        "status": element.get("status"),
                        "news": element.get("news"),
                        "news_added": element.get("news_added"),
                        "chance_of_playing_this_round": element.get(
                            "chance_of_playing_this_round"
                        ),
                        "chance_of_playing_next_round": element.get(
                            "chance_of_playing_next_round"
                        ),
                    },
                }
            )
        )
    fixture_ids: list[str] = []
    for fixture in fixtures:
        try:
            if int(fixture.get("event", 0)) != gameweek:
                continue
            raw_id = int(fixture["id"])
        except (TypeError, ValueError, KeyError) as exc:
            raise LiveEpisodeError("fixture identity is malformed") from exc
        fixture_id = f"fixture:{raw_id}"
        fixture_ids.append(fixture_id)
        value = {field: fixture.get(field) for field in OBSERVED_FIXTURE_FIELDS}
        records.append(
            normalise_observation(
                {
                    "source_id": SOURCE_ID,
                    "field_name": "fixture",
                    "entity_id": fixture_id,
                    "source_record_id": fixture_id,
                    "observed_at": observed_at,
                    "ingested_at": observed_at,
                    "value": value,
                }
            )
        )
    if not fixture_ids:
        raise LiveEpisodeError(f"capture contains no fixtures for Gameweek {gameweek}")
    records.sort(
        key=lambda row: (str(row["field_name"]), str(row["entity_id"]), row["observation_id"])
    )
    return records, {
        "ownership_percent": sorted(player_ids),
        "player_status": sorted(player_ids),
        "fixture_state": sorted(fixture_ids),
    }


def _feature_view(
    *,
    episode_id: str,
    cutoff: str,
    capture: Mapping[str, Any],
    endpoints: list[dict[str, Any]],
    bootstrap: Mapping[str, Any],
    fixtures: list[dict[str, Any]],
    gameweek: int,
) -> dict[str, Any]:
    capture_id = str(capture["capture_id"])
    observed_at = str(capture["observed_at"])
    records, expected_entities = _observations(
        bootstrap=bootstrap,
        fixtures=fixtures,
        gameweek=gameweek,
        observed_at=observed_at,
    )
    aggregate = {
        "capture_id": capture_id,
        "endpoints": [
            {
                "manifest_id": str(endpoint["manifest_id"]),
                "content_hash_sha256": str(endpoint["content_hash_sha256"]),
            }
            for endpoint in endpoints
        ],
    }
    aggregate_hash = _stable_hash(aggregate)
    synthetic_manifest = {
        "manifest_id": capture_id,
        "source_id": SOURCE_ID,
        "observed_at": observed_at,
        "acquisition_status": "success",
        "content_hash_sha256": aggregate_hash,
    }
    entities = sorted(
        {entity for entity_ids in expected_entities.values() for entity in entity_ids}
    )
    identity = {
        "metrics": {
            "total": len(entities),
            "resolved": len(entities),
            "review": 0,
            "unresolved": 0,
            "match_rate": 1.0,
        }
    }
    quality = evaluate_quality(
        source_id=SOURCE_ID,
        records=records,
        evaluation_at=cutoff,
        acquisition_manifest=synthetic_manifest,
        identity_report=identity,
        expected_entity_ids=entities,
        actual_content_hash=aggregate_hash,
        mode="enforce",
    )
    snapshot_ids = {record["observation_id"]: capture_id for record in records}
    return materialise_deadline_view(
        episode_id=episode_id,
        cutoff=cutoff,
        observations=records,
        quality_reports=[quality],
        observation_snapshot_ids=snapshot_ids,
        expected_entities=expected_entities,
    )


def _pending_outcome(
    *, episode_id: str, season: str, gameweek: int
) -> dict[str, Any]:
    pending: dict[str, Any] = {
        "pending_outcome_version": "1.0",
        "outcome_id": f"pending:{episode_id}",
        "episode_id": episode_id,
        "season": season,
        "gameweek": gameweek,
        "status": "pending",
        "reveal_after": "proposal_frozen",
        "contains_outcome_values": False,
    }
    pending["content_sha256"] = _content_hash(pending)
    _validate(PENDING_SCHEMA, pending, "pending outcome")
    return pending


def _observed_episode_hash(manifest: Mapping[str, Any]) -> str:
    return _stable_hash(
        {
            key: item
            for key, item in manifest.items()
            if key not in {"created_at", "hidden_outcome_ref"}
        }
    )


def build_live_episode(
    *,
    capture_summary_path: Path,
    manager_state_path: Path,
    out_dir: Path,
    rules_path: Path = DEFAULT_RULES_PATH,
    code_commit: str | None = None,
    compatibility_policy: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Build one immutable live-shadow episode and return a safe hash index."""

    capture, bootstrap, fixtures, endpoints = _verify_capture(capture_summary_path)
    manager_entry = _load_json(manager_state_path, "manual manager state")
    if not isinstance(manager_entry, dict):
        raise LiveEpisodeError("manual manager state must be an object")
    rules = load_rules(rules_path)
    rules_hash = ruleset_sha256(rules_path)
    manager = normalise_manager_state(
        manager_entry,
        bootstrap=bootstrap,
        rules=rules,
        ruleset_sha256=rules_hash,
        compatibility_policy=compatibility_policy,
    )
    cutoff = str(manager["cutoff"])
    capture_at = _timestamp(capture["observed_at"], "capture.observed_at")
    if parse_aware_datetime(capture_at, field="capture.observed_at") > parse_aware_datetime(
        cutoff, field="cutoff"
    ):
        raise LiveEpisodeError("capture observed_at is after episode cutoff")
    if capture_at > str(manager["available_at"]):
        created_at = capture_at
    else:
        created_at = str(manager["available_at"])

    commit = code_commit or _git_commit()
    if len(commit) not in {40, 64} or any(char not in "0123456789abcdef" for char in commit):
        raise LiveEpisodeError("code_commit must be a lower-case Git SHA")
    season = str(manager["season"])
    gameweek = int(manager["gameweek"])
    episode_id = f"live-shadow:{season}:gw{gameweek:02d}:{manager['manager_id']}"
    features = _feature_view(
        episode_id=episode_id,
        cutoff=cutoff,
        capture=capture,
        endpoints=endpoints,
        bootstrap=bootstrap,
        fixtures=fixtures,
        gameweek=gameweek,
    )
    feature_hash = _stable_hash(features)
    manager_hash = str(manager["content_sha256"])
    uncertainty = {
        "forecast_uncertainty_version": "1.0",
        "episode_id": episode_id,
        "status": "feature_view_ready_forecast_pending",
        "feature_view_status": str(features["status"]),
        "degraded_features": list(features["degraded_features"]),
        "feature_count": len(features["features"]),
    }
    uncertainty_hash = _stable_hash(uncertainty)
    pending = _pending_outcome(
        episode_id=episode_id,
        season=season,
        gameweek=gameweek,
    )
    source_artifacts = [
        {
            "source_id": SOURCE_ID,
            "artifact_id": str(endpoint["manifest_id"]),
            "content_sha256": str(endpoint["content_hash_sha256"]),
            "available_at": capture_at,
        }
        for endpoint in sorted(endpoints, key=lambda row: str(row["request_url"]))
    ]
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "episode_id": episode_id,
        "season": season,
        "gameweek": gameweek,
        "mode": "live_shadow",
        "cutoff": cutoff,
        "deadline": str(manager["deadline"]),
        "created_at": created_at,
        "code_commit": commit,
        "ruleset": {
            "ruleset_id": str(manager["ruleset_id"]),
            "content_sha256": rules_hash,
        },
        "observed": {
            "snapshot_ids": sorted(
                str(endpoint["manifest_id"]) for endpoint in endpoints
            ),
            "source_artifacts": source_artifacts,
            "manager_state_ref": {
                "artifact_id": str(manager["manager_state_id"]),
                "content_sha256": manager_hash,
            },
            "feature_snapshot_ref": {
                "artifact_id": str(features["feature_view_id"]),
                "content_sha256": feature_hash,
            },
            "forecast_uncertainty_ref": {
                "artifact_id": f"forecast-uncertainty:{episode_id}",
                "content_sha256": uncertainty_hash,
            },
        },
        "allowed_tools": [
            {
                "tool_id": "deadline-feature-query",
                "version": str(features["transformation_version"]),
                "access": "read_only",
            }
        ],
        "resource_budget": {
            "wall_clock_seconds": 120,
            "tool_calls": 20,
            "tokens": 10000,
            "cost_currency": "GBP",
            "cost_cap": 1.0,
        },
        "policy_arms": list(POLICY_ARMS),
        "hidden_outcome_ref": {
            "outcome_id": str(pending["outcome_id"]),
            "content_sha256": str(pending["content_sha256"]),
            "reveal_after": "proposal_frozen",
        },
    }
    _validate(EPISODE_SCHEMA, manifest, "episode manifest")
    for artifact in source_artifacts:
        if parse_aware_datetime(
            str(artifact["available_at"]), field="source_artifact.available_at"
        ) > parse_aware_datetime(cutoff, field="cutoff"):
            raise LiveEpisodeError("source artifact is available after episode cutoff")
    observed_hash = _observed_episode_hash(manifest)
    index: dict[str, Any] = {
        "episode_index_version": "1.0",
        "episode_id": episode_id,
        "mode": "live_shadow",
        "season": season,
        "gameweek": gameweek,
        "cutoff": cutoff,
        "deadline": str(manager["deadline"]),
        "observed_episode_sha256": observed_hash,
        "manager_state_sha256": manager_hash,
        "feature_view_sha256": feature_hash,
        "forecast_uncertainty_sha256": uncertainty_hash,
        "pending_outcome_sha256": str(pending["content_sha256"]),
        "ruleset_id": str(manager["ruleset_id"]),
        "ruleset_sha256": rules_hash,
        "snapshot_ids": sorted(str(endpoint["manifest_id"]) for endpoint in endpoints),
        "feature_view_status": str(features["status"]),
        "degraded_feature_count": len(features["degraded_features"]),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_immutable_json(out_dir / "manager-state.json", manager)
    _write_immutable_json(out_dir / "feature-view.json", features)
    _write_immutable_json(out_dir / "forecast-uncertainty.json", uncertainty)
    _write_immutable_json(out_dir / "pending-outcome.json", pending)
    _write_immutable_bytes(out_dir / "ruleset.yaml", ruleset_bytes(rules_path))
    _write_immutable_json(out_dir / "episode-manifest.json", manifest)
    _write_immutable_json(out_dir / "episode-index.json", index)
    return index
