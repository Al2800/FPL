"""Isolated, retrospective evidence forks over canonical replay checkpoints."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from src.evaluation.outcome_scorer import score_revealed_outcome
from src.evidence.lifecycle import assess_claim_for_decision, load_policy, scan_injection
from src.forecasting.live_faithful import artifact_hash
from src.forecasting.replay_adapter import build_replay_solver_input
from src.optimisation.io import fingerprint
from src.optimisation.solver import solve
from src.optimisation.types import SolverInput
from src.orchestration.policy_state import transition_policy_state
from src.orchestration.validated_plan import validate_and_freeze_plan


class EvidenceForkError(ValueError):
    """Raised when a retrospective fork is unsafe or internally inconsistent."""


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _timestamp(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceForkError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise EvidenceForkError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _sealed(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def _write_once(path: Path, value: Mapping[str, Any]) -> None:
    text = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise EvidenceForkError(f"Refusing to overwrite sealed fork artifact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def validate_reconstructed_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a published-before-cutoff but retrospectively captured bundle."""
    required = {
        "schema_version",
        "experiment_id",
        "evidence_mode",
        "decision_cutoff",
        "captured_at",
        "case_selection",
        "sources",
    }
    missing = sorted(required - set(bundle))
    if missing:
        raise EvidenceForkError("Evidence bundle missing fields: " + ", ".join(missing))
    if bundle["evidence_mode"] != "retrospective_published_before_deadline":
        raise EvidenceForkError("Evidence bundle must declare retrospective reconstruction")
    sources = bundle["sources"]
    if not isinstance(sources, list) or not sources:
        raise EvidenceForkError("Evidence bundle requires at least one source")

    cutoff = _timestamp(bundle["decision_cutoff"], "decision_cutoff")
    captured = _timestamp(bundle["captured_at"], "captured_at")
    policy = load_policy()
    assessments: list[dict[str, Any]] = []
    seen_claims: set[str] = set()
    seen_adjustments: set[str] = set()
    for index, raw in enumerate(sources):
        if not isinstance(raw, Mapping):
            raise EvidenceForkError(f"sources[{index}] must be an object")
        source = dict(raw)
        source_required = {
            "source_id",
            "url",
            "title",
            "published_at",
            "published_at_precision",
            "captured_at",
            "citation_excerpt",
            "claim_id",
            "claim_text",
            "confidence",
            "expires_at",
            "player_id",
            "adjustment",
        }
        source_missing = sorted(source_required - set(source))
        if source_missing:
            raise EvidenceForkError(
                f"sources[{index}] missing fields: " + ", ".join(source_missing)
            )
        published = _timestamp(source["published_at"], f"sources[{index}].published_at")
        source_captured = _timestamp(
            source["captured_at"], f"sources[{index}].captured_at"
        )
        expiry = _timestamp(source["expires_at"], f"sources[{index}].expires_at")
        if published > cutoff:
            raise EvidenceForkError(
                f"Source {source['source_id']} published after decision cutoff"
            )
        if source_captured != captured:
            raise EvidenceForkError("Source captured_at must match bundle captured_at")
        if source_captured < published:
            raise EvidenceForkError("Source captured_at cannot precede published_at")
        if expiry <= cutoff:
            raise EvidenceForkError("Evidence claim is expired at decision cutoff")
        if source["claim_id"] in seen_claims:
            raise EvidenceForkError("Evidence claim IDs must be unique")
        seen_claims.add(str(source["claim_id"]))
        adjustment = source["adjustment"]
        if not isinstance(adjustment, Mapping):
            raise EvidenceForkError("Evidence adjustment must be an object")
        for field in (
            "adjustment_id",
            "target",
            "after_value",
            "confidence",
            "rationale",
        ):
            if field not in adjustment:
                raise EvidenceForkError(f"Evidence adjustment missing {field}")
        if adjustment["adjustment_id"] in seen_adjustments:
            raise EvidenceForkError("Evidence adjustment IDs must be unique")
        seen_adjustments.add(str(adjustment["adjustment_id"]))
        claim_confidence = float(source["confidence"])
        adjustment_confidence = float(adjustment["confidence"])
        if claim_confidence < float(policy["thresholds"]["min_claim_confidence"]):
            raise EvidenceForkError("Claim confidence is below policy threshold")
        if adjustment_confidence < float(
            policy["thresholds"]["min_adjustment_confidence"]
        ):
            raise EvidenceForkError("Adjustment confidence is below policy threshold")
        if scan_injection(str(source["citation_excerpt"])).quarantined or scan_injection(
            str(source["claim_text"])
        ).quarantined:
            raise EvidenceForkError("Evidence text was quarantined")
        if adjustment["target"] == "start_probability_delta":
            delta = abs(float(adjustment["after_value"]))
            if delta > float(
                policy["thresholds"]["max_start_probability_delta"]
            ):
                raise EvidenceForkError("Start-probability delta exceeds policy maximum")
        elif adjustment["target"] != "availability_flag":
            raise EvidenceForkError(
                f"Unsupported fork adjustment target: {adjustment['target']}"
            )

        claim = {
            "claim_id": source["claim_id"],
            "document_id": f"document:{source['source_id']}",
            "claim_text": source["claim_text"],
            "published_at": source["published_at"],
            "observed_at": source["captured_at"],
            "available_at": source["captured_at"],
            "expires_at": source["expires_at"],
            "confidence": claim_confidence,
            "provenance": {
                "source_ids": [source["source_id"]],
                "transformation_version": "gw12-retrospective-evidence-v1",
                "content_hash_sha256": hashlib.sha256(
                    str(source["citation_excerpt"]).encode("utf-8")
                ).hexdigest(),
            },
        }
        production = assess_claim_for_decision(
            claim, str(bundle["decision_cutoff"]), policy
        )
        assessments.append(
            {
                "source_id": source["source_id"],
                "claim_id": source["claim_id"],
                "adjustment_id": adjustment["adjustment_id"],
                "player_id": source["player_id"],
                "published_at": source["published_at"],
                "captured_at": source["captured_at"],
                "citation_excerpt_sha256": claim["provenance"][
                    "content_hash_sha256"
                ],
                "production_eligible": production.eligible,
                "production_ineligibility_reasons": production.reasons,
                "exploratory_admissible": True,
            }
        )

    return _sealed(
        {
            "schema_version": "1.0",
            "experiment_id": bundle["experiment_id"],
            "evidence_mode": bundle["evidence_mode"],
            "decision_cutoff": bundle["decision_cutoff"],
            "captured_at": bundle["captured_at"],
            "case_selection": bundle["case_selection"],
            "production_eligible": all(
                item["production_eligible"] for item in assessments
            ),
            "exploratory_admissible": True,
            "sources": assessments,
            "limitations": [
                "sources_recovered_after_historical_decision",
                "case_selected_after_outcome_was_known",
                "not_eligible_for_headline_agent_performance",
            ],
        }
    )


