#!/usr/bin/env python3
"""Profile contingency-aware transfer search on the W10/kcc scale fixture."""

from __future__ import annotations

import argparse
import cProfile
import io
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.forecasting.appearance_distribution import calibration_hash
from src.optimisation.io import fingerprint
from src.optimisation.solver import solve
from src.optimisation.transfers import enumerate_transfer_sets, index_players, owned_records
from src.optimisation.types import SolverInput
from src.scoring.rules_loader import load_rules, ruleset_sha256

RULES_PATH = REPO / "control/rules/2025-26.yaml"
CALIBRATION_PATH = REPO / "control/models/appearance-distribution-v1.json"
OUT = REPO / "reports/performance/contingency-transfer-search.json"
DECLARED_LAYER_COUNTS = {1: 120, 2: 5_856, 3: 151_672}
BUDGET_P95_MS = {1: 5_000.0, 2: 60_000.0, 3: 300_000.0}


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def scale_input(max_transfers: int) -> SolverInput:
    counts = {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}
    players: list[dict[str, object]] = []
    squad_ids: list[str] = []
    player_number = 1
    for position, count in counts.items():
        for offset in range(count):
            player_id = str(player_number)
            squad_ids.append(player_id)
            players.append(
                {
                    "player_id": player_id,
                    "web_name": f"Owned{player_id}",
                    "position": position,
                    "club_id": f"owned-{player_id}",
                    "now_cost": 4.5,
                    "purchase_price": 4.5,
                    "expected_points": float(offset + 1),
                    "start_probability": min(0.95, max(0.05, float(offset + 1) / 20.0)),
                    "status": "a",
                }
            )
            player_number += 1
    for position in counts:
        for offset in range(8):
            player_id = str(player_number)
            players.append(
                {
                    "player_id": player_id,
                    "web_name": f"Buy{player_id}",
                    "position": position,
                    "club_id": f"buy-{player_id}",
                    "now_cost": 4.5,
                    "expected_points": float(20 - offset),
                    "start_probability": min(
                        0.95, max(0.05, float(20 - offset) / 20.0)
                    ),
                    "status": "a",
                }
            )
            player_number += 1
    rules = load_rules(RULES_PATH)
    calibration = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
    return SolverInput(
        season="2025-26",
        gameweek=2,
        ruleset_id=rules["meta"]["ruleset_id"],
        bank=32.5,
        free_transfers=1,
        squad_player_ids=squad_ids,
        players=players,
        max_transfers=max_transfers,
        sell_pool_per_pos=5,
        buy_pool_per_pos=8,
        squad_contingency_policy="probabilistic_v1",
        appearance_calibration=calibration,
    )


def layer_candidate_hash(solver_input: SolverInput, rules: dict, n_transfers: int) -> str:
    market = index_players(solver_input.players)
    owned = owned_records(solver_input.squad_player_ids, market, rules=rules)
    moves = list(
        enumerate_transfer_sets(
            owned,
            market,
            n_transfers=n_transfers,
            sell_pool_per_pos=solver_input.sell_pool_per_pos,
            buy_pool_per_pos=solver_input.buy_pool_per_pos,
            bank=solver_input.bank,
            availability_policy=solver_input.availability_policy,
            rules=rules,
        )
    )
    return fingerprint(
        {
            "n_transfers": n_transfers,
            "moves": [
                [{"player_out_id": out_id, "player_in_id": in_id} for out_id, in_id in move_set]
                for move_set in moves
            ],
        }
    )


def host_metadata(code_commit: str) -> dict:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor() or platform.machine(),
        "cpu_count": os.cpu_count(),
        "code_commit": code_commit,
    }


