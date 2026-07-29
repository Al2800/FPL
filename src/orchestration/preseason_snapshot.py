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

from src.ingestion.acquisition import content_hash, record_acquisition
from src.ingestion.registry import get_source, load_registry
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
    _, nominal = _timestamp(schedule[checkpoint_id], "nominal_slot")

    if idx < len(_CHECKPOINT_ORDER) - 1:
        _, upper = _timestamp(schedule[_CHECKPOINT_ORDER[idx + 1]], "next_slot")
    else:
        upper = deadline_utc

    if observed_at_utc >= upper:
        raise PreseasonSnapshotError(
            f"checkpoint_id={checkpoint_id!r}: observed_at {observed_at_utc.isoformat()} "
            f"is at or after the start of the next checkpoint window "
            f"{upper.isoformat()}; a missed checkpoint cannot be backfilled "
            "under an earlier label"
        )

    lower = nominal - CHECKPOINT_WINDOW_TOLERANCE
    if observed_at_utc < lower:
        raise PreseasonSnapshotError(
            f"checkpoint_id={checkpoint_id!r}: observed_at {observed_at_utc.isoformat()} "
            f"is more than {CHECKPOINT_WINDOW_TOLERANCE} before the nominal slot "
            f"{nominal.isoformat()}; use the launch or weekly label for non-deadline captures"
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
        "counts": dict(counts),
        "artifact_path": artifact_path,
        "artifact_sha256": artifact_sha256,
        "reasons": list(reasons or []),
    }


def _validate_source_id(source_id: str | None, registry: dict[str, Any]) -> str:
    """Return the registry collectable status: 'ok', 'disabled', 'prohibited', 'unregistered', 'unknown'."""
    if not source_id:
        return "unknown"
    registered = {
        str(row.get("source_id", "")): row
        for row in registry.get("sources", [])
        if isinstance(row, Mapping)
    }
    source = registered.get(source_id)
    if source is None:
        return "unregistered"
    if source.get("licence_status") in {"prohibited"}:
        return "prohibited"
    if not source.get("enabled"):
        return "disabled"
    if source.get("licence_status") in {None, "unknown"}:
        return "licence_unresolved"
    return "ok"


def _copy_optional_bytes(
    body: bytes,
    *,
    family_id: str,
    digest: str,
    checkpoint_dir: Path,
    extension: str = "bin",
) -> str:
    """Content-addressably copy optional artifact bytes into the checkpoint.

    Returns the checkpoint-relative path string.
    """
    safe_family = re.sub(r"[^A-Za-z0-9_-]", "-", family_id)
    dest = checkpoint_dir / "raw" / "optional" / f"{safe_family}-{digest}.{extension}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    encoded = body
    if not dest.exists():
        dest.write_bytes(encoded)
    elif dest.read_bytes() != encoded:
        raise PreseasonSnapshotConflict(
            f"Content-addressed optional artifact already exists with different bytes: {dest}"
        )
    return (Path("raw") / "optional" / f"{safe_family}-{digest}.{extension}").as_posix()


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
) -> dict[str, Any]:
    """Bind one optional artifact into the checkpoint.

    Behaviours:
    - Missing path → degraded/missing.
    - Source ID not collectable via registry → degraded.
    - Non-JSON binary/CSV without a temporal sidecar → quarantined.
    - Malformed (non-object) records are quarantined explicitly, never silently dropped.
    - Valid bytes are copied content-addressably into checkpoint_dir/raw/optional/.
    """
    counts = _empty_family_counts()

    if path is None:
        counts["missing"] = 1
        return _family_status(
            family_id=family_id,
            mandatory=False,
            status="degraded",
            counts=counts,
            reasons=[missing_reason],
            source_id=source_id,
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
        )

    # Validate source ID against registry before trusting any bytes.
    reg_status = _validate_source_id(source_id, registry)
    if reg_status in {"unregistered", "prohibited"}:
        counts["missing"] = 1
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

    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Non-JSON optional artifacts (e.g. CSV priors) require a temporal sidecar.
        if sidecar_path is None:
            counts["quarantined"] = 1
            return _family_status(
                family_id=family_id,
                mandatory=False,
                status="degraded",
                counts=counts,
                reasons=["missing_temporal_sidecar_for_binary"],
                source_id=source_id,
                registry_source_status=reg_status,
            )
        if not sidecar_path.exists():
            counts["quarantined"] = 1
            return _family_status(
                family_id=family_id,
                mandatory=False,
                status="degraded",
                counts=counts,
                reasons=[f"sidecar_missing:{sidecar_path.as_posix()}"],
                source_id=source_id,
                registry_source_status=reg_status,
            )
        try:
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            counts["quarantined"] = 1
            return _family_status(
                family_id=family_id,
                mandatory=False,
                status="degraded",
                counts=counts,
                reasons=["sidecar_not_valid_json"],
                source_id=source_id,
                registry_source_status=reg_status,
            )
        if not isinstance(sidecar, dict) or "available_at" not in sidecar:
            counts["quarantined"] = 1
            return _family_status(
                family_id=family_id,
                mandatory=False,
                status="degraded",
                counts=counts,
                reasons=["sidecar_missing_available_at"],
                source_id=source_id,
                registry_source_status=reg_status,
            )
        # Treat the sidecar as a single record and admit it.
        admission = admit_temporal_records([sidecar], deadline=deadline)
        counts["input"] = 1
        counts["admitted"] = admission["admitted_count"]
        counts["quarantined"] = admission["quarantined_count"]
        if admission["admitted_count"] == 0:
            counts["missing"] = 1
            reasons = sorted({row["reason"] for row in admission["quarantined"]}) or [missing_reason]
            return _family_status(
                family_id=family_id,
                mandatory=False,
                status="degraded",
                counts=counts,
                reasons=reasons,
                source_id=source_id,
                registry_source_status=reg_status,
            )
        artifact_relative = _copy_optional_bytes(
            body, family_id=family_id, digest=digest, checkpoint_dir=checkpoint_dir
        )
        return _family_status(
            family_id=family_id,
            mandatory=False,
            status="admitted",
            counts=counts,
            artifact_path=artifact_relative,
            artifact_sha256=digest,
            source_id=source_id,
            registry_source_status=reg_status,
        )

    # JSON payload: determine record list.
    records: list[Any]
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        raw_records = payload["records"]
        records = []
        extra_quarantined: list[dict[str, Any]] = []
        for idx, row in enumerate(raw_records):
            if isinstance(row, Mapping):
                records.append(row)
            else:
                extra_quarantined.append(
                    {
                        "index": idx,
                        "reason": "record_must_be_object",
                        "record": None,
                    }
                )
        extra_q = len(extra_quarantined)
    elif isinstance(payload, dict) and "available_at" in payload:
        records = [payload]
        extra_quarantined = []
        extra_q = 0
    elif isinstance(payload, dict):
        counts["admitted"] = 1
        artifact_relative = _copy_optional_bytes(
            body, family_id=family_id, digest=digest, checkpoint_dir=checkpoint_dir, extension="json"
        )
        return _family_status(
            family_id=family_id,
            mandatory=False,
            status="admitted",
            counts=counts,
            artifact_path=artifact_relative,
            artifact_sha256=digest,
            source_id=source_id,
            registry_source_status=reg_status,
        )
    else:
        counts["quarantined"] = 1
        return _family_status(
            family_id=family_id,
            mandatory=False,
            status="degraded",
            counts=counts,
            reasons=["payload_must_be_json_object"],
            source_id=source_id,
            registry_source_status=reg_status,
        )

    admission = admit_temporal_records(records, deadline=deadline)
    counts["input"] = admission["input_count"] + extra_q
    counts["admitted"] = admission["admitted_count"]
    counts["quarantined"] = admission["quarantined_count"] + extra_q

    if admission["admitted_count"] == 0:
        counts["missing"] = 1 if (admission["input_count"] + extra_q) == 0 else 0
        reasons = sorted({row["reason"] for row in admission["quarantined"] + extra_quarantined})
        if not reasons:
            reasons = [missing_reason]
        return _family_status(
            family_id=family_id,
            mandatory=False,
            status="degraded",
            counts=counts,
            artifact_path=path.as_posix(),
            artifact_sha256=digest,
            reasons=reasons,
            source_id=source_id,
            registry_source_status=reg_status,
        )

    status = "admitted" if (admission["quarantined_count"] + extra_q) == 0 else "degraded"
    reasons = sorted({row["reason"] for row in admission["quarantined"] + extra_quarantined})
    artifact_relative = _copy_optional_bytes(
        body, family_id=family_id, digest=digest, checkpoint_dir=checkpoint_dir, extension="json"
    )
    return _family_status(
        family_id=family_id,
        mandatory=False,
        status=status,
        counts=counts,
        artifact_path=artifact_relative,
        artifact_sha256=digest,
        reasons=reasons,
        source_id=source_id,
        registry_source_status=reg_status,
    )