def apply_reconstructed_adjustments(
    solver_input: Mapping[str, Any], bundle: Mapping[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Apply an already validated evidence bundle to a copied solver input."""
    adjusted = deepcopy(dict(solver_input))
    players = {str(row["player_id"]): row for row in adjusted["players"]}
    applied: list[dict[str, Any]] = []
    for source in bundle["sources"]:
        player_id = str(source["player_id"])
        if player_id not in players:
            raise EvidenceForkError(f"Evidence player is missing from market: {player_id}")
        row = players[player_id]
        spec = source["adjustment"]
        target = str(spec["target"])
        before = {
            "status": row.get("status"),
            "start_probability": float(row.get("start_probability", 0.0)),
            "expected_minutes": float(row.get("expected_minutes", 0.0)),
            "expected_points": float(row.get("expected_points", 0.0)),
        }
        if target == "availability_flag":
            if spec["after_value"] is not False:
                raise EvidenceForkError(
                    "The isolated fork only supports unavailable availability flags"
                )
            row.update(
                {
                    "status": "i",
                    "start_probability": 0.0,
                    "expected_minutes": 0.0,
                    "expected_points": 0.0,
                }
            )
        else:
            delta = float(spec["after_value"])
            probability = before["start_probability"]
            after_probability = min(1.0, max(0.0, probability + delta))
            scale = after_probability / probability if probability else 0.0
            row.update(
                {
                    "start_probability": round(after_probability, 4),
                    "expected_minutes": round(before["expected_minutes"] * scale, 1),
                    "expected_points": round(before["expected_points"] * scale, 2),
                }
            )
        row["evidence_adjustment_ids"] = [str(spec["adjustment_id"])]
        applied.append(
            {
                "adjustment_id": spec["adjustment_id"],
                "claim_id": source["claim_id"],
                "player_id": player_id,
                "target": target,
                "confidence": float(spec["confidence"]),
                "before": before,
                "after": {
                    "status": row.get("status"),
                    "start_probability": float(row.get("start_probability", 0.0)),
                    "expected_minutes": float(row.get("expected_minutes", 0.0)),
                    "expected_points": float(row.get("expected_points", 0.0)),
                },
                "rationale": spec["rationale"],
            }
        )
    return adjusted, applied


def _identity_index(identity_map: Mapping[str, Any]) -> dict[str, str]:
    return {
        str(row["fpl_player_id"]): str(row["canonical_id"])
        for row in identity_map["players"]
    }


def _score_ceiling(
    squad: list[Mapping[str, Any]], hidden: Mapping[str, Any]
) -> int:
    points: dict[str, int] = {}
    for row in hidden["player_outcomes"]:
        player_id = f"player:{hidden['season']}:{row['element']}"
        points[player_id] = points.get(player_id, 0) + int(row["total_points"])
    by_position: dict[str, list[int]] = {
        "GKP": [],
        "DEF": [],
        "MID": [],
        "FWD": [],
    }
    for row in squad:
        by_position[str(row["position"])].append(points.get(str(row["player_id"]), 0))
    for values in by_position.values():
        values.sort(reverse=True)
    best = 0
    for defenders in range(3, 6):
        for midfielders in range(2, 6):
            for forwards in range(1, 4):
                if defenders + midfielders + forwards != 10:
                    continue
                selected = (
                    by_position["GKP"][:1]
                    + by_position["DEF"][:defenders]
                    + by_position["MID"][:midfielders]
                    + by_position["FWD"][:forwards]
                )
                if len(selected) == 11:
                    best = max(best, sum(selected) + max(selected))
    return best


def _fixed_lineup_captain_ceiling(outcome: Mapping[str, Any]) -> int:
    """Optimise only captaincy over the already effective realised XI."""

    points = {
        str(row["player_id"]): int(row["total_points"])
        for row in outcome["aggregated_players"]
    }
    base = int(outcome["gross_points"]) - int(outcome["captain"]["extra_points"])
    best_captain = max(
        (points[str(player_id)] for player_id in outcome["effective_lineup_ids"]),
        default=0,
    )
    return base + best_captain


def _market_from_feature_state(value: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "player_id": str(row["player_id"]),
            "position": str(row["position"]),
            "club_id": str(row["club_id"]),
            "now_cost": float(row["quote"]["now_cost"]),
        }
        for row in value["players"]
    ]


def _canonical_span_hash(
    root: Path, *, start_gameweek: int, end_gameweek: int
) -> tuple[str, int]:
    digest = hashlib.sha256()
    count = 0
    for gameweek in range(start_gameweek, end_gameweek + 1):
        directory = root / f"gw-{gameweek:02d}"
        if not directory.is_dir():
            raise EvidenceForkError(f"Missing canonical GW{gameweek}")
        for item in sorted(path for path in directory.rglob("*") if path.is_file()):
            relative = item.relative_to(root).as_posix().encode("utf-8")
            digest.update(len(relative).to_bytes(8, "big"))
            digest.update(relative)
            digest.update(hashlib.sha256(item.read_bytes()).digest())
            count += 1
    return digest.hexdigest(), count


def _hindsight_points(
    hidden: Mapping[str, Any], identity: Mapping[str, Any]
) -> dict[str, int]:
    identity_index = _identity_index(identity)
    points: dict[str, int] = {}
    for row in hidden["player_outcomes"]:
        player_id = identity_index[str(row["element"])]
        points[player_id] = points.get(player_id, 0) + int(row["total_points"])
    return points


def _bounded_legal_market_ceiling(
    solver_input: Mapping[str, Any],
    *,
    hidden: Mapping[str, Any],
    identity: Mapping[str, Any],
    rules: Mapping[str, Any],
    ruleset_sha256: str,
) -> dict[str, Any]:
    """Optimise revealed points within the replay's legal three-transfer pool."""

    points = _hindsight_points(hidden, identity)
    value = deepcopy(dict(solver_input))
    value.update(
        {
            "active_chip": None,
            "transfer_value_policy": "none",
            "probability_extra_transfer_needed": 0.0,
            "future_transfer_discount": 0.0,
        }
    )
    for row in value["players"]:
        row["expected_points"] = float(points.get(str(row["player_id"]), 0))
        row["status"] = "a"
    output = solve(
        SolverInput.from_dict(value),
        rules=rules,
        ruleset_sha256=ruleset_sha256,
    )
    candidate = output["selected"]
    names = {
        str(row["player_id"]): str(row.get("web_name") or row["player_id"])
        for row in value["players"]
    }
    return {
        "gross_points": int(round(float(candidate["objective"]))),
        "transfer_bound": int(value["max_transfers"]),
        "transfers": [
            {
                "player_out_id": move["player_out_id"],
                "player_out_name": names[move["player_out_id"]],
                "player_in_id": move["player_in_id"],
                "player_in_name": names[move["player_in_id"]],
            }
            for move in candidate["transfers"]
        ],
        "lineup": deepcopy(candidate["lineup"]),
        "solver_output_sha256": fingerprint(output),
        "feasibility": (
            "legal under budget, position, club, formation and the declared "
            "zero-to-three-transfer replay candidate pool"
        ),
    }


def build_gw12_score_ceiling_review(
    *,
    canonical_root: Path,
    episode_root: Path,
    fork_root: Path,
) -> dict[str, Any]:
    """Separate actual, fixed-lineup, squad and market opportunity diagnostics."""

    canonical_gw = canonical_root / "gw-12"
    episode = episode_root / "gw-12"
    canonical_plan = _read(canonical_gw / "evidence_agent" / "validated-plan.json")
    canonical_outcome = _read(
        canonical_gw / "evidence_agent" / "realised-outcome.json"
    )
    fork_plan = _read(fork_root / "validated-plan.json")
    fork_outcome = _read(fork_root / "realised-outcome.json")
    state = _read(
        canonical_gw
        / "setup"
        / "arms"
        / "evidence_agent"
        / "starting-policy-state.json"
    )
    solver_input = _read(
        canonical_gw
        / "setup"
        / "arms"
        / "evidence_agent"
        / "reviewed-engine-input.json"
    )
    hidden = _read(episode / "hidden-outcome.json")
    identity = _read(episode / "identity-map.json")
    manifest = _read(episode / "episode-manifest.json")
    rules = yaml.safe_load((episode / "ruleset.yaml").read_text(encoding="utf-8"))
    rules_hash = str(manifest["ruleset"]["content_sha256"])
    market_rows = [
        {
            "player_id": str(row["player_id"]),
            "position": str(row["position"]),
        }
        for row in solver_input["players"]
    ]
    result = _sealed(
        {
            "schema_version": "1.0",
            "experiment_id": "2025-26-gw12-retrospective-availability-v1",
            "season": "2025-26",
            "gameweek": 12,
            "diagnostic_only": True,
            "outcome_information_used": True,
            "actual_selected_plan": {
                "canonical_gross_points": int(canonical_outcome["gross_points"]),
                "fork_gross_points": int(fork_outcome["gross_points"]),
            },
            "fixed_effective_lineup_captain_ceiling": {
                "canonical_gross_points": _fixed_lineup_captain_ceiling(
                    canonical_outcome
                ),
                "fork_gross_points": _fixed_lineup_captain_ceiling(fork_outcome),
                "feasibility": (
                    "holds the realised effective XI fixed and changes only captain"
                ),
            },
            "current_squad_xi_and_captain_ceiling": {
                "gross_points": _score_ceiling(state["squad"], hidden),
                "feasibility": (
                    "best legal formation and captain from the exact pre-GW12 squad; "
                    "no transfers"
                ),
            },
            "post_decision_squad_xi_and_captain_ceiling": {
                "canonical_gross_points": _score_ceiling(
                    canonical_plan["squad_after"], hidden
                ),
                "fork_gross_points": _score_ceiling(
                    fork_plan["squad_after"], hidden
                ),
                "feasibility": (
                    "best legal formation and captain after each already selected "
                    "transfer decision"
                ),
            },
            "bounded_legal_market_opportunity": _bounded_legal_market_ceiling(
                solver_input,
                hidden=hidden,
                identity=identity,
                rules=rules,
                ruleset_sha256=rules_hash,
            ),
            "whole_market_position_only_upper_bound": {
                "gross_points": _score_ceiling(market_rows, hidden),
                "feasibility": (
                    "not a selectable FPL squad: ignores budget, club limits and "
                    "transfer count; retained only as an opportunity upper bound"
                ),
            },
            "interpretation": (
                "The selected teams could not reach 100 points. The bounded legal "
                "three-transfer search reaches 99; the 173-point whole-market value "
                "is deliberately infeasible and must not be presented as attainable."
            ),
        }
    )
    _write_once(fork_root / "score-ceilings.json", result)
    return result


def run_isolated_evidence_fork(
    *,
    season: str,
    gameweek: int,
    evidence_bundle_path: Path,
    canonical_root: Path,
    episode_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Run one additive evidence-adjusted decision and score it after freeze."""
    if gameweek != 12:
        raise EvidenceForkError("The first evidence fork is intentionally limited to GW12")
    canonical_resolved = canonical_root.resolve()
    output_resolved = output_root.resolve()
    if output_resolved == canonical_resolved or canonical_resolved in output_resolved.parents:
        raise EvidenceForkError("Fork output must not be inside the canonical replay root")

    bundle = _read(evidence_bundle_path)
    assessment = validate_reconstructed_bundle(bundle)
    if str(bundle["decision_cutoff"]) != str(assessment["decision_cutoff"]):
        raise EvidenceForkError("Evidence assessment cutoff mismatch")

    canonical_gw = canonical_root / f"gw-{gameweek:02d}"
    episode = episode_root / f"gw-{gameweek:02d}"
    setup_arm = canonical_gw / "setup" / "arms" / "evidence_agent"
    manifest = _read(episode / "episode-manifest.json")
    if bundle["decision_cutoff"] != manifest["deadline"]:
        raise EvidenceForkError("Evidence bundle cutoff does not match episode deadline")
    state = _read(setup_arm / "starting-policy-state.json")
    solver_input = _read(setup_arm / "reviewed-engine-input.json")
    adjusted_input, applied = apply_reconstructed_adjustments(solver_input, bundle)
    rules = yaml.safe_load((episode / "ruleset.yaml").read_text(encoding="utf-8"))
    rules_hash = str(manifest["ruleset"]["content_sha256"])
    solver_output = solve(
        SolverInput.from_dict(adjusted_input),
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    candidate = deepcopy(dict(solver_output["selected"]))
    plan = validate_and_freeze_plan(
        episode_id=str(manifest["episode_id"]),
        policy_arm="evidence_agent",
        state=state,
        candidate=candidate,
        decision_market=adjusted_input["players"],
        active_chip=None,
        frozen_at=str(manifest["deadline"]),
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    if plan.get("validation", {}).get("status") != "passed" or not plan.get(
        "content_sha256"
    ):
        raise EvidenceForkError("Hidden outcome access requires a frozen valid plan")

    # This is the only hidden-outcome read in the fork and it occurs after freeze.
    hidden = _read(episode / "hidden-outcome.json")
    identity = _read(episode / "identity-map.json")
    shared = _read(canonical_gw / "shared-context.json")
    canonical_outcome = _read(canonical_gw / "evidence_agent" / "realised-outcome.json")
    outcome = score_revealed_outcome(
        plan,
        hidden,
        revealed_at=str(canonical_outcome["revealed_at"]),
        rules=rules,
        ruleset_sha256=rules_hash,
        player_identity_map=_identity_index(identity),
        identity_map_sha256=str(shared["identity_map_sha256"]),
    )
    names = {
        str(row["player_id"]): str(row.get("web_name") or row["player_id"])
        for row in adjusted_input["players"]
    }
    comparison = _sealed(
        {
            "schema_version": "1.0",
            "experiment_id": bundle["experiment_id"],
            "season": season,
            "gameweek": gameweek,
            "exploratory_only": True,
            "case_selection": bundle["case_selection"],
            "canonical_plan_sha256": canonical_outcome["plan_sha256"],
            "fork_plan_sha256": plan["content_sha256"],
            "canonical_gross_points": int(canonical_outcome["gross_points"]),
            "fork_gross_points": int(outcome["gross_points"]),
            "gross_points_delta": int(outcome["gross_points"])
            - int(canonical_outcome["gross_points"]),
            "selected_transfer_names": [
                {
                    "player_out": names[move["player_out_id"]],
                    "player_in": names[move["player_in_id"]],
                }
                for move in candidate["transfers"]
            ],
            "captain": names[candidate["lineup"]["captain_id"]],
            "active_chip": None,
            "hit_cost": int(candidate["hit_cost"]),
            "planning_objective": float(candidate["objective"]),
            "solver_input_sha256": fingerprint(adjusted_input),
            "solver_output_sha256": fingerprint(solver_output),
            "evidence_assessment_sha256": assessment["content_sha256"],
            "score_ceilings": {
                "canonical_selected_15_hindsight_xi_and_captain": _score_ceiling(
                    _read(canonical_gw / "forecast_optimizer" / "validated-plan.json")[
                        "squad_after"
                    ],
                    hidden,
                ),
                "fork_selected_15_hindsight_xi_and_captain": _score_ceiling(
                    plan["squad_after"], hidden
                ),
                "interpretation": (
                    "Availability evidence can improve GW12, but neither selected "
                    "15 contains a 100-point legal XI-and-captain combination."
                ),
            },
            "limitations": assessment["limitations"],
        }
    )

    _write_once(output_root / "evidence-assessment.json", assessment)
    _write_once(
        output_root / "applied-adjustments.json",
        _sealed(
            {
                "schema_version": "1.0",
                "experiment_id": bundle["experiment_id"],
                "adjustments": applied,
            }
        ),
    )
    _write_once(output_root / "adjusted-solver-input.json", adjusted_input)
    _write_once(
        output_root / "selected-candidate.json",
        _sealed(
            {
                "schema_version": "1.0",
                "candidate": candidate,
                "solver_output_sha256": fingerprint(solver_output),
            }
        ),
    )
    _write_once(output_root / "validated-plan.json", plan)
    _write_once(output_root / "realised-outcome.json", outcome)
    _write_once(output_root / "comparison.json", comparison)
    return comparison


def run_longitudinal_evidence_fork(
    *,
    season: str,
    gameweek: int,
    evidence_bundle_path: Path,
    canonical_root: Path,
    episode_root: Path,
    output_root: Path,
    terminal_gameweek: int = 38,
) -> dict[str, Any]:
    """Carry the isolated GW12 decision through an independent replanned season."""

    if gameweek != 12:
        raise EvidenceForkError("The first longitudinal fork must begin at GW12")
    if terminal_gameweek < gameweek or terminal_gameweek > 38:
        raise EvidenceForkError("terminal_gameweek must be between GW12 and GW38")
    canonical_before, file_count = _canonical_span_hash(
        canonical_root, start_gameweek=12, end_gameweek=terminal_gameweek
    )
    comparison = run_isolated_evidence_fork(
        season=season,
        gameweek=gameweek,
        evidence_bundle_path=evidence_bundle_path,
        canonical_root=canonical_root,
        episode_root=episode_root,
        output_root=output_root,
    )
    canonical_gw = canonical_root / "gw-12"
    episode = episode_root / "gw-12"
    state = _read(
        canonical_gw
        / "setup"
        / "arms"
        / "evidence_agent"
        / "starting-policy-state.json"
    )
    adjusted_input = _read(output_root / "adjusted-solver-input.json")
    plan = _read(output_root / "validated-plan.json")
    outcome = _read(output_root / "realised-outcome.json")
    manifest = _read(episode / "episode-manifest.json")
    rules = yaml.safe_load((episode / "ruleset.yaml").read_text(encoding="utf-8"))
    rules_hash = str(manifest["ruleset"]["content_sha256"])
    next_feature = _read(
        canonical_root / "gw-13" / "setup" / "shared-feature-state.json"
    )
    successor, transition = transition_policy_state(
        state,
        plan,
        outcome,
        decision_market=adjusted_input["players"],
        next_market=_market_from_feature_state(next_feature),
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    weeks: list[dict[str, Any]] = [
        {
            "gameweek": 12,
            "evidence_applied": True,
            "starting_state_sha256": state["content_sha256"],
            "solver_input_sha256": comparison["solver_input_sha256"],
            "solver_output_sha256": comparison["solver_output_sha256"],
            "plan_sha256": plan["content_sha256"],
            "outcome_sha256": outcome["content_sha256"],
            "transition_sha256": transition["content_sha256"],
            "next_state_sha256": successor["content_sha256"],
            "transfers": deepcopy(plan["transfers"]),
            "hit_cost": int(plan["finance"]["hit_cost"]),
            "gross_points": int(outcome["gross_points"]),
            "net_points": int(transition["net_points"]),
        }
    ]
    state = successor

    for current_gameweek in range(13, terminal_gameweek + 1):
        canonical_week = canonical_root / f"gw-{current_gameweek:02d}"
        setup = canonical_week / "setup"
        current_episode = episode_root / f"gw-{current_gameweek:02d}"
        feature = _read(setup / "shared-feature-state.json")
        forecast = _read(setup / "shared-locked-forecast.json")
        current_manifest = _read(current_episode / "episode-manifest.json")
        current_rules = yaml.safe_load(
            (current_episode / "ruleset.yaml").read_text(encoding="utf-8")
        )
        current_rules_hash = str(
            current_manifest["ruleset"]["content_sha256"]
        )
        solver_input = build_replay_solver_input(
            feature_state=feature,
            policy_state=state,
            forecast_view=forecast,
            max_transfers=3,
            transfer_value_policy="expected_hit_avoidance_v1",
            probability_extra_transfer_needed=(
                0.0 if current_gameweek == 38 else 0.5
            ),
            future_transfer_discount=0.9,
        )
        solver_output = solve(
            solver_input,
            rules=current_rules,
            ruleset_sha256=current_rules_hash,
        )
        candidate = solver_output["selected"]
        current_plan = validate_and_freeze_plan(
            episode_id=str(current_manifest["episode_id"]),
            policy_arm=str(state["policy_arm"]),
            state=state,
            candidate=candidate,
            decision_market=solver_input.players,
            active_chip=None,
            frozen_at=str(current_manifest["deadline"]),
            rules=current_rules,
            ruleset_sha256=current_rules_hash,
        )

        # Each week's hidden outcome is opened only after that week's plan freezes.
        hidden = _read(current_episode / "hidden-outcome.json")
        identity = _read(current_episode / "identity-map.json")
        shared = _read(canonical_week / "shared-context.json")
        canonical_outcome = _read(
            canonical_week / "evidence_agent" / "realised-outcome.json"
        )
        current_outcome = score_revealed_outcome(
            current_plan,
            hidden,
            revealed_at=str(canonical_outcome["revealed_at"]),
            rules=current_rules,
            ruleset_sha256=current_rules_hash,
            player_identity_map=_identity_index(identity),
            identity_map_sha256=str(shared["identity_map_sha256"]),
        )
        if current_gameweek == terminal_gameweek:
            next_market = _market_from_feature_state(feature)
        else:
            future_feature = _read(
                canonical_root
                / f"gw-{current_gameweek + 1:02d}"
                / "setup"
                / "shared-feature-state.json"
            )
            next_market = _market_from_feature_state(future_feature)
        next_state, current_transition = transition_policy_state(
            state,
            current_plan,
            current_outcome,
            decision_market=solver_input.players,
            next_market=next_market,
            rules=current_rules,
            ruleset_sha256=current_rules_hash,
        )
        names = {
            str(row["player_id"]): str(
                row.get("web_name") or row["player_id"]
            )
            for row in solver_input.players
        }
        weeks.append(
            {
                "gameweek": current_gameweek,
                "evidence_applied": False,
                "starting_state_sha256": state["content_sha256"],
                "solver_input_sha256": fingerprint(solver_input.as_dict()),
                "solver_output_sha256": fingerprint(solver_output),
                "plan_sha256": current_plan["content_sha256"],
                "outcome_sha256": current_outcome["content_sha256"],
                "transition_sha256": current_transition["content_sha256"],
                "next_state_sha256": next_state["content_sha256"],
                "transfers": [
                    {
                        **deepcopy(move),
                        "player_out_name": names[move["player_out_id"]],
                        "player_in_name": names[move["player_in_id"]],
                    }
                    for move in current_plan["transfers"]
                ],
                "hit_cost": int(current_plan["finance"]["hit_cost"]),
                "gross_points": int(current_outcome["gross_points"]),
                "net_points": int(current_transition["net_points"]),
            }
        )
        state = next_state

    canonical_weeks: list[dict[str, Any]] = []
    for current_gameweek in range(gameweek, terminal_gameweek + 1):
        directory = (
            canonical_root
            / f"gw-{current_gameweek:02d}"
            / "evidence_agent"
        )
        canonical_plan = _read(directory / "validated-plan.json")
        canonical_outcome = _read(directory / "realised-outcome.json")
        canonical_transition = _read(directory / "state-transition.json")
        canonical_weeks.append(
            {
                "gameweek": current_gameweek,
                "plan_sha256": canonical_plan["content_sha256"],
                "outcome_sha256": canonical_outcome["content_sha256"],
                "transition_sha256": canonical_transition["content_sha256"],
                "net_points": int(canonical_transition["net_points"]),
            }
        )
    canonical_after, after_count = _canonical_span_hash(
        canonical_root, start_gameweek=12, end_gameweek=terminal_gameweek
    )
    if (canonical_before, file_count) != (canonical_after, after_count):
        raise EvidenceForkError("Canonical replay changed during longitudinal fork")
    fork_total = sum(int(row["net_points"]) for row in weeks)
    canonical_total = sum(int(row["net_points"]) for row in canonical_weeks)
    result = _sealed(
        {
            "schema_version": "1.0",
            "experiment_id": comparison["experiment_id"],
            "season": season,
            "start_gameweek": gameweek,
            "terminal_gameweek": terminal_gameweek,
            "comparison_type": "retrospective_longitudinal_independent_state",
            "exploratory_only": True,
            "promotion_eligible": False,
            "case_selection": comparison["case_selection"],
            "evidence_applied_gameweeks": [12],
            "later_gameweek_policy": (
                "replan from independent state using each later week's canonical "
                "sealed structured forecast; no further evidence injection"
            ),
            "canonical_net_points": canonical_total,
            "fork_net_points": fork_total,
            "net_points_delta": fork_total - canonical_total,
            "terminal_cumulative_points": int(state["cumulative_points"]),
            "terminal_state_sha256": state["content_sha256"],
            "fork_weeks": weeks,
            "canonical_weeks": canonical_weeks,
            "canonical_artifacts": {
                "start_gameweek": 12,
                "end_gameweek": terminal_gameweek,
                "file_count": file_count,
                "tree_sha256_before": canonical_before,
                "tree_sha256_after": canonical_after,
                "unchanged": True,
            },
            "limitations": [
                *comparison["limitations"],
                "only_gw12_receives_reconstructed_unstructured_evidence",
                "later_decisions_use_structured_forecast_fallback",
                "retrospective_case_selection_can_overstate_evidence_value",
            ],
        }
    )
    _write_once(output_root / "longitudinal.json", result)
    return result
