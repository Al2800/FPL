"""Deterministic evidence retrieval around close FPL decisions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import math
from typing import Any

from src.forecasting.live_faithful import artifact_hash


class BoundaryRetrievalError(ValueError):
    """Raised when a decision boundary or evidence view is malformed."""


DECISION_TYPES = frozenset({"transfer", "lineup", "captaincy", "chip"})


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def _finite_non_negative(value: Any, field: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
        or float(value) < 0
    ):
        raise BoundaryRetrievalError(
            f"{field} must be a finite non-negative number"
        )
    return float(value)


def _validate_boundary(boundary: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "boundary_id",
        "decision_type",
        "incumbent_id",
        "alternative_id",
        "margin_points",
        "player_uids",
        "max_swing_points",
    }
    missing = sorted(required - set(boundary))
    if missing:
        raise BoundaryRetrievalError(
            "boundary missing required fields: " + ", ".join(missing)
        )
    if boundary["decision_type"] not in DECISION_TYPES:
        raise BoundaryRetrievalError("unsupported decision_type")
    player_uids = boundary["player_uids"]
    if (
        not isinstance(player_uids, list)
        or not player_uids
        or any(not isinstance(value, str) or not value for value in player_uids)
    ):
        raise BoundaryRetrievalError(
            "boundary player_uids must contain non-empty strings"
        )
    result = deepcopy(dict(boundary))
    result["margin_points"] = _finite_non_negative(
        boundary["margin_points"], "margin_points"
    )
    result["max_swing_points"] = _finite_non_negative(
        boundary["max_swing_points"], "max_swing_points"
    )
    result["player_uids"] = sorted(set(player_uids))
    return result


def build_boundary_evidence_pack(
    *,
    availability_view: Mapping[str, Any],
    boundaries: Sequence[Mapping[str, Any]],
    max_evidence: int = 12,
) -> dict[str, Any]:
    """Rank accepted evidence by its ability to alter declared choices."""

    if (
        not isinstance(max_evidence, int)
        or isinstance(max_evidence, bool)
        or max_evidence < 1
    ):
        raise BoundaryRetrievalError("max_evidence must be a positive integer")
    if availability_view.get("content_sha256") != artifact_hash(
        availability_view
    ):
        raise BoundaryRetrievalError("availability view content hash mismatch")
    normalised_boundaries = sorted(
        (_validate_boundary(value) for value in boundaries),
        key=lambda item: str(item["boundary_id"]),
    )
    boundary_ids = [
        str(value["boundary_id"]) for value in normalised_boundaries
    ]
    if len(boundary_ids) != len(set(boundary_ids)):
        raise BoundaryRetrievalError("boundary_id values must be unique")

    ranked: list[dict[str, Any]] = []
    for claim in availability_view.get("accepted", []):
        player_uid = str(claim["player_uid"])
        confidence = float(claim["confidence"])
        matches = []
        for boundary in normalised_boundaries:
            if player_uid not in boundary["player_uids"]:
                continue
            estimated_impact = round(
                float(boundary["max_swing_points"]) * confidence, 6
            )
            matches.append(
                {
                    "boundary_id": boundary["boundary_id"],
                    "decision_type": boundary["decision_type"],
                    "margin_points": boundary["margin_points"],
                    "estimated_impact_points": estimated_impact,
                    "can_flip": estimated_impact
                    >= float(boundary["margin_points"]),
                }
            )
        matches.sort(
            key=lambda item: (
                not item["can_flip"],
                item["margin_points"],
                -item["estimated_impact_points"],
                str(item["boundary_id"]),
            )
        )
        if matches:
            best = matches[0]
            ranked.append(
                {
                    "claim_id": claim["claim_id"],
                    "player_uid": player_uid,
                    "status": claim["status"],
                    "confidence": confidence,
                    "can_flip_any_boundary": any(
                        value["can_flip"] for value in matches
                    ),
                    "best_margin_points": best["margin_points"],
                    "best_estimated_impact_points": best[
                        "estimated_impact_points"
                    ],
                    "ranked_boundaries": matches,
                }
            )
    ranked.sort(
        key=lambda item: (
            not item["can_flip_any_boundary"],
            item["best_margin_points"],
            -item["best_estimated_impact_points"],
            -item["confidence"],
            str(item["claim_id"]),
        )
    )
    selected = ranked[:max_evidence]
    selected_ids = {str(item["claim_id"]) for item in selected}
    active_by_id = {
        str(item["claim_id"]): deepcopy(item)
        for item in availability_view.get("accepted", [])
    }
    return _seal(
        {
            "schema_version": "1.0",
            "decision_at": availability_view["decision_at"],
            "availability_view_sha256": availability_view[
                "content_sha256"
            ],
            "boundaries": normalised_boundaries,
            "accepted_evidence": [
                active_by_id[str(item["claim_id"])] for item in selected
            ],
            "ranking": selected,
            "omitted_accepted_claim_ids": sorted(
                set(active_by_id) - selected_ids
            ),
            "conflicts": deepcopy(availability_view.get("conflicts", [])),
            "abstentions": deepcopy(
                availability_view.get("abstentions", [])
            ),
            "limits": {
                "max_evidence": max_evidence,
                "accepted_count": len(selected),
                "candidate_count": len(ranked),
            },
        }
    )


def _plan_hash(plan: Mapping[str, Any]) -> str:
    value = plan.get("content_sha256")
    return (
        str(value)
        if isinstance(value, str) and value
        else artifact_hash(plan)
    )


def build_shadow_effect_record(
    *,
    accepted_evidence_ids: Sequence[str],
    control_plan: Mapping[str, Any],
    evidence_plan: Mapping[str, Any],
    control_score: int | None = None,
    evidence_score: int | None = None,
) -> dict[str, Any]:
    """Separate evidence acceptance, plan effects, transfers, and outcome."""

    if (control_score is None) != (evidence_score is None):
        raise BoundaryRetrievalError(
            "control_score and evidence_score must both be supplied or omitted"
        )
    control_transfers = deepcopy(list(control_plan.get("transfers", [])))
    evidence_transfers = deepcopy(list(evidence_plan.get("transfers", [])))
    return _seal(
        {
            "schema_version": "1.0",
            "accepted_evidence_ids": sorted(set(accepted_evidence_ids)),
            "plan_effect": {
                "changed": _plan_hash(control_plan)
                != _plan_hash(evidence_plan),
                "control_plan_sha256": _plan_hash(control_plan),
                "evidence_plan_sha256": _plan_hash(evidence_plan),
            },
            "transfer_effect": {
                "changed": control_transfers != evidence_transfers,
                "control": control_transfers,
                "evidence": evidence_transfers,
            },
            "score_effect": {
                "status": (
                    "pending" if control_score is None else "revealed"
                ),
                "control_score": control_score,
                "evidence_score": evidence_score,
                "delta": (
                    None
                    if control_score is None
                    else int(evidence_score) - int(control_score)
                ),
            },
        }
    )
