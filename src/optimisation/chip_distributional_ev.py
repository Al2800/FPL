"""Distributional chip-now vs later EV comparisons (ticket 09 / ADR-0023).

Consumes Monte Carlo plan-point samples. Does not change the live planning
horizon; destination 4-GW comparison is an explicit replay/annotation surface.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import hashlib
import json
from typing import Any

from src.forecasting.monte_carlo import percentile_summary, plan_points_samples


class ChipDistributionalEvError(ValueError):
    """Raised when distributional chip inputs are incomplete or unsafe."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def distributional_hash(value: Mapping[str, Any]) -> str:
    payload = {
        key: item for key, item in value.items() if key != "content_sha256"
    }
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = distributional_hash(result)
    return result


def _samples(values: Sequence[float], *, field: str) -> list[float]:
    if not values:
        raise ChipDistributionalEvError(f"{field} must contain at least one sample")
    out: list[float] = []
    for item in values:
        number = float(item)
        if number != number:  # NaN
            raise ChipDistributionalEvError(f"{field} contains a non-finite sample")
        out.append(number)
    return out


def compare_plan_distributions(
    *,
    candidate_id: str,
    samples: Sequence[float],
    alternative_id: str,
    alternative_samples: Sequence[float],
) -> dict[str, Any]:
    """Paired path comparison: P(candidate beats alternative) and delta EV."""

    left = _samples(samples, field="samples")
    right = _samples(alternative_samples, field="alternative_samples")
    if len(left) != len(right):
        raise ChipDistributionalEvError(
            "candidate and alternative sample paths must be the same length"
        )
    deltas = [a - b for a, b in zip(left, right, strict=True)]
    wins = sum(1 for delta in deltas if delta > 0)
    ties = sum(1 for delta in deltas if delta == 0)
    losses = len(deltas) - wins - ties
    summary = percentile_summary(deltas)
    return {
        "candidate_id": candidate_id,
        "alternative_id": alternative_id,
        "n_paths": len(deltas),
        "prob_candidate_beats_alternative": round(wins / len(deltas), 6),
        "prob_tie": round(ties / len(deltas), 6),
        "prob_alternative_beats_candidate": round(losses / len(deltas), 6),
        "mean_delta": summary["mean"],
        "p10_delta": summary["p10"],
        "p50_delta": summary["p50"],
        "p90_delta": summary["p90"],
    }


def plan_samples_from_chip_candidates(
    candidates: Sequence[Mapping[str, Any]],
    *,
    player_path_points: Mapping[str, Sequence[float]],
) -> dict[str, list[float]]:
    """Build per-candidate plan-point paths from Monte Carlo player paths."""

    if not candidates:
        raise ChipDistributionalEvError("candidates must be non-empty")
    samples_by_id: dict[str, list[float]] = {}
    for row in candidates:
        candidate_id = str(row["candidate_id"])
        candidate = row.get("candidate") if isinstance(row.get("candidate"), Mapping) else {}
        lineup = (
            candidate.get("lineup") if isinstance(candidate.get("lineup"), Mapping) else {}
        )
        starting = lineup.get("starting_xi_ids") or lineup.get("starting_xi") or []
        xi = [
            str(player["player_id"] if isinstance(player, Mapping) else player)
            for player in starting
        ]
        captain = lineup.get("captain_id")
        if not xi or captain is None:
            raise ChipDistributionalEvError(
                f"candidate {candidate_id} lacks starting XI / captain for sampling"
            )
        missing = [player_id for player_id in xi if player_id not in player_path_points]
        if missing:
            raise ChipDistributionalEvError(
                f"candidate {candidate_id} missing path points for {missing}"
            )
        samples_by_id[candidate_id] = plan_points_samples(
            player_path_points,
            starting_xi=xi,
            captain_id=str(captain),
            hit_cost=int(candidate.get("hit_cost") or 0),
        )
    return samples_by_id


def annotate_chip_candidates_with_distributions(
    selection: Mapping[str, Any],
    *,
    plan_samples_by_candidate: Mapping[str, Sequence[float]],
    later_reference_candidate_id: str | None = None,
) -> dict[str, Any]:
    """Attach distributional now-vs-later justification to a chip selection.

    ``later_reference_candidate_id`` defaults to the no-chip control. Chip-now
    candidates are compared pathwise against that reference.
    """

    candidates = list(selection.get("candidates") or [])
    if not candidates:
        raise ChipDistributionalEvError("selection has no candidates")
    reference_id = later_reference_candidate_id or str(
        selection.get("no_chip_control_id") or ""
    )
    if not reference_id:
        raise ChipDistributionalEvError("no-chip control id is required")
    if reference_id not in plan_samples_by_candidate:
        raise ChipDistributionalEvError(
            f"missing path samples for reference candidate {reference_id}"
        )
    reference_samples = plan_samples_by_candidate[reference_id]

    annotated: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    for row in candidates:
        item = deepcopy(dict(row))
        candidate_id = str(item["candidate_id"])
        if candidate_id not in plan_samples_by_candidate:
            raise ChipDistributionalEvError(
                f"missing path samples for candidate {candidate_id}"
            )
        samples = plan_samples_by_candidate[candidate_id]
        summary = percentile_summary(_samples(samples, field=candidate_id))
        item["points_distribution"] = {
            **summary,
            "n_paths": len(samples),
        }
        if candidate_id != reference_id:
            comparison = compare_plan_distributions(
                candidate_id=candidate_id,
                samples=samples,
                alternative_id=reference_id,
                alternative_samples=reference_samples,
            )
            item["distributional_vs_later"] = comparison
            comparisons.append(comparison)
        else:
            item["distributional_vs_later"] = None
        annotated.append(item)

    selected_id = str(selection.get("selected_candidate_id"))
    selected_comparison = next(
        (
            row["distributional_vs_later"]
            for row in annotated
            if row["candidate_id"] == selected_id
        ),
        None,
    )
    result = deepcopy(dict(selection))
    result["candidates"] = annotated
    result["distributional_justification"] = {
        "reference_candidate_id": reference_id,
        "selected_candidate_id": selected_id,
        "selected_vs_later": selected_comparison,
        "comparisons": comparisons,
        "interpretation": (
            "Pathwise Monte Carlo comparison of chip-now plan points versus the "
            "no-chip later-control distribution; does not authorise multi-GW "
            "live search by itself"
        ),
    }
    return result


