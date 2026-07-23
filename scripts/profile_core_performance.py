#!/usr/bin/env python3
"""Measure deterministic core workloads without changing production behaviour.

The report deliberately separates ordinary timings from instrumented CPU,
allocation, RSS and I/O measurements. Profilers perturb execution, so their
numbers are diagnostic rather than latency baselines.
"""

from __future__ import annotations

import argparse
import cProfile
import ctypes
import hashlib
import json
import math
import os
import platform
import pstats
import statistics
import sys
import threading
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from src.optimisation.io import load_solver_input
from src.optimisation.solver import solve
from src.orchestration.replay_harness import replay_gameweek
from src.scoring.rules_loader import load_rules, ruleset_sha256


REPO = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO / "evals" / "golden-cases" / "optimiser-gw3-input.json"
DEFAULT_RULES = REPO / "control" / "rules" / "2026-27.yaml"
DEFAULT_EPISODES = REPO / "data" / "benchmark-v0" / "episodes" / "v2" / "2025-26"
DEFAULT_OUT = REPO / "reports" / "performance" / "core-baseline.json"


@dataclass(frozen=True)
class Workload:
    name: str
    description: str
    operation: Callable[[], dict[str, Any]]
    units_per_operation: int = 1


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("read_operations", ctypes.c_ulonglong),
        ("write_operations", ctypes.c_ulonglong),
        ("other_operations", ctypes.c_ulonglong),
        ("read_bytes", ctypes.c_ulonglong),
        ("write_bytes", ctypes.c_ulonglong),
        ("other_bytes", ctypes.c_ulonglong),
    ]


class _ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("page_fault_count", ctypes.c_ulong),
        ("peak_working_set_size", ctypes.c_size_t),
        ("working_set_size", ctypes.c_size_t),
        ("quota_peak_paged_pool_usage", ctypes.c_size_t),
        ("quota_paged_pool_usage", ctypes.c_size_t),
        ("quota_peak_non_paged_pool_usage", ctypes.c_size_t),
        ("quota_non_paged_pool_usage", ctypes.c_size_t),
        ("pagefile_usage", ctypes.c_size_t),
        ("peak_pagefile_usage", ctypes.c_size_t),
    ]


def _io_counters() -> dict[str, int]:
    if os.name != "nt":
        return {}
    counters = _IoCounters()
    ok = ctypes.windll.kernel32.GetProcessIoCounters(  # type: ignore[attr-defined]
        ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(counters)  # type: ignore[attr-defined]
    )
    if not ok:
        return {}
    return {name: int(getattr(counters, name)) for name, _ in counters._fields_}


def _rss_bytes() -> int | None:
    if os.name != "nt":
        return None
    counters = _ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    ok = ctypes.windll.psapi.GetProcessMemoryInfo(  # type: ignore[attr-defined]
        ctypes.windll.kernel32.GetCurrentProcess(),  # type: ignore[attr-defined]
        ctypes.byref(counters),
        counters.cb,
    )
    return int(counters.working_set_size) if ok else None


def percentile(values: list[float], quantile: float) -> float:
    """Linear percentile with deterministic interpolation."""

    if not values:
        raise ValueError("percentile requires at least one value")
    if not 0 <= quantile <= 1:
        raise ValueError("quantile must be between zero and one")
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _delta(after: dict[str, int], before: dict[str, int]) -> dict[str, int]:
    return {key: after[key] - before.get(key, 0) for key in after}


def _profile_rows(profile: cProfile.Profile, limit: int = 20) -> list[dict[str, Any]]:
    stats = pstats.Stats(profile)
    rows = []
    for (filename, line, function), values in stats.stats.items():
        primitive_calls, total_calls, own_time, cumulative_time, _ = values
        normalised = filename.replace("\\", "/")
        if "/src/" not in normalised and "/scripts/" not in normalised:
            continue
        rows.append(
            {
                "file": normalised.rsplit("/", 2)[-1],
                "line": line,
                "function": function,
                "primitive_calls": primitive_calls,
                "total_calls": total_calls,
                "own_ms": round(own_time * 1000.0, 3),
                "cumulative_ms": round(cumulative_time * 1000.0, 3),
            }
        )
    return sorted(rows, key=lambda row: row["cumulative_ms"], reverse=True)[:limit]


