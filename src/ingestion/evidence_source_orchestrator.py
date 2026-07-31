"""Governed scheduling and accounting for broad live evidence sources."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from src.forecasting.live_faithful import artifact_hash


class EvidenceSourceOrchestratorError(ValueError):
    """Raised when evidence acquisition cannot be planned safely."""


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def _timestamp(value: Any, field: str) -> str:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise EvidenceSourceOrchestratorError(
            f"{field} must be an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise EvidenceSourceOrchestratorError(
            f"{field} must include a timezone"
        )
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _registry_index(source_registry: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows = source_registry.get("sources")
    if not isinstance(rows, list):
        raise EvidenceSourceOrchestratorError(
            "source registry must contain a sources list"
        )
    result: dict[str, dict[str, Any]] = {}
    for source in rows:
        if not isinstance(source, Mapping):
            raise EvidenceSourceOrchestratorError(
                "source registry entries must be objects"
            )
        source_id = str(source.get("source_id", ""))
        if not source_id or source_id in result:
            raise EvidenceSourceOrchestratorError(
                "source registry IDs must be unique and non-empty"
            )
        result[source_id] = deepcopy(dict(source))
    return result


def _checkpoint(config: Mapping[str, Any], checkpoint_id: str) -> dict[str, Any]:
    matches = [
        deepcopy(dict(row))
        for row in config.get("checkpoints", [])
        if row.get("checkpoint_id") == checkpoint_id
    ]
    if len(matches) != 1:
        raise EvidenceSourceOrchestratorError(
            f"Unknown or duplicate checkpoint: {checkpoint_id}"
        )
    return matches[0]


def _family_index(config: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for source in config.get("source_families", []):
        row = deepcopy(dict(source))
        family_id = str(row.get("family_id", ""))
        if not family_id or family_id in result:
            raise EvidenceSourceOrchestratorError(
                "source family IDs must be unique and non-empty"
            )
        result[family_id] = row
    return result


def _rights_reasons(
    registry: Mapping[str, Any] | None,
    *,
    automated: bool,
) -> list[str]:
    if registry is None:
        return ["source_unregistered"]
    reasons: list[str] = []
    licence = str(registry.get("licence_status", "unknown"))
    allowed_use = str(registry.get("allowed_use", ""))
    if licence == "prohibited":
        reasons.append("licence_prohibited")
    if not allowed_use or allowed_use == "unresolved":
        reasons.append("allowed_use_unresolved")
    if automated:
        if not registry.get("enabled"):
            reasons.append("registry_disabled")
        if licence in {"", "unknown"}:
            reasons.append("licence_unresolved_for_automation")
        method = str(registry.get("collection_method", ""))
        if method in {"", "manual", "manual_citation"}:
            reasons.append("collection_method_not_automated")
    return reasons


def build_evidence_acquisition_plan(
    *,
    checkpoint_id: str,
    observed_at: str,
    config: Mapping[str, Any],
    source_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a rights-aware plan without calling any source adapter."""

    if config.get("schema_version") != "1.0":
        raise EvidenceSourceOrchestratorError(
            "Unsupported evidence coverage configuration"
        )
    observed = _timestamp(observed_at, "observed_at")
    checkpoint = _checkpoint(config, checkpoint_id)
    families = _family_index(config)
    registry = _registry_index(source_registry)
    required = checkpoint.get("required_source_families")
    if (
        not isinstance(required, list)
        or not required
        or any(not isinstance(value, str) or not value for value in required)
    ):
        raise EvidenceSourceOrchestratorError(
            "checkpoint requires source family IDs"
        )

    actions: list[dict[str, Any]] = []
    for family_id in required:
        if family_id not in families:
            raise EvidenceSourceOrchestratorError(
                f"Checkpoint references unknown source family: {family_id}"
            )
        family = families[family_id]
        source_id = str(family.get("source_id", ""))
        mode = str(family.get("collection_mode", ""))
        source = registry.get(source_id)
        if mode == "automated_snapshot":
            reasons = _rights_reasons(source, automated=True)
            action = (
                "run_automated_adapter" if not reasons else "blocked"
            )
        elif mode == "manual_citation":
            reasons = _rights_reasons(source, automated=False)
            action = (
                "manual_citation_required" if not reasons else "blocked"
            )
        elif mode == "blocked_pending_registry":
            reasons = ["blocked_pending_registry_and_owner_approval"]
            if source is None:
                reasons.append("source_unregistered")
            action = "blocked"
        else:
            raise EvidenceSourceOrchestratorError(
                f"Unsupported collection mode: {mode}"
            )
        actions.append(
            {
                "family_id": family_id,
                "source_id": source_id,
                "channels": sorted(
                    str(value) for value in family.get("channels", [])
                ),
                "collection_mode": mode,
                "action": action,
                "reasons": sorted(set(reasons)),
                "manual_alternative": family.get("manual_alternative"),
                "max_staleness_hours": int(
                    family.get("max_staleness_hours", 0)
                ),
                "registry": (
                    {
                        "authority": str(source.get("authority", "unknown")),
                        "enabled": bool(source.get("enabled", False)),
                        "licence_status": str(
                            source.get("licence_status", "unknown")
                        ),
                        "allowed_use": str(source.get("allowed_use", "")),
                        "collection_method": str(
                            source.get("collection_method", "")
                        ),
                        "retention_policy": str(
                            source.get("retention_policy", "")
                        ),
                    }
                    if source is not None
                    else None
                ),
            }
        )

    return _seal(
        {
            "schema_version": "1.0",
            "season": str(config.get("season", "")),
            "checkpoint_id": checkpoint_id,
            "observed_at": observed,
            "actions": actions,
            "network_calls_performed": 0,
            "account_writes": False,
        }
    )


