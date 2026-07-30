from __future__ import annotations

import json
from pathlib import Path

from scripts.evaluate_w4_historical_availability import (
    build_w4_historical_qualification,
    write_once,
)
from src.forecasting.live_faithful import artifact_hash


ROOT = Path(__file__).resolve().parents[2]


def test_w4_historical_qualification_refuses_recovered_evidence(tmp_path: Path) -> None:
    report = build_w4_historical_qualification(
        evidence_root=ROOT / "evals/evidence-forks/2025-26",
        canonical_root=ROOT / "reports/benchmarks/2025-26",
        policy_path=ROOT / "control/policies/evidence-adjustments-v2.yaml",
        registry_path=ROOT / "control/sources/source-registry.yaml",
    )

    assert report["content_sha256"] == artifact_hash(report)
    assert report["gameweeks"] == [33, 34, 35, 36]
    assert report["summary"]["candidate_claim_count"] == 4
    assert report["summary"]["admitted_claim_count"] == 0
    assert report["summary"]["projection_effect_count"] == 0
    assert report["canonical_artifacts"]["unchanged"] is True
    assert all(
        "captured_after_historical_decision" in row["refusal_reasons"]
        for row in report["claim_qualification"]
    )

    path = tmp_path / "w4.json"
    write_once(path, report)
    write_once(path, report)
    assert json.loads(path.read_text(encoding="utf-8"))["content_sha256"] == report[
        "content_sha256"
    ]
