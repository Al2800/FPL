"""Causal decomposition for paired live-shadow outcomes."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping


class ShadowAttributionError(ValueError):
    """Raised when paired outcomes cannot support exact attribution."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def attribution_hash(value: Mapping[str, Any]) -> str:
    projection = {
        key: item for key, item in value.items() if key != "content_sha256"
    }
    return hashlib.sha256(_canonical_bytes(projection)).hexdigest()


def _net(
    outcome: Mapping[str, Any], plan: Mapping[str, Any], label: str
) -> tuple[int, int, int]:
    if outcome.get("plan_sha256") not in (None, plan.get("content_sha256")):
        raise ShadowAttributionError(f"{label} outcome is bound to a different plan")
    gross = outcome.get("gross_points")
    if isinstance(gross, bool) or not isinstance(gross, int):
        raise ShadowAttributionError(f"{label} gross_points must be an integer")
    hit = int(plan.get("finance", {}).get("hit_cost", -1))
    if hit < 0:
        raise ShadowAttributionError(f"{label} plan has no valid hit cost")
    return gross, hit, gross - hit


def attribute_shadow_outcomes(
    *,
    control_plan: Mapping[str, Any],
    evidence_baseline_plan: Mapping[str, Any],
    evidence_actual_plan: Mapping[str, Any],
    control_outcome: Mapping[str, Any],
    evidence_baseline_outcome: Mapping[str, Any],
    evidence_actual_outcome: Mapping[str, Any],
) -> dict[str, Any]:
    """Separate deterministic, inherited-state, and current-evidence points."""

    episode_ids = {
        str(plan.get("episode_id"))
        for plan in (control_plan, evidence_baseline_plan, evidence_actual_plan)
    }
    if len(episode_ids) != 1:
        raise ShadowAttributionError("All shadow plans must belong to one episode")
    control = _net(control_outcome, control_plan, "control")
    baseline = _net(
        evidence_baseline_outcome, evidence_baseline_plan, "evidence baseline"
    )
    actual = _net(evidence_actual_outcome, evidence_actual_plan, "evidence actual")
    current_evidence = actual[2] - baseline[2]
    inherited_state = baseline[2] - control[2]
    total = actual[2] - control[2]
    if current_evidence + inherited_state != total:
        raise ShadowAttributionError("Attribution is not additive")

    result: dict[str, Any] = {
        "schema_version": "1.0",
        "episode_id": next(iter(episode_ids)),
        "comparison": "paired_live_shadow_three_plan_bridge",
        "points": {
            "deterministic_control": {
                "gross": control[0],
                "hit": control[1],
                "net": control[2],
            },
            "evidence_state_no_evidence": {
                "gross": baseline[0],
                "hit": baseline[1],
                "net": baseline[2],
            },
            "evidence_actual": {
                "gross": actual[0],
                "hit": actual[1],
                "net": actual[2],
            },
        },
        "effects": {
            "current_evidence": current_evidence,
            "inherited_state": inherited_state,
            "total_evidence_trajectory": total,
            "identity": "total_evidence_trajectory=current_evidence+inherited_state",
        },
        "lineage": {
            "control_plan_sha256": str(control_plan["content_sha256"]),
            "evidence_baseline_plan_sha256": str(
                evidence_baseline_plan["content_sha256"]
            ),
            "evidence_actual_plan_sha256": str(
                evidence_actual_plan["content_sha256"]
            ),
            "outcome_sha256": {
                "control": str(control_outcome.get("content_sha256", "")),
                "evidence_baseline": str(
                    evidence_baseline_outcome.get("content_sha256", "")
                ),
                "evidence_actual": str(
                    evidence_actual_outcome.get("content_sha256", "")
                ),
            },
        },
    }
    result["content_sha256"] = attribution_hash(result)
    return deepcopy(result)
