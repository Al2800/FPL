"""Coverage, retrieval-quality, and downstream evidence-plane evaluation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import math
from typing import Any

from src.evidence.live_evidence_ledger import live_evidence_hash
from src.forecasting.live_faithful import artifact_hash


class EvidenceCoverageError(ValueError):
    """Raised when evidence coverage cannot be measured faithfully."""


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def _rate(numerator: int, denominator: int) -> float:
    return 1.0 if denominator == 0 else round(numerator / denominator, 6)


def _checkpoint(config: Mapping[str, Any], checkpoint_id: str) -> dict[str, Any]:
    matches = [
        row
        for row in config.get("checkpoints", [])
        if row.get("checkpoint_id") == checkpoint_id
    ]
    if len(matches) != 1:
        raise EvidenceCoverageError(
            f"Unknown or duplicate checkpoint: {checkpoint_id}"
        )
    return deepcopy(dict(matches[0]))


def _selected_claim_ids(packet: Mapping[str, Any]) -> list[str]:
    result = []
    for row in packet.get("evidence", []):
        claim = row.get("claim", row)
        claim_id = str(claim.get("claim_id", ""))
        if claim_id:
            result.append(claim_id)
    return sorted(set(result))


def build_evidence_coverage_report(
    *,
    checkpoint_id: str,
    decision_at: str,
    config: Mapping[str, Any],
    acquisition_funnel: Mapping[str, Any],
    evidence_view: Mapping[str, Any],
    packet: Mapping[str, Any],
    expected_club_ids: Sequence[str],
    expected_player_ids: Sequence[str],
    accepted_adjustments: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Measure distinct acquisition, ledger, retrieval and adjustment planes."""

    if acquisition_funnel.get("content_sha256") != artifact_hash(
        acquisition_funnel
    ):
        raise EvidenceCoverageError("Acquisition funnel hash mismatch")
    if evidence_view.get("content_sha256") != live_evidence_hash(
        evidence_view
    ):
        raise EvidenceCoverageError("Evidence view hash mismatch")
    if packet.get("content_sha256") != artifact_hash(packet):
        raise EvidenceCoverageError("Evidence packet hash mismatch")
    checkpoint = _checkpoint(config, checkpoint_id)
    required = set(checkpoint["required_source_families"])
    observations = [
        deepcopy(dict(row))
        for row in acquisition_funnel.get("observations", [])
    ]
    by_family = {str(row["family_id"]): row for row in observations}
    covered_required = {
        family_id
        for family_id in required
        if by_family.get(family_id, {}).get("status") == "complete"
    }
    automated = [row for row in observations if row.get("automated")]
    automated_complete = [
        row for row in automated if row.get("status") == "complete"
    ]
    observed_clubs = {
        str(value)
        for row in observations
        for value in row.get("observed_club_ids", [])
    }
    observed_players = {
        str(value)
        for row in observations
        for value in row.get("observed_player_ids", [])
    }
    expected_clubs = set(str(value) for value in expected_club_ids)
    expected_players = set(str(value) for value in expected_player_ids)
    raw_documents = sum(int(row.get("document_count", 0)) for row in observations)
    raw_claims = sum(int(row.get("raw_claim_count", 0)) for row in observations)
    added_claims = sum(
        int(row.get("claim_count_added", 0)) for row in observations
    )
    active_claims = len(evidence_view.get("accepted", []))
    retrieved_ids = _selected_claim_ids(packet)
    excluded = evidence_view.get("excluded", {})
    omitted = packet.get("omitted", {})
    stale_families = sorted(
        str(row["family_id"])
        for row in observations
        if not bool(row.get("fresh", False))
    )

    required_rate = _rate(len(covered_required), len(required))
    automated_rate = _rate(len(automated_complete), len(automated))
    club_rate = _rate(
        len(expected_clubs.intersection(observed_clubs)),
        len(expected_clubs),
    )
    player_rate = _rate(
        len(expected_players.intersection(observed_players)),
        len(expected_players),
    )
    sla = config["coverage_sla"]
    sla_checks = {
        "required_source_family_rate": required_rate
        >= float(sla["minimum_required_source_family_rate"]),
        "automated_source_success_rate": automated_rate
        >= float(sla["minimum_automated_source_success_rate"]),
        "expected_club_observation_rate": club_rate
        >= float(sla["minimum_expected_club_observation_rate"]),
        "expected_player_observation_rate": player_rate
        >= float(sla["minimum_expected_player_observation_rate"]),
    }
    gaps = sorted(set(str(value) for value in acquisition_funnel.get("gaps", [])))
    status = (
        "complete"
        if all(sla_checks.values()) and not gaps and not stale_families
        else "degraded"
    )
    return _seal(
        {
            "schema_version": "1.0",
            "checkpoint_id": checkpoint_id,
            "decision_at": str(decision_at),
            "status": status,
            "input_bindings": {
                "acquisition_funnel_sha256": acquisition_funnel[
                    "content_sha256"
                ],
                "evidence_view_sha256": evidence_view["content_sha256"],
                "packet_sha256": packet["content_sha256"],
            },
            "silence_interpretation": str(
                sla.get("silence_interpretation", "unknown_not_available")
            ),
            "planes": {
                "raw_acquisitions": len(automated),
                "raw_documents": raw_documents,
                "raw_claims": raw_claims,
                "deduplicated_claims_added": added_claims,
                "active_claims": active_claims,
                "retrieved_claims": len(retrieved_ids),
                "accepted_adjustments": len(accepted_adjustments),
            },
            "deduplication": {
                "duplicate_claims": max(0, raw_claims - added_claims),
                "duplicate_rate": _rate(
                    max(0, raw_claims - added_claims), raw_claims
                ),
            },
            "source_coverage": {
                "required_family_ids": sorted(required),
                "covered_required_family_ids": sorted(covered_required),
                "missing_required_family_ids": sorted(
                    required - covered_required
                ),
                "required_family_rate": required_rate,
                "source_attempt_count": len(observations),
                "successful_source_count": sum(
                    row.get("status") == "complete" for row in observations
                ),
                "automated_success_rate": automated_rate,
                "stale_family_ids": stale_families,
                "gaps": gaps,
            },
            "entity_coverage": {
                "club_rate": club_rate,
                "player_rate": player_rate,
                "observed_club_ids": sorted(observed_clubs),
                "observed_player_ids": sorted(observed_players),
                "unobserved_club_ids": sorted(
                    expected_clubs - observed_clubs
                ),
                "unobserved_player_ids": sorted(
                    expected_players - observed_players
                ),
            },
            "ledger": {
                "active": active_claims,
                "conflicts": len(evidence_view.get("conflicts", [])),
                "future": len(excluded.get("future", [])),
                "expired": len(excluded.get("expired", [])),
                "superseded": len(excluded.get("superseded", [])),
                "quarantined": len(excluded.get("quarantined", [])),
            },
            "retrieval": {
                "selected_claim_ids": retrieved_ids,
                "omission_counts": {
                    key: len(value) for key, value in omitted.items()
                },
            },
            "adjustments": {
                "accepted_count": len(accepted_adjustments),
                "plan_change_count": sum(
                    bool(row.get("plan_changed"))
                    for row in accepted_adjustments
                ),
                "revealed_score_delta": sum(
                    int(row.get("score_delta", 0))
                    for row in accepted_adjustments
                    if row.get("score_delta") is not None
                ),
            },
            "sla_checks": sla_checks,
        }
    )


