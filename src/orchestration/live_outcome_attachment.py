"""Attach post-lock outcomes and retrospectives to live Gameweek Decision Records.

Ingests recorded `event/{gw}/live` (plus bootstrap positions), scores the frozen
validated plan, computes decision metrics, and appends outcome/retrospective
fields. Provisional results never overwrite final ones (§7.5).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.evaluation.outcome_scorer import OutcomeScoringError, score_revealed_outcome
from src.optimisation.io import fingerprint
from src.reporting.baseline_comparison import (
    attach_retrospective,
    compare_realised_outcomes,
    retrospective_metrics,
)
from src.reporting.decision_record import write_decision_record
from src.scoring.rules_loader import load_rules, ruleset_sha256


POSITION_BY_TYPE = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}


class LiveOutcomeAttachmentError(ValueError):
    """Raised when a live outcome cannot be attached safely."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LiveOutcomeAttachmentError(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LiveOutcomeAttachmentError(f"Expected JSON object at {path}")
    return value


def _bootstrap_positions(bootstrap: Mapping[str, Any]) -> dict[str, str]:
    elements = bootstrap.get("elements")
    if not isinstance(elements, list) or not elements:
        raise LiveOutcomeAttachmentError("bootstrap elements catalogue is missing")
    positions: dict[str, str] = {}
    for row in elements:
        if not isinstance(row, Mapping):
            continue
        try:
            player_id = str(int(row["id"]))
            element_type = int(row["element_type"])
        except (KeyError, TypeError, ValueError) as exc:
            raise LiveOutcomeAttachmentError("bootstrap element row is malformed") from exc
        position = POSITION_BY_TYPE.get(element_type)
        if position is None:
            raise LiveOutcomeAttachmentError(f"unknown element_type {element_type}")
        positions[player_id] = position
    return positions


