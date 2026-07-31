"""Immutable 2026/27 preseason and launch snapshot capture.

Builds on the evidence-checkpoint immutability contract: create-only writes,
content-addressed manifests, identical restarts return existing bytes, and
differing payloads at the same path fail closed. This module captures data
only; it does not optimise a squad or write to an FPL account.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from src.forecasting.launch_context import LaunchContextError, load_launch_context

from src.ingestion.acquisition import content_hash, record_acquisition
from src.ingestion.registry import assert_collectable, load_registry
from src.ingestion.set_piece_roles import (
    SetPieceRoleError,
    build_set_piece_feature_payload,
    build_set_piece_role_ledger,
    normalise_official_set_piece_snapshot,
)
from src.orchestration.evidence_checkpoint_runner import (
    EvidenceCheckpointConflict,
    _exclusive_lock,
    _write_immutable_json as _ecr_write_immutable_json,
    _write_mutable_json,
    derive_deadline_checkpoints,
)
from src.scoring.rules_loader import ruleset_sha256

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "data_sources" / "2026-27-preseason.json"
DEFAULT_RULES_PATH = REPO_ROOT / "control" / "rules" / "2026-27.yaml"
DEFAULT_MANIFEST_PATH = REPO_ROOT / "control" / "manifests" / "2026-27-preseason.json"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "data" / "snapshots" / "2026-27" / "preseason"
DEFAULT_LAUNCH_CONTEXT_PATH = REPO_ROOT / "control" / "identities" / "2026-27-launch-context.json"
DEFAULT_WORLD_CUP_PRIORS_PATH = REPO_ROOT / "control" / "identities" / "world-cup-2026-priors.csv"

_WEEKLY = re.compile(r"^weekly-(\d{4}-\d{2}-\d{2})$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
DEADLINE_RELATIVE_IDS = ("T-48h", "T-24h", "T-8h", "T-2h", "final")
MANDATORY_FAMILIES = ("official_bootstrap", "official_fixtures", "ruleset")
OPTIONAL_FAMILIES = (
    "availability_role_evidence",
    "transfers_and_signings",
    "set_pieces",
    "promoted_team_priors",
    "world_cup_return_fatigue",
    "licensed_odds",
    "player_ratings",
    "launch_context",
)

# Maximum time before the nominal checkpoint slot that an observation is accepted.
# The upper bound (must be before the next slot) is the primary enforcement gate.
CHECKPOINT_WINDOW_TOLERANCE = timedelta(hours=12)

# Ordered sequence of deadline-relative checkpoint IDs.
_CHECKPOINT_ORDER = ["T-48h", "T-24h", "T-8h", "T-2h", "final"]


class PreseasonSnapshotError(ValueError):
    """Raised when a preseason checkpoint cannot be admitted safely."""


class PreseasonSnapshotConflict(PreseasonSnapshotError):
    """Raised when an immutable path already holds different bytes."""


def artifact_hash(value: Mapping[str, Any]) -> str:
    """Hash every field except the self-referential content digest."""

    payload = {key: deepcopy(item) for key, item in value.items() if key != "content_sha256"}
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    if not isinstance(value, str) or not value:
        raise PreseasonSnapshotError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PreseasonSnapshotError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise PreseasonSnapshotError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _write_immutable_json(path: Path, value: Mapping[str, Any]) -> None:
    """Delegate to evidence_checkpoint_runner's atomic immutable writer."""
    try:
        _ecr_write_immutable_json(path, value)
    except EvidenceCheckpointConflict as exc:
        raise PreseasonSnapshotConflict(str(exc)) from exc


