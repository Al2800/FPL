"""Cheap historical / synthetic Gameweek replay harness (WP-09).

Replays structured-data strategies only (plan §17.6): forecast inputs are whatever
is on the solver fixture; no news reconstruction. Designed to be fast enough for
hundreds of Gameweek runs.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from src.optimisation.io import fingerprint, load_solver_input, save_json
from src.optimisation.solver import solve
from src.orchestration.validated_plan import validate_and_freeze_plan
from src.reporting.baseline_comparison import (
    attach_retrospective,
    baseline_comparison_from_solver,
)
from src.reporting.decision_record import (
    build_decision_record,
    section_31_coverage,
    write_decision_record,
)
from src.scoring.rules_loader import load_rules, ruleset_sha256

REPO = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO / "evals" / "golden-cases" / "optimiser-gw3-input.json"
DEFAULT_OUT = REPO / "reports" / "gameweeks" / "replay-gw3"


def _stable_hash(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _lineup_names(solver_input_players: list[dict[str, Any]], lineup: dict[str, Any]) -> tuple[str, str]:
    names = {str(p["player_id"]): p.get("web_name", p["player_id"]) for p in solver_input_players}
    return (
        str(names.get(str(lineup["captain_id"]), lineup["captain_id"])),
        str(names.get(str(lineup["vice_captain_id"]), lineup["vice_captain_id"])),
    )


def replay_gameweek(
    solver_input_path: Path,
    *,
    out_dir: Path | None = None,
    decision_cutoff: str | None = None,
    deadline: str | None = None,
    attach_outcome_points: float | None = None,
    hindsight_best_points: float | None = None,
) -> dict[str, Any]:
    """Run optimiser → Gameweek Decision Record → optional retrospective metrics."""
    t0 = time.perf_counter()
    rules = load_rules()
    solver_input = load_solver_input(solver_input_path)
    solver_out = solve(solver_input)
    baseline = baseline_comparison_from_solver(solver_out)
    selected = solver_out["selected"]
    if not selected:
        raise RuntimeError("solver produced no selected plan")

    cap_name, vice_name = _lineup_names(solver_input.players, selected["lineup"])
    plans_summary = []
    for name, plan in (solver_out.get("plans") or {}).items():
        if not plan:
            continue
        plans_summary.append(
            {
                "strategy": plan.get("strategy", name),
                "objective": plan["objective"],
                "hit_cost": plan.get("hit_cost", 0),
                "transfers": plan.get("transfers") or [],
            }
        )

    no_transfer = (solver_out.get("plans") or {}).get("no_transfer")
    hit_plan = (solver_out.get("plans") or {}).get("hit")

    cutoff = decision_cutoff or f"{solver_input.season}-08-30T10:00:00Z"
    # Prefer ISO from fixture conventions; keep deterministic synthetic timestamps
    if decision_cutoff is None and solver_input.gameweek == 3:
        cutoff = "2024-08-30T10:00:00Z"
    dl = deadline or ("2024-08-30T11:00:00Z" if solver_input.gameweek == 3 else cutoff)

    observed = "2026-07-21T18:00:00Z"
    rules_hash = ruleset_sha256()
    market = {
        str(player["player_id"]): {
            "player_id": str(player["player_id"]),
            "position": player["position"],
            "club_id": str(player["club_id"]),
            "now_cost": player["now_cost"],
        }
        for player in solver_input.players
    }
    owned = {
        str(player["player_id"]): player
        for player in solver_input.players
        if str(player["player_id"]) in solver_input.squad_player_ids
    }
    predecessor = {
        "policy_arm": "forecast_optimizer",
        "season": solver_input.season,
        "gameweek": solver_input.gameweek,
        "ruleset_id": rules["meta"]["ruleset_id"],
        "ruleset_sha256": rules_hash,
        "squad": [
            {
                "player_id": player_id,
                "position": owned[player_id]["position"],
                "club_id": str(owned[player_id]["club_id"]),
                "purchase_price": owned[player_id].get(
                    "purchase_price", owned[player_id]["now_cost"]
                ),
            }
            for player_id in solver_input.squad_player_ids
        ],
        "bank": solver_input.bank,
        "free_transfers": solver_input.free_transfers,
        "chips_available": list(solver_input.chips_available),
    }
    predecessor["content_sha256"] = fingerprint(predecessor)
    validated_plan = validate_and_freeze_plan(
        episode_id=f"smoke:{solver_input_path.stem}:gw{solver_input.gameweek:02d}",
        policy_arm="forecast_optimizer",
        state=predecessor,
        candidate=selected,
        decision_market=market,
        active_chip=solver_input.active_chip,
        frozen_at=cutoff,
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    record = build_decision_record(
        {
            "record_id": f"gdr_replay_gw{solver_input.gameweek}",
            "gameweek": solver_input.gameweek,
            "season": solver_input.season,
            "fixture_id": solver_input_path.stem,
            "decision_cutoff": cutoff,
            "deadline": dl,
            "ruleset_id": rules["meta"]["ruleset_id"],
            "validated_plan": validated_plan,
            "data_quality": "Structured-data replay; no news corpus",
            "degraded": False,
            "manager_state": {
                "bank": solver_input.bank,
                "free_transfers": solver_input.free_transfers,
                "chips_available": list(solver_input.chips_available),
                "squad_player_ids": list(solver_input.squad_player_ids),
            },
            "projections_summary": {
                "n_players": len(solver_input.players),
                "model_versions": ["solver_input.expected_points"],
                "principal_uncertainty": "Fixture-supplied expected points",
            },
            "candidate_plans": plans_summary,
            "recommendation": {
                "strategy": selected.get("strategy", "highest_ev"),
                "objective": selected["objective"],
                "captain_name": cap_name,
                "vice_captain_name": vice_name,
                "validated_plan_sha256": validated_plan["content_sha256"],
            },
            "baseline_comparison": baseline,
            "alternatives": {
                "conservative": (
                    {
                        "strategy": "no_transfer",
                        "objective": no_transfer["objective"],
                    }
                    if no_transfer
                    else None
                ),
                "aggressive": (
                    {"strategy": "hit", "objective": hit_plan["objective"]} if hit_plan else None
                ),
            },
            "evidence": {
                "supporting_claim_ids": [],
                "conflicting_claim_ids": [],
                "conflict_ids": [],
                "proposed_adjustment_ids": [],
            },
            "validation": {
                "squad": {"ok": selected["validation"]["squad_ok"]},
                "lineup": {"ok": selected["validation"]["lineup_ok"]},
                "chips_ok": selected["validation"].get("chips_ok", True),
            },
            "approval": {"status": "pending"},
            "execution": {"mode": "manual", "notes": "Replay harness — advisory only"},
            "outcome": None,
            "retrospective": None,
            "confidence": "Moderate — deterministic optimiser on fixture projections",
            "principal_uncertainty": "No live evidence adjustments in structured replay",
            "pipeline": {
                "components": [
                    "optimisation.solve",
                    "reporting.baseline_comparison",
                    "reporting.decision_record",
                ],
                "orchestration": "plain_python",
                "solver_version": solver_out.get("solver_version"),
                "input_fingerprint": solver_out.get("input_fingerprint"),
            },
            "observed_at": observed,
            "available_at": observed,
            "provenance": {
                "source_ids": ["synthetic-fixture", "wp07-optimiser"],
                "transformation_version": "0.1.0",
                "ruleset_id": rules["meta"]["ruleset_id"],
            },
        },
        validate=True,
    )

    if attach_outcome_points is not None:
        record = attach_retrospective(
            record,
            process_notes="Replay finalisation with recorded realised points",
            lessons=[],
            realised_points=attach_outcome_points,
            hindsight_best_points=hindsight_best_points,
        )

    hashable = {
        "gameweek": record["gameweek"],
        "deadline": record["deadline"],
        "ruleset_id": record["ruleset_id"],
        "recommendation": {
            "strategy": record["recommendation"]["strategy"],
            "validated_plan_sha256": record["recommendation"]["validated_plan_sha256"],
        },
        "validated_plan_sha256": record["validated_plan"]["content_sha256"],
        "baseline_comparison": record["baseline_comparison"],
        "input_fingerprint": solver_out.get("input_fingerprint"),
    }
    record["repro_hash"] = _stable_hash(hashable)
    record["section_31_coverage"] = section_31_coverage(record)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    record["replay_elapsed_ms"] = round(elapsed_ms, 2)

    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        write_decision_record(record, out_dir / "decision-record.json")
        save_json(out_dir / "solver-output.json", solver_out)
        (out_dir / "repro-hash.txt").write_text(record["repro_hash"] + "\n", encoding="utf-8")
        meta = {
            "elapsed_ms": record["replay_elapsed_ms"],
            "repro_hash": record["repro_hash"],
            "expected_advantage": record["baseline_comparison"]["expected_advantage"],
            "section_31_coverage": record["section_31_coverage"],
        }
        save_json(out_dir / "replay-meta.json", meta)

    return record


def replay_batch(
    solver_input_path: Path,
    *,
    n: int,
    out_root: Path | None = None,
) -> dict[str, Any]:
    """Replay the same fixture n times to demonstrate cheap volume (timing only)."""
    times: list[float] = []
    hashes: set[str] = set()
    for i in range(n):
        out = None
        if out_root is not None and i == 0:
            out = out_root / "sample"
        rec = replay_gameweek(solver_input_path, out_dir=out)
        times.append(float(rec["replay_elapsed_ms"]))
        hashes.add(rec["repro_hash"])
    return {
        "n": n,
        "mean_elapsed_ms": round(sum(times) / len(times), 2),
        "max_elapsed_ms": round(max(times), 2),
        "unique_repro_hashes": len(hashes),
        "deterministic": len(hashes) == 1,
    }