def event_live_to_player_outcomes(
    live: Mapping[str, Any],
    *,
    bootstrap: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Flatten official event/{gw}/live elements into scorer player_outcome rows.

    Prefers top-level `stats` (one aggregate row per player). When stats are
    absent, falls back to per-fixture `explain` blocks.
    """

    positions = _bootstrap_positions(bootstrap)
    elements = live.get("elements")
    if not isinstance(elements, list):
        raise LiveOutcomeAttachmentError("event live payload missing elements array")
    rows: list[dict[str, Any]] = []
    for element in elements:
        if not isinstance(element, Mapping):
            raise LiveOutcomeAttachmentError("event live element must be an object")
        try:
            player_id = str(int(element["id"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise LiveOutcomeAttachmentError("event live element id is malformed") from exc
        position = positions.get(player_id)
        if position is None:
            continue
        stats = element.get("stats") if isinstance(element.get("stats"), Mapping) else None
        if stats is not None:
            minutes = stats.get("minutes", 0)
            points = stats.get("total_points", 0)
            if isinstance(minutes, bool) or not isinstance(minutes, int) or minutes < 0:
                raise LiveOutcomeAttachmentError(
                    f"live stats minutes invalid for player {player_id}"
                )
            if isinstance(points, bool) or not isinstance(points, int):
                raise LiveOutcomeAttachmentError(
                    f"live stats total_points invalid for player {player_id}"
                )
            rows.append(
                {
                    "element": int(player_id),
                    "fixture": "0",
                    "position": position,
                    "minutes": minutes,
                    "total_points": points,
                }
            )
            continue
        explain = element.get("explain") if isinstance(element.get("explain"), list) else []
        for block in explain:
            if not isinstance(block, Mapping):
                continue
            fixture_id = str(block.get("fixture") or "0")
            minutes = 0
            points = 0
            for item in block.get("stats") or []:
                if not isinstance(item, Mapping):
                    continue
                ident = str(item.get("identifier") or "")
                value = item.get("value")
                if ident == "minutes" and isinstance(value, int) and not isinstance(value, bool):
                    minutes = value
                if ident == "total_points" and isinstance(value, int) and not isinstance(
                    value, bool
                ):
                    points = value
            rows.append(
                {
                    "element": int(player_id),
                    "fixture": fixture_id,
                    "position": position,
                    "minutes": minutes,
                    "total_points": points,
                }
            )
    return rows


def build_hidden_outcome_from_event_live(
    *,
    live: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
    episode_id: str,
    season: str,
    gameweek: int,
) -> dict[str, Any]:
    """Build a reveal-gated hidden outcome from recorded live + bootstrap bytes."""

    return {
        "hidden_outcome_version": "1.0",
        "episode_id": episode_id,
        "season": season,
        "gameweek": int(gameweek),
        "reveal_after": "proposal_frozen",
        "player_outcomes": event_live_to_player_outcomes(live, bootstrap=bootstrap),
        "fixtures": [],
        "match_results": [],
        "source": "fpl-event-live",
    }


def _outcome_status(value: Mapping[str, Any] | None) -> str | None:
    if not value:
        return None
    explicit = value.get("status")
    if explicit in {"provisional", "final"}:
        return str(explicit)
    if value.get("finalised_at"):
        return "final"
    if value.get("points") is not None:
        return "provisional"
    return None


def assert_outcome_revision_allowed(
    existing: Mapping[str, Any] | None,
    *,
    incoming_status: str,
    incoming_points: float,
    incoming_sha256: str | None = None,
) -> None:
    """Refuse provisional overwrite of finals and conflicting final revisions."""

    if incoming_status not in {"provisional", "final"}:
        raise LiveOutcomeAttachmentError("outcome status must be provisional or final")
    current = _outcome_status(existing)
    if current is None:
        return
    if current == "final" and incoming_status == "provisional":
        raise LiveOutcomeAttachmentError(
            "Refusing to overwrite a final outcome with a provisional result"
        )
    if current == "final" and incoming_status == "final":
        existing_points = existing.get("points") if existing else None
        existing_hash = existing.get("realised_outcome_sha256") if existing else None
        if existing_points is not None and float(existing_points) != float(incoming_points):
            raise LiveOutcomeAttachmentError(
                "Refusing to overwrite a final outcome with different points"
            )
        if (
            existing_hash
            and incoming_sha256
            and str(existing_hash) != str(incoming_sha256)
        ):
            raise LiveOutcomeAttachmentError(
                "Refusing to overwrite a final outcome with different realised bytes"
            )


def compute_decision_metrics(
    *,
    record: Mapping[str, Any],
    recommended_outcome: Mapping[str, Any],
    do_nothing_outcome: Mapping[str, Any] | None = None,
    alternate_captain_outcome: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Decision metrics for live retrospectives (transfer, captain, bench, hits)."""

    plan = record.get("validated_plan") or {}
    finance = plan.get("finance") or {}
    hit_cost = int(finance.get("hit_cost") or 0)
    gross = float(recommended_outcome["gross_points"])
    bench_points = float(recommended_outcome.get("bench_points") or 0)
    metrics = retrospective_metrics(
        record=dict(record),
        realised_points=gross,
    )
    metrics.update(
        {
            "gross_points": gross,
            "bench_points": bench_points,
            "bench_effectiveness": bench_points,
            "hit_cost": hit_cost,
            "hit_recovery": round(gross - hit_cost, 4) if hit_cost else gross,
            "n_substitutions": len(recommended_outcome.get("substitutions") or []),
            "captain_source": (recommended_outcome.get("captain") or {}).get("source"),
            "realised_outcome_sha256": recommended_outcome.get("content_sha256"),
        }
    )
    if do_nothing_outcome is not None:
        paired = compare_realised_outcomes(
            evaluated_outcome=dict(recommended_outcome),
            baseline_outcome=dict(do_nothing_outcome),
            counterfactual_type="do_nothing",
        )
        metrics["transfer_gain_vs_do_nothing"] = paired["realised_gain"]
        metrics["do_nothing_points"] = float(do_nothing_outcome["gross_points"])
        metrics["paired_do_nothing"] = paired
    if alternate_captain_outcome is not None:
        paired_cap = compare_realised_outcomes(
            evaluated_outcome=dict(recommended_outcome),
            baseline_outcome=dict(alternate_captain_outcome),
            counterfactual_type="captain",
        )
        metrics["captaincy_gain_vs_alternate"] = paired_cap["realised_gain"]
        metrics["alternate_captain_points"] = float(alternate_captain_outcome["gross_points"])
        metrics["paired_captain"] = paired_cap
    return metrics


def score_plan_from_event_live(
    *,
    plan: Mapping[str, Any],
    live: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
    revealed_at: str,
    rules: Mapping[str, Any],
    ruleset_sha256_value: str,
) -> dict[str, Any]:
    """Score one frozen plan against recorded event live + bootstrap."""

    hidden = build_hidden_outcome_from_event_live(
        live=live,
        bootstrap=bootstrap,
        episode_id=str(plan["episode_id"]),
        season=str(plan["season"]),
        gameweek=int(plan["gameweek"]),
    )
    try:
        return score_revealed_outcome(
            plan,
            hidden,
            revealed_at=revealed_at,
            rules=rules,
            ruleset_sha256=ruleset_sha256_value,
        )
    except OutcomeScoringError as exc:
        raise LiveOutcomeAttachmentError(str(exc)) from exc


def attach_live_outcome(
    record: Mapping[str, Any],
    *,
    live: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
    revealed_at: str,
    rules_path: Path,
    status: str = "final",
    do_nothing_plan: Mapping[str, Any] | None = None,
    alternate_captain_plan: Mapping[str, Any] | None = None,
    process_notes: str | None = None,
) -> dict[str, Any]:
    """Return a GDR copy with outcome + retrospective attached under revision rules."""

    if status not in {"provisional", "final"}:
        raise LiveOutcomeAttachmentError("status must be provisional or final")
    plan = record.get("validated_plan")
    if not isinstance(plan, Mapping):
        raise LiveOutcomeAttachmentError("GDR is missing validated_plan")
    rules = load_rules(rules_path)
    rules_hash = ruleset_sha256(rules_path)

    recommended = score_plan_from_event_live(
        plan=plan,
        live=live,
        bootstrap=bootstrap,
        revealed_at=revealed_at,
        rules=rules,
        ruleset_sha256_value=rules_hash,
    )
    assert_outcome_revision_allowed(
        record.get("outcome") if isinstance(record.get("outcome"), Mapping) else None,
        incoming_status=status,
        incoming_points=float(recommended["gross_points"]),
        incoming_sha256=str(recommended["content_sha256"]),
    )

    do_nothing = None
    if do_nothing_plan is not None:
        do_nothing = score_plan_from_event_live(
            plan=do_nothing_plan,
            live=live,
            bootstrap=bootstrap,
            revealed_at=revealed_at,
            rules=rules,
            ruleset_sha256_value=rules_hash,
        )
    alternate = None
    if alternate_captain_plan is not None:
        alternate = score_plan_from_event_live(
            plan=alternate_captain_plan,
            live=live,
            bootstrap=bootstrap,
            revealed_at=revealed_at,
            rules=rules,
            ruleset_sha256_value=rules_hash,
        )

    metrics = compute_decision_metrics(
        record=record,
        recommended_outcome=recommended,
        do_nothing_outcome=do_nothing,
        alternate_captain_outcome=alternate,
    )
    notes = process_notes or (
        "Post-lock outcome attached from recorded event live + bootstrap; "
        f"status={status}"
    )
    updated = attach_retrospective(
        dict(record),
        process_notes=notes,
        lessons=[
            "Outcomes are revision-aware: provisional never overwrites final.",
            "Paired transfer/captain metrics require explicit counterfactual plans.",
        ],
        realised_points=float(recommended["gross_points"]),
    )
    updated["outcome"] = {
        "points": float(recommended["gross_points"]),
        "notes": f"Live event attachment ({status})",
        "status": status,
        "finalised_at": revealed_at if status == "final" else None,
        "realised_outcome_sha256": recommended["content_sha256"],
        "revealed_at": revealed_at,
    }
    if status == "final":
        updated["finalised_at"] = revealed_at
    updated["retrospective"]["metrics"] = metrics
    updated["retrospective"]["realised_outcomes"] = {
        "recommended": recommended,
        "do_nothing": do_nothing,
        "alternate_captain": alternate,
    }
    return updated


def write_attached_record(
    record: Mapping[str, Any],
    *,
    out_path: Path,
) -> None:
    """Write the updated GDR; refuse differing overwrite of an existing final file."""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        existing = _load_json(out_path)
        existing_status = _outcome_status(
            existing.get("outcome") if isinstance(existing.get("outcome"), Mapping) else None
        )
        incoming_status = _outcome_status(
            record.get("outcome") if isinstance(record.get("outcome"), Mapping) else None
        )
        if existing_status == "final" and incoming_status != "final":
            raise LiveOutcomeAttachmentError(
                f"Refusing to replace final GDR outcome at {out_path}"
            )
        if existing_status == "final" and incoming_status == "final":
            if fingerprint(existing) != fingerprint(dict(record)):
                # Allow identical re-write only.
                existing_hash = (existing.get("outcome") or {}).get("realised_outcome_sha256")
                incoming_hash = (record.get("outcome") or {}).get("realised_outcome_sha256")
                if existing_hash and incoming_hash and existing_hash == incoming_hash:
                    return
                raise LiveOutcomeAttachmentError(
                    f"Refusing to overwrite differing final GDR at {out_path}"
                )
    write_decision_record(dict(record), out_path)


def attach_live_outcome_files(
    *,
    decision_record_path: Path,
    event_live_path: Path,
    bootstrap_path: Path,
    rules_path: Path,
    revealed_at: str,
    status: str = "final",
    out_path: Path | None = None,
    do_nothing_plan_path: Path | None = None,
    alternate_captain_plan_path: Path | None = None,
) -> dict[str, Any]:
    """File-path wrapper used by the CLI and integration tests."""

    record = _load_json(decision_record_path)
    live = _load_json(event_live_path)
    bootstrap = _load_json(bootstrap_path)
    do_nothing_plan = (
        _load_json(do_nothing_plan_path) if do_nothing_plan_path is not None else None
    )
    alternate_plan = (
        _load_json(alternate_captain_plan_path)
        if alternate_captain_plan_path is not None
        else None
    )
    updated = attach_live_outcome(
        record,
        live=live,
        bootstrap=bootstrap,
        revealed_at=revealed_at,
        rules_path=rules_path,
        status=status,
        do_nothing_plan=do_nothing_plan,
        alternate_captain_plan=alternate_plan,
    )
    destination = out_path or decision_record_path
    write_attached_record(updated, out_path=destination)
    sidecar = destination.with_name("realised-outcome.json")
    recommended = updated["retrospective"]["realised_outcomes"]["recommended"]
    payload = dict(recommended)
    payload["status"] = status
    if status == "final":
        payload["finalised_at"] = revealed_at
    if sidecar.exists():
        existing = _load_json(sidecar)
        existing_status = _outcome_status(existing)
        if existing_status == "final" and status == "provisional":
            raise LiveOutcomeAttachmentError(
                f"Refusing to overwrite final realised-outcome sidecar at {sidecar}"
            )
        if existing_status == "final" and status == "final":
            if existing.get("content_sha256") != recommended.get("content_sha256"):
                raise LiveOutcomeAttachmentError(
                    f"Refusing conflicting final realised-outcome at {sidecar}"
                )
            return {
                "decision_record_path": str(destination),
                "realised_outcome_path": str(sidecar),
                "points": updated["outcome"]["points"],
                "status": status,
                "realised_outcome_sha256": recommended["content_sha256"],
                "metrics": updated["retrospective"]["metrics"],
                "record": updated,
            }
    sidecar.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "decision_record_path": str(destination),
        "realised_outcome_path": str(sidecar),
        "points": updated["outcome"]["points"],
        "status": status,
        "realised_outcome_sha256": recommended["content_sha256"],
        "metrics": updated["retrospective"]["metrics"],
        "record": updated,
    }
