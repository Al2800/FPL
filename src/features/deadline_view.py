"""Materialise immutable, quality-approved feature views at an episode cutoff."""

from __future__ import annotations

import hashlib
import json
from datetime import timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

from src.data.quality import require_admissible
from src.data.temporal import parse_aware_datetime

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = REPO_ROOT / "control" / "policies" / "feature-source-precedence.yaml"


class FeatureViewError(ValueError):
    """Raised when a required cutoff-safe feature cannot be materialised."""


def load_feature_policy(path: Path | None = None) -> dict[str, Any]:
    policy_path = path or DEFAULT_POLICY
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    if not isinstance(policy, dict) or not policy.get("policy_version"):
        raise FeatureViewError(f"Invalid feature-source policy: {policy_path}")
    if not isinstance(policy.get("features"), dict):
        raise FeatureViewError("Feature-source policy must define features")
    for name, definition in policy["features"].items():
        if not isinstance(definition.get("required"), bool):
            raise FeatureViewError(f"Feature {name!r} must declare required")
        if definition.get("on_missing") not in {"stop", "record_degraded"}:
            raise FeatureViewError(f"Feature {name!r} has invalid on_missing policy")
        candidates = definition.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise FeatureViewError(f"Feature {name!r} has no source candidates")
        if any(not item.get("source_id") or not item.get("field_name") for item in candidates):
            raise FeatureViewError(
                f"Feature {name!r} candidates require source_id and field_name"
            )
    return policy


def _utc(value: str, *, field: str):
    return parse_aware_datetime(value, field=field).astimezone(timezone.utc)


def _timestamp(value: str, *, field: str) -> str:
    return _utc(value, field=field).isoformat().replace("+00:00", "Z")


def _stable_id(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _select_quality_reports(
    reports: Iterable[dict[str, Any]], cutoff: str
) -> dict[str, dict[str, Any]]:
    cutoff_at = _utc(cutoff, field="cutoff")
    eligible: dict[str, list[dict[str, Any]]] = {}
    for report in reports:
        evaluated_at = _utc(
            str(report["evaluated_at"]), field="quality_report.evaluated_at"
        )
        if evaluated_at <= cutoff_at:
            eligible.setdefault(str(report["source_id"]), []).append(report)
    selected: dict[str, dict[str, Any]] = {}
    for source_id, source_reports in sorted(eligible.items()):
        latest_at = max(
            _utc(str(report["evaluated_at"]), field="quality_report.evaluated_at")
            for report in source_reports
        )
        latest = {
            str(report["report_id"]): report
            for report in source_reports
            if _utc(str(report["evaluated_at"]), field="quality_report.evaluated_at")
            == latest_at
        }
        if len(latest) > 1:
            raise FeatureViewError(
                f"Ambiguous quality reports for source={source_id!r} at {latest_at.isoformat()}"
            )
        selected[source_id] = next(iter(latest.values()))
    return selected


def _quality_lineage(reports: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "source_id": source_id,
            "report_id": str(report["report_id"]),
            "quality_policy_version": str(report["policy_version"]),
            "quality_mode": str(report["mode"]),
            "snapshot_id": str(report["snapshot_id"]),
            "evaluated_at": str(report["evaluated_at"]),
            "recommended_disposition": str(report["recommended_disposition"]),
            "enforced_disposition": str(report["enforced_disposition"]),
            "admissible": bool(report["admissible"]),
            "degraded_capabilities": sorted(report.get("degraded_capabilities", [])),
        }
        for source_id, report in sorted(reports.items())
    ]