def _memory_and_io(operation: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    stop = threading.Event()
    samples: list[int] = []

    def sample_rss() -> None:
        while not stop.wait(0.002):
            value = _rss_bytes()
            if value is not None:
                samples.append(value)

    sampler = threading.Thread(target=sample_rss, daemon=True)
    before_io = _io_counters()
    before_rss = _rss_bytes()
    tracemalloc.start()
    sampler.start()
    try:
        oracle = operation()
        current_heap, peak_heap = tracemalloc.get_traced_memory()
        snapshot = tracemalloc.take_snapshot()
    finally:
        stop.set()
        sampler.join(timeout=1.0)
        tracemalloc.stop()
    after_io = _io_counters()
    after_rss = _rss_bytes()
    allocations = []
    for stat in snapshot.statistics("lineno")[:20]:
        frame = stat.traceback[0]
        allocations.append(
            {
                "file": str(frame.filename).replace("\\", "/"),
                "line": frame.lineno,
                "bytes": stat.size,
                "blocks": stat.count,
            }
        )
    return {
        "oracle": oracle,
        "python_heap_current_bytes": current_heap,
        "python_heap_peak_bytes": peak_heap,
        "rss_before_bytes": before_rss,
        "rss_after_bytes": after_rss,
        "rss_sampled_peak_bytes": max(samples, default=after_rss),
        "io_delta": _delta(after_io, before_io),
        "top_allocations": allocations,
    }


def _measure(workload: Workload, *, iterations: int, warmups: int) -> dict[str, Any]:
    for _ in range(warmups):
        workload.operation()

    wall_ms: list[float] = []
    cpu_ms: list[float] = []
    oracle_hashes: set[str] = set()
    for _ in range(iterations):
        cpu_start = time.process_time()
        wall_start = time.perf_counter()
        oracle = workload.operation()
        wall_ms.append((time.perf_counter() - wall_start) * 1000.0)
        cpu_ms.append((time.process_time() - cpu_start) * 1000.0)
        oracle_hashes.add(
            hashlib.sha256(
                json.dumps(oracle, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
        )

    profile = cProfile.Profile()
    profile.enable()
    profiled_oracle = workload.operation()
    profile.disable()

    total_seconds = sum(wall_ms) / 1000.0
    total_units = iterations * workload.units_per_operation
    return {
        "name": workload.name,
        "description": workload.description,
        "iterations": iterations,
        "warmups": warmups,
        "units_per_operation": workload.units_per_operation,
        "wall_ms": {
            "min": round(min(wall_ms), 3),
            "p50": round(percentile(wall_ms, 0.50), 3),
            "p95": round(percentile(wall_ms, 0.95), 3),
            "p99": round(percentile(wall_ms, 0.99), 3),
            "max": round(max(wall_ms), 3),
            "mean": round(statistics.fmean(wall_ms), 3),
        },
        "cpu_ms": {
            "p50": round(percentile(cpu_ms, 0.50), 3),
            "p95": round(percentile(cpu_ms, 0.95), 3),
            "p99": round(percentile(cpu_ms, 0.99), 3),
        },
        "throughput_units_per_second": round(total_units / total_seconds, 3),
        "deterministic": len(oracle_hashes) == 1,
        "oracle_sha256": sorted(oracle_hashes),
        "cpu_profile": _profile_rows(profile),
        "instrumented_memory_io": _memory_and_io(workload.operation),
        "profiled_oracle_matches": profiled_oracle == workload.operation(),
    }


def _workloads() -> dict[str, Workload]:
    solver_input = load_solver_input(DEFAULT_INPUT)
    rules = load_rules(DEFAULT_RULES)
    rules_hash = ruleset_sha256(DEFAULT_RULES)
    episode_paths = sorted(DEFAULT_EPISODES.glob("gw-*/observed.json"))

    def solver_golden() -> dict[str, Any]:
        output = solve(
            solver_input, rules=rules, ruleset_sha256=rules_hash
        )
        return {
            "input_fingerprint": output["input_fingerprint"],
            "output_fingerprint": output["output_fingerprint"],
            "n_candidates": output["n_candidates"],
            "selected": output["selected"],
        }

    def replay_golden() -> dict[str, Any]:
        output = replay_gameweek(DEFAULT_INPUT)
        return {
            "repro_hash": output["repro_hash"],
            "recommendation": output["recommendation"],
            "baseline_comparison": output["baseline_comparison"],
        }

    def scan_observed_episodes() -> dict[str, Any]:
        rows = []
        total_bytes = 0
        for path in episode_paths:
            payload = path.read_bytes()
            total_bytes += len(payload)
            observed = json.loads(payload)
            rows.append(
                {
                    "episode_id": observed["episode_id"],
                    "gameweek": observed["gameweek"],
                    "content_sha256": hashlib.sha256(payload).hexdigest(),
                    "lagged_rows": len(observed["lagged_player_features"]),
                    "fixture_rows": len(observed["fixtures"]),
                    "prior_result_rows": len(observed["prior_match_results"]),
                }
            )
        return {
            "episode_count": len(rows),
            "bytes_read": total_bytes,
            "rows_sha256": hashlib.sha256(
                json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
        }

    return {
        "solver_golden": Workload(
            "solver_golden",
            "One warm deterministic solve of the committed 20-player, two-transfer fixture.",
            solver_golden,
        ),
        "replay_golden": Workload(
            "replay_golden",
            "One in-memory WP-09 replay; no artefact writes.",
            replay_golden,
        ),
        "episode_observed_scan": Workload(
            "episode_observed_scan",
            "Read and decode all 38 immutable v2 observed partitions once.",
            scan_observed_episodes,
            units_per_operation=max(1, len(episode_paths)),
        ),
    }


def _environment() -> dict[str, Any]:
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "logical_cpus": os.cpu_count(),
        "executable": sys.executable,
        "input_bytes": DEFAULT_INPUT.stat().st_size,
        "episode_observed_files": len(list(DEFAULT_EPISODES.glob("gw-*/observed.json"))),
        "episode_observed_bytes": sum(
            path.stat().st_size for path in DEFAULT_EPISODES.glob("gw-*/observed.json")
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workload",
        action="append",
        choices=sorted(_workloads()),
        help="Workload to run; repeatable. Defaults to all.",
    )
    parser.add_argument("--iterations", type=int, default=7)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    if args.iterations < 1 or args.warmups < 0:
        parser.error("iterations must be positive and warmups non-negative")

    available = _workloads()
    selected = args.workload or list(available)
    report = {
        "schema_version": "1.0",
        "method": {
            "latency": "perf_counter; profiler disabled; warm process",
            "cpu": "process_time; profiler disabled; warm process",
            "percentiles": "linear interpolation over per-operation samples",
            "memory": "separate tracemalloc plus 2ms Windows RSS sampling run",
            "io": "separate Windows GetProcessIoCounters run",
            "cpu_profile": "separate cProfile run; project frames only",
            "warning": "Instrumented runs are diagnostic and are not latency baselines.",
        },
        "environment": _environment(),
        "workloads": [
            _measure(available[name], iterations=args.iterations, warmups=args.warmups)
            for name in selected
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
