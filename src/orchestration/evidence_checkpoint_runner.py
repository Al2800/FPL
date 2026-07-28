"""Single-writer orchestration for one live evidence checkpoint."""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
from typing import Any, Callable, Iterator, Mapping, Sequence
from urllib.parse import urlparse

from src.evaluation.evidence_coverage import build_evidence_coverage_report
from src.evidence.candidate_boundary_retrieval import (
    build_candidate_boundary_packet,
    discover_candidate_boundaries,
)
from src.evidence.live_evidence_ledger import (
    append_live_evidence_claim,
    live_evidence_hash,
    new_live_evidence_ledger,
    project_live_evidence,
    validate_live_evidence_ledger,
)
from src.forecasting.live_faithful import artifact_hash
from src.ingestion.evidence_source_orchestrator import (
    build_evidence_acquisition_plan,
    execute_evidence_acquisition_plan,
)


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_ID = re.compile(r"[^A-Za-z0-9._-]+")


class EvidenceCheckpointError(ValueError):
    """Raised when a checkpoint cannot be admitted safely."""


class EvidenceCheckpointConflict(EvidenceCheckpointError):
    """Raised before collection when another writer advanced the head."""


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    if not isinstance(value, str) or not value:
        raise EvidenceCheckpointError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceCheckpointError(
            f"{field} must be an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise EvidenceCheckpointError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _value_hash(value: Any) -> str:
    return artifact_hash({"value": deepcopy(value)})


def derive_deadline_checkpoints(
    bootstrap: Mapping[str, Any],
    *,
    gameweek: int,
    final_offset_minutes: int = 5,
) -> dict[str, str]:
    """Derive pre-deadline checkpoints from the official event timestamp."""

    if isinstance(gameweek, bool) or not isinstance(gameweek, int) or gameweek < 1:
        raise EvidenceCheckpointError("gameweek must be a positive integer")
    if (
        isinstance(final_offset_minutes, bool)
        or not isinstance(final_offset_minutes, int)
        or not 1 <= final_offset_minutes <= 60
    ):
        raise EvidenceCheckpointError(
            "final_offset_minutes must be an integer in [1, 60]"
        )
    events = bootstrap.get("events")
    if not isinstance(events, list):
        raise EvidenceCheckpointError("bootstrap events must be a list")
    matches = [
        row
        for row in events
        if isinstance(row, Mapping) and row.get("id") == gameweek
    ]
    if len(matches) != 1:
        raise EvidenceCheckpointError(
            f"Expected exactly one official event for gameweek {gameweek}"
        )
    _, deadline = _timestamp(matches[0].get("deadline_time"), "deadline_time")

    def stamp(delta: timedelta) -> str:
        return (deadline - delta).isoformat().replace("+00:00", "Z")

    return {
        "T-48h": stamp(timedelta(hours=48)),
        "T-24h": stamp(timedelta(hours=24)),
        "T-8h": stamp(timedelta(hours=8)),
        "T-2h": stamp(timedelta(hours=2)),
        "final_pre_deadline": stamp(
            timedelta(minutes=final_offset_minutes)
        ),
    }


def new_checkpoint_head(
    *,
    season: str,
    ledger_sha256: str | None = None,
) -> dict[str, Any]:
    if not isinstance(season, str) or not season:
        raise EvidenceCheckpointError("season must be a non-empty string")
    if ledger_sha256 is not None and not _SHA256.fullmatch(ledger_sha256):
        raise EvidenceCheckpointError(
            "ledger_sha256 must be a lowercase SHA-256 digest"
        )
    return _seal(
        {
            "schema_version": "1.0",
            "season": season,
            "generation": 0,
            "ledger_sha256": ledger_sha256,
            "last_checkpoint_id": None,
            "last_checkpoint_sha256": None,
            "last_checkpoint_path": None,
            "last_request_sha256": None,
            "updated_at": None,
        }
    )


def _validate_head(head: Mapping[str, Any], *, season: str) -> None:
    if head.get("schema_version") != "1.0":
        raise EvidenceCheckpointError("Unsupported checkpoint head schema")
    if head.get("season") != season:
        raise EvidenceCheckpointError("Checkpoint head season mismatch")
    if head.get("content_sha256") != artifact_hash(head):
        raise EvidenceCheckpointError("Checkpoint head content hash mismatch")
    generation = head.get("generation")
    if (
        isinstance(generation, bool)
        or not isinstance(generation, int)
        or generation < 0
    ):
        raise EvidenceCheckpointError(
            "Checkpoint head generation must be non-negative"
        )
    for field in (
        "ledger_sha256",
        "last_checkpoint_sha256",
        "last_request_sha256",
    ):
        value = head.get(field)
        if value is not None and not _SHA256.fullmatch(str(value)):
            raise EvidenceCheckpointError(
                f"Checkpoint head {field} is not a SHA-256 digest"
            )


def _read_head(
    path: Path,
    *,
    season: str,
    ledger_sha256: str,
) -> dict[str, Any]:
    if not path.exists():
        head = new_checkpoint_head(
            season=season, ledger_sha256=ledger_sha256
        )
        _write_mutable_json(path, head)
        return head
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceCheckpointError(
            f"Cannot read checkpoint head: {path}"
        ) from exc
    if not isinstance(value, Mapping):
        raise EvidenceCheckpointError("Checkpoint head must be an object")
    head = deepcopy(dict(value))
    _validate_head(head, season=season)
    return head


def _write_mutable_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(value, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    mode = "r+b" if path.exists() else "xb"
    with path.open(mode) as handle:
        handle.seek(0)
        handle.write(encoded)
        handle.truncate()
        handle.flush()
        os.fsync(handle.fileno())


def _write_immutable_json(path: Path, value: Mapping[str, Any]) -> None:
    encoded = (
        json.dumps(value, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        if path.read_bytes() != encoded:
            raise EvidenceCheckpointConflict(
                f"Immutable checkpoint path already has different content: {path}"
            )


@contextmanager
def _exclusive_lock(path: Path) -> Iterator[None]:
    """Hold a persistent one-byte file lock without deleting a lock file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _validate_manual_observations(
    manual_observations: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    required = {
        "document_id",
        "source_url",
        "source_hash_sha256",
        "observed_at",
    }
    for family_id, rows in manual_observations.items():
        if not isinstance(family_id, str) or not family_id:
            raise EvidenceCheckpointError(
                "manual observation family IDs must be non-empty strings"
            )
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            raise EvidenceCheckpointError(
                f"manual observations for {family_id} must be a list"
            )
        validated: list[dict[str, Any]] = []
        for index, source in enumerate(rows):
            if not isinstance(source, Mapping):
                raise EvidenceCheckpointError(
                    f"manual observation {family_id}[{index}] must be an object"
                )
            missing = sorted(required - set(source))
            if missing:
                raise EvidenceCheckpointError(
                    f"manual observation {family_id}[{index}] missing "
                    + ", ".join(missing)
                )
            row = deepcopy(dict(source))
            for field in ("document_id", "source_url"):
                if not isinstance(row[field], str) or not row[field].strip():
                    raise EvidenceCheckpointError(
                        f"manual observation {family_id}[{index}] {field} "
                        "must be non-empty"
                    )
            parsed = urlparse(row["source_url"])
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise EvidenceCheckpointError(
                    f"manual observation {family_id}[{index}] source_url "
                    "must be an HTTP(S) citation"
                )
            if not _SHA256.fullmatch(str(row["source_hash_sha256"])):
                raise EvidenceCheckpointError(
                    f"manual observation {family_id}[{index}] "
                    "source_hash_sha256 must be a lowercase SHA-256 digest"
                )
            row["observed_at"] = _timestamp(
                row["observed_at"],
                f"manual observation {family_id}[{index}] observed_at",
            )[0]
            claim_count = row.get("claim_count", 0)
            if (
                isinstance(claim_count, bool)
                or not isinstance(claim_count, int)
                or claim_count < 0
            ):
                raise EvidenceCheckpointError(
                    f"manual observation {family_id}[{index}] claim_count "
                    "must be non-negative"
                )
            row["claim_count"] = claim_count
            validated.append(row)
        result[family_id] = validated
    return result


def _validate_manual_claims(
    manual_claims: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    observations: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for family_id, rows in manual_claims.items():
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            raise EvidenceCheckpointError(
                f"manual claims for {family_id} must be a list"
            )
        citations = {
            (
                str(row["document_id"]),
                str(row["source_url"]),
                str(row["source_hash_sha256"]),
            )
            for row in observations.get(family_id, [])
        }
        for index, source in enumerate(rows):
            if not isinstance(source, Mapping):
                raise EvidenceCheckpointError(
                    f"manual claim {family_id}[{index}] must be an object"
                )
            claim = deepcopy(dict(source))
            binding = (
                str(claim.get("document_id", "")),
                str(claim.get("source_url", "")),
                str(claim.get("source_hash_sha256", "")),
            )
            if binding not in citations:
                raise EvidenceCheckpointError(
                    f"manual claim {family_id}[{index}] has no matching "
                    "citation artifact"
                )
            result.append(claim)
    return result


def _capture_claims(
    adapter_results: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for capture in adapter_results.values():
        ledger = capture.get("ledger")
        if ledger is None:
            continue
        if not isinstance(ledger, Mapping):
            raise EvidenceCheckpointError(
                "Automated capture ledger must be an object"
            )
        validate_live_evidence_ledger(ledger)
        result.extend(deepcopy(list(ledger["claims"])))
    return result


def _normalise_claim(
    claim: Mapping[str, Any],
    *,
    season: str,
    created_at: str,
    source_registry: Mapping[str, Any],
    evidence_config: Mapping[str, Any],
) -> dict[str, Any]:
    ledger = new_live_evidence_ledger(
        season=season, created_at=created_at
    )
    ledger = append_live_evidence_claim(
        ledger,
        claim,
        source_registry=source_registry,
        config=evidence_config,
    )
    return deepcopy(ledger["claims"][0])


def _subject_key(claim: Mapping[str, Any]) -> tuple[Any, ...]:
    identities = tuple(
        sorted(
            (
                str(row["entity_type"]),
                str(row["stable_id"]),
            )
            for row in claim["identity_bindings"]
        )
    )
    return (
        str(claim["source_id"]),
        str(claim["claim_type"]),
        identities,
    )


def _merge_claims(
    current_ledger: Mapping[str, Any],
    incoming_claims: Sequence[Mapping[str, Any]],
    *,
    source_registry: Mapping[str, Any],
    evidence_config: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    ledger = deepcopy(dict(current_ledger))
    normalised = [
        _normalise_claim(
            row,
            season=str(ledger["season"]),
            created_at=str(ledger["created_at"]),
            source_registry=source_registry,
            evidence_config=evidence_config,
        )
        for row in incoming_claims
    ]
    normalised.sort(
        key=lambda row: (str(row["available_at"]), str(row["claim_id"]))
    )
    added: list[str] = []
    for candidate in normalised:
        by_id = {
            str(row["claim_id"]): row for row in ledger["claims"]
        }
        claim_id = str(candidate["claim_id"])
        if claim_id in by_id:
            if by_id[claim_id] != candidate:
                raise EvidenceCheckpointError(
                    f"Claim ID reused with different content: {claim_id}"
                )
            continue
        if not candidate["supersedes_claim_ids"]:
            superseded = {
                str(value)
                for row in ledger["claims"]
                for value in row.get("supersedes_claim_ids", [])
            }
            key = _subject_key(candidate)
            prior = next(
                (
                    row
                    for row in reversed(ledger["claims"])
                    if str(row["claim_id"]) not in superseded
                    and _subject_key(row) == key
                ),
                None,
            )
            if prior is not None:
                candidate["supersedes_claim_ids"] = [
                    str(prior["claim_id"])
                ]
        ledger = append_live_evidence_claim(
            ledger,
            candidate,
            source_registry=source_registry,
            config=evidence_config,
        )
        added.append(claim_id)
    return ledger, added


def _acquisition_manifest_ids(
    adapter_results: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    ids: set[str] = set()
    for capture in adapter_results.values():
        acquisitions: list[Any] = [capture.get("acquisition")]
        acquisitions.extend(
            row.get("acquisition")
            for row in capture.get("endpoint_captures", [])
            if isinstance(row, Mapping)
        )
        for acquisition in acquisitions:
            if isinstance(acquisition, Mapping) and acquisition.get(
                "manifest_id"
            ):
                ids.add(str(acquisition["manifest_id"]))
    return sorted(ids)


def _claim_bindings(
    ledger: Mapping[str, Any],
    claim_ids: Sequence[str],
) -> list[dict[str, str]]:
    wanted = set(claim_ids)
    return [
        {
            "claim_id": str(row["claim_id"]),
            "source_id": str(row["source_id"]),
            "document_id": str(row["document_id"]),
            "source_hash_sha256": str(row["source_hash_sha256"]),
        }
        for row in ledger["claims"]
        if str(row["claim_id"]) in wanted
    ]


def _checkpoint_request_hash(
    *,
    season: str,
    gameweek: int,
    checkpoint_id: str,
    decision_at: str,
    solver_input: Mapping[str, Any],
    solver_output: Mapping[str, Any],
    coverage_config: Mapping[str, Any],
    evidence_config: Mapping[str, Any],
    source_registry: Mapping[str, Any],
    adapter_source_ids: Sequence[str],
    supplemental_source_ids: Sequence[str],
    manual_observations: Mapping[str, Any],
    manual_claims: Mapping[str, Any],
    expected_club_ids: Sequence[str],
    expected_player_ids: Sequence[str],
    accepted_adjustments: Sequence[Mapping[str, Any]],
) -> str:
    return _value_hash(
        {
            "season": season,
            "gameweek": gameweek,
            "checkpoint_id": checkpoint_id,
            "decision_at": decision_at,
            "solver_input_sha256": _value_hash(solver_input),
            "solver_output_sha256": _value_hash(solver_output),
            "coverage_config_sha256": _value_hash(coverage_config),
            "evidence_config_sha256": _value_hash(evidence_config),
            "source_registry_sha256": _value_hash(source_registry),
            "adapter_source_ids": sorted(adapter_source_ids),
            "supplemental_source_ids": sorted(supplemental_source_ids),
            "manual_observations_sha256": _value_hash(manual_observations),
            "manual_claims_sha256": _value_hash(manual_claims),
            "expected_club_ids": sorted(set(expected_club_ids)),
            "expected_player_ids": sorted(set(expected_player_ids)),
            "accepted_adjustments_sha256": _value_hash(
                list(accepted_adjustments)
            ),
        }
    )


def _read_idempotent_checkpoint(
    head: Mapping[str, Any],
    *,
    request_sha256: str,
) -> dict[str, Any] | None:
    if head.get("last_request_sha256") != request_sha256:
        return None
    path_value = head.get("last_checkpoint_path")
    if not isinstance(path_value, str) or not path_value:
        raise EvidenceCheckpointError(
            "Checkpoint head lacks path for idempotent request"
        )
    path = Path(path_value)
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceCheckpointError(
            "Cannot recover idempotent checkpoint artifact"
        ) from exc
    if not isinstance(value, Mapping):
        raise EvidenceCheckpointError(
            "Idempotent checkpoint artifact must be an object"
        )
    artifact = deepcopy(dict(value))
    if artifact.get("content_sha256") != artifact_hash(artifact):
        raise EvidenceCheckpointError(
            "Idempotent checkpoint artifact hash mismatch"
        )
    if artifact["content_sha256"] != head.get("last_checkpoint_sha256"):
        raise EvidenceCheckpointError(
            "Checkpoint artifact does not match checkpoint head"
        )
    return artifact


def run_evidence_checkpoint(
    *,
    season: str,
    gameweek: int,
    checkpoint_id: str,
    decision_at: str,
    current_ledger: Mapping[str, Any],
    solver_input: Mapping[str, Any],
    solver_output: Mapping[str, Any],
    coverage_config: Mapping[str, Any],
    evidence_config: Mapping[str, Any],
    source_registry: Mapping[str, Any],
    automated_adapters: Mapping[str, Callable[[], Mapping[str, Any]]],
    supplemental_adapters: Mapping[str, Callable[[], Mapping[str, Any]]] | None = None,
    manual_observations: Mapping[str, Sequence[Mapping[str, Any]]],
    manual_claims: Mapping[str, Sequence[Mapping[str, Any]]],
    expected_club_ids: Sequence[str],
    expected_player_ids: Sequence[str],
    accepted_adjustments: Sequence[Mapping[str, Any]],
    head_path: Path,
    checkpoint_dir: Path,
    expected_head_sha256: str | None,
) -> dict[str, Any]:
    """Run and commit one evidence checkpoint under a single-writer lock."""

    decision_text, _ = _timestamp(decision_at, "decision_at")
    if isinstance(gameweek, bool) or not isinstance(gameweek, int) or gameweek < 1:
        raise EvidenceCheckpointError("gameweek must be a positive integer")
    validate_live_evidence_ledger(current_ledger)
    if current_ledger.get("season") != season:
        raise EvidenceCheckpointError("Current ledger season mismatch")
    if coverage_config.get("season") != season:
        raise EvidenceCheckpointError("Coverage configuration season mismatch")
    if evidence_config.get("season") != season:
        raise EvidenceCheckpointError("Evidence configuration season mismatch")

    supplemental = dict(supplemental_adapters or {})
    registered_sources = {
        str(row.get("source_id", "")): row
        for row in source_registry.get("sources", [])
        if isinstance(row, Mapping)
    }
    for source_id in supplemental:
        source = registered_sources.get(source_id)
        if source is None or not bool(source.get("enabled", False)):
            raise EvidenceCheckpointError(
                f"Supplemental source is not enabled in the registry: {source_id}"
            )
        if str(source.get("licence_status", "")) in {"", "unknown"}:
            raise EvidenceCheckpointError(
                f"Supplemental source licence is unresolved: {source_id}"
            )
        if not str(source.get("allowed_use", "")):
            raise EvidenceCheckpointError(
                f"Supplemental source allowed use is unresolved: {source_id}"
            )

    citations = _validate_manual_observations(manual_observations)
    manual_rows = _validate_manual_claims(
        manual_claims, observations=citations
    )
    request_sha256 = _checkpoint_request_hash(
        season=season,
        gameweek=gameweek,
        checkpoint_id=checkpoint_id,
        decision_at=decision_text,
        solver_input=solver_input,
        solver_output=solver_output,
        coverage_config=coverage_config,
        evidence_config=evidence_config,
        source_registry=source_registry,
        adapter_source_ids=list(automated_adapters),
        supplemental_source_ids=list(supplemental),
        manual_observations=citations,
        manual_claims=manual_claims,
        expected_club_ids=expected_club_ids,
        expected_player_ids=expected_player_ids,
        accepted_adjustments=accepted_adjustments,
    )

    lock_path = head_path.with_suffix(head_path.suffix + ".lock")
    with _exclusive_lock(lock_path):
        head = _read_head(
            head_path,
            season=season,
            ledger_sha256=str(current_ledger["content_sha256"]),
        )
        idempotent = _read_idempotent_checkpoint(
            head, request_sha256=request_sha256
        )
        if idempotent is not None:
            return idempotent
        if (
            expected_head_sha256 is not None
            and expected_head_sha256 != head["content_sha256"]
        ):
            raise EvidenceCheckpointConflict(
                "stale checkpoint head; another writer advanced the ledger"
            )
        bound_ledger = head.get("ledger_sha256")
        if (
            bound_ledger is not None
            and bound_ledger != current_ledger["content_sha256"]
        ):
            raise EvidenceCheckpointConflict(
                "current ledger does not match checkpoint head"
            )

        plan = build_evidence_acquisition_plan(
            checkpoint_id=checkpoint_id,
            observed_at=decision_text,
            config=coverage_config,
            source_registry=source_registry,
        )
        adapter_results: dict[str, Mapping[str, Any]] = {}
        fatal_safety_errors: list[str] = []

        def cached(
            source_id: str,
            callback: Callable[[], Mapping[str, Any]],
        ) -> Mapping[str, Any]:
            if source_id not in adapter_results:
                result = callback()
                if not isinstance(result, Mapping):
                    raise EvidenceCheckpointError(
                        f"Adapter {source_id} must return an object"
                    )
                capture = deepcopy(dict(result))
                if capture.get("account_writes") not in {None, False}:
                    fatal_safety_errors.append(
                        f"Adapter {source_id} reported an account write"
                    )
                if capture.get(
                    "frozen_no_evidence_control_preserved"
                ) is False:
                    fatal_safety_errors.append(
                        f"Adapter {source_id} did not preserve frozen control"
                    )
                adapter_results[source_id] = capture
            return adapter_results[source_id]

        wrapped = {
            source_id: (
                lambda source_id=source_id, callback=callback: cached(
                    source_id, callback
                )
            )
            for source_id, callback in automated_adapters.items()
        }
        funnel = execute_evidence_acquisition_plan(
            plan=plan,
            automated_adapters=wrapped,
            manual_observations=citations,
        )
        if fatal_safety_errors:
            raise EvidenceCheckpointError(
                "; ".join(sorted(set(fatal_safety_errors)))
            )
        supplemental_results: dict[str, Mapping[str, Any]] = {}
        for source_id, callback in supplemental.items():
            try:
                raw_result = callback()
                if not isinstance(raw_result, Mapping):
                    raise EvidenceCheckpointError(
                        f"Supplemental adapter {source_id} must return an object"
                    )
                capture = deepcopy(dict(raw_result))
                if capture.get("account_writes") not in {None, False}:
                    raise EvidenceCheckpointError(
                        f"Supplemental adapter {source_id} reported an account write"
                    )
                if capture.get("content_sha256") is not None and capture.get(
                    "content_sha256"
                ) != artifact_hash(capture):
                    raise EvidenceCheckpointError(
                        f"Supplemental adapter {source_id} hash mismatch"
                    )
            except EvidenceCheckpointError:
                raise
            except Exception as exc:  # isolated, non-blocking shadow input
                capture = _seal(
                    {
                        "schema_version": "1.0",
                        "source_id": source_id,
                        "status": "degraded",
                        "degraded_reasons": [
                            f"adapter_error:{type(exc).__name__}"
                        ],
                        "acquisition": None,
                        "account_writes": False,
                    }
                )
            supplemental_results[source_id] = capture
        all_capture_results = dict(adapter_results)
        overlap = set(all_capture_results).intersection(supplemental_results)
        if overlap:
            raise EvidenceCheckpointError(
                "Source configured as both governed and supplemental adapter: "
                + ", ".join(sorted(overlap))
            )
        all_capture_results.update(supplemental_results)
        incoming = _capture_claims(all_capture_results) + manual_rows
        ledger_after, claim_ids_added = _merge_claims(
            current_ledger,
            incoming,
            source_registry=source_registry,
            evidence_config=evidence_config,
        )
        evidence_view = project_live_evidence(
            ledger_after, decision_at=decision_text
        )
        discovery = discover_candidate_boundaries(
            solver_input=solver_input,
            solver_output=solver_output,
            config=coverage_config,
        )
        packet = build_candidate_boundary_packet(
            discovery=discovery,
            evidence_view=evidence_view,
            config=coverage_config,
        )
        coverage_audit = build_evidence_coverage_report(
            checkpoint_id=checkpoint_id,
            decision_at=decision_text,
            config=coverage_config,
            acquisition_funnel=funnel,
            evidence_view=evidence_view,
            packet=packet,
            expected_club_ids=expected_club_ids,
            expected_player_ids=expected_player_ids,
            accepted_adjustments=accepted_adjustments,
        )
        manifest_ids = _acquisition_manifest_ids(all_capture_results)
        manifests_by_source = {
            source_id: _acquisition_manifest_ids({source_id: capture})
            for source_id, capture in all_capture_results.items()
        }
        claims_by_source: dict[str, list[str]] = {}
        for row in ledger_after["claims"]:
            claim_id = str(row["claim_id"])
            if claim_id in claim_ids_added:
                claims_by_source.setdefault(str(row["source_id"]), []).append(
                    claim_id
                )
        observation_bindings = [
            {
                "family_id": str(row["family_id"]),
                "source_id": str(row["source_id"]),
                "status": str(row["status"]),
                "acquisition_manifest_ids": manifests_by_source.get(
                    str(row["source_id"]), []
                ),
                "claim_ids_added": sorted(
                    claims_by_source.get(str(row["source_id"]), [])
                ),
            }
            for row in funnel["observations"]
        ]
        observation_bindings.extend(
            {
                "family_id": f"supplemental:{source_id}",
                "source_id": source_id,
                "status": str(capture.get("status", "degraded")),
                "acquisition_manifest_ids": manifests_by_source[source_id],
                "claim_ids_added": [],
            }
            for source_id, capture in sorted(supplemental_results.items())
        )
        degraded_reasons = sorted(
            set(funnel.get("gaps", []))
            | {
                reason
                for capture in all_capture_results.values()
                for reason in capture.get("degraded_reasons", [])
            }
        )
        status = (
            "complete"
            if funnel["status"] == "complete"
            and coverage_audit["status"] == "complete"
            and not degraded_reasons
            else "degraded"
        )
        artifact = _seal(
            {
                "schema_version": "1.0",
                "checkpoint_run_id": (
                    f"evidence-checkpoint:{season}:gw{gameweek}:"
                    f"{checkpoint_id}:{decision_text}"
                ),
                "season": season,
                "gameweek": gameweek,
                "checkpoint_id": checkpoint_id,
                "decision_at": decision_text,
                "status": status,
                "degraded_reasons": degraded_reasons,
                "request_sha256": request_sha256,
                "head_before": {
                    "generation": head["generation"],
                    "content_sha256": head["content_sha256"],
                },
                "bindings": {
                    "acquisition_plan_sha256": plan["content_sha256"],
                    "acquisition_funnel_sha256": funnel["content_sha256"],
                    "acquisition_manifest_ids": manifest_ids,
                    "observation_bindings": observation_bindings,
                    "supplemental_capture_sha256": {
                        source_id: capture.get("content_sha256")
                        for source_id, capture in sorted(supplemental_results.items())
                    },
                    "claim_ids_added": sorted(claim_ids_added),
                    "claim_citation_bindings": _claim_bindings(
                        ledger_after, claim_ids_added
                    ),
                    "ledger_before_sha256": current_ledger[
                        "content_sha256"
                    ],
                    "ledger_after_sha256": ledger_after["content_sha256"],
                    "evidence_view_sha256": evidence_view["content_sha256"],
                    "discovery_sha256": discovery["content_sha256"],
                    "packet_sha256": packet["content_sha256"],
                    "coverage_audit_sha256": coverage_audit[
                        "content_sha256"
                    ],
                },
                "alerts": {
                    "coverage_status": coverage_audit["status"],
                    "degraded_reasons": degraded_reasons,
                    "retry_after_seconds_by_source": {
                        source_id: int(capture["retry_after_seconds"])
                        for source_id, capture in sorted(
                            all_capture_results.items()
                        )
                        if isinstance(capture.get("retry_after_seconds"), int)
                    },
                },

                "acquisition_plan": plan,
                "acquisition_funnel": funnel,
                "ledger_after": ledger_after,
                "evidence_view": evidence_view,
                "discovery": discovery,
                "packet": packet,
                "coverage_audit": coverage_audit,
                "frozen_no_evidence_control_preserved": True,
                "account_writes": False,
            }
        )
        safe_checkpoint = _SAFE_ID.sub("-", checkpoint_id).strip("-")
        path = (
            checkpoint_dir
            / season
            / f"gw-{gameweek:02d}"
            / safe_checkpoint
            / f"{request_sha256}.json"
        ).resolve()
        _write_immutable_json(path, artifact)
        next_head = _seal(
            {
                "schema_version": "1.0",
                "season": season,
                "generation": int(head["generation"]) + 1,
                "ledger_sha256": ledger_after["content_sha256"],
                "last_checkpoint_id": artifact["checkpoint_run_id"],
                "last_checkpoint_sha256": artifact["content_sha256"],
                "last_checkpoint_path": str(path),
                "last_request_sha256": request_sha256,
                "updated_at": decision_text,
            }
        )
        _write_mutable_json(head_path, next_head)
        return artifact
