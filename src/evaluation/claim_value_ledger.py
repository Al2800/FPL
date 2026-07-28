"""Deterministic ex-post accounting for evidence claims and paired outcomes."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from src.forecasting.live_faithful import artifact_hash


class ClaimValueLedgerError(ValueError):
    """Raised when replay artifacts cannot support faithful claim accounting."""


@dataclass(frozen=True)
class ClaimValueRun:
    """One evidence decision namespace included in a claim-value report."""

    arm: str
    gameweek: int
    root: Path
    source_ref: str
    namespace: str

    verification_root: Path | None = None
    verification_source_ref: str | None = None

_GAMEWEEK_RE = re.compile(r"^gw-(\d+)$")
_SOLUTION_RE = re.compile(r"^sol-v(\d+)$")
_ARTIFACT_NAMES = (
    "host-bundle.json",
    "evidence-run.json",
    "adapter-audit.json",
    "comparison.json",
    "same-state-attribution.json",
    "realised-outcome.json",
)


def _read_object(path: Path, *, required: bool = True) -> dict[str, Any] | None:
    if not path.exists():
        if required:
            raise ClaimValueLedgerError(f"Required artifact is missing: {path}")
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ClaimValueLedgerError(f"Cannot read JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise ClaimValueLedgerError(f"Artifact must contain a JSON object: {path}")
    supplied_hash = value.get("content_sha256")
    if not isinstance(supplied_hash, str) or not supplied_hash:
        raise ClaimValueLedgerError(f"Artifact has no content_sha256: {path}")
    if supplied_hash != artifact_hash(value):
        raise ClaimValueLedgerError(f"Artifact hash mismatch: {path}")
    return value

def _read_unsealed_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ClaimValueLedgerError(f"Cannot read JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise ClaimValueLedgerError(f"Artifact must contain a JSON object: {path}")
    return value




def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _age_hours(published_at: Any, decision_at: Any) -> float | None:
    published = _timestamp(published_at)
    decision = _timestamp(decision_at)
    if published is None or decision is None:
        return None
    return round((decision - published).total_seconds() / 3600.0, 6)


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _mapping(value: Any) -> dict[str, Any]:
    return deepcopy(dict(value)) if isinstance(value, Mapping) else {}


def _raw_claims(evidence_run: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    structured = (
        _mapping(evidence_run.get("artifacts"))
        .get("response", {})
        .get("payload", {})
        .get("structured_output", {})
    )
    return {
        str(row["claim_id"]): _mapping(row)
        for row in _list(_mapping(structured).get("claims"))
        if isinstance(row, Mapping) and row.get("claim_id")
    }


def _claim_entities(validated: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in _list(validated.get("claim_entities")):
        if not isinstance(row, Mapping):
            continue
        claim_id = str(row.get("claim_id", ""))
        entity_uid = str(row.get("entity_uid", ""))
        if claim_id and entity_uid:
            result[claim_id] = entity_uid
    return result


def _signal_claims(validated: Mapping[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for row in _list(validated.get("signals")):
        if not isinstance(row, Mapping) or not row.get("signal_id"):
            continue
        result[str(row["signal_id"])] = sorted(
            {
                str(claim_id)
                for claim_id in _list(row.get("claim_ids"))
                if claim_id
            }
        )
    return result


def _resolve_claim_refs(
    refs: Iterable[Any],
    *,
    known_claim_ids: set[str],
    signal_claims: Mapping[str, Sequence[str]],
) -> list[str]:
    result: set[str] = set()
    for raw_ref in refs:
        ref = str(raw_ref)
        if ref in known_claim_ids:
            result.add(ref)
        result.update(str(value) for value in signal_claims.get(ref, []))
    return sorted(result)


def _proposal_claims(
    *,
    evidence_run: Mapping[str, Any],
    validated: Mapping[str, Any],
    known_claim_ids: set[str],
    signal_claims: Mapping[str, Sequence[str]],
) -> tuple[dict[str, list[str]], dict[str, dict[str, Any]]]:
    raw_structured = (
        _mapping(evidence_run.get("artifacts"))
        .get("response", {})
        .get("payload", {})
        .get("structured_output", {})
    )
    raw_by_id = {
        str(row["adjustment_id"]): _mapping(row)
        for row in _list(_mapping(raw_structured).get("proposed_adjustments"))
        if isinstance(row, Mapping) and row.get("adjustment_id")
    }
    result: dict[str, list[str]] = {}
    proposals: dict[str, dict[str, Any]] = {}
    for row in _list(validated.get("proposed_adjustments")):
        if not isinstance(row, Mapping) or not row.get("adjustment_id"):
            continue
        adjustment_id = str(row["adjustment_id"])
        proposal = _mapping(row)
        raw = raw_by_id.get(adjustment_id, {})
        refs = [
            *_list(proposal.get("claim_ids")),
            *_list(proposal.get("signal_ids")),
            *_list(raw.get("claim_ids")),
            *_list(raw.get("signal_ids")),
        ]
        result[adjustment_id] = _resolve_claim_refs(
            refs,
            known_claim_ids=known_claim_ids,
            signal_claims=signal_claims,
        )
        proposals[adjustment_id] = proposal
    return result, proposals


def _applied_claims(
    *,
    adapter_audit: Mapping[str, Any],
    proposal_claims: Mapping[str, Sequence[str]],
    known_claim_ids: set[str],
    signal_claims: Mapping[str, Sequence[str]],
) -> tuple[dict[str, list[str]], dict[str, dict[str, Any]]]:
    if not bool(adapter_audit.get("applied", False)):
        return {}, {}
    result: dict[str, list[str]] = {}
    adjustments: dict[str, dict[str, Any]] = {}
    for row in _list(adapter_audit.get("adjustments")):
        if not isinstance(row, Mapping) or not row.get("adjustment_id"):
            continue
        adjustment_id = str(row["adjustment_id"])
        refs = _resolve_claim_refs(
            _list(row.get("claim_ids")),
            known_claim_ids=known_claim_ids,
            signal_claims=signal_claims,
        )
        if not refs:
            refs = sorted(set(proposal_claims.get(adjustment_id, [])))
        result[adjustment_id] = refs
        adjustments[adjustment_id] = _mapping(row)
    return result, adjustments


def _reverse_adjustment_links(
    links: Mapping[str, Sequence[str]],
) -> dict[str, list[str]]:
    result: defaultdict[str, list[str]] = defaultdict(list)
    for adjustment_id, claim_ids in links.items():
        for claim_id in claim_ids:
            result[str(claim_id)].append(str(adjustment_id))
    return {
        claim_id: sorted(set(adjustment_ids))
        for claim_id, adjustment_ids in result.items()
    }


def _player_minutes(outcome: Mapping[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in _list(outcome.get("aggregated_players")):
        if not isinstance(row, Mapping) or not row.get("player_id"):
            continue
        minutes = row.get("minutes")
        if isinstance(minutes, bool) or not isinstance(minutes, int):
            continue
        result[str(row["player_id"])] = minutes
    return result


def _zero_minutes_target(row: Mapping[str, Any]) -> bool:
    target = str(row.get("target", ""))
    if target not in {"expected_minutes", "start_probability"}:
        return False
    after = row.get("after_value")
    if after is None and isinstance(row.get("after"), Mapping):
        after = row["after"].get(target)
    return (
        not isinstance(after, bool)
        and isinstance(after, (int, float))
        and float(after) == 0.0
    )


def _verification(
    *,
    player_uid: str | None,
    actual_minutes: int | None,
    minutes_source: str,
    proposal_ids: Sequence[str],
    proposals: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    zero_targets = sorted(
        adjustment_id
        for adjustment_id in proposal_ids
        if _zero_minutes_target(proposals.get(adjustment_id, {}))
    )
    if not player_uid:
        return {
            "status": "unavailable",
            "basis": "claim_has_no_player_binding",
            "actual_minutes": None,
            "minutes_source": minutes_source,
            "tested_adjustment_ids": zero_targets,
        }
    if actual_minutes is None:
        return {
            "status": "unavailable",
            "basis": "post_match_minutes_missing",
            "actual_minutes": None,
            "minutes_source": minutes_source,
            "tested_adjustment_ids": zero_targets,
        }
    if not zero_targets:
        return {
            "status": "indeterminate",
            "basis": "minutes_observed_but_claim_has_no_binary_zero_minutes_assertion",
            "actual_minutes": actual_minutes,
            "minutes_source": minutes_source,
            "tested_adjustment_ids": [],
        }
    return {
        "status": "verified" if actual_minutes == 0 else "contradicted",
        "basis": "binary_zero_minutes_assertion_vs_realised_minutes",
        "actual_minutes": actual_minutes,
        "minutes_source": minutes_source,
        "tested_adjustment_ids": zero_targets,
    }


def _claim_class(
    claim: Mapping[str, Any],
    proposal_ids: Sequence[str],
    proposals: Mapping[str, Mapping[str, Any]],
) -> dict[str, str]:
    explicit = claim.get("claim_type") or claim.get("claim_class")
    if isinstance(explicit, str) and explicit:
        return {"value": explicit, "basis": "recorded"}
    targets = {
        str(proposals.get(adjustment_id, {}).get("target", ""))
        for adjustment_id in proposal_ids
    }
    if targets.intersection({"expected_minutes", "start_probability"}):
        return {
            "value": "player_availability",
            "basis": "derived_from_adjustment_target",
        }
    return {
        "value": "unclassified_historical",
        "basis": "not_recorded",
    }


def _source_metadata(
    claim: Mapping[str, Any],
    raw_claim: Mapping[str, Any],
    document: Mapping[str, Any],
) -> dict[str, Any]:
    rights = _mapping(claim.get("source_rights"))
    source_ids = _list(_mapping(claim.get("provenance")).get("source_ids"))
    source_id = (
        claim.get("source_id")
        or raw_claim.get("source_id")
        or document.get("source_id")
        or (source_ids[0] if source_ids else None)
    )
    family = (
        claim.get("source_family_id")
        or claim.get("source_family")
        or rights.get("source_family_id")
    )
    authority = claim.get("source_authority") or rights.get("authority")
    return {
        "source_id": str(source_id) if source_id else None,
        "source_family_id": str(family) if family else None,
        "source_family_status": "recorded" if family else "not_recorded",
        "authority": str(authority) if authority else None,
        "authority_status": "recorded" if authority else "not_recorded",
    }


def _document_lookup(host_bundle: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row["document_id"]): _mapping(row)
        for row in _list(host_bundle.get("evidence_documents"))
        if isinstance(row, Mapping) and row.get("document_id")
    }


def _plan_change(
    attribution: Mapping[str, Any] | None,
) -> tuple[bool | None, int | None]:
    if attribution is None:
        return None, None
    agent_hash = attribution.get("agent_plan_sha256")
    control_hash = attribution.get("control_plan_sha256")
    delta = attribution.get("agent_evidence_delta")
    if isinstance(delta, bool) or not isinstance(delta, int):
        raise ClaimValueLedgerError(
            "same-state-attribution agent_evidence_delta must be an integer"
        )
    return bool(agent_hash != control_hash), delta


def _binding(
    *,
    run: ClaimValueRun,
    name: str,
    artifact: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "source_ref": f"{run.source_ref}/{name}",
        "content_sha256": str(artifact["content_sha256"]),
    }


def _sealed_episode_minutes(
    run: ClaimValueRun,
    replay_outcome: Mapping[str, Any],
) -> tuple[dict[str, int] | None, list[dict[str, Any]]]:
    if run.verification_root is None:
        return None, []
    manifest_path = run.verification_root / "episode-manifest.json"
    hidden_path = run.verification_root / "hidden-outcome.json"
    manifest = _read_unsealed_object(manifest_path)
    hidden = _read_unsealed_object(hidden_path)
    hidden_hash = artifact_hash(hidden)
    manifest_hidden_hash = str(
        _mapping(manifest.get("hidden_outcome_ref")).get("content_sha256", "")
    )
    replay_hidden_hash = str(replay_outcome.get("source_outcome_sha256", ""))
    if not manifest_hidden_hash or hidden_hash != manifest_hidden_hash:
        raise ClaimValueLedgerError(
            f"Hidden outcome is not bound by its episode manifest: {hidden_path}"
        )
    if replay_hidden_hash and replay_hidden_hash != hidden_hash:
        raise ClaimValueLedgerError(
            f"Replay outcome is bound to a different hidden outcome: {run.source_ref}"
        )
    minutes: defaultdict[str, int] = defaultdict(int)
    for row in _list(hidden.get("player_outcomes")):
        if not isinstance(row, Mapping):
            continue
        element = row.get("element")
        value = row.get("minutes")
        if (
            isinstance(element, bool)
            or not isinstance(element, int)
            or isinstance(value, bool)
            or not isinstance(value, int)
        ):
            continue
        minutes[f"player:2025-26:{element}"] += value
    source_ref = run.verification_source_ref or (
        f"sealed_episode/gw-{run.gameweek:02d}"
    )
    bindings = [
        {
            "source_ref": f"{source_ref}/episode-manifest.json",
            "content_sha256": artifact_hash(manifest),
        },
        {
            "source_ref": f"{source_ref}/hidden-outcome.json",
            "content_sha256": hidden_hash,
        },
    ]
    return dict(minutes), bindings


def _extract_run(
    run: ClaimValueRun,
) -> tuple[
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
]:
    loaded: dict[str, dict[str, Any] | None] = {}
    for name in _ARTIFACT_NAMES:
        loaded[name] = _read_object(
            run.root / name,
            required=name != "same-state-attribution.json",
        )
    host_bundle = loaded["host-bundle.json"] or {}
    evidence_run = loaded["evidence-run.json"] or {}
    adapter_audit = loaded["adapter-audit.json"] or {}
    comparison = loaded["comparison.json"] or {}
    attribution = loaded["same-state-attribution.json"]
    outcome = loaded["realised-outcome.json"] or {}
    if int(comparison.get("gameweek", -1)) != run.gameweek:
        raise ClaimValueLedgerError(
            f"Comparison gameweek mismatch in {run.source_ref}"
        )

    validated = _mapping(evidence_run.get("validated_output"))
    claims = [
        _mapping(row)
        for row in _list(validated.get("claims"))
        if isinstance(row, Mapping) and row.get("claim_id")
    ]
    known_claim_ids = {str(row["claim_id"]) for row in claims}
    raw_claims = _raw_claims(evidence_run)
    entities = _claim_entities(validated)
    signal_claims = _signal_claims(validated)
    proposal_claims, proposals = _proposal_claims(
        evidence_run=evidence_run,
        validated=validated,
        known_claim_ids=known_claim_ids,
        signal_claims=signal_claims,
    )
    applied_claims, applied_adjustments = _applied_claims(
        adapter_audit=adapter_audit,
        proposal_claims=proposal_claims,
        known_claim_ids=known_claim_ids,
        signal_claims=signal_claims,
    )
    proposals_by_claim = _reverse_adjustment_links(proposal_claims)
    applied_by_claim = _reverse_adjustment_links(applied_claims)
    documents = _document_lookup(host_bundle)
    sealed_minutes, verification_bindings = _sealed_episode_minutes(run, outcome)
    if sealed_minutes is None:
        minutes_by_player = _player_minutes(outcome)
        minutes_source = "scored_squad_realised_outcome"
    else:
        minutes_by_player = sealed_minutes
        minutes_source = "sealed_all_player_hidden_outcome"
    plan_changed, paired_delta = _plan_change(attribution)
    decision_at = (
        _mapping(evidence_run.get("trace")).get("decision_cutoff")
        or _mapping(host_bundle.get("episode")).get("decision_at")
    )
    evidence_mode = (
        validated.get("evidence_mode")
        or host_bundle.get("evidence_mode")
        or _mapping(evidence_run.get("trace")).get("run_mode")
    )

    claim_rows: list[dict[str, Any]] = []
    for claim in sorted(claims, key=lambda row: str(row["claim_id"])):
        claim_id = str(claim["claim_id"])
        raw_claim = raw_claims.get(claim_id, {})
        document_id = str(
            claim.get("document_id") or raw_claim.get("document_id") or ""
        )
        document = documents.get(document_id, {})
        player_uid = (
            entities.get(claim_id)
            or raw_claim.get("player_uid")
            or claim.get("player_uid")
        )
        player_uid = str(player_uid) if player_uid else None
        proposal_ids = proposals_by_claim.get(claim_id, [])
        applied_ids = applied_by_claim.get(claim_id, [])
        citation_passage = raw_claim.get("passage_id")
        citation_excerpt = raw_claim.get("citation_excerpt")
        cited = bool(
            document_id
            and document_id in documents
            and (citation_passage or citation_excerpt)
        )
        source = _source_metadata(claim, raw_claim, document)
        claim_rows.append(
            {
                "claim_id": claim_id,
                "arm": run.arm,
                "gameweek": run.gameweek,
                "namespace": run.namespace,
                "claim_text": str(
                    claim.get("claim_text") or raw_claim.get("claim_text") or ""
                ),
                "claim_class": _claim_class(claim, proposal_ids, proposals),
                "source": source,
                "confidence": claim.get("confidence", raw_claim.get("confidence")),
                "published_at": claim.get(
                    "published_at", document.get("published_at")
                ),
                "observed_at": claim.get(
                    "observed_at", document.get("observed_at")
                ),
                "available_at": claim.get(
                    "available_at", document.get("available_at")
                ),
                "expires_at": claim.get("expires_at", raw_claim.get("expires_at")),
                "decision_at": decision_at,
                "age_at_deadline_hours": _age_hours(
                    claim.get("published_at", document.get("published_at")),
                    decision_at,
                ),
                "evidence_mode": evidence_mode,
                "production_eligible": _mapping(
                    claim.get("decision_eligibility")
                ).get("production_eligible", validated.get("production_eligible")),
                "retrospective_caveat": evidence_mode
                == "retrospective_published_before_deadline",
                "player_uid": player_uid,
                "retrieval": {
                    "document_id": document_id or None,
                    "retrieved_into_host_bundle": document_id in documents,
                },
                "citation": {
                    "cited_by_agent": cited,
                    "passage_id": str(citation_passage)
                    if citation_passage
                    else None,
                    "citation_excerpt_sha256": raw_claim.get(
                        "citation_excerpt_sha256"
                    ),
                },
                "proposal": {
                    "proposed": bool(proposal_ids),
                    "adjustment_ids": proposal_ids,
                },
                "application": {
                    "applied": bool(applied_ids),
                    "adjustment_ids": applied_ids,
                    "application_group_id": (
                        f"{run.arm}:gw-{run.gameweek:02d}:{run.namespace}"
                    ),
                    "plan_changed": plan_changed,
                    "paired_delta_scope": "gameweek_arm_not_claim",
                },
                "verification": _verification(
                    player_uid=player_uid,
                    actual_minutes=minutes_by_player.get(player_uid)
                    if player_uid
                    else None,
                    minutes_source=minutes_source,
                    proposal_ids=proposal_ids,
                    proposals=proposals,
                ),
            }
        )

    applied_ids = sorted(
        {
            claim_id
            for claim_ids in applied_claims.values()
            for claim_id in claim_ids
        }
    )
    application_group = {
        "application_group_id": f"{run.arm}:gw-{run.gameweek:02d}:{run.namespace}",
        "arm": run.arm,
        "gameweek": run.gameweek,
        "namespace": run.namespace,
        "adapter_applied": bool(adapter_audit.get("applied", False)),
        "fallback_reason": adapter_audit.get("fallback_reason"),
        "applied_adjustment_ids": sorted(applied_adjustments),
        "applied_claim_ids": applied_ids,
        "plan_changed": plan_changed,
        "paired_same_state_delta": paired_delta,
        "paired_delta_scope": "gameweek_arm",
        "attribution_available": attribution is not None,
    }
    gameweek = {
        "arm": run.arm,
        "gameweek": run.gameweek,
        "namespace": run.namespace,
        "run_status": evidence_run.get("status"),
        "claim_count": len(claim_rows),
        "retrieved_claim_count": sum(
            bool(row["retrieval"]["retrieved_into_host_bundle"])
            for row in claim_rows
        ),
        "cited_claim_count": sum(
            bool(row["citation"]["cited_by_agent"]) for row in claim_rows
        ),
        "proposed_claim_count": sum(
            bool(row["proposal"]["proposed"]) for row in claim_rows
        ),
        "applied_claim_count": sum(
            bool(row["application"]["applied"]) for row in claim_rows
        ),
        "adapter_applied": bool(adapter_audit.get("applied", False)),
        "plan_changed": plan_changed,
        "paired_same_state_delta": paired_delta,
        "application_group_id": application_group["application_group_id"],
    }
    bindings = [
        _binding(run=run, name=name, artifact=artifact)
        for name, artifact in loaded.items()
        if artifact is not None
    ]
    bindings.extend(verification_bindings)
    return claim_rows, application_group, gameweek, bindings


def _zero_gameweek(arm: str, gameweek: int, status: str) -> dict[str, Any]:
    return {
        "arm": arm,
        "gameweek": gameweek,
        "namespace": None,
        "run_status": status,
        "claim_count": 0,
        "retrieved_claim_count": 0,
        "cited_claim_count": 0,
        "proposed_claim_count": 0,
        "applied_claim_count": 0,
        "adapter_applied": False,
        "plan_changed": None,
        "paired_same_state_delta": None,
        "application_group_id": None,
    }


def _arm_summary(
    arm: str, gameweeks: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    rows = [row for row in gameweeks if row.get("arm") == arm]
    paired = [
        row
        for row in rows
        if isinstance(row.get("paired_same_state_delta"), int)
        and not isinstance(row.get("paired_same_state_delta"), bool)
    ]
    return {
        "arm": arm,
        "gameweek_count": len(rows),
        "evidence_run_count": sum(
            row.get("run_status") not in {"not_applicable_seed", "missing"}
            for row in rows
        ),
        "claim_count": sum(int(row.get("claim_count", 0)) for row in rows),
        "applied_week_count": sum(
            bool(row.get("adapter_applied")) for row in rows
        ),
        "plan_changed_week_count": sum(
            row.get("plan_changed") is True for row in rows
        ),
        "paired_week_count": len(paired),
        "paired_same_state_sum": sum(
            int(row["paired_same_state_delta"]) for row in paired
        ),
        "nonzero_paired_gameweeks": [
            int(row["gameweek"])
            for row in paired
            if int(row["paired_same_state_delta"]) != 0
        ],
    }


def _group_rollups(
    claims: Sequence[Mapping[str, Any]],
    application_groups: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    buckets: defaultdict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(
        list
    )
    claim_bucket: dict[str, tuple[str, str]] = {}
    for claim in claims:
        claim_class = str(
            _mapping(claim.get("claim_class")).get(
                "value", "unclassified_historical"
            )
        )
        source_family = str(
            _mapping(claim.get("source")).get("source_family_id")
            or "unavailable"
        )
        key = (claim_class, source_family)
        buckets[key].append(claim)
        claim_bucket[str(claim["claim_id"])] = key

    exclusive: defaultdict[tuple[str, str], list[int]] = defaultdict(list)
    shared: defaultdict[tuple[str, str], int] = defaultdict(int)
    for group in application_groups:
        applied_ids = [str(value) for value in _list(group.get("applied_claim_ids"))]
        group_buckets = {
            claim_bucket[claim_id]
            for claim_id in applied_ids
            if claim_id in claim_bucket
        }
        delta = group.get("paired_same_state_delta")
        if len(group_buckets) == 1 and isinstance(delta, int) and not isinstance(
            delta, bool
        ):
            exclusive[next(iter(group_buckets))].append(delta)
        elif len(group_buckets) > 1:
            for key in group_buckets:
                shared[key] += 1

    result: list[dict[str, Any]] = []
    for key in sorted(buckets):
        rows = buckets[key]
        verification_counts: defaultdict[str, int] = defaultdict(int)
        for row in rows:
            verification_counts[
                str(_mapping(row.get("verification")).get("status", "unavailable"))
            ] += 1
        deltas = exclusive.get(key, [])
        result.append(
            {
                "claim_class": key[0],
                "source_family_id": None if key[1] == "unavailable" else key[1],
                "claim_count": len(rows),
                "retrieved_count": sum(
                    bool(_mapping(row.get("retrieval")).get(
                        "retrieved_into_host_bundle"
                    ))
                    for row in rows
                ),
                "cited_count": sum(
                    bool(_mapping(row.get("citation")).get("cited_by_agent"))
                    for row in rows
                ),
                "proposed_count": sum(
                    bool(_mapping(row.get("proposal")).get("proposed"))
                    for row in rows
                ),
                "applied_count": sum(
                    bool(_mapping(row.get("application")).get("applied"))
                    for row in rows
                ),
                "verification_counts": dict(sorted(verification_counts.items())),
                "exclusive_application_group_count": len(deltas),
                "exclusive_group_paired_same_state_sum": sum(deltas),
                "shared_application_group_count": shared.get(key, 0),
                "delta_note": (
                    "Paired deltas are counted only for application groups whose "
                    "applied claims all belong to this bucket."
                ),
            }
        )
    return result


def build_claim_value_ledger(
    *,
    report_id: str,
    season: str,
    mode: str,
    runs: Sequence[ClaimValueRun],
    expected_gameweeks: Mapping[str, Sequence[int]],
    zero_statuses: Mapping[tuple[str, int], str] | None = None,
    caveats: Sequence[str] = (),
) -> dict[str, Any]:
    """Build a sealed report from explicit replay decision namespaces."""

    if not report_id or not season or not mode:
        raise ClaimValueLedgerError("report_id, season and mode are required")
    seen = {(run.arm, run.gameweek) for run in runs}
    if len(seen) != len(runs):
        raise ClaimValueLedgerError("Duplicate arm/gameweek run specifications")
    expected = {
        (str(arm), int(gameweek))
        for arm, gameweeks in expected_gameweeks.items()
        for gameweek in gameweeks
    }
    unexpected = sorted(seen - expected)
    if unexpected:
        raise ClaimValueLedgerError(f"Unexpected run specifications: {unexpected}")

    claims: list[dict[str, Any]] = []
    groups: list[dict[str, Any]] = []
    gameweeks: list[dict[str, Any]] = []
    bindings: list[dict[str, Any]] = []
    for run in sorted(runs, key=lambda item: (item.arm, item.gameweek)):
        run_claims, group, week, run_bindings = _extract_run(run)
        claims.extend(run_claims)
        groups.append(group)
        gameweeks.append(week)
        bindings.extend(run_bindings)

    zero_statuses = dict(zero_statuses or {})
    for arm, gameweek in sorted(expected - seen):
        gameweeks.append(
            _zero_gameweek(
                arm,
                gameweek,
                zero_statuses.get((arm, gameweek), "missing"),
            )
        )
    gameweeks.sort(key=lambda row: (str(row["arm"]), int(row["gameweek"])))
    claims.sort(
        key=lambda row: (
            str(row["arm"]),
            int(row["gameweek"]),
            str(row["claim_id"]),
        )
    )
    groups.sort(
        key=lambda row: (
            str(row["arm"]),
            int(row["gameweek"]),
            str(row["namespace"]),
        )
    )
    bindings.sort(key=lambda row: str(row["source_ref"]))
    arms = sorted(expected_gameweeks)
    summaries = [_arm_summary(arm, gameweeks) for arm in arms]
    nonzero_union = sorted(
        {
            int(gameweek)
            for summary in summaries
            for gameweek in summary["nonzero_paired_gameweeks"]
        }
    )
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "report_id": report_id,
        "season": season,
        "mode": mode,
        "read_only": True,
        "policy_effect": "none",
        "causal_scope": {
            "claim_rows": "lifecycle_and_application_participation",
            "paired_deltas": "gameweek_arm_application_group",
            "claim_level_delta_allocation": "prohibited",
        },
        "caveats": sorted(set(str(value) for value in caveats)),
        "input_bindings": bindings,
        "claims": claims,
        "application_groups": groups,
        "gameweeks": gameweeks,
        "rollups": {
            "arms": summaries,
            "nonzero_paired_gameweeks_union": nonzero_union,
            "claim_class_source_family": _group_rollups(claims, groups),
        },
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def enhanced_factorial_runs(
    *,
    enhanced_root: Path,
    early_evidence_root: Path,
    episode_root: Path | None = None,
) -> list[ClaimValueRun]:
    """Return the two evidence arms in their exact published composition."""

    result: list[ClaimValueRun] = []
    early_longitudinal = early_evidence_root / "longitudinal"
    for gameweek in range(2, 12):
        result.append(
            ClaimValueRun(
                arm="scout_evidence",
                gameweek=gameweek,
                root=early_longitudinal / f"gw-{gameweek:02d}",
                source_ref=f"early_longitudinal/gw-{gameweek:02d}",
                namespace="longitudinal",
                verification_root=(
                    episode_root / f"gw-{gameweek:02d}"
                    if episode_root is not None
                    else None
                ),
                verification_source_ref=f"episodes-v1/gw-{gameweek:02d}",
            )
        )
    for gameweek in range(12, 39):
        result.append(
            ClaimValueRun(
                arm="scout_evidence",
                gameweek=gameweek,
                root=(
                    enhanced_root
                    / "arms"
                    / "scout_evidence"
                    / f"gw-{gameweek:02d}"
                ),
                source_ref=f"enhanced/scout_evidence/gw-{gameweek:02d}",
                namespace="enhanced",
                verification_root=(
                    episode_root / f"gw-{gameweek:02d}"
                    if episode_root is not None
                    else None
                ),
                verification_source_ref=f"episodes-v1/gw-{gameweek:02d}",
            )
        )
    for gameweek in range(2, 39):
        result.append(
            ClaimValueRun(
                arm="optimized_evidence",
                gameweek=gameweek,
                root=(
                    enhanced_root
                    / "arms"
                    / "optimized_evidence"
                    / f"gw-{gameweek:02d}"
                ),
                source_ref=f"enhanced/optimized_evidence/gw-{gameweek:02d}",
                namespace="enhanced",
                verification_root=(
                    episode_root / f"gw-{gameweek:02d}"
                    if episode_root is not None
                    else None
                ),
                verification_source_ref=f"episodes-v1/gw-{gameweek:02d}",
            )
        )
    return result


def build_enhanced_factorial_ledger(
    *,
    enhanced_root: Path,
    early_evidence_root: Path,
    episode_root: Path | None = None,
) -> dict[str, Any]:
    """Build the published two-arm enhanced factorial accounting report."""

    arms = ("scout_evidence", "optimized_evidence")
    return build_claim_value_ledger(
        report_id="claim-value:2025-26:enhanced-factorial",
        season="2025-26",
        mode="enhanced_factorial",
        runs=enhanced_factorial_runs(
            enhanced_root=enhanced_root,
            early_evidence_root=early_evidence_root,
            episode_root=episode_root,
        ),
        expected_gameweeks={arm: list(range(1, 39)) for arm in arms},
        zero_statuses={(arm, 1): "not_applicable_seed" for arm in arms},
        caveats=(
            "Evidence was recovered retrospectively but published before the "
            "historical deadline; it is exploratory and production-ineligible.",
            "The Scout arm composes early longitudinal GW2-GW11 with enhanced "
            "GW12-GW38 artifacts.",
            "Historical source family and registry authority are reported as "
            "unavailable when the frozen claim did not record them.",
        ),
    )


def accepted_agent_fork_runs(
    agent_fork_root: Path,
    *,
    episode_root: Path | None = None,
) -> list[ClaimValueRun]:
    """Select the highest completed evidence+challenger namespace per GW."""

    result: list[ClaimValueRun] = []
    for gameweek_root in sorted(agent_fork_root.iterdir()):
        match = _GAMEWEEK_RE.match(gameweek_root.name)
        if not gameweek_root.is_dir() or match is None:
            continue
        gameweek = int(match.group(1))
        candidates: list[tuple[int, Path]] = []
        for solution_root in gameweek_root.iterdir():
            solution_match = _SOLUTION_RE.match(solution_root.name)
            if not solution_root.is_dir() or solution_match is None:
                continue
            evidence = _read_object(
                solution_root / "evidence-run.json", required=False
            )
            challenger = _read_object(
                solution_root / "challenger-run.json", required=False
            )
            comparison = _read_object(
                solution_root / "comparison.json", required=False
            )
            if (
                evidence is not None
                and challenger is not None
                and comparison is not None
                and evidence.get("status") == "completed"
                and challenger.get("status") == "completed"
            ):
                candidates.append((int(solution_match.group(1)), solution_root))
        if not candidates:
            raise ClaimValueLedgerError(
                f"No completed accepted namespace for {gameweek_root.name}"
            )
        _, selected = max(candidates, key=lambda item: item[0])
        result.append(
            ClaimValueRun(
                arm="agent_fork",
                gameweek=gameweek,
                root=selected,
                source_ref=f"agent_fork/{gameweek_root.name}/{selected.name}",
                namespace=selected.name,
                verification_root=(
                    episode_root / gameweek_root.name
                    if episode_root is not None
                    else None
                ),
                verification_source_ref=f"episodes-v1/{gameweek_root.name}",
            )
        )
    return result


def build_agent_fork_ledger(
    *,
    agent_fork_root: Path,
    episode_root: Path | None = None,
) -> dict[str, Any]:
    """Build the accepted GW12-GW38 agent-fork accounting report."""

    return build_claim_value_ledger(
        report_id="claim-value:2025-26:agent-fork",
        season="2025-26",
        mode="accepted_agent_fork",
        runs=accepted_agent_fork_runs(
            agent_fork_root,
            episode_root=episode_root,
        ),
        expected_gameweeks={"agent_fork": list(range(12, 39))},
        caveats=(
            "Evidence was recovered retrospectively but published before the "
            "historical deadline; it is exploratory and production-ineligible.",
            "GW12 has no paired same-state artifact; direct paired attribution "
            "therefore covers GW13-GW38 only.",
            "Accepted retries are selected as the highest sol-vN namespace with "
            "completed evidence and challenger runs plus a comparison.",
        ),
    )


def claim_value_report_bytes(report: Mapping[str, Any]) -> bytes:
    """Return byte-stable, human-readable JSON for a sealed report."""

    if report.get("content_sha256") != artifact_hash(report):
        raise ClaimValueLedgerError("Claim-value report hash mismatch")
    return (
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def write_claim_value_report(path: Path, report: Mapping[str, Any]) -> bool:
    """Write once; return False when identical bytes already exist."""

    payload = claim_value_report_bytes(report)
    if path.exists():
        if path.read_bytes() != payload:
            raise ClaimValueLedgerError(
                f"Refusing to overwrite different claim-value report: {path}"
            )
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return True
