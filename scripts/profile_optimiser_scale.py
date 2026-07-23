#!/usr/bin/env python3
"""Profile the exact realistic one/two/three-transfer declared pools."""

from __future__ import annotations

import json
import math
import statistics
import time
import tracemalloc
from pathlib import Path

from src.optimisation.solver import solve
from src.optimisation.types import SolverInput
from src.scoring.rules_loader import load_rules, ruleset_sha256


REPO = Path(__file__).resolve().parents[1]
RULES_PATH = REPO / "control/rules/2025-26.yaml"
OUT = REPO / "reports/performance/optimiser-scale.json"
DECLARED_LAYER_COUNTS = {1: 120, 2: 5_856, 3: 151_672}


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
                    "status": "a",
                }
            )
            player_number += 1
    rules = load_rules(RULES_PATH)
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
    )


def main() -> int:
    rules = load_rules(RULES_PATH)
    rules_hash = ruleset_sha256(RULES_PATH)
    rows = []
    for width in (1, 2, 3):
        solver_input = scale_input(width)
        solve(solver_input, rules=rules, ruleset_sha256=rules_hash)
        timings = []
        fingerprints = set()
        candidates = None
        for _ in range(5):
            started = time.perf_counter()
            result = solve(
                solver_input, rules=rules, ruleset_sha256=rules_hash
            )
            timings.append((time.perf_counter() - started) * 1000.0)
            fingerprints.add(result["output_fingerprint"])
            candidates = result["n_candidates"]

        tracemalloc.start()
        measured = solve(
            solver_input, rules=rules, ruleset_sha256=rules_hash
        )
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        total_seconds = sum(timings) / 1000.0
        rows.append(
            {
                "max_transfers": width,
                "declared_layer_candidates": DECLARED_LAYER_COUNTS[width],
                "cumulative_valid_candidates_including_no_transfer": candidates,
                "samples": len(timings),
                "wall_ms": {
                    "p50": round(percentile(timings, 0.50), 3),
                    "p95": round(percentile(timings, 0.95), 3),
                    "p99": round(percentile(timings, 0.99), 3),
                    "mean": round(statistics.fmean(timings), 3),
                },
                "throughput_candidates_per_second": round(
                    5 * int(candidates) / total_seconds, 3
                ),
                "python_heap_peak_bytes": peak_bytes,
                "retained_ranked_candidates": len(measured["all_candidates"]),
                "deterministic": len(fingerprints) == 1,
                "output_fingerprint": measured["output_fingerprint"],
            }
        )
    report = {
        "schema_version": "1.0",
        "ruleset_id": rules["meta"]["ruleset_id"],
        "ruleset_sha256": rules_hash,
        "method": {
            "latency": "five warm-process perf_counter samples after one warmup",
            "percentiles": "linear interpolation",
            "memory": "separate tracemalloc run; profiler overhead excluded from latency",
            "scope": "full declared pool through plan evaluation and bounded ranking",
        },
        "widths": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
