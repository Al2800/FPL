"""Reusable isolated and longitudinal timestamp-sealed evidence programme."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import yaml

from src.evaluation.outcome_scorer import score_revealed_outcome
from src.forecasting.live_faithful import artifact_hash
from src.forecasting.replay_adapter import build_replay_solver_input
from src.optimisation.io import fingerprint
from src.optimisation.solver import solve
from src.optimisation.types import SolverInput
from src.orchestration.evidence_fork import (
    EvidenceForkError,
    _canonical_span_hash,
    apply_reconstructed_adjustments,
    validate_reconstructed_bundle,
)
from src.orchestration.policy_state import transition_policy_state
from src.orchestration.validated_plan import validate_and_freeze_plan


class WeeklyEvidenceProgrammeError(ValueError):
    """Raised when a weekly evidence programme violates its temporal contract."""


PROGRAMME_VERSION = "weekly-evidence-programme-v1"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sealed(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def _identity_index(identity_map: Mapping[str, Any]) -> dict[str, str]:
    return {
        str(row["fpl_player_id"]): str(row["canonical_id"])
        for row in identity_map["players"]
    }


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


def _load_week(
    *,
    canonical_root: Path,
    episode_root: Path,
    gameweek: int,
) -> dict[str, Any]:
    canonical = canonical_root / f"gw-{gameweek:02d}"
    episode = episode_root / f"gw-{gameweek:02d}"
    feature = _read(canonical / "setup" / "shared-feature-state.json")
    forecast = _read(canonical / "setup" / "shared-locked-forecast.json")
    manifest = _read(episode / "episode-manifest.json")
    rules = yaml.safe_load((episode / "ruleset.yaml").read_text(encoding="utf-8"))
    return {
        "canonical": canonical,
        "episode": episode,
        "feature": feature,
        "forecast": forecast,
        "manifest": manifest,
        "rules": rules,
        "rules_hash": str(manifest["ruleset"]["content_sha256"]),
    }


def _load_bundles(
    bundle_paths: Mapping[int, Path],
    *,
    episode_root: Path,
    start_gameweek: int,
    terminal_gameweek: int,
) -> dict[int, dict[str, Any]]:
    if not bundle_paths:
        raise WeeklyEvidenceProgrammeError("at least one evidence bundle is required")
    result: dict[int, dict[str, Any]] = {}
    for raw_gameweek, path in sorted(bundle_paths.items()):
        gameweek = int(raw_gameweek)
        if not start_gameweek <= gameweek <= terminal_gameweek:
            raise WeeklyEvidenceProgrammeError(
                f"evidence GW{gameweek} is outside the programme range"
            )
        if gameweek in result:
            raise WeeklyEvidenceProgrammeError(
                f"duplicate evidence bundle for GW{gameweek}"
            )
        bundle = _read(path)
        try:
            assessment = validate_reconstructed_bundle(bundle)
        except EvidenceForkError as exc:
            raise WeeklyEvidenceProgrammeError(str(exc)) from exc
        manifest = _read(
            episode_root / f"gw-{gameweek:02d}" / "episode-manifest.json"
        )
        if str(bundle["decision_cutoff"]) != str(manifest["deadline"]):
            raise WeeklyEvidenceProgrammeError(
                f"GW{gameweek} evidence cutoff does not match episode deadline"
            )
        result[gameweek] = {
            "path": path.as_posix(),
            "bundle": bundle,
            "bundle_sha256": artifact_hash(bundle),
            "assessment": assessment,
        }
    return result


def _solver_input_for_state(
    *,
    week: Mapping[str, Any],
    state: Mapping[str, Any],
    gameweek: int,
) -> SolverInput:
    return build_replay_solver_input(
        feature_state=week["feature"],
        policy_state=state,
        forecast_view=week["forecast"],
        max_transfers=3,
        transfer_value_policy="expected_hit_avoidance_v1",
        probability_extra_transfer_needed=0.0 if gameweek == 38 else 0.5,
        future_transfer_discount=0.9,
    )


def _evidence_summary(
    bundle_record: Mapping[str, Any],
    applied: list[Mapping[str, Any]],
) -> dict[str, Any]:
    bundle = bundle_record["bundle"]
    assessment = bundle_record["assessment"]
    assessed = {
        str(row["claim_id"]): row for row in assessment["sources"]
    }
    return {
        "bundle_path": bundle_record["path"],
        "bundle_sha256": bundle_record["bundle_sha256"],
        "assessment_sha256": assessment["content_sha256"],
        "decision_cutoff": bundle["decision_cutoff"],
        "captured_at": bundle["captured_at"],
        "production_eligible": bool(assessment["production_eligible"]),
        "case_selection": bundle["case_selection"],
        "claims": [
            {
                "source_id": source["source_id"],
                "url": source["url"],
                "claim_id": source["claim_id"],
                "player_id": source["player_id"],
                "published_at": source["published_at"],
                "captured_at": source["captured_at"],
                "expires_at": source["expires_at"],
                "claim_confidence": float(source["confidence"]),
                "citation_excerpt_sha256": assessed[source["claim_id"]][
                    "citation_excerpt_sha256"
                ],
                "adjustment_id": source["adjustment"]["adjustment_id"],
                "adjustment_target": source["adjustment"]["target"],
                "adjustment_confidence": float(
                    source["adjustment"]["confidence"]
                ),
            }
            for source in bundle["sources"]
        ],
        "applied_adjustments": deepcopy(applied),
    }


def _freeze_and_score(
    *,
    state: Mapping[str, Any],
    solver_input: Mapping[str, Any],
    week: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    output = solve(
        SolverInput.from_dict(dict(solver_input)),
        rules=week["rules"],
        ruleset_sha256=week["rules_hash"],
    )
    candidate = output["selected"]
    plan = validate_and_freeze_plan(
        episode_id=str(week["manifest"]["episode_id"]),
        policy_arm=str(state["policy_arm"]),
        state=state,
        candidate=candidate,
        decision_market=solver_input["players"],
        active_chip=None,
        frozen_at=str(week["manifest"]["deadline"]),
        rules=week["rules"],
        ruleset_sha256=week["rules_hash"],
    )
    if plan["validation"]["status"] != "passed":
        raise WeeklyEvidenceProgrammeError("plan did not freeze before reveal")

    # This outcome read is deliberately after the validated-plan boundary.
    hidden = _read(week["episode"] / "hidden-outcome.json")
    identity = _read(week["episode"] / "identity-map.json")
    shared = _read(week["canonical"] / "shared-context.json")
    canonical_outcome = _read(
        week["canonical"] / "evidence_agent" / "realised-outcome.json"
    )
    outcome = score_revealed_outcome(
        plan,
        hidden,
        revealed_at=str(canonical_outcome["revealed_at"]),
        rules=week["rules"],
        ruleset_sha256=week["rules_hash"],
        player_identity_map=_identity_index(identity),
        identity_map_sha256=str(shared["identity_map_sha256"]),
    )
    return output, plan, outcome


def _isolated_week(
    *,
    season: str,
    gameweek: int,
    bundle_record: Mapping[str, Any],
    canonical_root: Path,
    episode_root: Path,
) -> dict[str, Any]:
    week = _load_week(
        canonical_root=canonical_root,
        episode_root=episode_root,
        gameweek=gameweek,
    )
    state = _read(
        week["canonical"]
        / "setup"
        / "arms"
        / "evidence_agent"
        / "starting-policy-state.json"
    )
    base_input = _solver_input_for_state(
        week=week, state=state, gameweek=gameweek
    ).as_dict()
    adjusted_input, applied = apply_reconstructed_adjustments(
        base_input, bundle_record["bundle"]
    )
    output, plan, outcome = _freeze_and_score(
        state=state,
        solver_input=adjusted_input,
        week=week,
    )
    canonical_plan = _read(
        week["canonical"] / "evidence_agent" / "validated-plan.json"
    )
    canonical_outcome = _read(
        week["canonical"] / "evidence_agent" / "realised-outcome.json"
    )
    canonical_net = int(canonical_outcome["gross_points"]) - int(
        canonical_plan["finance"]["hit_cost"]
    )
    fork_net = int(outcome["gross_points"]) - int(plan["finance"]["hit_cost"])
    names = {
        str(row["player_id"]): str(row.get("web_name") or row["player_id"])
        for row in adjusted_input["players"]
    }
    return {
        "season": season,
        "gameweek": gameweek,
        "comparison_type": "isolated_same_starting_state",
        "state_advanced": False,
        "starting_state_sha256": state["content_sha256"],
        "canonical_plan_sha256": canonical_plan["content_sha256"],
        "canonical_outcome_sha256": canonical_outcome["content_sha256"],
        "fork_plan_sha256": plan["content_sha256"],
        "fork_outcome_sha256": outcome["content_sha256"],
        "solver_input_sha256": fingerprint(adjusted_input),
        "solver_output_sha256": fingerprint(output),
        "canonical_net_points": canonical_net,
        "fork_net_points": fork_net,
        "net_points_delta": fork_net - canonical_net,
        "transfers": [
            {
                **deepcopy(move),
                "player_out_name": names[move["player_out_id"]],
                "player_in_name": names[move["player_in_id"]],
            }
            for move in plan["transfers"]
        ],
        "evidence": _evidence_summary(bundle_record, applied),
    }


def run_weekly_evidence_programme(
    *,
    season: str,
    bundle_paths: Mapping[int, Path],
    canonical_root: Path,
    episode_root: Path,
    terminal_gameweek: int = 38,
) -> dict[str, Any]:
    """Run isolated attribution and one independently compounded trajectory."""

    selected = sorted(int(value) for value in bundle_paths)
    if not selected:
        raise WeeklyEvidenceProgrammeError("no selected evidence Gameweeks")
    start_gameweek = selected[0]
    if start_gameweek < 2 or terminal_gameweek > 38:
        raise WeeklyEvidenceProgrammeError(
            "historical programme supports GW2 through GW38"
        )
    bundles = _load_bundles(
        bundle_paths,
        episode_root=episode_root,
        start_gameweek=start_gameweek,
        terminal_gameweek=terminal_gameweek,
    )
    before_hash, before_count = _canonical_span_hash(
        canonical_root,
        start_gameweek=start_gameweek,
        end_gameweek=terminal_gameweek,
    )
    isolated = [
        _isolated_week(
            season=season,
            gameweek=gameweek,
            bundle_record=bundles[gameweek],
            canonical_root=canonical_root,
            episode_root=episode_root,
        )
        for gameweek in selected
    ]

    opening_week = _load_week(
        canonical_root=canonical_root,
        episode_root=episode_root,
        gameweek=start_gameweek,
    )
    state = _read(
        opening_week["canonical"]
        / "setup"
        / "arms"
        / "evidence_agent"
        / "starting-policy-state.json"
    )
    longitudinal_weeks: list[dict[str, Any]] = []
    for gameweek in range(start_gameweek, terminal_gameweek + 1):
        week = (
            opening_week
            if gameweek == start_gameweek
            else _load_week(
                canonical_root=canonical_root,
                episode_root=episode_root,
                gameweek=gameweek,
            )
        )
        solver_input = _solver_input_for_state(
            week=week, state=state, gameweek=gameweek
        ).as_dict()
        evidence: dict[str, Any] | None = None
        if gameweek in bundles:
            solver_input, applied = apply_reconstructed_adjustments(
                solver_input, bundles[gameweek]["bundle"]
            )
            evidence = _evidence_summary(bundles[gameweek], applied)
        output, plan, outcome = _freeze_and_score(
            state=state,
            solver_input=solver_input,
            week=week,
        )
        if gameweek == terminal_gameweek:
            next_market = _market_from_feature_state(week["feature"])
        else:
            next_feature = _read(
                canonical_root
                / f"gw-{gameweek + 1:02d}"
                / "setup"
                / "shared-feature-state.json"
            )
            next_market = _market_from_feature_state(next_feature)
        successor, transition = transition_policy_state(
            state,
            plan,
            outcome,
            decision_market=solver_input["players"],
            next_market=next_market,
            rules=week["rules"],
            ruleset_sha256=week["rules_hash"],
        )
        canonical_plan = _read(
            week["canonical"] / "evidence_agent" / "validated-plan.json"
        )
        canonical_outcome = _read(
            week["canonical"] / "evidence_agent" / "realised-outcome.json"
        )
        canonical_transition = _read(
            week["canonical"] / "evidence_agent" / "state-transition.json"
        )
        names = {
            str(row["player_id"]): str(
                row.get("web_name") or row["player_id"]
            )
            for row in solver_input["players"]
        }
        longitudinal_weeks.append(
            {
                "gameweek": gameweek,
                "evidence_applied": evidence is not None,
                "starting_state_sha256": state["content_sha256"],
                "solver_input_sha256": fingerprint(solver_input),
                "solver_output_sha256": fingerprint(output),
                "plan_sha256": plan["content_sha256"],
                "outcome_sha256": outcome["content_sha256"],
                "transition_sha256": transition["content_sha256"],
                "next_state_sha256": successor["content_sha256"],
                "canonical_plan_sha256": canonical_plan["content_sha256"],
                "canonical_outcome_sha256": canonical_outcome["content_sha256"],
                "canonical_transition_sha256": canonical_transition[
                    "content_sha256"
                ],
                "canonical_net_points": int(canonical_transition["net_points"]),
                "fork_net_points": int(transition["net_points"]),
                "net_points_delta": int(transition["net_points"])
                - int(canonical_transition["net_points"]),
                "transfers": [
                    {
                        **deepcopy(move),
                        "player_out_name": names[move["player_out_id"]],
                        "player_in_name": names[move["player_in_id"]],
                    }
                    for move in plan["transfers"]
                ],
                "evidence": evidence,
            }
        )
        state = successor

    after_hash, after_count = _canonical_span_hash(
        canonical_root,
        start_gameweek=start_gameweek,
        end_gameweek=terminal_gameweek,
    )
    if (before_hash, before_count) != (after_hash, after_count):
        raise WeeklyEvidenceProgrammeError(
            "canonical artifacts changed during evidence programme"
        )
    direct = sum(int(row["net_points_delta"]) for row in isolated)
    longitudinal_delta = sum(
        int(row["net_points_delta"]) for row in longitudinal_weeks
    )
    production_eligible = all(
        bool(record["assessment"]["production_eligible"])
        for record in bundles.values()
    )
    report = {
        "schema_version": "1.0",
        "programme_version": PROGRAMME_VERSION,
        "programme_id": (
            f"{PROGRAMME_VERSION}:{season}:gw{start_gameweek:02d}-"
            f"gw{terminal_gameweek:02d}"
        ),
        "season": season,
        "start_gameweek": start_gameweek,
        "terminal_gameweek": terminal_gameweek,
        "selected_evidence_gameweeks": selected,
        "production_eligible": production_eligible,
        "promotion_eligible": production_eligible,
        "isolated_results": isolated,
        "longitudinal": {
            "comparison_type": "independent_state_compounding",
            "weeks": longitudinal_weeks,
            "canonical_net_points": sum(
                int(row["canonical_net_points"])
                for row in longitudinal_weeks
            ),
            "fork_net_points": sum(
                int(row["fork_net_points"]) for row in longitudinal_weeks
            ),
            "net_points_delta": longitudinal_delta,
            "terminal_cumulative_points": int(state["cumulative_points"]),
            "terminal_state_sha256": state["content_sha256"],
        },
        "attribution": {
            "isolated_direct_net_points_delta": direct,
            "longitudinal_net_points_delta": longitudinal_delta,
            "state_compounding_net_points_delta": longitudinal_delta - direct,
            "interpretation": (
                "isolated direct effects do not advance altered state; the "
                "difference between longitudinal and isolated totals is compounding"
            ),
        },
        "canonical_artifacts": {
            "file_count": before_count,
            "tree_sha256_before": before_hash,
            "tree_sha256_after": after_hash,
            "unchanged": True,
        },
        "limitations": sorted(
            {
                limitation
                for record in bundles.values()
                for limitation in record["assessment"]["limitations"]
            }
        ),
    }
    report["content_sha256"] = artifact_hash(report)
    return report


def write_weekly_evidence_report(
    path: Path, report: Mapping[str, Any]
) -> None:
    """Write once and fail if an existing sealed report would change."""

    text = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise WeeklyEvidenceProgrammeError(
                f"refusing to overwrite different sealed report: {path}"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