def evaluate_retrieval_golden(
    *,
    packet: Mapping[str, Any],
    relevant_claim_ids: Sequence[str],
    irrelevant_claim_ids: Sequence[str],
    latency_ms: float,
    maximum_latency_ms: float,
) -> dict[str, Any]:
    """Evaluate one outcome-blind retrieval fixture against preregistered labels."""

    if (
        isinstance(latency_ms, bool)
        or not isinstance(latency_ms, (int, float))
        or not math.isfinite(float(latency_ms))
        or float(latency_ms) < 0
    ):
        raise EvidenceCoverageError("latency_ms must be finite and non-negative")
    if (
        isinstance(maximum_latency_ms, bool)
        or not isinstance(maximum_latency_ms, (int, float))
        or not math.isfinite(float(maximum_latency_ms))
        or float(maximum_latency_ms) <= 0
    ):
        raise EvidenceCoverageError(
            "maximum_latency_ms must be finite and positive"
        )
    selected = set(_selected_claim_ids(packet))
    relevant = set(str(value) for value in relevant_claim_ids)
    irrelevant = set(str(value) for value in irrelevant_claim_ids)
    if relevant.intersection(irrelevant):
        raise EvidenceCoverageError(
            "Golden relevant and irrelevant labels must be disjoint"
        )
    selected_relevant = selected.intersection(relevant)
    selected_irrelevant = selected.intersection(irrelevant)
    return {
        "relevant_claim_recall": _rate(
            len(selected_relevant), len(relevant)
        ),
        "selected_claim_precision": _rate(
            len(selected_relevant), len(selected)
        ),
        "irrelevant_claim_rejection_rate": _rate(
            len(irrelevant - selected_irrelevant), len(irrelevant)
        ),
        "missed_relevant_claim_ids": sorted(relevant - selected),
        "selected_irrelevant_claim_ids": sorted(selected_irrelevant),
        "latency_ms": float(latency_ms),
        "maximum_latency_ms": float(maximum_latency_ms),
        "latency_within_budget": float(latency_ms)
        <= float(maximum_latency_ms),
    }