def build_horizon_policy_comparison(
    *,
    baseline_label: str,
    baseline_metrics: Mapping[str, Any],
    destination_label: str,
    destination_metrics: Mapping[str, Any],
    paired_delta: Mapping[str, Any] | None = None,
    source_refs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Seal a reproducible horizon-policy comparison for ADR-0023 ratification.

    Live optimisation remains single-GW until cutoff-safe 4-GW forecasts exist;
    this artifact records the paired replay difference only.
    """

    return _seal(
        {
            "schema_version": "chip-horizon-policy-comparison-v1",
            "baseline": {
                "label": baseline_label,
                "horizon_gameweeks": 1,
                "policy": "ADR-0020 expected_hit_avoidance bridge",
                "metrics": dict(baseline_metrics),
            },
            "destination": {
                "label": destination_label,
                "horizon_gameweeks": 4,
                "discount_factor": 0.9,
                "policy": "ADR-0023 / transfer-horizon-v1 alignment",
                "metrics": dict(destination_metrics),
                "live_active": False,
            },
            "paired_delta": dict(paired_delta or {}),
            "source_refs": dict(source_refs or {}),
            "notes": (
                "Ticket 09 horizon ratification surface. Destination metrics must "
                "come from cutoff-safe multi-GW forecasts; do not invent future "
                "player points in the live path."
            ),
        }
    )


def build_horizon_comparison_from_transfer_hit_evaluation(
    evaluation: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive a sealed 1-GW vs 4-GW comparison from a sealed hit-gate evaluation."""

    gated = evaluation.get("gated_solver_selection")
    gate = (
        gated.get("transfer_hit_gate")
        if isinstance(gated, Mapping)
        else evaluation.get("transfer_hit_gate")
    )
    if not isinstance(gate, Mapping):
        raise ChipDistributionalEvError("evaluation lacks transfer_hit_gate")
    selected_id = str(gate.get("selected_candidate_id") or "")
    if not selected_id:
        raise ChipDistributionalEvError("transfer_hit_gate lacks selected_candidate_id")

    hit_ladder = evaluation.get("transfer_hit_ladder")
    ladder: Any = None
    if isinstance(hit_ladder, Mapping):
        ladder = hit_ladder.get("transfer_ladder")
    if not isinstance(ladder, list):
        ladder = evaluation.get("transfer_ladder")
    if not isinstance(ladder, list):
        raise ChipDistributionalEvError("evaluation lacks transfer_ladder")

    selected_row = next(
        (
            row
            for row in ladder
            if isinstance(row, Mapping) and str(row.get("candidate_id")) == selected_id
        ),
        None,
    )
    if selected_row is None:
        raise ChipDistributionalEvError(
            f"selected candidate {selected_id} missing from transfer_ladder"
        )

    immediate = float(selected_row["immediate_net_points"])
    horizon_net = float(selected_row["horizon_net_value"])
    weekly = list(selected_row.get("horizon_weekly_net_values") or [])
    return build_horizon_policy_comparison(
        baseline_label="single_gw_adr0020_selected",
        baseline_metrics={
            "immediate_net_points": immediate,
            "selected_candidate_id": selected_id,
        },
        destination_label="four_gw_destination_selected",
        destination_metrics={
            "horizon_net_value": horizon_net,
            "horizon_weekly_net_values": weekly,
            "selected_candidate_id": selected_id,
            "horizon_gameweeks": list(evaluation.get("horizon_gameweeks") or []),
        },
        paired_delta={
            "horizon_minus_immediate_net_points": round(horizon_net - immediate, 6),
        },
        source_refs={
            "report_id": evaluation.get("report_id"),
            "content_sha256": evaluation.get("content_sha256"),
            "horizon_sha256": evaluation.get("horizon_sha256"),
            "season": evaluation.get("season"),
            "gameweek": evaluation.get("gameweek"),
        },
    )


def attach_distributional_chip_annotation_to_gdr(
    record: Mapping[str, Any],
    *,
    chip_selection: Mapping[str, Any],
    horizon_comparison: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Copy distributional chip justification onto a Gameweek Decision Record."""

    result = deepcopy(dict(record))
    justification = chip_selection.get("distributional_justification")
    if justification is None:
        raise ChipDistributionalEvError(
            "chip_selection lacks distributional_justification; annotate first"
        )
    result["chip_distributional_ev"] = {
        "selected_candidate_id": chip_selection.get("selected_candidate_id"),
        "selected_active_chip": chip_selection.get("selected_active_chip"),
        "justification": deepcopy(dict(justification)),
        "horizon_comparison_sha256": (
            horizon_comparison.get("content_sha256")
            if isinstance(horizon_comparison, Mapping)
            else None
        ),
    }
    if horizon_comparison is not None:
        result["chip_horizon_policy_comparison"] = deepcopy(dict(horizon_comparison))
    return result
