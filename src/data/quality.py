"""Deterministic data-quality gates with staged, scoped quarantine."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from src.data.temporal import parse_aware_datetime

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = REPO_ROOT / "control" / "policies" / "data-quality.yaml"
TEMPORAL_SCHEMA = REPO_ROOT / "control" / "schemas" / "data" / "temporal-observation.json"
MODES = {"observe_only", "shadow", "enforce"}
DISPOSITION_RANK = {"pass": 0, "degrade": 1, "quarantine": 2, "stop": 3}


class DataQualityError(ValueError):
    """Raised when quality configuration or inputs are invalid."""


class QuarantinedDataError(DataQualityError):
    """Raised when downstream code requests data excluded by an enforced report."""


def load_quality_policy(path: Path | None = None) -> dict[str, Any]:
    policy_path = path or DEFAULT_POLICY
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    if not isinstance(policy, dict) or not policy.get("policy_version"):
        raise DataQualityError(f"Invalid data-quality policy: {policy_path}")
    if policy.get("default_mode") not in MODES:
        raise DataQualityError("data-quality default_mode is invalid")
    return policy


def _source_policy(policy: dict[str, Any], source_id: str) -> dict[str, Any]:
    try:
        result = policy["sources"][source_id]
    except (KeyError, TypeError) as exc:
        raise DataQualityError(f"No data-quality policy for source={source_id!r}") from exc
    return result


def _utc(value: str, *, field: str) -> datetime:
    return parse_aware_datetime(value, field=field).astimezone(timezone.utc)


def _timestamp(value: str, *, field: str) -> str:
    return _utc(value, field=field).isoformat().replace("+00:00", "Z")


def _target(record: dict[str, Any], index: int) -> str:
    fallback = hashlib.sha256(_stable_value(record).encode("utf-8")).hexdigest()
    return str(record.get("observation_id") or f"invalid:{fallback}")


def _stable_value(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _check(
    check_id: str,
    *,
    category: str,
    status: str,
    scope: str,
    disposition: str,
    enforcement_enabled: bool,
    reason_code: str,
    observed: Any,
    threshold: Any,
    targets: Iterable[str] = (),
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "category": category,
        "status": status,
        "scope": scope,
        "recommended_disposition": disposition,
        "enforcement_enabled": enforcement_enabled,
        "reason_code": reason_code,
        "observed": observed,
        "threshold": threshold,
        "targets": sorted(set(targets)),
        "details": details or {},
    }


def _worst(dispositions: Iterable[str]) -> str:
    return max(dispositions, key=lambda item: DISPOSITION_RANK[item], default="pass")


def _schema_check(
    records: list[dict[str, Any]], gate: dict[str, Any], schema_path: Path
) -> tuple[dict[str, Any], set[str], int]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    failures: list[dict[str, Any]] = []
    targets: set[str] = set()
    for index, record in enumerate(records):
        errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
        if not errors:
            continue
        target = _target(record, index)
        targets.add(target)
        failures.extend(
            {
                "target": target,
                "path": "/".join(str(part) for part in error.path),
                "validator": str(error.validator),
            }
            for error in errors
        )
    failures.sort(key=lambda item: (item["target"], item["path"], item["validator"]))
    count = len(targets)
    return (
        _check(
            "schema.temporal_observation",
            category="schema",
            status="fail" if count else "pass",
            scope="record",
            disposition=gate["failure_disposition"] if count else "pass",
            enforcement_enabled=bool(gate.get("enforce")),
            reason_code="schema_invalid" if count else "schema_valid",
            observed=count,
            threshold=0,
            targets=targets,
            details={"errors": failures},
        ),
        targets,
        count,
    )


def _duplicate_check(
    records: list[dict[str, Any]], gate: dict[str, Any]
) -> tuple[list[dict[str, Any]], set[str], int, int, int]:
    by_id: dict[str, int] = defaultdict(int)
    by_key: dict[tuple[str, ...], list[tuple[str, str]]] = defaultdict(list)
    key_fields = tuple(gate["natural_key_fields"])
    for index, record in enumerate(records):
        target = _target(record, index)
        by_id[target] += 1
        key = tuple(str(record.get(field, "")) for field in key_fields)
        by_key[key].append((target, _stable_value(record.get("value"))))

    exact_count = sum(count - 1 for count in by_id.values() if count > 1)
    conflict_targets: set[str] = set()
    redundant_targets: set[str] = set()
    equivalent_groups: list[dict[str, Any]] = []
    conflict_groups: list[dict[str, Any]] = []
    for key, values in sorted(by_key.items()):
        distinct_values = sorted({value for _, value in values})
        targets = sorted({target for target, _ in values})
        if len(distinct_values) == 1 and len(targets) > 1:
            redundant = targets[1:]
            redundant_targets.update(redundant)
            equivalent_groups.append(
                {"natural_key": dict(zip(key_fields, key)), "kept": targets[0], "collapsed": redundant}
            )
            continue
        if len(distinct_values) <= 1:
            continue
        conflict_targets.update(targets)
        conflict_groups.append(
            {"natural_key": dict(zip(key_fields, key)), "targets": targets, "value_count": len(distinct_values)}
        )

    exact = _check(
        "duplicates.exact",
        category="duplicates",
        status="warn" if exact_count else "pass",
        scope="record",
        disposition=gate["exact_disposition"] if exact_count else "pass",
        enforcement_enabled=bool(gate.get("enforce_exact")),
        reason_code="exact_duplicates" if exact_count else "no_exact_duplicates",
        observed=exact_count,
        threshold=0,
    )
    equivalent_count = len(redundant_targets)
    equivalent = _check(
        "duplicates.equivalent",
        category="duplicates",
        status="warn" if equivalent_count else "pass",
        scope="record",
        disposition="pass",
        enforcement_enabled=False,
        reason_code="equivalent_duplicates" if equivalent_count else "no_equivalent_duplicates",
        observed=equivalent_count,
        threshold=0,
        targets=redundant_targets,
        details={"groups": equivalent_groups},
    )
    conflict_count = len(conflict_groups)
    conflicting = _check(
        "duplicates.conflicting",
        category="duplicates",
        status="fail" if conflict_count else "pass",
        scope="record",
        disposition=gate["conflicting_disposition"] if conflict_count else "pass",
        enforcement_enabled=bool(gate.get("enforce_conflicting")),
        reason_code="conflicting_duplicates" if conflict_count else "no_conflicting_duplicates",
        observed=conflict_count,
        threshold=0,
        targets=conflict_targets,
        details={"groups": conflict_groups},
    )
    return (
        [exact, equivalent, conflicting],
        redundant_targets,
        exact_count,
        equivalent_count,
        conflict_count,
    )


def _report_id(report: dict[str, Any]) -> str:
    payload = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def evaluate_quality(
    *,
    source_id: str,
    records: list[dict[str, Any]],
    evaluation_at: str,
    acquisition_manifest: dict[str, Any] | None,
    identity_report: dict[str, Any] | None = None,
    expected_entity_ids: Iterable[str] | None = None,
    reconciliations: Iterable[dict[str, Any]] = (),
    actual_content_hash: str | None = None,
    mode: str | None = None,
    policy_path: Path | None = None,
    temporal_schema_path: Path | None = None,
) -> dict[str, Any]:
    """Evaluate one source snapshot without silently discarding evidence."""

    policy = load_quality_policy(policy_path)
    source_policy = _source_policy(policy, source_id)
    selected_mode = mode or str(policy["default_mode"])
    if selected_mode not in MODES:
        raise DataQualityError(f"Unknown quality mode: {selected_mode}")
    evaluated_at = _timestamp(evaluation_at, field="evaluation_at")
    gates = source_policy["gates"]
    observation_ids = sorted({_target(record, index) for index, record in enumerate(records)})
    checks: list[dict[str, Any]] = []

    acquisition_gate = gates["acquisition"]
    acquisition_ok = acquisition_manifest is not None and acquisition_manifest.get("acquisition_status") == "success"
    hash_ok = (
        acquisition_manifest is not None
        and (
            actual_content_hash is None
            or actual_content_hash == acquisition_manifest.get("content_hash_sha256")
        )
    )
    acquisition_passed = acquisition_ok and hash_ok
    checks.append(
        _check(
            "acquisition.integrity",
            category="acquisition",
            status="pass" if acquisition_passed else "fail",
            scope="snapshot",
            disposition=acquisition_gate["failure_disposition"] if not acquisition_passed else "pass",
            enforcement_enabled=bool(acquisition_gate.get("enforce")),
            reason_code="acquisition_valid" if acquisition_passed else "acquisition_invalid",
            observed={"status": acquisition_manifest.get("acquisition_status") if acquisition_manifest else None, "hash_match": hash_ok},
            threshold={"status": "success", "hash_match": True},
            targets=[str(acquisition_manifest.get("manifest_id", "missing"))] if acquisition_manifest else ["missing"],
        )
    )

    schema_check, schema_targets, schema_errors = _schema_check(
        records, gates["schema"], temporal_schema_path or TEMPORAL_SCHEMA
    )
    checks.append(schema_check)

    freshness_gate = gates["freshness"]
    staleness_seconds: float | None = None
    freshness_failed = False
    if acquisition_manifest and acquisition_manifest.get("observed_at"):
        staleness_seconds = (_utc(evaluated_at, field="evaluation_at") - _utc(str(acquisition_manifest["observed_at"]), field="observed_at")).total_seconds()
        freshness_failed = staleness_seconds < 0 or staleness_seconds > float(freshness_gate["max_age_seconds"])
    else:
        freshness_failed = True
    checks.append(
        _check(
            "freshness.snapshot_age",
            category="freshness",
            status="fail" if freshness_failed else "pass",
            scope="snapshot",
            disposition=freshness_gate["failure_disposition"] if freshness_failed else "pass",
            enforcement_enabled=bool(freshness_gate.get("enforce")),
            reason_code="snapshot_stale_or_unclocked" if freshness_failed else "snapshot_fresh",
            observed=staleness_seconds,
            threshold=float(freshness_gate["max_age_seconds"]),
        )
    )

    coverage_gate = gates["coverage"]
    expected = set(expected_entity_ids) if expected_entity_ids is not None else None
    observed_entities = {str(record.get("entity_id")) for record in records if record.get("entity_id")}
    coverage_rate = None if expected is None or not expected else len(observed_entities & expected) / len(expected)
    coverage_failed = coverage_rate is None or coverage_rate < float(coverage_gate["min_rate"])
    checks.append(
        _check(
            "coverage.expected_entities",
            category="coverage",
            status="fail" if coverage_rate is not None and coverage_failed else ("warn" if coverage_failed else "pass"),
            scope="partition",
            disposition=(coverage_gate["missing_denominator_disposition"] if coverage_rate is None else coverage_gate["failure_disposition"]) if coverage_failed else "pass",
            enforcement_enabled=bool(coverage_gate.get("enforce")),
            reason_code="coverage_denominator_missing" if coverage_rate is None else ("coverage_below_threshold" if coverage_failed else "coverage_sufficient"),
            observed=coverage_rate,
            threshold=float(coverage_gate["min_rate"]),
            details={"expected_count": len(expected) if expected is not None else None, "observed_expected_count": len(observed_entities & expected) if expected is not None else None},
        )
    )

    (
        duplicate_checks,
        redundant_duplicates,
        exact_duplicates,
        equivalent_duplicates,
        conflicting_duplicates,
    ) = _duplicate_check(
        records,
        gates["duplicates"],
    )
    checks.extend(duplicate_checks)

    identity_gate = gates["identity"]
    identity_rate = identity_report.get("metrics", {}).get("match_rate") if identity_report else None
    identity_failed = identity_rate is None or float(identity_rate) < float(identity_gate["min_match_rate"])
    identity_targets = observation_ids if identity_failed else []
    checks.append(
        _check(
            "identity.match_rate",
            category="identity",
            status="fail" if identity_rate is not None and identity_failed else ("warn" if identity_failed else "pass"),
            scope="partition",
            disposition=(identity_gate["missing_report_disposition"] if identity_rate is None else identity_gate["failure_disposition"]) if identity_failed else "pass",
            enforcement_enabled=bool(identity_gate.get("enforce")),
            reason_code="identity_report_missing" if identity_rate is None else ("identity_match_below_threshold" if identity_failed else "identity_match_sufficient"),
            observed=identity_rate,
            threshold=float(identity_gate["min_match_rate"]),
            targets=identity_targets,
            details={"metrics": identity_report.get("metrics", {}) if identity_report else {}},
        )
    )

    disagreements: list[dict[str, Any]] = []
    reconciliation_count = 0
    for reconciliation in reconciliations:
        reconciliation_count += 1
        claims = sorted(
            [dict(claim) for claim in reconciliation.get("claims", [])],
            key=lambda claim: (str(claim.get("source_id")), str(claim.get("observation_id"))),
        )
        if len({_stable_value(claim.get("value")) for claim in claims}) <= 1:
            continue
        disagreements.append(
            {
                "entity_id": str(reconciliation.get("entity_id", "")),
                "field_name": str(reconciliation.get("field_name", "")),
                "claims": claims,
            }
        )
    disagreements.sort(key=lambda item: (item["entity_id"], item["field_name"]))
    disagreement_gate = gates["disagreement"]
    disagreement_targets = [
        str(claim.get("observation_id"))
        for disagreement in disagreements
        for claim in disagreement["claims"]
        if claim.get("observation_id")
    ]
    checks.append(
        _check(
            "reconciliation.cross_source",
            category="disagreement",
            status="warn" if disagreements else "pass",
            scope="record",
            disposition=disagreement_gate["failure_disposition"] if disagreements else "pass",
            enforcement_enabled=bool(disagreement_gate.get("enforce")),
            reason_code="cross_source_disagreement" if disagreements else "sources_agree",
            observed=len(disagreements),
            threshold=0,
            targets=disagreement_targets,
            details={"disagreements": disagreements},
        )
    )

    checks.sort(key=lambda item: item["check_id"])
    nonpassing = [check for check in checks if check["status"] != "pass"]
    recommended = _worst(check["recommended_disposition"] for check in nonpassing)
    enforced_checks = [
        check
        for check in nonpassing
        if selected_mode == "enforce" and check["enforcement_enabled"]
    ]
    enforced = _worst(check["recommended_disposition"] for check in enforced_checks)

    quarantine: list[dict[str, Any]] = []
    excluded: set[str] = set()
    snapshot_blocked = False
    for check in nonpassing:
        if check["recommended_disposition"] not in {"quarantine", "stop"}:
            continue
        is_enforced = selected_mode == "enforce" and check["enforcement_enabled"]
        quarantine.append(
            {
                "scope": check["scope"],
                "reason_code": check["reason_code"],
                "targets": check["targets"],
                "enforced": is_enforced,
            }
        )
        if is_enforced and check["scope"] in {"record", "partition"}:
            excluded.update(check["targets"])
        if is_enforced and check["scope"] in {"snapshot", "episode"}:
            snapshot_blocked = True
    quarantine.sort(key=lambda item: (item["scope"], item["reason_code"], item["targets"]))
    observation_id_set = set(observation_ids)
    admitted = (
        []
        if snapshot_blocked
        else sorted(observation_id_set - excluded - redundant_duplicates)
    )

    record_count = len(records)
    metrics = {
        "record_count": record_count,
        "admitted_record_count": len(admitted),
        "quarantined_record_count": len(observation_id_set) if snapshot_blocked else len(excluded & observation_id_set),
        "deduplicated_record_count": exact_duplicates + equivalent_duplicates,
        "schema_error_count": schema_errors,
        "schema_error_rate": schema_errors / record_count if record_count else 0.0,
        "exact_duplicate_count": exact_duplicates,
        "exact_duplicate_rate": exact_duplicates / record_count if record_count else 0.0,
        "equivalent_duplicate_count": equivalent_duplicates,
        "equivalent_duplicate_rate": equivalent_duplicates / record_count if record_count else 0.0,
        "conflicting_duplicate_count": conflicting_duplicates,
        "conflicting_duplicate_rate": conflicting_duplicates / record_count if record_count else 0.0,
        "coverage_rate": coverage_rate,
        "identity_match_rate": identity_rate,
        "staleness_seconds": staleness_seconds,
        "reconciliation_count": reconciliation_count,
        "disagreement_count": len(disagreements),
        "disagreement_rate": len(disagreements) / reconciliation_count if reconciliation_count else 0.0,
    }
    degraded_capabilities = sorted(
        {
            check["category"]
            for check in nonpassing
            if check["recommended_disposition"] in {"degrade", "quarantine", "stop"}
        }
    )
    report: dict[str, Any] = {
        "report_version": "1.0",
        "policy_version": str(policy["policy_version"]),
        "mode": selected_mode,
        "source_id": source_id,
        "snapshot_id": str(acquisition_manifest.get("manifest_id", "missing")) if acquisition_manifest else "missing",
        "evaluated_at": evaluated_at,
        "required_source": bool(source_policy["required"]),
        "recommended_disposition": recommended,
        "enforced_disposition": enforced,
        "admissible": not snapshot_blocked and bool(admitted),
        "checks": checks,
        "metrics": metrics,
        "quarantine": quarantine,
        "admitted_observation_ids": admitted,
        "degraded_capabilities": degraded_capabilities,
        "disagreements": disagreements,
    }
    report["report_id"] = _report_id(report)
    return report


def require_admissible(
    report: dict[str, Any], observation_ids: Iterable[str] | None = None
) -> dict[str, Any]:
    """Fail closed if a downstream view requests excluded quality-gated data."""

    if not report.get("admissible"):
        raise QuarantinedDataError(
            f"Snapshot {report.get('snapshot_id')} is not admissible ({report.get('enforced_disposition')})"
        )
    if observation_ids is not None:
        requested = set(observation_ids)
        admitted = set(report.get("admitted_observation_ids", []))
        excluded = sorted(requested - admitted)
        if excluded:
            raise QuarantinedDataError(f"Observations are quarantined or unknown: {', '.join(excluded)}")
    return report
