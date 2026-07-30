#!/usr/bin/env python3
"""Qualify GW33--GW36 evidence for the persistent-availability challenger."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from src.forecasting.live_faithful import artifact_hash


REPO = Path(__file__).resolve().parents[1]


def _tree_hash(root: Path) -> tuple[str, int]:
    if not root.exists():
        raise ValueError(f"canonical root is missing: {root}")
    entries: list[str] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append(f"{relative}\t{digest}\n")
    return hashlib.sha256("".join(entries).encode("utf-8")).hexdigest(), len(entries)


def _registry_source_ids(registry: Mapping[str, Any]) -> set[str]:
    rows = registry.get("sources")
    if not isinstance(rows, list):
        raise ValueError("source registry must contain sources")
    return {
        str(row["source_id"])
        for row in rows
        if isinstance(row, Mapping) and isinstance(row.get("source_id"), str)
    }


def build_w4_historical_qualification(
    *,
    evidence_root: Path,
    canonical_root: Path,
    policy_path: Path,
    registry_path: Path,
) -> dict[str, Any]:
    """Report whether reconstructed evidence can legally enter the live ledger.

    This is intentionally a qualification evaluation rather than a performance
    replay. Historical sources recovered after their deadlines cannot be made
    point-in-time live merely by assigning a convenient observation timestamp.
    """

    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registered = _registry_source_ids(registry)
    before_hash, before_count = _tree_hash(canonical_root)
    rows: list[dict[str, Any]] = []
    for gameweek in range(33, 37):
        bundle_path = evidence_root / f"gw-{gameweek:02d}" / "evidence-bundle.json"
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        cutoff = str(bundle["decision_cutoff"])
        captured_at = str(bundle["captured_at"])
        for source in bundle["sources"]:
            reasons: list[str] = []
            if captured_at > cutoff:
                reasons.append("captured_after_historical_decision")
            if str(source["source_id"]) not in registered:
                reasons.append("source_id_not_in_live_registry")
            if source.get("published_at_precision") != "exact":
                reasons.append("publication_timestamp_not_exact")
            reasons.append("immutable_source_hash_not_available")
            rows.append(
                {
                    "gameweek": gameweek,
                    "claim_id": str(source["claim_id"]),
                    "player_uid": str(source["player_id"]),
                    "source_id": str(source["source_id"]),
                    "published_at": str(source["published_at"]),
                    "captured_at": captured_at,
                    "decision_cutoff": cutoff,
                    "eligible_for_live_availability_ledger": False,
                    "refusal_reasons": sorted(reasons),
                }
            )
    after_hash, after_count = _tree_hash(canonical_root)
    result = {
        "schema_version": "1.0",
        "evaluation_id": "w4-persistent-availability-gw33-gw36",
        "season": "2025-26",
        "gameweeks": [33, 34, 35, 36],
        "policy": {
            "path": policy_path.relative_to(REPO).as_posix(),
            "policy_sha256": artifact_hash(policy),
            "default_enabled": bool(policy["persistent_availability"]["enabled"]),
            "challenger_id": str(
                policy["persistent_availability"]["challenger_id"]
            ),
        },
        "evaluation_status": "qualified_no_historical_injection",
        "claim_qualification": rows,
        "summary": {
            "candidate_claim_count": len(rows),
            "admitted_claim_count": 0,
            "projection_effect_count": 0,
            "realised_score_comparison": "not_run",
            "reason": (
                "All available GW33--GW36 unstructured sources were recovered "
                "after their historical decisions and lack the live source/hash "
                "admission contract. They are not injected into the challenger."
            ),
        },
        "mechanics_coverage": {
            "live_official_bridge": "covered_by_focused_contract_test",
            "n_plus_one_persistence": "covered_by_focused_contract_test",
            "expiry_and_recovery": "covered_by_focused_contract_test",
            "duplicate_idempotence": "covered_by_focused_contract_test",
            "unregistered_or_post_cutoff_refusal": "covered_by_focused_contract_test",
        },
        "production_recommendation": {
            "status": "not_approved",
            "reason": (
                "The challenger is default-disabled. Historical qualification "
                "does not ratify promotion; live evidence, an ADR and owner "
                "approval remain required."
            ),
        },
        "canonical_artifacts": {
            "tree_sha256_before": before_hash,
            "tree_sha256_after": after_hash,
            "file_count_before": before_count,
            "file_count_after": after_count,
            "unchanged": (before_hash, before_count) == (after_hash, after_count),
        },
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def write_once(path: Path, report: Mapping[str, Any]) -> None:
    encoded = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise ValueError(f"refusing to overwrite different report: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO / "reports/evaluation/w4-persistent-availability-gw33-gw36.json",
    )
    args = parser.parse_args()
    report = build_w4_historical_qualification(
        evidence_root=REPO / "evals/evidence-forks/2025-26",
        canonical_root=REPO / "reports/benchmarks/2025-26",
        policy_path=REPO / "control/policies/evidence-adjustments-v2.yaml",
        registry_path=REPO / "control/sources/source-registry.yaml",
    )
    write_once(args.out, report)
    print(json.dumps({"out": str(args.out), "content_sha256": report["content_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
