"""Set-piece effect-weight application and fail-closed ablation (ticket 15)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.forecasting.live_faithful import artifact_hash
from src.ingestion.set_piece_roles import build_set_piece_feature_payload


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY_PATH = ROOT / "control" / "policies" / "set-piece-effect-weights-v1.json"


class SetPieceAblationError(ValueError):
    """Raised when set-piece weights or ablation inputs are unsafe."""


def load_set_piece_weight_policy(path: Path | None = None) -> dict[str, Any]:
    """Load the versioned candidate weight policy and seal its content hash."""

    import json

    policy_path = path or DEFAULT_POLICY_PATH
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SetPieceAblationError("weight policy must be a JSON object")
    if payload.get("schema_version") != "set-piece-effect-weights-v1":
        raise SetPieceAblationError("unsupported set-piece weight schema")
    if payload.get("live_active") is True:
        raise SetPieceAblationError(
            "candidate weight policy must not be live_active until promotion"
        )
    sealed = deepcopy(payload)
    sealed.pop("content_sha256", None)
    sealed["content_sha256"] = artifact_hash(sealed)
    return sealed


def weight_for_role_rank(
    policy: Mapping[str, Any],
    *,
    role: str,
    rank: int,
    confidence: float,
) -> float:
    """Return the additive expected-goals bump, or 0 when below thresholds."""

    if int(rank) > int(policy.get("rank_cap", 3)):
        return 0.0
    if float(confidence) < float(policy.get("requires_confidence_min", 0.0)):
        return 0.0
    role_weights = (policy.get("weights") or {}).get(str(role))
    if not isinstance(role_weights, Mapping):
        return 0.0
    return float(role_weights.get(str(int(rank)), 0.0))


def apply_set_piece_effect_weights(
    feature_payload: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Attach candidate weights and per-player expected-goals addends.

    Live production continues to emit ``effect_weights: None``. This helper is
    for ablation / shadow evaluation copies only.
    """

    if not policy.get("content_sha256"):
        raise SetPieceAblationError("weight policy requires content_sha256")
    if policy.get("live_active") is True:
        raise SetPieceAblationError("refusing to apply a live_active weight policy")
    payload = deepcopy(dict(feature_payload))
    adjustments = []
    for row in payload.get("adjustments") or []:
        item = deepcopy(dict(row))
        bump = weight_for_role_rank(
            policy,
            role=str(item["role"]),
            rank=int(item["rank"]),
            confidence=float(item["confidence"]),
        )
        item["expected_goals_addend"] = bump
        adjustments.append(item)
    payload["adjustments"] = adjustments
    payload["effect_weights"] = {
        "policy_id": policy.get("policy_id"),
        "transformation_version": policy.get("transformation_version"),
        "content_sha256": policy.get("content_sha256"),
        "unit": policy.get("unit"),
        "weights": deepcopy(dict(policy.get("weights") or {})),
    }
    payload["promotion_status"] = "ablation_candidate_not_live"
    payload["content_sha256"] = artifact_hash(payload)
    return payload


def assess_set_piece_ablation_corpus(
    *,
    pit_ledger_paths: Sequence[Path] | None = None,
    finalised_outcome_paths: Sequence[Path] | None = None,
    min_paired_gameweeks: int = 3,
) -> dict[str, Any]:
    """Record whether a cutoff-safe paired corpus exists for promotion folds."""

    ledgers = [Path(path) for path in (pit_ledger_paths or []) if Path(path).is_file()]
    outcomes = [
        Path(path) for path in (finalised_outcome_paths or []) if Path(path).is_file()
    ]
    gaps: list[str] = []
    if len(ledgers) < min_paired_gameweeks:
        gaps.append("insufficient_cutoff_safe_set_piece_ledgers")
    if len(outcomes) < min_paired_gameweeks:
        gaps.append("insufficient_finalised_outcome_artifacts")
    if not ledgers:
        gaps.append("no_immutable_historical_set_piece_pit_snapshots")
    ready = not gaps
    return {
        "schema_version": "set-piece-ablation-corpus-v1",
        "ready_for_promotion_folds": ready,
        "min_paired_gameweeks": min_paired_gameweeks,
        "pit_ledger_count": len(ledgers),
        "finalised_outcome_count": len(outcomes),
        "gaps": gaps,
        "notes": (
            "Vaastav end-of-season role columns are not cutoff-safe. Live 2026/27 "
            "promotion requires immutable pre-deadline ledgers plus finalised "
            "outcomes across the preregistered folds."
        ),
    }


def build_set_piece_ablation_decision(
    *,
    policy: Mapping[str, Any],
    corpus: Mapping[str, Any],
    feature_payload_example: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Seal the ticket-15 promotion decision (fail closed when corpus incomplete)."""

    if corpus.get("ready_for_promotion_folds"):
        decision = "eligible_for_owner_review"
        promotion_eligible = True
        reason = None
    else:
        decision = "remain_shadow_only"
        promotion_eligible = False
        reason = "no_complete_point_in_time_ablation_rows"
    result = {
        "schema_version": "set-piece-ablation-decision-v1",
        "report_id": "feature-ablation:set_piece_role",
        "family": "set_piece_role",
        "arm_id": "forecast_optimizer_plus_set_piece_role",
        "policy_id": policy.get("policy_id"),
        "policy_content_sha256": policy.get("content_sha256"),
        "transformation_version": policy.get("transformation_version"),
        "source_ids": list(policy.get("source_ids") or []),
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
        "historical_finding": "no_isolated_point_in_time_set_piece_role_ablation",
        "notes": (
            "Ticket 15 records versioned candidate weights and a fail-closed "
            "decision. Live feature payloads keep effect_weights=null until an "
            "owner-reviewed promotion against cutoff-safe paired rows."
        ),
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def run_set_piece_ablation(
    *,
    policy_path: Path | None = None,
    pit_ledger_paths: Sequence[Path] | None = None,
    finalised_outcome_paths: Sequence[Path] | None = None,
    sample_ledger: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Load policy, assess corpus, optionally demonstrate applicator, seal decision."""

    policy = load_set_piece_weight_policy(policy_path)
    corpus = assess_set_piece_ablation_corpus(
        pit_ledger_paths=pit_ledger_paths,
        finalised_outcome_paths=finalised_outcome_paths,
    )
    example_payload = None
    if sample_ledger is not None:
        base = build_set_piece_feature_payload(sample_ledger)
        example_payload = apply_set_piece_effect_weights(base, policy)
    return build_set_piece_ablation_decision(
        policy=policy,
        corpus=corpus,
        feature_payload_example=example_payload,
    )