def profile_hotspots(solver_input: SolverInput, rules: dict, rules_hash: str) -> list[dict]:
    profiler = cProfile.Profile()
    profiler.enable()
    solve(solver_input, rules=rules, ruleset_sha256=rules_hash)
    profiler.disable()
    stream = io.StringIO()
    stats = __import__("pstats").Stats(profiler, stream=stream)
    stats.sort_stats("tottime")
    rows: list[dict] = []
    for func, (cc, nc, tt, ct, callers) in list(stats.stats.items())[:8]:
        filename, line, name = func
        rows.append(
            {
                "function": name,
                "file": filename,
                "line": line,
                "tottime_s": round(tt, 6),
                "cumtime_s": round(ct, 6),
                "calls": nc,
            }
        )
    rows.sort(key=lambda item: item["tottime_s"], reverse=True)
    return rows[:5]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--widths", default="1,2,3")
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--skip-three-full", action="store_true")
    parser.add_argument("--three-deadline-ms", type=int, default=300_000)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args(argv)

    rules = load_rules(RULES_PATH)
    rules_hash = ruleset_sha256(RULES_PATH)
    calibration = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
    code_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()
    widths = [int(part) for part in args.widths.split(",") if part.strip()]
    rows: list[dict] = []

    for width in widths:
        solver_input = scale_input(width)
        declared = DECLARED_LAYER_COUNTS[width]
        candidate_hash = layer_candidate_hash(solver_input, rules, width)
        assert len(list(
            enumerate_transfer_sets(
                owned_records(
                    solver_input.squad_player_ids,
                    index_players(solver_input.players),
                    rules=rules,
                ),
                index_players(solver_input.players),
                n_transfers=width,
                sell_pool_per_pos=5,
                buy_pool_per_pos=8,
                bank=solver_input.bank,
                availability_policy="available_only",
                rules=rules,
            )
        )) == declared

        use_deadline = width == 3 and args.skip_three_full
        if use_deadline:
            payload = solver_input.as_dict()
            payload["search_deadline_ms"] = args.three_deadline_ms
            solver_input = SolverInput.from_dict(payload)

        # Warmup
        solve(solver_input, rules=rules, ruleset_sha256=rules_hash)

        timings: list[float] = []
        fingerprints: set[str] = set()
        degraded = False
        selected_objective = None
        n_candidates = None
        for _ in range(args.samples):
            started = time.perf_counter()
            result = solve(solver_input, rules=rules, ruleset_sha256=rules_hash)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            timings.append(elapsed_ms)
            fingerprints.add(result["output_fingerprint"])
            degraded = bool(result["search_scope"].get("search_degraded"))
            selected_objective = result["selected"]["objective"] if result["selected"] else None
            n_candidates = result["n_candidates"]

        tracemalloc.start()
        solve(solver_input, rules=rules, ruleset_sha256=rules_hash)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        hotspots = profile_hotspots(solver_input, rules, rules_hash)
        p95 = percentile(timings, 0.95)
        budget = BUDGET_P95_MS[width]
        rows.append(
            {
                "max_transfers": width,
                "declared_layer_candidates": declared,
                "layer_candidate_sha256": candidate_hash,
                "cumulative_valid_candidates_including_no_transfer": n_candidates,
                "samples": args.samples,
                "warmup": 1,
                "wall_ms": {
                    "mean": round(statistics.mean(timings), 3),
                    "p50": round(percentile(timings, 0.50), 3),
                    "p95": round(p95, 3),
                    "p99": round(percentile(timings, 0.99), 3),
                },
                "throughput_candidates_per_second": round(
                    (n_candidates or 0) / (statistics.mean(timings) / 1000.0), 3
                )
                if timings and n_candidates
                else None,
                "python_heap_peak_bytes": peak,
                "output_fingerprint": next(iter(fingerprints)),
                "deterministic": len(fingerprints) == 1,
                "selected_objective": selected_objective,
                "search_degraded": degraded,
                "budget_p95_ms": budget,
                "meets_budget": (not degraded) and p95 <= budget and peak <= 1024**3,
                "hotspots": hotspots,
                "full_declared_set": not degraded,
            }
        )

    report = {
        "schema_version": "1.0",
        "method": {
            "latency": f"{args.samples} warm-process perf_counter samples after one warmup",
            "memory": "separate tracemalloc run; profiler overhead excluded from latency",
            "percentiles": "linear interpolation",
            "scope": "probabilistic_v1 contingency valuation over the declared transfer pool",
            "levers": [
                "shared_missing_state_per_starting_xi",
                "lineup_and_evaluation_memoisation",
                "hot_path_local_appearance_caches",
                "formation_upper_bound_pruning",
                "configurable_search_deadline_ms",
            ],
        },
        "host": host_metadata(code_commit),
        "ruleset_id": rules["meta"]["ruleset_id"],
        "ruleset_sha256": rules_hash,
        "appearance_calibration_sha256": calibration_hash(calibration),
        "fixture": "scripts/profile_contingency_transfer_search.scale_input",
        "production_default_unchanged": True,
        "three_transfer_contingency_enabled": False,
        "verdict": {
            "one_transfer_budget_met": any(
                row["max_transfers"] == 1 and row["meets_budget"] for row in rows
            ),
            "two_transfer_budget_met": any(
                row["max_transfers"] == 2 and row["meets_budget"] for row in rows
            ),
            "three_transfer_isomorphic_budget_met": any(
                row["max_transfers"] == 3
                and row["meets_budget"]
                and row["full_declared_set"]
                for row in rows
            ),
            "promotion_decision": "reject_three_transfer_contingency_default",
        },
        "widths": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "verdict": report["verdict"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
