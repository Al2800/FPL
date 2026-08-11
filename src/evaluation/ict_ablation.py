"""ICT feature-weight application and fail-closed ablation (ticket 16)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from copy import deepcopy
from math import sqrt
from pathlib import Path
from typing import Any

from src.forecasting.live_faithful import artifact_hash


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY_PATH = ROOT / "control" / "policies" / "ict-feature-weights-v1.json"
ICT_COMPONENTS = ("influence", "creativity", "threat", "ict_index")


class IctAblationError(ValueError):
    """Raised when ICT weights or ablation inputs are unsafe."""


def load_ict_weight_policy(path: Path | None = None) -> dict[str, Any]:
    """Load the versioned candidate ICT policy and seal its content hash."""

    import json

    policy_path = path or DEFAULT_POLICY_PATH
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise IctAblationError("weight policy must be a JSON object")
    if payload.get("schema_version") != "ict-feature-weights-v1":
        raise IctAblationError("unsupported ICT weight schema")
    if payload.get("live_active") is True:
        raise IctAblationError(
            "candidate weight policy must not be live_active until promotion"
        )
    sealed = deepcopy(payload)
    sealed.pop("content_sha256", None)
    sealed["content_sha256"] = artifact_hash(sealed)
    return sealed


def _zscore(values: Sequence[float]) -> list[float]:
    if not values:
        return []
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    std = sqrt(variance)
    if std == 0.0:
        return [0.0 for _ in values]
    return [(value - mean) / std for value in values]


def build_ict_feature_payload(
    players: Sequence[Mapping[str, Any]],
    *,
    lag_window_gameweeks: int = 3,
) -> dict[str, Any]:
    """Build a shadow ICT feature payload from lag aggregates.

    Live production does not feed ICT into projections. This payload keeps
    ``effect_weights: null`` until an ablation applicator attaches candidate
    coefficients.
    """

    adjustments = []
    for row in players:
        item = {
            "official_player_id": int(row["official_player_id"]),
            "position": str(row.get("position") or "UNK"),
            "lag_window_gameweeks": int(lag_window_gameweeks),
            "components": {
                component: float(row.get(component) or 0.0)
                for component in ICT_COMPONENTS
            },
            "expected_points_addend": 0.0,
        }
        adjustments.append(item)
    payload = {
        "schema_version": "ict-feature-payload-v1",
        "family": "ict_index",
        "promotion_status": "shadow_only_pending_point_in_time_ablation",
        "effect_weights": None,
        "adjustments": adjustments,
        "notes": (
            "ICT lags are preserved for historical ablation only; live "
            "player_events projections remain ICT-free."
        ),
    }
    payload["content_sha256"] = artifact_hash(payload)
    return payload


def weight_for_component(
    policy: Mapping[str, Any],
    *,
    component: str,
    zscore: float,
) -> float:
    """Return the additive expected-points bump for one standardised component."""

    component_weights = (policy.get("weights") or {}).get(str(component))
    if not isinstance(component_weights, Mapping):
        return 0.0
    return float(component_weights.get("expected_points_addend_per_std", 0.0)) * float(
        zscore
    )


def apply_ict_effect_weights(
    feature_payload: Mapping[str, Any],
    policy: Mapping[str, Any],
    *,
    arm: str = "joint_components",
) -> dict[str, Any]:
    """Attach candidate ICT weights and per-player expected-points addends.

    Live production continues to omit ICT from projections. This helper is for
    ablation / shadow evaluation copies only.
    """

    if not policy.get("content_sha256"):
        raise IctAblationError("weight policy requires content_sha256")
    if policy.get("live_active") is True:
        raise IctAblationError("refusing to apply a live_active weight policy")
    if arm not in set(policy.get("candidate_arms") or []):
        raise IctAblationError(f"unsupported ICT candidate arm: {arm}")

    payload = deepcopy(dict(feature_payload))
    rows = [deepcopy(dict(row)) for row in payload.get("adjustments") or []]
    by_position: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        by_position[str(row.get("position") or "UNK")].append(index)

    zscores: dict[tuple[int, str], float] = {}
    for indices in by_position.values():
        for component in ICT_COMPONENTS:
            values = [
                float((rows[index].get("components") or {}).get(component) or 0.0)
                for index in indices
            ]
            for index, score in zip(indices, _zscore(values), strict=True):
                zscores[(index, component)] = score

    blend = policy.get("joint_blend") or {}
    for index, row in enumerate(rows):
        bump = 0.0
        if arm.endswith("_only"):
            component = arm[: -len("_only")]
            bump = weight_for_component(
                policy,
                component=component,
                zscore=zscores.get((index, component), 0.0),
            )
        else:
            for component in ICT_COMPONENTS:
                component_bump = weight_for_component(
                    policy,
                    component=component,
                    zscore=zscores.get((index, component), 0.0),
                )
                bump += float(blend.get(component, 0.0)) * component_bump
        row["candidate_arm"] = arm
        row["expected_points_addend"] = round(bump, 6)
        rows[index] = row

    payload["adjustments"] = rows
    payload["effect_weights"] = {
        "policy_id": policy.get("policy_id"),
        "transformation_version": policy.get("transformation_version"),
        "content_sha256": policy.get("content_sha256"),
        "unit": policy.get("unit"),
        "candidate_arm": arm,
        "lag_window_gameweeks": policy.get("lag_window_gameweeks"),
        "normalisation": policy.get("normalisation"),
        "weights": deepcopy(dict(policy.get("weights") or {})),
        "joint_blend": deepcopy(dict(blend)),
    }
    payload["promotion_status"] = "ablation_candidate_not_live"
    payload["content_sha256"] = artifact_hash(payload)
    return payload


def assess_ict_ablation_corpus(
    *,
    pit_snapshot_paths: Sequence[Path] | None = None,
    finalised_outcome_paths: Sequence[Path] | None = None,
    min_paired_gameweeks: int = 3,
) -> dict[str, Any]:
    """Record whether a cutoff-safe paired ICT corpus exists for promotion folds."""

    snapshots = [
        Path(path) for path in (pit_snapshot_paths or []) if Path(path).is_file()
    ]
    outcomes = [
        Path(path) for path in (finalised_outcome_paths or []) if Path(path).is_file()
    ]
    gaps: list[str] = []
    if len(snapshots) < min_paired_gameweeks:
        gaps.append("insufficient_cutoff_safe_ict_lag_snapshots")
    if len(outcomes) < min_paired_gameweeks:
        gaps.append("insufficient_finalised_outcome_artifacts")
    if not snapshots:
        gaps.append("no_immutable_historical_ict_pit_snapshots")
    ready = not gaps
    return {
        "schema_version": "ict-ablation-corpus-v1",
        "ready_for_promotion_folds": ready,
        "min_paired_gameweeks": min_paired_gameweeks,
        "pit_snapshot_count": len(snapshots),
        "finalised_outcome_count": len(outcomes),
        "gaps": gaps,
        "notes": (
            "Historical lag aggregates retain ICT fields, but promotion requires "
            "immutable pre-deadline ICT snapshots paired with finalised outcomes. "
            "ICT is outside the frozen four-family optional_family_arms matrix."
        ),
    }


def build_ict_ablation_decision(
    *,
    policy: Mapping[str, Any],
    corpus: Mapping[str, Any],
    feature_payload_example: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Seal the ticket-16 promotion decision (fail closed when corpus incomplete)."""

    if corpus.get("ready_for_promotion_folds"):
        decision = "eligible_for_owner_review"
        promotion_eligible = True
        reason = None
    else:
        decision = "remain_shadow_only"
        promotion_eligible = False
        reason = "no_complete_point_in_time_ablation_rows"
    result = {
        "schema_version": "ict-ablation-decision-v1",
        "report_id": "feature-ablation:ict_index",
        "family": "ict_index",
        "arm_id": "forecast_optimizer_plus_ict_index_shadow",
        "frozen_four_family_prereg": False,
        "policy_id": policy.get("policy_id"),
        "policy_content_sha256": policy.get("content_sha256"),
        "transformation_version": policy.get("transformation_version"),
        "source_ids": list(policy.get("source_ids") or []),
        "lag_window_gameweeks": policy.get("lag_window_gameweeks"),
        "candidate_arms": list(policy.get("candidate_arms") or []),
        "evaluation_metrics": list(policy.get("evaluation_metrics") or []),
        "live_effect_weights": None,
        "candidate_policy_live_active": bool(policy.get("live_active")),
        "corpus": deepcopy(dict(corpus)),
        "example_adjustment_count": (
            len((feature_payload_example or {}).get("adjustments") or [])
            if feature_payload_example is not None
            else 0
        ),
        "promotion_eligible": promotion_eligible,
        "decision": decision,
        "reason": reason,
        "historical_finding": "no_isolated_point_in_time_ict_ablation",
        "notes": (
            "Ticket 16 records versioned candidate ICT lag weights and a "
            "fail-closed decision. Live player_events / live_faithful stay "
            "ICT-free until an owner-reviewed promotion against cutoff-safe "
            "paired rows. This track does not thaw the frozen four-family "
            "preregistration."
        ),
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def run_ict_ablation(
    *,
    policy_path: Path | None = None,
    pit_snapshot_paths: Sequence[Path] | None = None,
    finalised_outcome_paths: Sequence[Path] | None = None,
    sample_players: Sequence[Mapping[str, Any]] | None = None,
    arm: str = "joint_components",
) -> dict[str, Any]:
    """Load policy, assess corpus, optionally demonstrate applicator, seal decision."""

    policy = load_ict_weight_policy(policy_path)
    corpus = assess_ict_ablation_corpus(
        pit_snapshot_paths=pit_snapshot_paths,
        finalised_outcome_paths=finalised_outcome_paths,
        min_paired_gameweeks=int(
            (policy.get("promotion_thresholds") or {}).get("min_paired_gameweeks", 3)
        ),
    )
    example_payload = None
    if sample_players is not None:
        base = build_ict_feature_payload(
            sample_players,
            lag_window_gameweeks=int(policy.get("lag_window_gameweeks") or 3),
        )
        example_payload = apply_ict_effect_weights(base, policy, arm=arm)
    return build_ict_ablation_decision(
        policy=policy,
        corpus=corpus,
        feature_payload_example=example_payload,
    )
