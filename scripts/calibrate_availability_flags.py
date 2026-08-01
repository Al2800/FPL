#!/usr/bin/env python3
"""W7 — calibrate FPL availability flags to empirical start rates (leakage-safe)."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.forecasting.live_faithful import artifact_hash  # noqa: E402

DEFAULT_VAASTAV = (
    REPO_ROOT / "data" / "raw" / "vaastav" / "Fantasy-Premier-League" / "data"
)
FIT_SEASONS = ("2022-23", "2023-24")
LOCKED_SEASON = "2024-25"
HOLD_OUT = "2025-26"
CHANCE_BUCKETS = (25, 50, 75, 100)


def _wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (float("nan"), float("nan"))
    phat = successes / n
    denom = 1.0 + z**2 / n
    centre = phat + z**2 / (2 * n)
    margin = z * math.sqrt(phat * (1 - phat) / n + z**2 / (4 * n**2))
    return ((centre - margin) / denom, (centre + margin) / denom)


def _brier(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    return float(np.mean((y_prob - y_true) ** 2))


def _load_season(vaastav_root: Path, season: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    season_root = vaastav_root / season
    players_path = season_root / "players_raw.csv"
    gw_path = season_root / "gws" / "merged_gw.csv"
    if not players_path.exists() or not gw_path.exists():
        raise FileNotFoundError(f"missing vaastav files for {season}")
    players = pd.read_csv(players_path, low_memory=False)
    gws = pd.read_csv(gw_path, low_memory=False)
    required_player = {"id", "status", "chance_of_playing_next_round", "element_type"}
    missing = required_player - set(players.columns)
    if missing:
        raise ValueError(f"{season} players_raw missing {sorted(missing)}")
    if "minutes" not in gws.columns or "element" not in gws.columns:
        raise ValueError(f"{season} merged_gw missing minutes/element")
    # Limitation: players_raw is not a pre-deadline GW snapshot in vaastav.
    # Join end-of-export flags to per-GW outcomes as a coarse archive calibration.
    flags = players[
        ["id", "status", "chance_of_playing_next_round", "element_type"]
    ].rename(columns={"id": "element"})
    frame = gws.merge(flags, on="element", how="inner")
    frame["started"] = (pd.to_numeric(frame["minutes"], errors="coerce").fillna(0) >= 60).astype(
        int
    )
    frame["chance_bucket"] = pd.to_numeric(
        frame["chance_of_playing_next_round"], errors="coerce"
    )
    meta = {
        "season": season,
        "players_raw_sha256": __import__("hashlib")
        .sha256(players_path.read_bytes())
        .hexdigest(),
        "merged_gw_sha256": __import__("hashlib").sha256(gw_path.read_bytes()).hexdigest(),
        "rows": int(len(frame)),
        "limitation": (
            "vaastav gw CSVs lack chance_of_playing; flags come from season "
            "players_raw export timing, not immutable pre-deadline snapshots"
        ),
    }
    return frame, meta


def _summarise(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for status, group in frame.groupby(frame["status"].fillna("unknown")):
        n = int(len(group))
        starts = int(group["started"].sum())
        rate = starts / n if n else float("nan")
        lo, hi = _wilson_interval(starts, n)
        rows.append(
            {
                "key": f"status:{status}",
                "status": str(status),
                "chance_bucket": None,
                "n": n,
                "starts": starts,
                "start_rate": round(rate, 6) if n else None,
                "wilson_low": None if n == 0 else round(lo, 6),
                "wilson_high": None if n == 0 else round(hi, 6),
            }
        )
    chance = frame[frame["chance_bucket"].isin(CHANCE_BUCKETS)]
    for bucket, group in chance.groupby("chance_bucket"):
        n = int(len(group))
        starts = int(group["started"].sum())
        rate = starts / n if n else float("nan")
        lo, hi = _wilson_interval(starts, n)
        rows.append(
            {
                "key": f"chance:{int(bucket)}",
                "status": None,
                "chance_bucket": int(bucket),
                "n": n,
                "starts": starts,
                "start_rate": round(rate, 6) if n else None,
                "wilson_low": None if n == 0 else round(lo, 6),
                "wilson_high": None if n == 0 else round(hi, 6),
            }
        )
    return sorted(rows, key=lambda row: row["key"])


def _predict(frame: pd.DataFrame, table: dict[str, float], *, naive: bool) -> np.ndarray:
    probs = []
    for _, row in frame.iterrows():
        if naive:
            # Hard-override baseline: explicit chance/100, else 1.0 if status=a else 0.0
            chance = row["chance_bucket"]
            if pd.notna(chance) and float(chance) in CHANCE_BUCKETS:
                probs.append(float(chance) / 100.0)
            elif str(row["status"]) == "a":
                probs.append(1.0)
            else:
                probs.append(0.0)
            continue
        chance = row["chance_bucket"]
        if pd.notna(chance) and f"chance:{int(chance)}" in table:
            probs.append(table[f"chance:{int(chance)}"])
        elif f"status:{row['status']}" in table:
            probs.append(table[f"status:{row['status']}"])
        else:
            probs.append(0.5)
    return np.asarray(probs, dtype=float)


def calibrate(
    *,
    vaastav_root: Path,
    output_model: Path,
    output_report: Path,
) -> dict[str, Any]:
    season_meta: list[dict[str, Any]] = []
    fit_frames: list[pd.DataFrame] = []
    for season in FIT_SEASONS:
        frame, meta = _load_season(vaastav_root, season)
        season_meta.append(meta)
        fit_frames.append(frame)
    fit = pd.concat(fit_frames, ignore_index=True)
    fit_summary = _summarise(fit)
    table = {
        row["key"]: float(row["start_rate"])
        for row in fit_summary
        if row["start_rate"] is not None and row["n"] >= 50
    }
    # Ensure explicit chance buckets fall back to nominal percentages when thin.
    for bucket in CHANCE_BUCKETS:
        table.setdefault(f"chance:{bucket}", bucket / 100.0)

    locked_frame, locked_meta = _load_season(vaastav_root, LOCKED_SEASON)
    season_meta.append(locked_meta)
    y = locked_frame["started"].to_numpy(dtype=float)
    calibrated = _predict(locked_frame, table, naive=False)
    naive = _predict(locked_frame, table, naive=True)
    report = {
        "schema_version": "availability-flags-calibration-v1",
        "work_item": "W7",
        "fit_seasons": list(FIT_SEASONS),
        "locked_validation_season": LOCKED_SEASON,
        "holdout_unused": HOLD_OUT,
        "limitation": (
            "vaastav merged_gw has no pre-deadline chance_of_playing fields; "
            "calibration joins season players_raw flags to GW outcomes and is "
            "therefore provisional / non-point-in-time. Live path should prefer "
            "immutable bootstrap snapshots once a T-48h…final chain exists."
        ),
        "season_inputs": season_meta,
        "fit_summary": fit_summary,
        "locked_validation": {
            "n": int(len(locked_frame)),
            "base_rate": round(float(y.mean()), 6),
            "brier_calibrated": round(_brier(y, calibrated), 6),
            "brier_naive_hard_override": round(_brier(y, naive), 6),
            "brier_improvement_vs_naive": round(
                _brier(y, naive) - _brier(y, calibrated), 6
            ),
        },
        "recommendation": (
            "Publish table for research consumers; do not silently replace the "
            "live hard-override path until PIT bootstrap archives exist."
        ),
    }
    model = {
        "schema_version": "availability-flags-v1",
        "model_id": "availability-flags-v1.provisional",
        "fit_seasons": list(FIT_SEASONS),
        "locked_validation_season": LOCKED_SEASON,
        "point_in_time": False,
        "start_probability_by_key": {
            key: round(value, 6) for key, value in sorted(table.items())
        },
        "fallback_policy": {
            "explicit_chance_percent_over_100": "ignore_use_status",
            "missing_key": 0.5,
            "status_a_without_chance_live_default": 1.0,
        },
        "limitation": report["limitation"],
    }
    model["content_sha256"] = artifact_hash(model)
    report["model_content_sha256"] = model["content_sha256"]
    report["content_sha256"] = artifact_hash(report)

    output_model.parent.mkdir(parents=True, exist_ok=True)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_model.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_report.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {"model": model, "report": report, "model_path": str(output_model)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vaastav-root", type=Path, default=DEFAULT_VAASTAV)
    parser.add_argument(
        "--output-model",
        type=Path,
        default=REPO_ROOT / "control" / "models" / "availability-flags-v1.provisional.json",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=REPO_ROOT
        / "reports"
        / "forecasting"
        / "availability-flags-calibration-w7.json",
    )
    args = parser.parse_args(argv)
    try:
        result = calibrate(
            vaastav_root=args.vaastav_root,
            output_model=args.output_model,
            output_report=args.output_report,
        )
    except (OSError, ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "model_path": result["model_path"],
                "model_content_sha256": result["model"]["content_sha256"],
                "locked_validation": result["report"]["locked_validation"],
                "limitation": result["report"]["limitation"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
