"""Offline calibration of data-quality gates from replay and live-shadow evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator, FormatChecker

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLAN = REPO_ROOT / "evals" / "data-quality" / "calibration-plan.yaml"
DEFAULT_SHADOW_SCHEMA = (
    REPO_ROOT / "evals" / "data-quality" / "live-shadow-manifest.schema.json"
)
EVIDENCE_MODES = {"historical_replay", "live_shadow"}
EXCLUDING_DISPOSITIONS = {"quarantine", "stop"}
METRIC_FIELDS = (
    "schema_error_rate",
    "exact_duplicate_rate",
    "equivalent_duplicate_rate",
    "conflicting_duplicate_rate",
    "coverage_rate",
    "identity_match_rate",
    "staleness_seconds",
    "disagreement_rate",
)


class CalibrationError(ValueError):
    """Raised when calibration evidence or criteria are invalid."""


def load_calibration_plan(path: Path | None = None) -> dict[str, Any]:
    plan_path = path or DEFAULT_PLAN
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    if not isinstance(plan, dict) or not plan.get("calibration_plan_version"):
        raise CalibrationError(f"Invalid calibration plan: {plan_path}")
    criteria = plan.get("promotion_criteria", {})
    required = {
        "minimum_cases_total",
        "minimum_cases_per_segment",
        "required_evidence_modes",
        "max_false_quarantine_rate",
        "max_false_admission_rate",
    }
    if not required.issubset(criteria):
        raise CalibrationError("Calibration plan is missing promotion criteria")
    return plan


def validate_live_shadow_manifest(
    manifest: dict[str, Any], schema_path: Path | None = None
) -> dict[str, Any]:
    schema = json.loads((schema_path or DEFAULT_SHADOW_SCHEMA).read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(manifest)
    return manifest


def _quantile(values: list[float], proportion: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * proportion
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _distribution(values: Iterable[Any]) -> dict[str, Any]:
    numeric = sorted(float(value) for value in values if value is not None)
    if not numeric:
        return {"count": 0, "min": None, "max": None, "mean": None, "p50": None, "p95": None}
    return {
        "count": len(numeric),
        "min": numeric[0],
        "max": numeric[-1],
        "mean": sum(numeric) / len(numeric),
        "p50": _quantile(numeric, 0.5),
        "p95": _quantile(numeric, 0.95),
    }


def _confusion(cases: list[dict[str, Any]]) -> dict[str, Any]:
    false_quarantine = 0
    false_admission = 0
    correct = 0
    for case in cases:
        recommended_exclude = (
            str(case["quality_report"]["recommended_disposition"])
            in EXCLUDING_DISPOSITIONS
        )
        should_exclude = bool(case["adjudication"]["should_exclude"])
        if recommended_exclude and not should_exclude:
            false_quarantine += 1
        elif not recommended_exclude and should_exclude:
            false_admission += 1
        else:
            correct += 1
    count = len(cases)
    return {
        "case_count": count,
        "correct_count": correct,
        "false_quarantine_count": false_quarantine,
        "false_quarantine_rate": false_quarantine / count if count else 0.0,
        "false_admission_count": false_admission,
        "false_admission_rate": false_admission / count if count else 0.0,
    }


def _decision_delta(case: dict[str, Any]) -> dict[str, Any]:
    unrestricted = case.get("unrestricted_decision")
    gated = case.get("gated_decision")
    unrestricted_action = unrestricted.get("action_id") if unrestricted else None
    gated_action = gated.get("action_id") if gated else None
    unrestricted_score = unrestricted.get("projected_score") if unrestricted else None
    gated_score = gated.get("projected_score") if gated else None
    score_delta = (
        float(gated_score) - float(unrestricted_score)
        if unrestricted_score is not None and gated_score is not None
        else None
    )
    unrestricted_realized = unrestricted.get("realized_score") if unrestricted else None
    gated_realized = gated.get("realized_score") if gated else None
    realized_delta = (
        float(gated_realized) - float(unrestricted_realized)
        if unrestricted_realized is not None and gated_realized is not None
        else None
    )
    return {
        "case_id": str(case["case_id"]),
        "unrestricted_action_id": unrestricted_action,
        "gated_action_id": gated_action,
        "action_changed": unrestricted_action != gated_action,
        "projected_score_delta": score_delta,
        "realized_score_delta": realized_delta,
    }


def _segment(cases: list[dict[str, Any]]) -> dict[str, Any]:
    first = cases[0]
    confusion = _confusion(cases)
    deltas = [_decision_delta(case) for case in cases]
    return {
        "gate_id": str(first["gate_id"]),
        "source_id": str(first["source_id"]),
        "field_name": str(first["field_name"]),
        "entity_type": str(first["entity_type"]),
        "evidence_modes": sorted({str(case["evidence_mode"]) for case in cases}),
        "gameweeks": sorted({int(case["gameweek"]) for case in cases}),
        "case_count": len(cases),
        "metrics": {
            field: _distribution(
                case["quality_report"].get("metrics", {}).get(field) for case in cases
            )
            for field in METRIC_FIELDS
        },
        "confusion": confusion,
        "decision_change_rate": sum(delta["action_changed"] for delta in deltas) / len(deltas),
        "projected_score_delta": _distribution(
            delta["projected_score_delta"] for delta in deltas
        ),
        "realized_score_delta": _distribution(
            delta["realized_score_delta"] for delta in deltas
        ),
    }


def _promotion_review(
    cases: list[dict[str, Any]], segments: list[dict[str, Any]], plan: dict[str, Any]
) -> dict[str, Any]:
    criteria = plan["promotion_criteria"]
    confusion = _confusion(cases)
    modes = sorted({str(case["evidence_mode"]) for case in cases})
    reasons: list[str] = []
    if len(cases) < int(criteria["minimum_cases_total"]):
        reasons.append("insufficient_case_count")
    if any(segment["case_count"] < int(criteria["minimum_cases_per_segment"]) for segment in segments):
        reasons.append("insufficient_segment_case_count")
    missing_modes = sorted(set(criteria["required_evidence_modes"]) - set(modes))
    if missing_modes:
        reasons.append("missing_required_evidence_modes")
    if any(set(criteria["required_evidence_modes"]) - set(segment["evidence_modes"]) for segment in segments):
        reasons.append("segment_missing_required_evidence_modes")
    if confusion["false_quarantine_rate"] > float(criteria["max_false_quarantine_rate"]):
        reasons.append("false_quarantine_rate_too_high")
    if confusion["false_admission_rate"] > float(criteria["max_false_admission_rate"]):
        reasons.append("false_admission_rate_too_high")
    if any(segment["confusion"]["false_quarantine_rate"] > float(criteria["max_false_quarantine_rate"]) for segment in segments):
        reasons.append("segment_false_quarantine_rate_too_high")
    if any(segment["confusion"]["false_admission_rate"] > float(criteria["max_false_admission_rate"]) for segment in segments):
        reasons.append("segment_false_admission_rate_too_high")

    if any(reason.startswith("insufficient_") or "missing_required_evidence" in reason for reason in reasons):
        status = "insufficient_evidence"
    elif reasons:
        status = "retain_observe_only"
    else:
        status = "eligible_for_owner_review"
    return {
        "status": status,
        "automatic_policy_update": False,
        "reason_codes": reasons,
        "observed_evidence_modes": modes,
        "criteria": dict(criteria),
        "confusion": confusion,
    }


def calibrate_quality_cases(
    cases: Iterable[dict[str, Any]], *, plan_path: Path | None = None
) -> dict[str, Any]:
    """Summarise replay/shadow evidence without changing production policy."""

    ordered = sorted((dict(case) for case in cases), key=lambda case: str(case["case_id"]))
    case_ids = [str(case["case_id"]) for case in ordered]
    if len(case_ids) != len(set(case_ids)):
        raise CalibrationError("Calibration case_id values must be unique")
    if not ordered:
        raise CalibrationError("At least one calibration case is required")
    invalid_modes = sorted(
        {str(case["evidence_mode"]) for case in ordered} - EVIDENCE_MODES
    )
    if invalid_modes:
        raise CalibrationError("Unknown evidence modes: " + ", ".join(invalid_modes))
    plan = load_calibration_plan(plan_path)

    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for case in ordered:
        key = (
            str(case["gate_id"]),
            str(case["source_id"]),
            str(case["field_name"]),
            str(case["entity_type"]),
        )
        grouped.setdefault(key, []).append(case)
    segments = [_segment(grouped[key]) for key in sorted(grouped)]
    decision_deltas = [_decision_delta(case) for case in ordered]
    report: dict[str, Any] = {
        "calibration_version": "1.0",
        "calibration_plan_version": str(plan["calibration_plan_version"]),
        "case_ids": case_ids,
        "case_count": len(ordered),
        "segments": segments,
        "overall_confusion": _confusion(ordered),
        "decision_deltas": decision_deltas,
        "promotion_review": _promotion_review(ordered, segments, plan),
    }
    report["calibration_id"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return report
