"""Immutable, advisory-only GW1 live-readiness rehearsal orchestration.

The rehearsal deliberately composes the initial-squad checkpoint runner rather
than reimplementing forecasting or optimisation.  It proves the operational
path while preserving the selected forecast's own approval gates.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import platform
from pathlib import Path
import sys
from time import perf_counter
from typing import Any, Mapping

from src.forecasting.live_faithful import artifact_hash
from src.orchestration.evidence_checkpoint_runner import (
    EvidenceCheckpointConflict,
    _exclusive_lock,
    _write_immutable_json,
)
from src.orchestration.initial_squad_checkpoint import (
    DEFAULT_POLICY_PATH,
    InitialSquadCheckpointConflict,
    InitialSquadCheckpointError,
    run_initial_squad_checkpoint,
    verify_preseason_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "evals" / "live-readiness" / "2026-27-gw1"
_T48 = "T-48h"
_REHEARSAL_SCHEMA_VERSION = "1.0"


class LiveReadinessRehearsalError(ValueError):
    """Raised when a live-readiness rehearsal cannot be safely completed."""


class LiveReadinessRehearsalConflict(LiveReadinessRehearsalError):
    """Raised when immutable rehearsal output would be overwritten."""


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise LiveReadinessRehearsalError(
            f"{field} must be an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise LiveReadinessRehearsalError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_immutable_text(path: Path, text: str) -> None:
    encoded = text.encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
    except FileExistsError:
        if path.read_bytes() != encoded:
            raise LiveReadinessRehearsalConflict(
                f"Immutable rehearsal path already has different content: {path}"
            )


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    try:
        _write_immutable_json(path, value)
    except EvidenceCheckpointConflict as exc:
        raise LiveReadinessRehearsalConflict(str(exc)) from exc


def _stage_file_hashes(root: Path) -> list[dict[str, str]]:
    if not root.is_dir():
        raise LiveReadinessRehearsalError(f"Missing staged checkpoint directory: {root}")
    rows: list[dict[str, str]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": _sha256_file(path),
            }
        )
    return rows


def _sealed_artifact_hashes(root: Path) -> list[dict[str, str]]:
    """Hash the immutable payloads bound by a report without self-reference."""

    excluded = {
        "rehearsal-report.json",
        "rehearsal-report.md",
        "rerun-comparison.json",
    }
    return [row for row in _stage_file_hashes(root) if row["path"] not in excluded]


def _rerun_artifact_hashes(root: Path) -> list[dict[str, str]]:
    """Hash every frozen file except the comparison that records those hashes."""

    return [
        row
        for row in _stage_file_hashes(root)
        if row["path"] != "rerun-comparison.json"
    ]


def _copy_immutable(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise LiveReadinessRehearsalError(f"Expected staged artifact is missing: {source}")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as handle:
            handle.write(source.read_bytes())
            handle.flush()
    except FileExistsError:
        if destination.read_bytes() != source.read_bytes():
            raise LiveReadinessRehearsalConflict(
                f"Immutable rehearsal path already has different content: {destination}"
            )


def _policy_sha256(policy_path: Path) -> str:
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LiveReadinessRehearsalError(
            f"Cannot read initial-squad policy: {policy_path}"
        ) from exc
    if not isinstance(policy, Mapping):
        raise LiveReadinessRehearsalError("Initial-squad policy must be an object")
    return artifact_hash(dict(policy))


def _t48_target(verified: Mapping[str, Any]) -> str:
    _, deadline = _timestamp(verified["deadline"], "manifest.deadline")
    return (deadline - timedelta(hours=48)).isoformat().replace("+00:00", "Z")


def _validate_t48_capture(
    verified: Mapping[str, Any],
    *,
    checkpoint: str,
    maximum_lag_minutes: int,
) -> str:
    if checkpoint != _T48:
        raise LiveReadinessRehearsalError(
            f"GW1 rehearsal only accepts checkpoint {_T48}"
        )
    if isinstance(maximum_lag_minutes, bool) or maximum_lag_minutes < 0:
        raise LiveReadinessRehearsalError(
            "maximum_lag_minutes must be a non-negative integer"
        )
    target_text = _t48_target(verified)
    _, target = _timestamp(target_text, "T-48h target")
    _, observed = _timestamp(verified["observed_at"], "manifest.observed_at")
    _, available = _timestamp(verified["available_at"], "manifest.available_at")
    latest = target + timedelta(minutes=maximum_lag_minutes)
    if observed < target or observed > latest:
        raise LiveReadinessRehearsalError(
            "Manifest observation is not a T-48h capture within scheduler lag"
        )
    if available < target or available > latest:
        raise LiveReadinessRehearsalError(
            "Manifest availability is not a T-48h capture within scheduler lag"
        )
    return target_text


def _coverage(verified: Mapping[str, Any]) -> dict[str, Any]:
    families = deepcopy(dict(verified["family_states"]))
    mandatory_gaps = sorted(
        family_id
        for family_id, state in families.items()
        if state["mandatory"] and state["state"] != "admitted"
    )
    optional_gaps = sorted(
        family_id
        for family_id, state in families.items()
        if not state["mandatory"] and state["state"] != "admitted"
    )
    quarantined_families = [
        {
            "family_id": family_id,
            "manifest_status": state["manifest_status"],
            "reasons": list(state["reasons"]),
        }
        for family_id, state in sorted(families.items())
        if state["manifest_status"] == "quarantined"
    ]
    result: dict[str, Any] = {
        "schema_version": _REHEARSAL_SCHEMA_VERSION,
        "families": families,
        "mandatory_gaps": mandatory_gaps,
        "optional_gaps": optional_gaps,
        "quarantine_summary": {
            "count": len(quarantined_families),
            "families": quarantined_families,
        },
        "degraded": bool(optional_gaps),
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def _validate_selection(recommendation: Mapping[str, Any]) -> dict[str, Any]:
    selection = recommendation.get("selection")
    if not isinstance(selection, Mapping):
        raise LiveReadinessRehearsalError("Initial-squad recommendation lacks selection")
    proposal = selection.get("selection", {}).get("proposal")
    if not isinstance(proposal, Mapping):
        raise LiveReadinessRehearsalError("Initial-squad recommendation lacks proposal")
    validation = proposal.get("validation")
    if not isinstance(validation, Mapping):
        raise LiveReadinessRehearsalError("Initial-squad proposal lacks validation")
    squad = validation.get("squad")
    first_lineup = validation.get("first_lineup")
    if not isinstance(squad, Mapping) or squad.get("ok") is not True:
        raise LiveReadinessRehearsalError("Initial-squad proposal is not a legal squad")
    if not isinstance(first_lineup, Mapping) or first_lineup.get("ok") is not True:
        raise LiveReadinessRehearsalError("Initial-squad proposal is not a legal first XI")
    if recommendation.get("account_writes") is not False:
        raise LiveReadinessRehearsalError("Initial-squad recommendation allows account writes")
    if recommendation.get("browser_actions") is not False:
        raise LiveReadinessRehearsalError("Initial-squad recommendation allows browser actions")
    return deepcopy(dict(proposal))


def _decision_record(
    *,
    verified: Mapping[str, Any],
    recommendation: Mapping[str, Any],
    checkpoint: Mapping[str, Any],
    coverage: Mapping[str, Any],
) -> dict[str, Any]:
    selection = dict(recommendation["selection"])
    proposal = _validate_selection(recommendation)
    first_week = proposal["weekly_plans"][0]
    lineup = first_week["lineup"]
    decision: dict[str, Any] = {
        "schema_version": _REHEARSAL_SCHEMA_VERSION,
        "record_id": f"live-readiness:{verified['manifest']['season']}:gw1:{verified['checkpoint_id']}",
        "record_kind": "initial_squad_advisory",
        "season": verified["manifest"]["season"],
        "gameweek": 1,
        "decision_cutoff": verified["deadline"],
        "deadline": verified["deadline"],
        "observed_at": verified["observed_at"],
        "available_at": verified["available_at"],
        "ruleset_id": checkpoint["configuration"]["ruleset_id"],
        "ruleset_sha256": checkpoint["configuration"]["ruleset_sha256"],
        "manager_state": {
            "bank": round(float(proposal["bank"]), 4),
            "free_transfers": 0,
            "chips_available": [],
            "squad_player_ids": list(proposal["squad_player_ids"]),
        },
        "validated_plan": {
            "kind": "initial_squad",
            "proposal_sha256": proposal["proposal_sha256"],
            "squad_player_ids": list(proposal["squad_player_ids"]),
            "lineup": deepcopy(lineup),
            "validation": deepcopy(proposal["validation"]),
        },
        "recommendation": {
            "strategy": selection["selection"]["selected_arm"],
            "objective": float(proposal["objective"]),
            "captain_name": str(lineup["captain_id"]),
            "vice_captain_name": str(lineup["vice_captain_id"]),
            "validated_plan_sha256": proposal["proposal_sha256"],
        },
        "baseline_comparison": {
            "do_nothing_objective": float(proposal["objective"]),
            "recommended_objective": float(proposal["objective"]),
            "expected_advantage": 0.0,
            "notes": "Initial-squad selection has no pre-existing squad baseline.",
        },
        "validation": deepcopy(proposal["validation"]),
        "data_quality": "degraded" if coverage["degraded"] else "complete",
        "degraded": bool(coverage["degraded"]),
        "approval": {
            "status": "deferred",
            "notes": "Advisory-only rehearsal; no automatic account entry is permitted.",
        },
        "execution": {"mode": "manual", "notes": "No browser or account writes loaded."},
        "provenance": {
            "input_manifest_sha256": verified["manifest"]["content_sha256"],
            "recommendation_sha256": recommendation["content_sha256"],
            "checkpoint_sha256": checkpoint["content_sha256"],
            "coverage_sha256": coverage["content_sha256"],
        },
        "account_writes": False,
        "browser_actions": False,
    }
    decision["content_sha256"] = artifact_hash(decision)
    return decision


def _runtime_metadata() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
    }


def _report_markdown(report: Mapping[str, Any]) -> str:
    coverage = report["coverage"]
    lines = [
        f"# GW1 live-readiness rehearsal — {report['checkpoint_id']}",
        "",
        f"- Operational result: `{report['operational_status']}`",
        f"- Approval status: `{report['approval_status']}`",
        f"- T-48h target: `{report['target_at']}`",
        f"- Optional degraded families: {', '.join(coverage['optional_gaps']) or 'none'}",
        f"- Manifest: `{report['bindings']['input_manifest_sha256']}`",
        f"- Recommendation: `{report['bindings']['recommendation_sha256']}`",
        "",
        "This is an advisory-only rehearsal. It neither invokes nor authorises FPL account writes.",
        "",
    ]
    return "\n".join(lines)


def _stage_root(
    *, output_root: Path, checkpoint_id: str, manifest_sha256: str, policy_sha256: str
) -> Path:
    return (
        output_root
        / ".staging"
        / f"{checkpoint_id}-{manifest_sha256[:16]}-{policy_sha256[:16]}"
    )


def run_live_readiness_rehearsal(
    *,
    manifest_path: Path,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    policy_path: Path = DEFAULT_POLICY_PATH,
    checkpoint: str = _T48,
    maximum_lag_minutes: int = 15,
    maximum_total_seconds: float = 30 * 60,
    maximum_checkpoint_seconds: float = 10 * 60,
) -> dict[str, Any]:
    """Run one T-48h rehearsal and freeze its advisory-only decision record."""

    if maximum_total_seconds <= 0 or maximum_checkpoint_seconds <= 0:
        raise LiveReadinessRehearsalError("Rehearsal time budgets must be positive")
    total_started = perf_counter()
    try:
        verified = verify_preseason_manifest(manifest_path)
    except InitialSquadCheckpointError as exc:
        raise LiveReadinessRehearsalError(str(exc)) from exc
    target_at = _validate_t48_capture(
        verified, checkpoint=checkpoint, maximum_lag_minutes=maximum_lag_minutes
    )
    coverage = _coverage(verified)
    if coverage["mandatory_gaps"]:
        raise LiveReadinessRehearsalError("Mandatory source family is unavailable")

    output_root = output_root.resolve()
    policy_path = policy_path.resolve()
    checkpoint_id = str(verified["checkpoint_id"])
    run_dir = output_root / checkpoint_id
    policy_sha256 = _policy_sha256(policy_path)
    request = {
        "schema_version": _REHEARSAL_SCHEMA_VERSION,
        "checkpoint": checkpoint,
        "checkpoint_id": checkpoint_id,
        "input_manifest_sha256": verified["manifest"]["content_sha256"],
        "policy_sha256": policy_sha256,
        "target_at": target_at,
        "maximum_lag_minutes": maximum_lag_minutes,
        "maximum_total_seconds": maximum_total_seconds,
        "maximum_checkpoint_seconds": maximum_checkpoint_seconds,
        "account_writes": False,
    }
    request["content_sha256"] = artifact_hash(request)

    with _exclusive_lock(output_root / ".live-readiness.lock"):
        existing_report = run_dir / "rehearsal-report.json"
        if existing_report.exists():
            try:
                report = json.loads(existing_report.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise LiveReadinessRehearsalError(
                    f"Cannot read existing rehearsal report: {existing_report}"
                ) from exc
            if report.get("request_sha256") != request["content_sha256"]:
                raise LiveReadinessRehearsalConflict(
                    "Refusing to overwrite an existing rehearsal with a different request"
                )
            expected = report.get("output_file_hashes")
            actual = _sealed_artifact_hashes(run_dir)
            if expected != actual:
                raise LiveReadinessRehearsalConflict(
                    "Existing rehearsal output does not match its frozen file hashes"
                )
            if report.get("content_sha256") != artifact_hash(report):
                raise LiveReadinessRehearsalConflict(
                    "Existing rehearsal report content hash mismatch"
                )
            return deepcopy(dict(report))

        stage_root = _stage_root(
            output_root=output_root,
            checkpoint_id=checkpoint_id,
            manifest_sha256=verified["manifest"]["content_sha256"],
            policy_sha256=policy_sha256,
        )
        stage_started = perf_counter()
        try:
            staged_checkpoint = run_initial_squad_checkpoint(
                manifest_path=manifest_path,
                output_root=stage_root,
                policy_path=policy_path,
            )
        except (InitialSquadCheckpointError, InitialSquadCheckpointConflict) as exc:
            raise LiveReadinessRehearsalError(str(exc)) from exc
        checkpoint_seconds = perf_counter() - stage_started
        total_seconds = perf_counter() - total_started
        if checkpoint_seconds > maximum_checkpoint_seconds:
            raise LiveReadinessRehearsalError(
                "Deterministic checkpoint stage exceeded the rehearsal time budget"
            )
        if total_seconds > maximum_total_seconds:
            raise LiveReadinessRehearsalError(
                "Total rehearsal exceeded the wall-time budget"
            )

        staged_dir = stage_root / checkpoint_id
        recommendation_path = staged_dir / "recommendation.json"
        checkpoint_path = staged_dir / "checkpoint.json"
        try:
            packet_value = json.loads((staged_dir / "input-packet.json").read_text(encoding="utf-8"))
            recommendation = json.loads(recommendation_path.read_text(encoding="utf-8"))
            checkpoint_value = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise LiveReadinessRehearsalError(
                "Staged initial-squad output cannot be read"
            ) from exc
        if staged_checkpoint.get("content_sha256") != checkpoint_value.get("content_sha256"):
            raise LiveReadinessRehearsalError("Staged checkpoint binding mismatch")
        decision = _decision_record(
            verified=verified,
            recommendation=recommendation,
            checkpoint=checkpoint_value,
            coverage=coverage,
        )
        _write_json(run_dir / "request.json", request)
        _copy_immutable(manifest_path.resolve(), run_dir / "input-manifest.json")
        _write_json(run_dir / "source-coverage.json", coverage)
        for name in (
            "input-packet.json",
            "recommendation.json",
            "diff.json",
            "checkpoint.json",
        ):
            _copy_immutable(staged_dir / name, run_dir / name)
        _copy_immutable(staged_dir / "diff.md", run_dir / "diff.md")
        _write_json(run_dir / "gameweek-decision-record.json", decision)
        output_hashes = _sealed_artifact_hashes(run_dir)
        report: dict[str, Any] = {
            "schema_version": _REHEARSAL_SCHEMA_VERSION,
            "checkpoint": checkpoint,
            "checkpoint_id": checkpoint_id,
            "target_at": target_at,
            "request_sha256": request["content_sha256"],
            "operational_status": "go_degraded" if coverage["degraded"] else "go",
            "approval_status": recommendation["selection"]["approval_gate"]["status"],
            "approval_blockers": list(
                recommendation["selection"]["approval_gate"].get("blockers", [])
            ),
            "coverage": coverage,
            "timings": {
                "checkpoint_seconds": round(checkpoint_seconds, 6),
                "total_seconds": round(total_seconds, 6),
                "checkpoint_budget_seconds": maximum_checkpoint_seconds,
                "total_budget_seconds": maximum_total_seconds,
                "within_budget": True,
            },
            "peak_memory_bytes": None,
            "peak_memory_note": "Not instrumented for this process rehearsal; performance profiling is deliberately deferred.",
            "runtime": _runtime_metadata(),
            "bindings": {
                "input_manifest_sha256": verified["manifest"]["content_sha256"],
                "input_packet_sha256": packet_value["content_sha256"],
                "recommendation_sha256": recommendation["content_sha256"],
                "checkpoint_sha256": checkpoint_value["content_sha256"],
                "decision_record_sha256": decision["content_sha256"],
                "source_coverage_sha256": coverage["content_sha256"],
            },
            "account_writes": False,
            "browser_actions": False,
            "output_file_hashes": output_hashes,
        }
        report["content_sha256"] = artifact_hash(report)
        _write_json(run_dir / "rehearsal-report.json", report)
        _write_immutable_text(run_dir / "rehearsal-report.md", _report_markdown(report))
        final_hashes = _rerun_artifact_hashes(run_dir)
        comparison: dict[str, Any] = {
            "schema_version": _REHEARSAL_SCHEMA_VERSION,
            "checkpoint_id": checkpoint_id,
            "request_sha256": request["content_sha256"],
            "status": "identical",
            "file_hashes": final_hashes,
        }
        comparison["content_sha256"] = artifact_hash(comparison)
        _write_json(run_dir / "rerun-comparison.json", comparison)
        return deepcopy(report)


def compare_final_checkpoint(
    *,
    rehearsal_root: Path,
    rehearsal_checkpoint_id: str,
    final_checkpoint_path: Path,
) -> dict[str, Any]:
    """Write an additive comparison without changing frozen T-48h artifacts."""

    rehearsal_dir = rehearsal_root.resolve() / rehearsal_checkpoint_id
    report_path = rehearsal_dir / "rehearsal-report.json"
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        final = json.loads(final_checkpoint_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LiveReadinessRehearsalError("Cannot read rehearsal or final checkpoint") from exc
    if report.get("content_sha256") != artifact_hash(report):
        raise LiveReadinessRehearsalError("Rehearsal report content hash mismatch")
    if final.get("content_sha256") != artifact_hash(final):
        raise LiveReadinessRehearsalError("Final checkpoint content hash mismatch")
    comparison: dict[str, Any] = {
        "schema_version": _REHEARSAL_SCHEMA_VERSION,
        "rehearsal_checkpoint_id": rehearsal_checkpoint_id,
        "rehearsal_report_sha256": report["content_sha256"],
        "final_checkpoint_id": final.get("checkpoint_id"),
        "final_checkpoint_sha256": final["content_sha256"],
        "same_recommendation": (
            report["bindings"]["recommendation_sha256"]
            == final.get("recommendation_sha256")
        ),
        "comparison_kind": "additive_final_checkpoint_comparison",
    }
    comparison["content_sha256"] = artifact_hash(comparison)
    digest = comparison["content_sha256"][:16]
    output_path = (
        rehearsal_root.resolve()
        / "final-comparisons"
        / f"{rehearsal_checkpoint_id}-{digest}.json"
    )
    _write_json(output_path, comparison)
    return comparison