def _persist_official_payload(
    *,
    family_id: str,
    body: bytes,
    checkpoint_dir: Path,
    artifact_name: str,
    observed_at: str,
    registry_version: str,
    origin: str,
) -> dict[str, Any]:
    if not body:
        raise PreseasonSnapshotError(f"Mandatory family {family_id} returned an empty body")
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
) -> dict[str, str | None]:
    """Pre-compute content digests for all optional artifacts provided.

    Returns a mapping from family_id to digest (or None if path is absent/missing).
    """
    result: dict[str, str | None] = {}
    for family_id, path in optional_paths.items():
        if path is not None and path.exists():
            result[family_id] = content_hash(path.read_bytes())
        else:
            result[family_id] = None
    return result


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

    # Compute optional artifact digests before request hash.
    optional_digests = _compute_optional_digests(optional_paths)

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
        "optional_artifact_sha256": {k: v for k, v in sorted(optional_digests.items())},
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

        bootstrap_result = _persist_official_payload(
            family_id="official_bootstrap",
            body=bootstrap_bytes,
            checkpoint_dir=checkpoint_dir,
            artifact_name="bootstrap-static.json",
            observed_at=observed_text,
            registry_version=registry_version,
            origin="fixture://fpl/bootstrap-static",
        )
        fixtures_result = _persist_official_payload(
            family_id="official_fixtures",
            body=fixtures_bytes,
            checkpoint_dir=checkpoint_dir,
            artifact_name="fixtures.json",
            observed_at=observed_text,
            registry_version=registry_version,
            origin="fixture://fpl/fixtures",
        )

        bootstrap_payload = bootstrap_result["payload"]
        assert isinstance(bootstrap_payload, dict)
        official_deadline = assert_deadline_matches_bootstrap(
            bootstrap_payload, deadline=deadline_text
        )
        schedule = expected_deadline_schedule(bootstrap_payload)

        # Enforce scheduling contract: verify observed_at is in the correct window.
        enforce_checkpoint_window(
            checkpoint_id,
            observed_utc,
            schedule,
            deadline_utc,
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
        }
        for family_id in OPTIONAL_FAMILIES:
            families[family_id] = _bind_optional_artifact(
                family_id=family_id,
                path=optional_paths[family_id],
                deadline=official_deadline,
                source_id=optional_sources[family_id],
                missing_reason=optional_missing_reasons[family_id],
                checkpoint_dir=checkpoint_dir,
                sidecar_path=sidecars[family_id],
                registry=registry,
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
