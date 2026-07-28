#!/usr/bin/env python3
"""Audit one offline live-evidence checkpoint without performing acquisition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.evaluation.evidence_coverage import (
    build_evidence_coverage_report,
    evaluate_retrieval_golden,
)
from src.evidence.live_evidence_ledger import write_live_evidence_artifact
from src.forecasting.live_faithful import artifact_hash


ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def run_audit(
    *,
    checkpoint_id: str,
    decision_at: str,
    config: dict[str, Any],
    acquisition_funnel: dict[str, Any],
    evidence_view: dict[str, Any],
    packet: dict[str, Any],
    expected_entities: dict[str, Any],
    adjustments: list[dict[str, Any]] | None = None,
    golden: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report = build_evidence_coverage_report(
        checkpoint_id=checkpoint_id,
        decision_at=decision_at,
        config=config,
        acquisition_funnel=acquisition_funnel,
        evidence_view=evidence_view,
        packet=packet,
        expected_club_ids=expected_entities.get("club_ids", []),
        expected_player_ids=expected_entities.get("player_ids", []),
        accepted_adjustments=adjustments or [],
    )
    if golden is not None:
        report = {
            **{
                key: value
                for key, value in report.items()
                if key != "content_sha256"
            },
            "golden_retrieval": evaluate_retrieval_golden(
                packet=packet,
                relevant_claim_ids=golden.get("relevant_claim_ids", []),
                irrelevant_claim_ids=golden.get("irrelevant_claim_ids", []),
                latency_ms=float(golden["latency_ms"]),
                maximum_latency_ms=float(
                    config["retrieval"]["maximum_packet_latency_ms"]
                ),
            ),
        }
        report["content_sha256"] = artifact_hash(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit an offline live evidence coverage checkpoint"
    )
    parser.add_argument("--checkpoint-id", required=True)
    parser.add_argument("--decision-at", required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=(
            ROOT
            / "config"
            / "data_sources"
            / "2026-27-evidence-coverage.json"
        ),
    )
    parser.add_argument("--acquisition-funnel", type=Path, required=True)
    parser.add_argument("--evidence-view", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--expected-entities", type=Path, required=True)
    parser.add_argument("--adjustments", type=Path)
    parser.add_argument("--golden", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    adjustments: list[dict[str, Any]] | None = None
    if args.adjustments is not None:
        value = json.loads(args.adjustments.read_text(encoding="utf-8"))
        if not isinstance(value, list):
            raise ValueError("--adjustments must contain a JSON list")
        adjustments = [dict(row) for row in value]
    report = run_audit(
        checkpoint_id=args.checkpoint_id,
        decision_at=args.decision_at,
        config=_read(args.config),
        acquisition_funnel=_read(args.acquisition_funnel),
        evidence_view=_read(args.evidence_view),
        packet=_read(args.packet),
        expected_entities=_read(args.expected_entities),
        adjustments=adjustments,
        golden=_read(args.golden) if args.golden is not None else None,
    )
    write_live_evidence_artifact(args.output, report)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "status": report["status"],
                "planes": report["planes"],
                "content_sha256": report["content_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