def _string_ids(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise EvidenceSourceOrchestratorError(
            "observed entity IDs must be a sequence"
        )
    return sorted(set(str(item) for item in value if str(item)))


def _observation(
    *,
    family_id: str,
    source_id: str,
    automated: bool,
    status: str,
    reasons: Sequence[str] = (),
    document_count: int = 0,
    raw_claim_count: int = 0,
    claim_count_added: int = 0,
    observed_club_ids: Sequence[str] = (),
    observed_player_ids: Sequence[str] = (),
    fresh: bool = False,
    observed_at: str | None = None,
) -> dict[str, Any]:
    for field, value in (
        ("document_count", document_count),
        ("raw_claim_count", raw_claim_count),
        ("claim_count_added", claim_count_added),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise EvidenceSourceOrchestratorError(
                f"{field} must be a non-negative integer"
            )
    return {
        "family_id": family_id,
        "source_id": source_id,
        "status": status,
        "reasons": sorted(set(str(reason) for reason in reasons)),
        "automated": automated,
        "document_count": document_count,
        "raw_claim_count": raw_claim_count,
        "claim_count_added": claim_count_added,
        "observed_club_ids": _string_ids(observed_club_ids),
        "observed_player_ids": _string_ids(observed_player_ids),
        "fresh": bool(fresh),
        "observed_at": observed_at,
    }


def _freshness(
    value: Any,
    *,
    checkpoint_at: str,
    maximum_hours: int,
) -> tuple[str | None, bool, list[str]]:
    if value is None:
        return None, False, ["observation_timestamp_missing"]
    try:
        observed = _timestamp(value, "source observed_at")
        observed_time = datetime.fromisoformat(
            observed.replace("Z", "+00:00")
        )
        checkpoint_time = datetime.fromisoformat(
            checkpoint_at.replace("Z", "+00:00")
        )
    except EvidenceSourceOrchestratorError:
        return None, False, ["observation_timestamp_invalid"]
    if observed_time > checkpoint_time:
        return observed, False, ["observation_after_checkpoint"]
    age_hours = (checkpoint_time - observed_time).total_seconds() / 3600.0
    if age_hours > maximum_hours:
        return observed, False, ["source_stale"]
    return observed, True, []

def execute_evidence_acquisition_plan(
    *,
    plan: Mapping[str, Any],
    automated_adapters: Mapping[str, Callable[[], Mapping[str, Any]]],
    manual_observations: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    """Execute only pre-authorised callbacks and record every missing family."""

    if plan.get("content_sha256") != artifact_hash(plan):
        raise EvidenceSourceOrchestratorError(
            "Evidence acquisition plan hash mismatch"
        )
    observations: list[dict[str, Any]] = []
    gaps: list[str] = []
    called_source_ids: set[str] = set()
    cached_results: dict[str, Mapping[str, Any]] = {}

    for action in plan.get("actions", []):
        family_id = str(action["family_id"])
        source_id = str(action["source_id"])
        instruction = str(action["action"])
        if instruction == "run_automated_adapter":
            adapter = automated_adapters.get(source_id)
            if adapter is None:
                row = _observation(
                    family_id=family_id,
                    source_id=source_id,
                    automated=True,
                    status="degraded",
                    reasons=["automated_adapter_missing"],
                )
            else:
                if source_id not in cached_results:
                    try:
                        cached_results[source_id] = deepcopy(dict(adapter()))
                    except Exception as exc:  # callback is an isolation boundary
                        cached_results[source_id] = {
                            "status": "degraded",
                            "degraded_reasons": [
                                f"adapter_error:{type(exc).__name__}"
                            ],
                        }
                    called_source_ids.add(source_id)
                result = cached_results[source_id]
                status = str(result.get("status", "degraded"))
                observed_at, fresh, freshness_reasons = _freshness(
                    result.get("observed_at"),
                    checkpoint_at=str(plan["observed_at"]),
                    maximum_hours=int(action["max_staleness_hours"]),
                )
                complete = (
                    status in {"complete", "success"}
                    and not freshness_reasons
                )
                row = _observation(
                    family_id=family_id,
                    source_id=source_id,
                    automated=True,
                    status="complete" if complete else "degraded",
                    reasons=(
                        []
                        if complete
                        else (
                            list(result.get("degraded_reasons", []))
                            + freshness_reasons
                            or ["adapter_incomplete"]
                        )
                    ),
                    document_count=int(
                        result.get("document_count", 1 if complete else 0)
                    ),
                    raw_claim_count=int(result.get("raw_claim_count", 0)),
                    claim_count_added=int(result.get("claim_count_added", 0)),
                    observed_club_ids=result.get("observed_club_ids", []),
                    observed_player_ids=result.get("observed_player_ids", []),
                    fresh=fresh,
                    observed_at=observed_at,
                )
        elif instruction == "manual_citation_required":
            rows = list(manual_observations.get(family_id, []))
            if not rows:
                row = _observation(
                    family_id=family_id,
                    source_id=source_id,
                    automated=False,
                    status="manual_required",
                    reasons=["manual_citation_missing"],
                )
            else:
                timestamps = [
                    _freshness(
                        item.get("observed_at"),
                        checkpoint_at=str(plan["observed_at"]),
                        maximum_hours=int(action["max_staleness_hours"]),
                    )
                    for item in rows
                ]
                timestamp_reasons = sorted(
                    {
                        reason
                        for _, _, reasons in timestamps
                        for reason in reasons
                    }
                )
                complete = not timestamp_reasons
                row = _observation(
                    family_id=family_id,
                    source_id=source_id,
                    automated=False,
                    status="complete" if complete else "degraded",
                    reasons=timestamp_reasons,
                    document_count=len(rows),
                    raw_claim_count=sum(
                        int(item.get("claim_count", 0)) for item in rows
                    ),
                    claim_count_added=sum(
                        int(item.get("claim_count", 0)) for item in rows
                    ),
                    observed_club_ids=[
                        value
                        for item in rows
                        for value in item.get("observed_club_ids", [])
                    ],
                    observed_player_ids=[
                        value
                        for item in rows
                        for value in item.get("observed_player_ids", [])
                    ],
                    fresh=complete and all(value[1] for value in timestamps),
                    observed_at=max(
                        (
                            value[0]
                            for value in timestamps
                            if value[0] is not None
                        ),
                        default=None,
                    ),
                )
        elif instruction == "blocked":
            row = _observation(
                family_id=family_id,
                source_id=source_id,
                automated=action.get("collection_mode")
                == "automated_snapshot",
                status="blocked",
                reasons=action.get("reasons", ["source_blocked"]),
            )
        else:
            raise EvidenceSourceOrchestratorError(
                f"Unsupported acquisition action: {instruction}"
            )
        observations.append(row)
        if row["status"] != "complete":
            reason = ",".join(row["reasons"]) or row["status"]
            gaps.append(f"{family_id}:{reason}")

    return _seal(
        {
            "schema_version": "1.0",
            "season": plan["season"],
            "checkpoint_id": plan["checkpoint_id"],
            "observed_at": plan["observed_at"],
            "plan_sha256": plan["content_sha256"],
            "status": "complete" if not gaps else "degraded",
            "observations": observations,
            "gaps": sorted(gaps),
            "automated_source_ids_called": sorted(called_source_ids),
            "frozen_no_evidence_control_preserved": True,
            "account_writes": False,
        }
    )
