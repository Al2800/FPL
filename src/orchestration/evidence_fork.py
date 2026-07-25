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
from src.optimisation.io import fingerprint
from src.optimisation.solver import solve
from src.optimisation.types import SolverInput
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


def _apply_adjustments(
    solver_input: Mapping[str, Any], bundle: Mapping[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
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
    adjusted_input, applied = _apply_adjustments(solver_input, bundle)
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