def _git_commit(code_commit: str | None = None) -> str:
    if code_commit is not None:
        if not re.fullmatch(r"[0-9a-f]{40}", code_commit):
            raise PreseasonSnapshotError("code_commit must be a full 40-character Git SHA")
        return code_commit
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    commit = result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise PreseasonSnapshotError("Unable to resolve a full Git SHA for code_commit")
    return commit


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PreseasonSnapshotError(f"Unable to read {label}: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PreseasonSnapshotError(f"{label} must be a JSON object")
    return payload


def load_preseason_config(path: Path | None = None) -> dict[str, Any]:
    config = _load_json_object(path or DEFAULT_CONFIG_PATH, "preseason config")
    if config.get("schema_version") != "1.0":
        raise PreseasonSnapshotError("Unsupported preseason config schema")
    if config.get("season") != "2026-27":
        raise PreseasonSnapshotError("preseason config season must be 2026-27")
    return config


def validate_checkpoint_id(checkpoint_id: str, *, deadline: str) -> str:
    """Accept launch, weekly-YYYY-MM-DD, and deadline-relative IDs only.

    This function validates the checkpoint ID format and deadline parsing only.
    Schedule-window enforcement (observed_at within the correct slot window)
    is performed separately by enforce_checkpoint_window once bootstrap data
    is available.
    """

    if not isinstance(checkpoint_id, str) or not checkpoint_id:
        raise PreseasonSnapshotError("checkpoint_id must be a non-empty string")
    deadline_text, deadline_at = _timestamp(deadline, "deadline")
    if checkpoint_id == "launch":
        return checkpoint_id
    weekly = _WEEKLY.fullmatch(checkpoint_id)
    if weekly:
        try:
            datetime.strptime(weekly.group(1), "%Y-%m-%d")
        except ValueError as exc:
            raise PreseasonSnapshotError(
                "weekly checkpoint_id must use a real calendar date"
            ) from exc
        return checkpoint_id
    if checkpoint_id in DEADLINE_RELATIVE_IDS:
        _ = deadline_text, deadline_at
        return checkpoint_id
    raise PreseasonSnapshotError(
        "checkpoint_id must be launch, weekly-YYYY-MM-DD, "
        "T-48h, T-24h, T-8h, T-2h, or final"
    )


def enforce_checkpoint_window(
    checkpoint_id: str,
    observed_at_utc: datetime,
    schedule: dict[str, str],
    deadline_utc: datetime,
) -> None:
    """Raise PreseasonSnapshotError if observed_at falls outside the valid window.

    For deadline-relative IDs the window is:
      lower: nominal_slot - CHECKPOINT_WINDOW_TOLERANCE
      upper: next_slot (or deadline for 'final') — exclusive

    A capture labelled T-48h must have been observed before the T-24h window
    opens; it cannot be backdated from a T-2h observation.

    For weekly-YYYY-MM-DD the observation date (UTC) must equal the label date.
    """

    weekly = _WEEKLY.fullmatch(checkpoint_id)
    if weekly:
        label_date = datetime.strptime(weekly.group(1), "%Y-%m-%d").date()
        obs_date = observed_at_utc.date()
        if obs_date != label_date:
            raise PreseasonSnapshotError(
                f"weekly checkpoint_id={checkpoint_id!r}: label date {label_date} "
                f"does not match observation date {obs_date} (UTC); "
                "capture on the labelled date or use the correct date label"
            )
        return

    if checkpoint_id not in DEADLINE_RELATIVE_IDS:
        return

    idx = _CHECKPOINT_ORDER.index(checkpoint_id)
    nominal_times = [
        _timestamp(schedule[item], f"schedule.{item}")[1]
        for item in _CHECKPOINT_ORDER
    ]
    nominal = nominal_times[idx]
    if idx == 0:
        lower = nominal - CHECKPOINT_WINDOW_TOLERANCE
    else:
        previous = nominal_times[idx - 1]
        lower = previous + (nominal - previous) / 2
    if idx == len(_CHECKPOINT_ORDER) - 1:
        upper = deadline_utc
    else:
        following = nominal_times[idx + 1]
        upper = nominal + (following - nominal) / 2

    if observed_at_utc < lower or observed_at_utc >= upper:
        raise PreseasonSnapshotError(
            f"checkpoint_id={checkpoint_id!r}: observed_at "
            f"{observed_at_utc.isoformat()} is outside the assigned window "
            f"[{lower.isoformat()}, {upper.isoformat()}); a missed checkpoint "
            "cannot be backfilled under an earlier label"
        )

def expected_deadline_schedule(bootstrap: Mapping[str, Any], *, gameweek: int = 1) -> dict[str, str]:
    """Map bead checkpoint IDs onto official deadline-relative timestamps."""

    raw = derive_deadline_checkpoints(bootstrap, gameweek=gameweek)
    return {
        "T-48h": raw["T-48h"],
        "T-24h": raw["T-24h"],
        "T-8h": raw["T-8h"],
        "T-2h": raw["T-2h"],
        "final": raw["final_pre_deadline"],
    }


def assert_deadline_matches_bootstrap(
    bootstrap: Mapping[str, Any],
    *,
    deadline: str,
    gameweek: int = 1,
) -> str:
    events = bootstrap.get("events")
    if not isinstance(events, list):
        raise PreseasonSnapshotError("bootstrap events must be a list")
    matches = [
        row for row in events if isinstance(row, Mapping) and row.get("id") == gameweek
    ]
    if len(matches) != 1:
        raise PreseasonSnapshotError(
            f"Expected exactly one official event for gameweek {gameweek}"
        )
    official_text, _ = _timestamp(matches[0].get("deadline_time"), "deadline_time")
    requested_text, _ = _timestamp(deadline, "deadline")
    if official_text != requested_text:
        raise PreseasonSnapshotError(
            "deadline must equal the official Gameweek 1 deadline_time "
            f"({official_text})"
        )
    return official_text


def admit_temporal_records(
    records: Sequence[Mapping[str, Any]],
    *,
    deadline: str,
) -> dict[str, Any]:
    """Admit only records with available_at strictly before the deadline."""

    deadline_text, deadline_at = _timestamp(deadline, "deadline")
    admitted: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            quarantined.append(
                {
                    "index": index,
                    "reason": "record_must_be_object",
                    "record": None,
                }
            )
            continue
        available_raw = record.get("available_at")
        if available_raw is None:
            quarantined.append(
                {
                    "index": index,
                    "reason": "missing_available_at",
                    "record": deepcopy(dict(record)),
                }
            )
            continue
        try:
            available_text, available_at = _timestamp(available_raw, "available_at")
        except PreseasonSnapshotError:
            quarantined.append(
                {
                    "index": index,
                    "reason": "invalid_available_at",
                    "record": deepcopy(dict(record)),
                }
            )
            continue
        if available_at >= deadline_at:
            quarantined.append(
                {
                    "index": index,
                    "reason": "available_at_at_or_after_deadline",
                    "available_at": available_text,
                    "deadline": deadline_text,
                    "record": deepcopy(dict(record)),
                }
            )
            continue
        admitted.append(deepcopy(dict(record)))
    return {
        "deadline": deadline_text,
        "input_count": len(records),
        "admitted_count": len(admitted),
        "quarantined_count": len(quarantined),
        "admitted": admitted,
        "quarantined": quarantined,
    }


def _empty_family_counts() -> dict[str, int]:
    return {
        "input": 0,
        "admitted": 0,
        "duplicate": 0,
        "quarantined": 0,
        "missing": 0,
    }


def _family_status(
    *,
    family_id: str,
    mandatory: bool,
    status: str,
    counts: Mapping[str, int],
    artifact_path: str | None = None,
    artifact_sha256: str | None = None,
    sidecar_path: str | None = None,
    sidecar_sha256: str | None = None,
    observed_at: str | None = None,
    available_at: str | None = None,
    reasons: Sequence[str] | None = None,
    source_id: str | None = None,
    registry_source_status: str | None = None,
) -> dict[str, Any]:
    return {
        "family_id": family_id,
        "mandatory": mandatory,
        "status": status,
        "source_id": source_id,
        "registry_source_status": registry_source_status,
        "observed_at": observed_at,
        "available_at": available_at,
        "counts": dict(counts),
        "artifact_path": artifact_path,
        "artifact_sha256": artifact_sha256,
        "sidecar_path": sidecar_path,
        "sidecar_sha256": sidecar_sha256,
        "reasons": list(reasons or []),
    }


def _validate_source_id(source_id: str | None, registry: dict[str, Any]) -> str:
    """Return the authoritative registry admission state for a source."""

    if not source_id:
        return "missing_source_id"
    registered = {
        str(row.get("source_id", "")): row
        for row in registry.get("sources", [])
        if isinstance(row, Mapping)
    }
    source = registered.get(source_id)
    if source is None:
        return "unregistered"
    if not source.get("enabled"):
        return "disabled"
    licence_status = source.get("licence_status")
    if licence_status == "prohibited":
        return "prohibited"
    if licence_status in {None, "", "unknown"}:
        return "licence_unresolved"
    allowed_use = source.get("allowed_use")
    if not isinstance(allowed_use, str) or not allowed_use.strip() or allowed_use in {
        "unknown",
        "prohibited",
    }:
        return "allowed_use_unresolved"
    try:
        assert_collectable(source_id)
    except KeyError:
        return "unregistered"
    except PermissionError as exc:
        message = str(exc).lower()
        if "disabled" in message:
            return "disabled"
        if "licence" in message:
            return "licence_unresolved"
        if "allowed_use" in message:
            return "allowed_use_unresolved"
        return "not_collectable"
    except ValueError:
        return "invalid_registry_entry"
    return "ok"


def _copy_optional_bytes(
    body: bytes,
    *,
    family_id: str,
    digest: str,
    checkpoint_dir: Path,
    extension: str = "bin",
    suffix: str = "artifact",
) -> str:
    """Content-addressably copy optional bytes inside the checkpoint lock."""

    safe_family = re.sub(r"[^A-Za-z0-9_-]", "-", family_id)
    safe_extension = re.sub(r"[^A-Za-z0-9]", "", extension.lower()) or "bin"
    safe_suffix = re.sub(r"[^A-Za-z0-9_-]", "-", suffix)
    filename = f"{safe_family}-{safe_suffix}-{digest}.{safe_extension}"
    dest = checkpoint_dir / "raw" / "optional" / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        dest.write_bytes(body)
    elif dest.read_bytes() != body:
        raise PreseasonSnapshotConflict(
            f"Content-addressed optional artifact already exists with different bytes: {dest}"
        )
    return (Path("raw") / "optional" / filename).as_posix()


def _bind_optional_artifact(
    *,
    family_id: str,
    path: Path | None,
    deadline: str,
    source_id: str | None,
    missing_reason: str,
    checkpoint_dir: Path,
    sidecar_path: Path | None = None,
    registry: dict[str, Any],
    capture_observed_at: str | None = None,
) -> dict[str, Any]:
    """Validate, temporally admit, and immutably bind one optional artifact."""

    counts = _empty_family_counts()
    reg_status = _validate_source_id(source_id, registry)

    if path is None:
        counts["missing"] = 1
        return _family_status(
            family_id=family_id,
            mandatory=False,
            status="degraded",
            counts=counts,
            reasons=[missing_reason],
            source_id=source_id,
            registry_source_status=reg_status,
        )
    if not path.exists():
        counts["missing"] = 1
        return _family_status(
            family_id=family_id,
            mandatory=False,
            status="degraded",
            counts=counts,
            reasons=[f"optional_artifact_missing:{path.as_posix()}"],
            source_id=source_id,
            registry_source_status=reg_status,
        )
    if reg_status != "ok":
        counts["input"] = 1
        counts["quarantined"] = 1
        return _family_status(
            family_id=family_id,
            mandatory=False,
            status="degraded",
            counts=counts,
            reasons=[f"source_not_collectable:{reg_status}"],
            source_id=source_id,
            registry_source_status=reg_status,
        )

    body = path.read_bytes()
    digest = content_hash(body)
    counts["input"] = 1
    extension = path.suffix.lstrip(".") or "bin"
    artifact_relative = _copy_optional_bytes(
        body,
        family_id=family_id,
        digest=digest,
        checkpoint_dir=checkpoint_dir,
        extension=extension,
    )

    sidecar: dict[str, Any] | None = None
    sidecar_relative: str | None = None
    sidecar_digest: str | None = None
    sidecar_observed_at: str | None = None
    sidecar_available_at: str | None = None
    sidecar_reason: str | None = None
    if sidecar_path is not None:
        if not sidecar_path.exists():
            sidecar_reason = f"sidecar_missing:{sidecar_path.as_posix()}"
        else:
            sidecar_body = sidecar_path.read_bytes()
            sidecar_digest = content_hash(sidecar_body)
            sidecar_relative = _copy_optional_bytes(
                sidecar_body,
                family_id=family_id,
                digest=sidecar_digest,
                checkpoint_dir=checkpoint_dir,
                extension="json",
                suffix="sidecar",
            )
            try:
                parsed_sidecar = json.loads(sidecar_body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                sidecar_reason = "sidecar_not_valid_json"
            else:
                if not isinstance(parsed_sidecar, dict):
                    sidecar_reason = "sidecar_must_be_object"
                else:
                    sidecar = parsed_sidecar
                    missing_fields = [
                        field
                        for field in ("source_id", "observed_at", "available_at")
                        if not sidecar.get(field)
                    ]
                    if missing_fields:
                        sidecar_reason = "sidecar_missing_fields:" + ",".join(missing_fields)
                    elif sidecar.get("source_id") != source_id:
                        sidecar_reason = "sidecar_source_id_mismatch"
                    else:
                        try:
                            sidecar_observed_at, observed_dt = _timestamp(
                                sidecar["observed_at"], "sidecar.observed_at"
                            )
                            sidecar_available_at, available_dt = _timestamp(
                                sidecar["available_at"], "sidecar.available_at"
                            )
                        except PreseasonSnapshotError:
                            sidecar_reason = "sidecar_invalid_timestamp"
                        else:
                            capture_dt = (
                                _timestamp(capture_observed_at, "capture_observed_at")[1]
                                if capture_observed_at is not None
                                else None
                            )
                            if observed_dt < available_dt:
                                sidecar_reason = "sidecar_observed_before_available"
                            elif capture_dt is not None and observed_dt > capture_dt:
                                sidecar_reason = "sidecar_observed_after_capture"
                            else:
                                sidecar_admission = admit_temporal_records(
                                    [{"available_at": sidecar_available_at}],
                                    deadline=deadline,
                                )
                                if sidecar_admission["admitted_count"] != 1:
                                    sidecar_reason = sidecar_admission["quarantined"][0][
                                        "reason"
                                    ]

    def bound_status(
        *,
        status: str,
        reasons: Sequence[str] | None = None,
        available_at: str | None = None,
    ) -> dict[str, Any]:
        return _family_status(
            family_id=family_id,
            mandatory=False,
            status=status,
            counts=counts,
            artifact_path=artifact_relative,
            artifact_sha256=digest,
            sidecar_path=sidecar_relative,
            sidecar_sha256=sidecar_digest,
            observed_at=sidecar_observed_at or capture_observed_at,
            available_at=sidecar_available_at or available_at,
            reasons=reasons,
            source_id=source_id,
            registry_source_status=reg_status,
        )

    if sidecar_reason is not None:
        counts["quarantined"] = 1
        return bound_status(status="degraded", reasons=[sidecar_reason])

    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        if sidecar is None:
            counts["quarantined"] = 1
            return bound_status(
                status="degraded", reasons=["missing_temporal_sidecar_for_binary"]
            )
        counts["admitted"] = 1
        return bound_status(status="admitted")

    records: list[Any]
    extra_quarantined: list[dict[str, Any]] = []
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        records = []
        for index, row in enumerate(payload["records"]):
            if isinstance(row, Mapping):
                records.append(row)
            else:
                extra_quarantined.append(
                    {"index": index, "reason": "record_must_be_object", "record": None}
                )
    elif isinstance(payload, dict) and "available_at" in payload:
        records = [payload]
    elif isinstance(payload, dict) and sidecar is not None:
        records = [{"available_at": sidecar_available_at}]
    elif isinstance(payload, dict):
        counts["quarantined"] = 1
        return bound_status(
            status="degraded", reasons=["missing_temporal_envelope"]
        )
    else:
        counts["quarantined"] = 1
        return bound_status(
            status="degraded", reasons=["payload_must_be_json_object"]
        )

    admission = admit_temporal_records(records, deadline=deadline)
    extra_count = len(extra_quarantined)
    counts["input"] = admission["input_count"] + extra_count
    counts["admitted"] = admission["admitted_count"]
    counts["quarantined"] = admission["quarantined_count"] + extra_count
    reasons = sorted(
        {
            row["reason"]
            for row in admission["quarantined"] + extra_quarantined
        }
    )
    if admission["admitted_count"] == 0:
        counts["missing"] = 1 if counts["input"] == 0 else 0
        return bound_status(
            status="degraded", reasons=reasons or [missing_reason]
        )

    admitted_available = [
        _timestamp(row["available_at"], "available_at")[0]
        for row in admission["admitted"]
        if row.get("available_at") is not None
    ]
    latest_available = max(admitted_available) if admitted_available else None
    status = "admitted" if counts["quarantined"] == 0 else "degraded"
    return bound_status(
        status=status,
        reasons=reasons,
        available_at=latest_available,
    )


def _bind_derived_set_piece_artifact(
    *,
    bootstrap: Mapping[str, Any],
    source_sha256: str,
    observed_at: str,
    deadline: str,
    checkpoint_dir: Path,
    source_id: str | None,
    registry: dict[str, Any],
) -> dict[str, Any]:
    """Derive and bind the official set-piece ledger from admitted bootstrap bytes."""

    counts = _empty_family_counts()
    reg_status = _validate_source_id(source_id, registry)
    if reg_status != "ok":
        counts["input"] = 1
        counts["quarantined"] = 1
        return _family_status(
            family_id="set_pieces",
            mandatory=False,
            status="degraded",
            counts=counts,
            reasons=[f"source_not_collectable:{reg_status}"],
            source_id=source_id,
            registry_source_status=reg_status,
        )

    try:
        snapshot = normalise_official_set_piece_snapshot(
            bootstrap,
            source_sha256=source_sha256,
            observed_at=observed_at,
            available_at=observed_at,
        )
        ledger = build_set_piece_role_ledger([snapshot], as_of=observed_at)
        feature = build_set_piece_feature_payload(ledger)
        artifact = _seal(
            {
                "schema_version": "preseason-set-piece-bind-v1",
                "family": "set_pieces",
                "source_id": source_id,
                "source_sha256": source_sha256,
                "observed_at": observed_at,
                "available_at": observed_at,
                "snapshot": snapshot,
                "ledger": ledger,
                "feature": feature,
                "promotion_status": "shadow_only_pending_point_in_time_ablation",
                "effect_weights": None,
            }
        )
    except (SetPieceRoleError, TypeError, ValueError) as exc:
        counts["input"] = 1
        counts["quarantined"] = 1
        return _family_status(
            family_id="set_pieces",
            mandatory=False,
            status="degraded",
            counts=counts,
            reasons=[f"derived_set_piece_ledger_failed:{exc}"],
            source_id=source_id,
            registry_source_status=reg_status,
        )

    body = (json.dumps(artifact, indent=2, sort_keys=True) + "\n").encode("utf-8")
    digest = content_hash(body)
    artifact_relative = _copy_optional_bytes(
        body,
        family_id="set_pieces",
        digest=digest,
        checkpoint_dir=checkpoint_dir,
        extension="json",
        suffix="derived-ledger",
    )
    counts["input"] = 1
    counts["admitted"] = 1
    return _family_status(
        family_id="set_pieces",
        mandatory=False,
        status="admitted",
        counts=counts,
        artifact_path=artifact_relative,
        artifact_sha256=digest,
        observed_at=observed_at,
        available_at=observed_at,
        source_id=source_id,
        registry_source_status=reg_status,
    )


def _launch_context_input_digests(
    context_path: Path | None, world_cup_priors_path: Path | None
) -> dict[str, str | None]:
    """Bind reviewed launch-context inputs into an immutable checkpoint request."""

    return {
        "context_sha256": (
            content_hash(context_path.read_bytes())
            if context_path is not None and context_path.is_file()
            else None
        ),
        "world_cup_priors_sha256": (
            content_hash(world_cup_priors_path.read_bytes())
            if world_cup_priors_path is not None and world_cup_priors_path.is_file()
            else None
        ),
    }


def _bind_launch_context(
    *,
    context_path: Path | None,
    world_cup_priors_path: Path | None,
    bootstrap_sha256: str,
    checkpoint_dir: Path,
    checkpoint_observed_at: str,
    deadline: str,
    source_id: str | None,
) -> dict[str, Any]:
    """Bind a reviewed context only to its exact official player universe.

    This is intentionally separate from generic optional ingestion: it verifies a
    semantic JSON self-hash and preserves a second reviewed CSV input.
    """

    counts = _empty_family_counts()
    derived_status = "derived_hash_bound"

    def degraded(reason: str) -> dict[str, Any]:
        counts["quarantined"] = max(counts["quarantined"], 1)
        return _family_status(
            family_id="launch_context",
            mandatory=False,
            status="degraded",
            counts=counts,
            reasons=[reason],
            source_id=source_id,
            registry_source_status=derived_status,
        )

    if context_path is None or not context_path.is_file():
        counts["missing"] = 1
        return _family_status(
            family_id="launch_context",
            mandatory=False,
            status="degraded",
            counts=counts,
            reasons=["launch_context_not_supplied"],
            source_id=source_id,
            registry_source_status=derived_status,
        )
    if world_cup_priors_path is None or not world_cup_priors_path.is_file():
        counts["missing"] = 1
        return _family_status(
            family_id="launch_context",
            mandatory=False,
            status="degraded",
            counts=counts,
            reasons=["launch_context_world_cup_priors_missing"],
            source_id=source_id,
            registry_source_status=derived_status,
        )

    context_body = context_path.read_bytes()
    world_cup_body = world_cup_priors_path.read_bytes()
    context_digest = content_hash(context_body)
    world_cup_digest = content_hash(world_cup_body)
    counts["input"] = 3
    try:
        context = load_launch_context(context_path)
    except (LaunchContextError, OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return degraded("launch_context_self_hash_invalid")
    if not isinstance(context, Mapping):
        return degraded("launch_context_must_be_object")
    if context.get("season") != "2026-27":
        return degraded("launch_context_season_invalid")
    bindings = context.get("source_bindings")
    if not isinstance(bindings, Mapping):
        return degraded("launch_context_source_bindings_invalid")
    official_binding = bindings.get("official_bootstrap")
    world_cup_binding = bindings.get("world_cup_priors")
    if not isinstance(official_binding, Mapping) or not isinstance(world_cup_binding, Mapping):
        return degraded("launch_context_source_bindings_invalid")
    bound_bootstrap = str(official_binding.get("sha256", ""))
    if not _SHA256.fullmatch(bound_bootstrap):
        return degraded("launch_context_official_bootstrap_hash_invalid")
    if bound_bootstrap != bootstrap_sha256:
        return degraded("official_bootstrap_hash_mismatch")
    if str(world_cup_binding.get("sha256", "")) != world_cup_digest:
        return degraded("world_cup_priors_hash_mismatch")
    try:
        context_observed, context_observed_at = _timestamp(
            context.get("observed_at"), "launch_context.observed_at"
        )
        binding_observed, binding_observed_at = _timestamp(
            official_binding.get("observed_at"),
            "launch_context.official_bootstrap.observed_at",
        )
        checkpoint_observed, checkpoint_at = _timestamp(
            checkpoint_observed_at, "checkpoint_observed_at"
        )
        _, deadline_at = _timestamp(deadline, "deadline")
    except PreseasonSnapshotError:
        return degraded("launch_context_temporal_metadata_invalid")
    if context_observed_at > checkpoint_at or binding_observed_at > checkpoint_at:
        return degraded("launch_context_observed_after_checkpoint")
    if context_observed_at >= deadline_at or binding_observed_at >= deadline_at:
        return degraded("launch_context_available_at_or_after_deadline")

    provenance = _seal(
        {
            "schema_version": "1.0",
            "source_id": source_id,
            "observed_at": checkpoint_observed,
            "available_at": context_observed,
            "context_content_sha256": str(context["content_sha256"]),
            "context_artifact_sha256": context_digest,
            "world_cup_priors_sha256": world_cup_digest,
            "bound_official_bootstrap_sha256": bound_bootstrap,
            "context_observed_at": context_observed,
            "official_bootstrap_observed_at": binding_observed,
        }
    )
    provenance_body = (json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode("utf-8")
    provenance_digest = content_hash(provenance_body)
    context_relative = _copy_optional_bytes(
        context_body,
        family_id="launch_context",
        digest=context_digest,
        checkpoint_dir=checkpoint_dir,
        extension="json",
        suffix="context",
    )
    world_cup_relative = _copy_optional_bytes(
        world_cup_body,
        family_id="launch_context",
        digest=world_cup_digest,
        checkpoint_dir=checkpoint_dir,
        extension="csv",
        suffix="world-cup-priors",
    )
    provenance_relative = _copy_optional_bytes(
        provenance_body,
        family_id="launch_context",
        digest=provenance_digest,
        checkpoint_dir=checkpoint_dir,
        extension="json",
        suffix="provenance",
    )
    counts["admitted"] = 3
    family = _family_status(
        family_id="launch_context",
        mandatory=False,
        status="admitted",
        counts=counts,
        artifact_path=context_relative,
        artifact_sha256=context_digest,
        sidecar_path=provenance_relative,
        sidecar_sha256=provenance_digest,
        observed_at=checkpoint_observed,
        available_at=context_observed,
        source_id=source_id,
        registry_source_status=derived_status,
    )
    family.update(
        {
            "context_content_sha256": str(context["content_sha256"]),
            "world_cup_priors_path": world_cup_relative,
            "world_cup_priors_sha256": world_cup_digest,
            "provenance_path": provenance_relative,
            "provenance_sha256": provenance_digest,
            "bound_official_bootstrap_sha256": bound_bootstrap,
        }
    )
    return family

def _decode_official_payload(family_id: str, body: bytes) -> Any:
    if not body:
        raise PreseasonSnapshotError(
            f"Mandatory family {family_id} returned an empty body"
        )
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise PreseasonSnapshotError(
            f"Mandatory family {family_id} must be JSON"
        ) from exc
    if family_id == "official_bootstrap" and not isinstance(payload, dict):
        raise PreseasonSnapshotError("official bootstrap must be a JSON object")
    if family_id == "official_fixtures" and not isinstance(payload, list):
        raise PreseasonSnapshotError("official fixtures must be a JSON array")
    return payload


def _persist_official_payload(
    *,
    family_id: str,
    body: bytes,
    payload: Any,
    checkpoint_dir: Path,
    artifact_name: str,
    observed_at: str,
    registry_version: str,
    origin: str,
) -> dict[str, Any]:
    acquisition = record_acquisition(
        source_id="fpl-official-endpoints",
        mode="fixture",
        origin=origin,
        body=body,
        out_dir=checkpoint_dir / "raw",
        artifact_name=artifact_name,
        status="success",
        registry_version=registry_version,
        observed_at=observed_at,
        http_status=200,
        request_url=origin,
    )
    counts = _empty_family_counts()
    counts["input"] = 1
    counts["admitted"] = 1
    relative = (
        Path("raw")
        / observed_at.replace(":", "").replace("-", "")
        / artifact_name
    ).as_posix()
    return {
        "payload": payload,
        "family": _family_status(
            family_id=family_id,
            mandatory=True,
            status="admitted",
            counts=counts,
            artifact_path=relative,
            artifact_sha256=str(acquisition["content_hash_sha256"]),
            observed_at=observed_at,
            available_at=observed_at,
            source_id="fpl-official-endpoints",
            registry_source_status="ok",
        ),
        "acquisition": acquisition,
    }

def _optional_source_ids_from_config(config: Mapping[str, Any]) -> dict[str, str | None]:
    """Read optional family source IDs from config rather than hardcoding them."""
    result: dict[str, str | None] = {fid: None for fid in OPTIONAL_FAMILIES}
    for entry in config.get("optional_families", []):
        fid = str(entry.get("family_id", ""))
        src = entry.get("source_id")
        if fid in result:
            result[fid] = str(src) if src else None
    return result


def _compute_optional_digests(
    optional_paths: Mapping[str, Path | None],
    sidecar_paths: Mapping[str, Path | None],
) -> dict[str, dict[str, str | None]]:
    """Hash every optional artifact and temporal sidecar before request sealing."""

    result: dict[str, dict[str, str | None]] = {}
    for family_id in OPTIONAL_FAMILIES:
        artifact_path = optional_paths.get(family_id)
        sidecar_path = sidecar_paths.get(family_id)
        result[family_id] = {
            "artifact_sha256": (
                content_hash(artifact_path.read_bytes())
                if artifact_path is not None and artifact_path.exists()
                else None
            ),
            "sidecar_sha256": (
                content_hash(sidecar_path.read_bytes())
                if sidecar_path is not None and sidecar_path.exists()
                else None
            ),
        }
    return result


def _verify_existing_bound_artifacts(
    manifest: Mapping[str, Any], checkpoint_dir: Path
) -> None:
    """Fail closed if any artifact bound by an existing manifest is missing or changed."""

    families = manifest.get("families")
    if not isinstance(families, Mapping):
        raise PreseasonSnapshotConflict("Existing manifest families must be an object")
    checkpoint_root = checkpoint_dir.resolve()
    for family_id, raw_family in families.items():
        if not isinstance(raw_family, Mapping):
            raise PreseasonSnapshotConflict(
                f"Existing family entry is invalid: {family_id}"
            )
        for path_key, digest_key in (
            ("artifact_path", "artifact_sha256"),
            ("sidecar_path", "sidecar_sha256"),
            ("world_cup_priors_path", "world_cup_priors_sha256"),
            ("provenance_path", "provenance_sha256"),
        ):
            path_text = raw_family.get(path_key)
            expected = raw_family.get(digest_key)
            if path_text is None and expected is None:
                continue
            if not isinstance(path_text, str) or not _SHA256.fullmatch(str(expected)):
                raise PreseasonSnapshotConflict(
                    f"Existing {family_id} {path_key}/{digest_key} binding is invalid"
                )
            candidate_path = Path(path_text)
            if candidate_path.is_absolute():
                candidate = candidate_path.resolve()
            else:
                candidate = (checkpoint_root / candidate_path).resolve()
                if candidate != checkpoint_root and checkpoint_root not in candidate.parents:
                    raise PreseasonSnapshotConflict(
                        f"Existing {family_id} artifact escapes checkpoint root"
                    )
            if not candidate.is_file():
                raise PreseasonSnapshotConflict(
                    f"Existing {family_id} artifact is missing: {candidate}"
                )
            if content_hash(candidate.read_bytes()) != expected:
                raise PreseasonSnapshotConflict(
                    f"Existing {family_id} artifact failed hash validation: {candidate}"
                )

def capture_preseason_snapshot(
    *,
    season: str,
    checkpoint_id: str,
    deadline: str,
    output_root: Path,
    observed_at: str | None = None,
    bootstrap_body: bytes | None = None,
    fixtures_body: bytes | None = None,
    bootstrap_fetcher: Callable[[], bytes] | None = None,
    fixtures_fetcher: Callable[[], bytes] | None = None,
    rules_path: Path | None = None,
    config_path: Path | None = None,
    index_manifest_path: Path | None = None,
    predecessor_checkpoint_hash: str | None = None,
    code_commit: str | None = None,
    optional_artifacts: Mapping[str, Path | None] | None = None,
    optional_sidecars: Mapping[str, Path | None] | None = None,
    launch_context_path: Path | None = DEFAULT_LAUNCH_CONTEXT_PATH,
    world_cup_priors_path: Path | None = DEFAULT_WORLD_CUP_PRIORS_PATH,
    update_index: bool = True,
) -> dict[str, Any]:
    """Capture one immutable preseason checkpoint and return its sealed manifest.

    The entire write sequence (manifest + index update) is protected by an
    exclusive file lock, reusing the single-writer contract from
    evidence_checkpoint_runner.  Optional artifacts are copied
    content-addressably into the checkpoint and their digests are included in
    the request hash so that a changed artifact at the same checkpoint is
    detected as a conflict.
    """

    if season != "2026-27":
        raise PreseasonSnapshotError("Only season 2026-27 is supported")
    config = load_preseason_config(config_path)
    deadline_text, deadline_utc = _timestamp(deadline, "deadline")
    validate_checkpoint_id(checkpoint_id, deadline=deadline_text)
    if observed_at is None:
        raise PreseasonSnapshotError("observed_at is required")
    observed_text, observed_utc = _timestamp(observed_at, "observed_at")
    if observed_utc >= deadline_utc:
        raise PreseasonSnapshotError(
            "observed_at must be strictly before the GW1 deadline"
        )

    registry = load_registry()
    registry_version = str(registry.get("registry_version", "unknown"))
    commit = _git_commit(code_commit)
    rules = rules_path or DEFAULT_RULES_PATH
    if not rules.exists():
        raise PreseasonSnapshotError(f"Mandatory ruleset is missing: {rules}")
    rules_hash = ruleset_sha256(rules)

    if predecessor_checkpoint_hash is not None and not _SHA256.fullmatch(
        predecessor_checkpoint_hash
    ):
        raise PreseasonSnapshotError(
            "predecessor_checkpoint_hash must be a lowercase SHA-256 digest"
        )

    checkpoint_dir = output_root / checkpoint_id
    manifest_path = checkpoint_dir / "manifest.json"

    optional_paths: dict[str, Path | None] = {fid: None for fid in OPTIONAL_FAMILIES}
    if optional_artifacts:
        for key, value in optional_artifacts.items():
            if key not in optional_paths:
                raise PreseasonSnapshotError(f"Unknown optional family: {key}")
            optional_paths[key] = value

    sidecars: dict[str, Path | None] = {fid: None for fid in OPTIONAL_FAMILIES}
    if optional_sidecars:
        for key, value in optional_sidecars.items():
            if key not in sidecars:
                raise PreseasonSnapshotError(f"Unknown optional family for sidecar: {key}")
            sidecars[key] = value

    # The launch context has two reviewed source artifacts and an internally
    # generated provenance envelope, so it cannot use the generic one-file
    # optional family contract.
    if optional_paths["launch_context"] is not None or sidecars["launch_context"] is not None:
        raise PreseasonSnapshotError(
            "launch_context must use launch_context_path and world_cup_priors_path"
        )

    # Compute optional artifact digests before request hash.
    optional_digests = _compute_optional_digests(optional_paths, sidecars)
    launch_context_digests = _launch_context_input_digests(
        launch_context_path, world_cup_priors_path
    )

    request = {
        "season": season,
        "checkpoint_id": checkpoint_id,
        "deadline": deadline_text,
        "output_root": output_root.as_posix(),
        "observed_at": observed_text,
        "predecessor_checkpoint_hash": predecessor_checkpoint_hash,
        "ruleset_sha256": rules_hash,
        "code_commit": commit,
        "config_sha256": content_hash(
            json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ),
        "optional_input_sha256": {k: v for k, v in sorted(optional_digests.items())},
        "launch_context_input_sha256": launch_context_digests,
    }
    request_sha256 = artifact_hash({"request": request})

    lock_path = output_root / ".preseason.lock"
    with _exclusive_lock(lock_path):
        if manifest_path.exists():
            existing = _load_json_object(manifest_path, "existing preseason manifest")
            if existing.get("content_sha256") != artifact_hash(existing):
                raise PreseasonSnapshotConflict(
                    f"Existing manifest failed hash validation: {manifest_path}"
                )
            if existing.get("request_sha256") != request_sha256:
                raise PreseasonSnapshotConflict(
                    f"Refusing to overwrite immutable preseason checkpoint: {manifest_path}"
                )
            _verify_existing_bound_artifacts(existing, checkpoint_dir)
            # Same logical request: verify supplied mandatory bytes still match.
            bootstrap_bytes = bootstrap_body
            if bootstrap_bytes is None and bootstrap_fetcher is not None:
                bootstrap_bytes = bootstrap_fetcher()
            fixtures_bytes = fixtures_body
            if fixtures_bytes is None and fixtures_fetcher is not None:
                fixtures_bytes = fixtures_fetcher()
            if bootstrap_bytes is not None:
                expected = existing["families"]["official_bootstrap"]["artifact_sha256"]
                if content_hash(bootstrap_bytes) != expected:
                    raise PreseasonSnapshotConflict(
                        "Refusing to overwrite immutable official bootstrap bytes"
                    )
            if fixtures_bytes is not None:
                expected = existing["families"]["official_fixtures"]["artifact_sha256"]
                if content_hash(fixtures_bytes) != expected:
                    raise PreseasonSnapshotConflict(
                        "Refusing to overwrite immutable official fixtures bytes"
                    )
            return existing

        bootstrap_bytes = bootstrap_body
        if bootstrap_bytes is None and bootstrap_fetcher is not None:
            bootstrap_bytes = bootstrap_fetcher()
        fixtures_bytes = fixtures_body
        if fixtures_bytes is None and fixtures_fetcher is not None:
            fixtures_bytes = fixtures_fetcher()
        if bootstrap_bytes is None or fixtures_bytes is None:
            raise PreseasonSnapshotError(
                "Mandatory official state is missing: bootstrap and fixtures are required"
            )

        # Parse and validate mandatory bytes and the checkpoint window before
        # creating any acquisition path beneath the checkpoint directory.
        bootstrap_payload = _decode_official_payload(
            "official_bootstrap", bootstrap_bytes
        )
        fixtures_payload = _decode_official_payload(
            "official_fixtures", fixtures_bytes
        )
        assert isinstance(bootstrap_payload, dict)
        official_deadline = assert_deadline_matches_bootstrap(
            bootstrap_payload, deadline=deadline_text
        )
        schedule = expected_deadline_schedule(bootstrap_payload)
        enforce_checkpoint_window(
            checkpoint_id,
            observed_utc,
            schedule,
            deadline_utc,
        )

        bootstrap_result = _persist_official_payload(
            family_id="official_bootstrap",
            body=bootstrap_bytes,
            payload=bootstrap_payload,
            checkpoint_dir=checkpoint_dir,
            artifact_name="bootstrap-static.json",
            observed_at=observed_text,
            registry_version=registry_version,
            origin="fixture://fpl/bootstrap-static",
        )
        fixtures_result = _persist_official_payload(
            family_id="official_fixtures",
            body=fixtures_bytes,
            payload=fixtures_payload,
            checkpoint_dir=checkpoint_dir,
            artifact_name="fixtures.json",
            observed_at=observed_text,
            registry_version=registry_version,
            origin="fixture://fpl/fixtures",
        )
        rules_counts = _empty_family_counts()
        rules_counts["input"] = 1
        rules_counts["admitted"] = 1
        families: dict[str, Any] = {
            "official_bootstrap": bootstrap_result["family"],
            "official_fixtures": fixtures_result["family"],
            "ruleset": _family_status(
                family_id="ruleset",
                mandatory=True,
                status="admitted",
                counts=rules_counts,
                artifact_path=rules.as_posix(),
                artifact_sha256=rules_hash,
                source_id="fpl-official-rules-news",
                registry_source_status="ok",
            ),
        }

        # Read source IDs from config rather than hardcoding them.
        optional_sources = _optional_source_ids_from_config(config)
        optional_missing_reasons = {
            "availability_role_evidence": "optional_availability_evidence_not_supplied",
            "transfers_and_signings": "optional_transfer_context_not_supplied",
            "set_pieces": "optional_set_piece_ledger_not_supplied",
            "promoted_team_priors": "optional_promoted_team_priors_not_supplied",
            "world_cup_return_fatigue": "optional_world_cup_priors_not_supplied",
            "licensed_odds": "optional_licensed_odds_not_configured",
            "player_ratings": "optional_player_ratings_not_supplied",
            "launch_context": "launch_context_not_supplied",
        }
        for family_id in OPTIONAL_FAMILIES:
            if family_id == "launch_context":
                families[family_id] = _bind_launch_context(
                    context_path=launch_context_path,
                    world_cup_priors_path=world_cup_priors_path,
                    bootstrap_sha256=bootstrap_result["family"]["artifact_sha256"],
                    checkpoint_dir=checkpoint_dir,
                    checkpoint_observed_at=observed_text,
                    deadline=official_deadline,
                    source_id=optional_sources[family_id],
                )
                continue
            if family_id == "set_pieces" and optional_paths[family_id] is None:
                families[family_id] = _bind_derived_set_piece_artifact(
                    bootstrap=bootstrap_payload,
                    source_sha256=bootstrap_result["family"]["artifact_sha256"],
                    observed_at=observed_text,
                    deadline=official_deadline,
                    checkpoint_dir=checkpoint_dir,
                    source_id=optional_sources[family_id],
                    registry=registry,
                )
                continue
            families[family_id] = _bind_optional_artifact(
                family_id=family_id,
                path=optional_paths[family_id],
                deadline=observed_text,
                source_id=optional_sources[family_id],
                missing_reason=optional_missing_reasons[family_id],
                checkpoint_dir=checkpoint_dir,
                sidecar_path=sidecars[family_id],
                registry=registry,
                capture_observed_at=observed_text,
            )

        source_gaps = sorted(
            family_id
            for family_id, row in families.items()
            if row["status"] == "degraded" or row["counts"]["missing"] > 0
        )
        status = "complete"
        if source_gaps:
            status = "degraded"

        manifest = _seal(
            {
                "schema_version": "1.0",
                "season": season,
                "checkpoint_id": checkpoint_id,
                "status": status,
                "source_registry_version": registry_version,
                "observed_at": observed_text,
                "available_at": observed_text,
                "deadline": official_deadline,
                "deadline_schedule": schedule,
                "request_sha256": request_sha256,
                "code_commit": commit,
                "ruleset_sha256": rules_hash,
                "predecessor_checkpoint_hash": predecessor_checkpoint_hash,
                "account_writes": False,
                "families": families,
                "source_gaps": source_gaps,
                "artifact_root": checkpoint_dir.as_posix(),
                "raw_acquisitions": [
                    {
                        "family_id": "official_bootstrap",
                        "manifest_id": bootstrap_result["acquisition"]["manifest_id"],
                        "content_hash_sha256": bootstrap_result["acquisition"][
                            "content_hash_sha256"
                        ],
                    },
                    {
                        "family_id": "official_fixtures",
                        "manifest_id": fixtures_result["acquisition"]["manifest_id"],
                        "content_hash_sha256": fixtures_result["acquisition"][
                            "content_hash_sha256"
                        ],
                    },
                ],
            }
        )
        _write_immutable_json(manifest_path, manifest)

        if update_index:
            _update_index_manifest(
                index_path=index_manifest_path or DEFAULT_MANIFEST_PATH,
                checkpoint_manifest=manifest,
                manifest_path=manifest_path,
            )
        return manifest


def _update_index_manifest(
    *,
    index_path: Path,
    checkpoint_manifest: Mapping[str, Any],
    manifest_path: Path,
) -> None:
    if index_path.exists():
        index = _load_json_object(index_path, "preseason index manifest")
    else:
        index = {
            "schema_version": "1.0",
            "season": "2026-27",
            "account_writes": False,
            "capture_mode": "immutable_preseason_checkpoints",
            "checkpoints": {},
        }
    checkpoints = dict(index.get("checkpoints") or {})
    entry = {
        "checkpoint_id": checkpoint_manifest["checkpoint_id"],
        "status": checkpoint_manifest["status"],
        "observed_at": checkpoint_manifest["observed_at"],
        "deadline": checkpoint_manifest["deadline"],
        "manifest_path": manifest_path.as_posix(),
        "manifest_sha256": checkpoint_manifest["content_sha256"],
        "request_sha256": checkpoint_manifest["request_sha256"],
        "predecessor_checkpoint_hash": checkpoint_manifest[
            "predecessor_checkpoint_hash"
        ],
        "source_gaps": list(checkpoint_manifest.get("source_gaps") or []),
    }
    existing = checkpoints.get(str(checkpoint_manifest["checkpoint_id"]))
    if existing is not None and existing != entry:
        raise PreseasonSnapshotConflict(
            "Refusing to rewrite preseason index entry with different bytes"
        )
    checkpoints[str(checkpoint_manifest["checkpoint_id"])] = entry
    index["checkpoints"] = dict(sorted(checkpoints.items()))
    index["updated_at"] = checkpoint_manifest["observed_at"]
    index["account_writes"] = False
    sealed = _seal(index)
    # Index is a mutable coordination pointer: use the atomic mutable writer.
    _write_mutable_json(index_path, sealed)


def load_index_manifest(path: Path | None = None) -> dict[str, Any]:
    return _load_json_object(path or DEFAULT_MANIFEST_PATH, "preseason index manifest")