def materialise_deadline_view(
    *,
    episode_id: str,
    cutoff: str,
    observations: Iterable[dict[str, Any]],
    quality_reports: Iterable[dict[str, Any]],
    observation_snapshot_ids: dict[str, str],
    expected_entities: dict[str, Iterable[str]],
    policy_path: Path | None = None,
) -> dict[str, Any]:
    """Build a deterministic feature view using explicit quality and source precedence."""

    if not episode_id:
        raise FeatureViewError("episode_id is required")
    cutoff_value = _timestamp(cutoff, field="cutoff")
    cutoff_at = _utc(cutoff_value, field="cutoff")
    policy = load_feature_policy(policy_path)
    feature_policy = policy["features"]
    records = list(observations)
    unknown_features = sorted(set(expected_entities) - set(feature_policy))
    if unknown_features:
        raise FeatureViewError(
            "Unknown feature scopes: " + ", ".join(unknown_features)
        )
    relevant_sources = {
        str(candidate["source_id"])
        for feature_name in expected_entities
        for candidate in feature_policy[feature_name]["candidates"]
    }
    selected_reports = _select_quality_reports(
        (
            report
            for report in quality_reports
            if str(report.get("source_id")) in relevant_sources
        ),
        cutoff_value,
    )

    required_features = sorted(
        name for name, definition in feature_policy.items() if definition.get("required")
    )
    missing_scopes = [name for name in required_features if name not in expected_entities]
    if missing_scopes:
        raise FeatureViewError(
            "Expected entity scopes missing for required features: " + ", ".join(missing_scopes)
        )

    candidates_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for record in records:
        observation_id = str(record.get("observation_id", ""))
        if not observation_id or observation_id not in observation_snapshot_ids:
            continue
        available_at = _utc(str(record["available_at"]), field="available_at")
        if available_at > cutoff_at:
            continue
        source_id = str(record["source_id"])
        report = selected_reports.get(source_id)
        if report is None:
            continue
        if str(report["snapshot_id"]) != str(observation_snapshot_ids[observation_id]):
            continue
        if observation_id not in set(report.get("admitted_observation_ids", [])):
            continue
        key = (source_id, str(record["field_name"]), str(record["entity_id"]))
        candidates_by_key.setdefault(key, []).append(record)

    for values in candidates_by_key.values():
        values.sort(key=lambda row: (str(row["available_at"]), str(row["observation_id"])))

    features: list[dict[str, Any]] = []
    degraded: list[dict[str, Any]] = []
    for feature_name, definition in sorted(feature_policy.items()):
        if feature_name not in expected_entities:
            continue
        entities = sorted({str(entity_id) for entity_id in expected_entities[feature_name]})
        candidates = definition.get("candidates", [])
        if not candidates:
            raise FeatureViewError(f"Feature {feature_name!r} has no source candidates")
        for entity_id in entities:
            selected_record: dict[str, Any] | None = None
            selected_index: int | None = None
            for index, candidate in enumerate(candidates):
                key = (
                    str(candidate["source_id"]),
                    str(candidate["field_name"]),
                    entity_id,
                )
                matching = candidates_by_key.get(key, [])
                if matching:
                    selected_record = matching[-1]
                    selected_index = index
                    break

            preferred = candidates[0]
            if selected_record is None:
                reason = "missing_required_feature" if definition.get("required") else "missing_optional_feature"
                missing = {
                    "feature_name": feature_name,
                    "entity_id": entity_id,
                    "required": bool(definition.get("required")),
                    "reason": reason,
                    "preferred_source_id": str(preferred["source_id"]),
                    "selected_source_id": None,
                    "details": {
                        "candidate_sources": [str(item["source_id"]) for item in candidates],
                        "on_missing": str(definition["on_missing"]),
                    },
                }
                if definition.get("required") or definition.get("on_missing") == "stop":
                    raise FeatureViewError(
                        f"Required feature unavailable: {feature_name}:{entity_id}"
                    )
                degraded.append(missing)
                continue

            observation_id = str(selected_record["observation_id"])
            report = selected_reports[str(selected_record["source_id"])]
            require_admissible(report, [observation_id])
            selection_method = "preferred_source" if selected_index == 0 else "fallback_source"
            feature = {
                "feature_name": feature_name,
                "entity_id": entity_id,
                "value": selected_record.get("value"),
                "source_id": str(selected_record["source_id"]),
                "field_name": str(selected_record["field_name"]),
                "observation_id": observation_id,
                "snapshot_id": str(observation_snapshot_ids[observation_id]),
                "quality_report_id": str(report["report_id"]),
                "available_at": str(selected_record["available_at"]),
                "observed_at": str(selected_record["observed_at"]),
                "selection_method": selection_method,
            }
            features.append(feature)
            if selected_index:
                degraded.append(
                    {
                        "feature_name": feature_name,
                        "entity_id": entity_id,
                        "required": bool(definition.get("required")),
                        "reason": "fallback_source",
                        "preferred_source_id": str(preferred["source_id"]),
                        "selected_source_id": str(selected_record["source_id"]),
                        "details": {"selected_precedence": selected_index + 1},
                    }
                )

    features.sort(key=lambda row: (row["feature_name"], row["entity_id"]))
    degraded.sort(key=lambda row: (row["feature_name"], row["entity_id"], row["reason"]))
    quality_lineage = _quality_lineage(selected_reports)
    manifest: dict[str, Any] = {
        "feature_view_version": "1.0",
        "episode_id": episode_id,
        "cutoff": cutoff_value,
        "policy_version": str(policy["policy_version"]),
        "transformation_version": str(policy["transformation_version"]),
        "status": "degraded" if degraded else "complete",
        "features": features,
        "degraded_features": degraded,
        "included_observation_ids": sorted({row["observation_id"] for row in features}),
        "source_snapshot_ids": sorted({row["snapshot_id"] for row in features}),
        "quality_reports": quality_lineage,
    }
    manifest["feature_view_id"] = _stable_id(manifest)
    return manifest
