#!/usr/bin/env python3
"""Run one hash-bound evidence checkpoint against approved collectors."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
import yaml

from src.evidence.live_evidence_ledger import (
    new_live_evidence_ledger,
    write_live_evidence_artifact,
)
from src.ingestion.live_evidence_collector import (
    capture_official_fpl_evidence,
)
from src.ingestion.live_odds_provider import capture_the_odds_api
from src.orchestration.evidence_checkpoint_runner import (
    EvidenceCheckpointError,
    derive_deadline_checkpoints,
    run_evidence_checkpoint,
)


REPO = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = (
    REPO / "config" / "data_sources" / "2026-27-evidence.json"
)
DEFAULT_COVERAGE = (
    REPO
    / "config"
    / "data_sources"
    / "2026-27-evidence-coverage.json"
)
DEFAULT_ODDS = (
    REPO
    / "config"
    / "data_sources"
    / "2026-27-live-odds-provider.json"
)
DEFAULT_REGISTRY = REPO / "control" / "sources" / "source-registry.yaml"
DEFAULT_HEAD = (
    REPO / "control" / "manifests" / "evidence-checkpoint-head.json"
)
DEFAULT_CHECKPOINTS = (
    REPO / "data" / "live-shadow" / "evidence" / "checkpoints"
)
DEFAULT_RAW_EVIDENCE = (
    REPO / "data" / "live-shadow" / "evidence" / "raw"
)
DEFAULT_RAW_ODDS = REPO / "data" / "live-shadow" / "odds" / "raw"
DEFAULT_LEDGERS = REPO / "data" / "live-shadow" / "evidence" / "ledgers"
USER_AGENT = "fpl-agentic-decision-lab/0.1 (private read-only research)"
PREDEADLINE = {
    "T-48h",
    "T-24h",
    "T-8h",
    "T-2h",
    "final_pre_deadline",
}
ODDS_SLOTS = {
    "T-24h": "T-24h",
    "T-8h": "T-8h",
    "T-2h": "T-2h",
    "final_pre_deadline": "final",
}


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EvidenceCheckpointError(f"Expected a JSON object: {path}")
    return value


def _read_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EvidenceCheckpointError(f"Expected a YAML object: {path}")
    return value


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise EvidenceCheckpointError("decision-at must include a timezone")
    return parsed.astimezone(timezone.utc)


def _deadline(
    bootstrap: Mapping[str, Any],
    *,
    gameweek: int,
) -> str:
    events = bootstrap.get("events")
    rows = [
        row
        for row in events if isinstance(row, Mapping) and row.get("id") == gameweek
    ] if isinstance(events, list) else []
    if len(rows) != 1 or not isinstance(rows[0].get("deadline_time"), str):
        raise EvidenceCheckpointError(
            f"Official bootstrap lacks one deadline for gameweek {gameweek}"
        )
    return str(rows[0]["deadline_time"])


def _validate_schedule(
    *,
    bootstrap: Mapping[str, Any],
    gameweek: int,
    checkpoint_id: str,
    decision_at: str,
    maximum_lag_minutes: int,
) -> str:
    schedule = derive_deadline_checkpoints(
        bootstrap, gameweek=gameweek
    )
    target = _timestamp(schedule[checkpoint_id])
    actual = _timestamp(decision_at)
    lag_seconds = (actual - target).total_seconds()
    if lag_seconds < 0 or lag_seconds > maximum_lag_minutes * 60:
        raise EvidenceCheckpointError(
            f"{checkpoint_id} decision-at must be from its official scheduled "
            f"time through +{maximum_lag_minutes} minutes"
        )
    return _deadline(bootstrap, gameweek=gameweek)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Operate one transactional live evidence checkpoint"
    )
    parser.add_argument("--season", default="2026-27")
    parser.add_argument("--gameweek", type=int, required=True)
    parser.add_argument(
        "--checkpoint",
        required=True,
        choices=(
            "daily_preseason",
            "T-48h",
            "T-24h",
            "T-8h",
            "T-2h",
            "final_pre_deadline",
            "post_match",
        ),
    )
    parser.add_argument("--decision-at", required=True)
    parser.add_argument("--solver-input", type=Path, required=True)
    parser.add_argument("--solver-output", type=Path, required=True)
    parser.add_argument("--current-ledger", type=Path)
    parser.add_argument("--manual-observations", type=Path)
    parser.add_argument("--manual-claims", type=Path)
    parser.add_argument("--expected-entities", type=Path)
    parser.add_argument("--accepted-adjustments", type=Path)
    parser.add_argument("--deadline-bootstrap", type=Path)
    parser.add_argument("--maximum-schedule-lag-minutes", type=int, default=15)
    parser.add_argument("--player-id", type=int, action="append")
    parser.add_argument("--with-odds", action="store_true")
    parser.add_argument("--mode", choices=("live", "fixture"), default="live")
    parser.add_argument("--evidence-config", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--coverage-config", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--odds-config", type=Path, default=DEFAULT_ODDS)
    parser.add_argument("--source-registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--head", type=Path, default=DEFAULT_HEAD)
    parser.add_argument("--checkpoint-dir", type=Path, default=DEFAULT_CHECKPOINTS)
    parser.add_argument("--raw-evidence-out", type=Path, default=DEFAULT_RAW_EVIDENCE)
    parser.add_argument("--raw-odds-out", type=Path, default=DEFAULT_RAW_ODDS)
    parser.add_argument("--ledger-out-dir", type=Path, default=DEFAULT_LEDGERS)
    parser.add_argument(
        "--fpl-base-url", default="https://fantasy.premierleague.com"
    )
    parser.add_argument("--odds-base-url")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        evidence_config = _read_json(args.evidence_config)
        coverage_config = _read_json(args.coverage_config)
        odds_config = _read_json(args.odds_config)
        registry = _read_yaml(args.source_registry)
        solver_input = _read_json(args.solver_input)
        solver_output = _read_json(args.solver_output)
        manual_observations = (
            _read_json(args.manual_observations)
            if args.manual_observations
            else {}
        )
        manual_claims = (
            _read_json(args.manual_claims) if args.manual_claims else {}
        )
        entities = (
            _read_json(args.expected_entities)
            if args.expected_entities
            else {}
        )
        adjustments_value = (
            json.loads(args.accepted_adjustments.read_text(encoding="utf-8"))
            if args.accepted_adjustments
            else []
        )
        if not isinstance(adjustments_value, list):
            raise EvidenceCheckpointError(
                "accepted-adjustments must contain a JSON list"
            )
        current_ledger = (
            _read_json(args.current_ledger)
            if args.current_ledger
            else new_live_evidence_ledger(
                season=args.season, created_at=args.decision_at
            )
        )
        expected_head = (
            _read_json(args.head).get("content_sha256")
            if args.head.exists()
            else None
        )

        deadline_at: str | None = None
        if args.checkpoint in PREDEADLINE:
            if args.deadline_bootstrap is None:
                raise EvidenceCheckpointError(
                    "pre-deadline runs require --deadline-bootstrap"
                )
            deadline_at = _validate_schedule(
                bootstrap=_read_json(args.deadline_bootstrap),
                gameweek=args.gameweek,
                checkpoint_id=args.checkpoint,
                decision_at=args.decision_at,
                maximum_lag_minutes=args.maximum_schedule_lag_minutes,
            )
        if args.with_odds and args.checkpoint not in ODDS_SLOTS:
            raise EvidenceCheckpointError(
                f"Odds are not configured for checkpoint {args.checkpoint}"
            )
        if args.with_odds and deadline_at is None:
            raise EvidenceCheckpointError(
                "Odds capture requires the official FPL deadline"
            )

        with httpx.Client(headers={"User-Agent": USER_AGENT}) as client:
            official = {
                "fpl-official-endpoints": lambda: capture_official_fpl_evidence(
                    client,
                    season=args.season,
                    observed_at=args.decision_at,
                    raw_out_dir=args.raw_evidence_out,
                    config=evidence_config,
                    base_url=args.fpl_base_url,
                    mode=args.mode,
                    previous_ledger=None,
                    registry_path=args.source_registry,
                    checkpoint_id=args.checkpoint,
                    player_ids=args.player_id,
                    gameweek=args.gameweek,
                )
            }
            supplemental = (
                {
                    "the-odds-api": lambda: capture_the_odds_api(
                        client,
                        season=args.season,
                        slot=ODDS_SLOTS[args.checkpoint],
                        observed_at=args.decision_at,
                        decision_cutoff=str(deadline_at),
                        raw_out_dir=args.raw_odds_out,
                        config=odds_config,
                        mode=args.mode,
                        registry_path=args.source_registry,
                        base_url=args.odds_base_url,
                    )
                }
                if args.with_odds
                else {}
            )
            artifact = run_evidence_checkpoint(
                season=args.season,
                gameweek=args.gameweek,
                checkpoint_id=args.checkpoint,
                decision_at=args.decision_at,
                current_ledger=current_ledger,
                solver_input=solver_input,
                solver_output=solver_output,
                coverage_config=coverage_config,
                evidence_config=evidence_config,
                source_registry=registry,
                automated_adapters=official,
                supplemental_adapters=supplemental,
                manual_observations=manual_observations,
                manual_claims=manual_claims,
                expected_club_ids=entities.get("club_ids", []),
                expected_player_ids=entities.get("player_ids", []),
                accepted_adjustments=adjustments_value,
                head_path=args.head,
                checkpoint_dir=args.checkpoint_dir,
                expected_head_sha256=(
                    str(expected_head) if expected_head else None
                ),
            )
        ledger_path = (
            args.ledger_out_dir
            / f"{artifact['ledger_after']['content_sha256']}.json"
        )
        write_live_evidence_artifact(ledger_path, artifact["ledger_after"])
    except (
        EvidenceCheckpointError,
        OSError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        print(
            json.dumps(
                {
                    "status": "refused",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2

    print(
        json.dumps(
            {
                "status": artifact["status"],
                "checkpoint_run_id": artifact["checkpoint_run_id"],
                "ledger": str(ledger_path),
                "ledger_sha256": artifact["bindings"][
                    "ledger_after_sha256"
                ],
                "checkpoint_sha256": artifact["content_sha256"],
                "manifest_count": len(
                    artifact["bindings"]["acquisition_manifest_ids"]
                ),
                "claims_added": len(
                    artifact["bindings"]["claim_ids_added"]
                ),
                "coverage_status": artifact["coverage_audit"]["status"],
                "account_writes": artifact["account_writes"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if artifact["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
