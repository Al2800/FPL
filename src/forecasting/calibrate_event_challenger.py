"""Build and evaluate the sealed player-event challenger."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from src.forecasting.event_challenger import (
    evaluate_event_challenger,
    select_preseason_event_candidate,
)
from src.forecasting.live_faithful import artifact_hash


def run_event_challenger(
    *,
    base_config_path: Path,
    locked_calibration_path: Path,
    reports_root: Path,
    outcomes_csv: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    base = json.loads(base_config_path.read_text(encoding="utf-8"))
    locked = json.loads(locked_calibration_path.read_text(encoding="utf-8"))
    config = select_preseason_event_candidate(base, locked)
    evaluation = evaluate_event_challenger(
        reports_root,
        outcomes_csv,
        event_model_weight=float(config["event_model_weight"]),
    )
    report = {
        "schema_version": "1.0",
        "report_id": "live-faithful-v2-events-out-of-sample-evaluation",
        "model_config_sha256": config["content_sha256"],
        **evaluation,
        "decision": "promote" if evaluation["promotion_eligible"] else "reject",
        "note": "A rejected challenger remains recorded; live-faithful-v1 stays control.",
    }
    report["content_sha256"] = artifact_hash(report)
    return config, report
