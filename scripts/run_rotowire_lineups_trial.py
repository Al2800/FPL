#!/usr/bin/env python3
"""Run the Rotowire lineup trial window from local sealed citations + FPL state.

Until Gameweeks are finished this records a shadow consolidation and a
fail-closed admission verdict (scored_fixtures = 0). It never enables live
influence without the preregistered sample.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from src.evidence.lineup_consolidator import (
    consolidate_lineup_evidence,
    evaluate_trial_admission,
    load_trial_policy,
)


REPO = Path(__file__).resolve().parents[1]
DEFAULT_PACK = (
    REPO
    / "data/live-shadow/lineups/rotowire/2026-08-05-gw1-predicted-lineups-citation.json"
)
DEFAULT_BOOTSTRAP = (
    REPO / "data/live-shadow/fpl/20260805T090103Z/api_bootstrap-static.json"
)
DEFAULT_OUT = REPO / "data/live-shadow/lineups/rotowire/trial"


def _availability_from_bootstrap(path: Path) -> list[dict[str, Any]]:
    bootstrap = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for element in bootstrap.get("elements") or []:
        rows.append(
            {
                "fpl_player_id": str(element["id"]),
                "chance_of_playing": element.get("chance_of_playing_next_round"),
                "status": element.get("status"),
                "web_name": element.get("web_name"),
            }
        )
    return rows


def _event_summary(bootstrap_path: Path) -> dict[str, Any]:
    bootstrap = json.loads(bootstrap_path.read_text(encoding="utf-8"))
    events = bootstrap.get("events") or []
    finished = [e for e in events if e.get("finished")]
    return {
        "finished_gameweeks": [int(e["id"]) for e in finished],
        "next_deadline": next(
            (
                e.get("deadline_time")
                for e in events
                if not e.get("finished") and e.get("deadline_time")
            ),
            None,
        ),
        "gw1_finished": bool(events and events[0].get("finished")),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    parser.add_argument("--bootstrap", type=Path, default=DEFAULT_BOOTSTRAP)
    parser.add_argument("--aliases", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    policy = load_trial_policy()
    pack = json.loads(args.pack.read_text(encoding="utf-8"))
    aliases = {"aliases": []}
    if args.aliases and args.aliases.exists():
        aliases = json.loads(args.aliases.read_text(encoding="utf-8"))

    availability = _availability_from_bootstrap(args.bootstrap)
    event_summary = _event_summary(args.bootstrap)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    # Decision cutoff for this shadow run: GW1 deadline from bootstrap if present.
    cutoff = event_summary["next_deadline"] or now

    consolidation = consolidate_lineup_evidence(
        fpl_availability=availability,
        aliases=aliases,
        rotowire_pack=pack,
        official_snapshots=[],
        observed_at=str(pack.get("observed_at") or now),
        decision_cutoff=str(cutoff),
        trial_policy=policy,
        live_influence_admitted=False,
    )

    fixture_count = int(pack.get("fixture_count") or len(pack.get("fixtures") or []))
    metrics = {
        "fixture_coverage": 0.0,
        "identity_match_rate": 0.0,
        "brier_improvement_vs_chance_of_playing": 0.0,
        "brier_improvement_vs_started_last_gw": 0.0,
        "confirmed_minutes_mae": 999.0,
        "citation_latency_hours": 0.0,
        "scored_fixtures": float(len(event_summary["finished_gameweeks"])),
        "matchdays": float(len(event_summary["finished_gameweeks"])),
        "rotowire_cited_fixtures": fixture_count,
        "unmapped_rotowire_fixture_count": consolidation[
            "unmapped_rotowire_fixture_count"
        ],
        "notes": (
            "Pre-match shadow run. No finished 2026/27 Gameweeks yet, so start/"
            "minutes calibration cannot be scored. Aliases empty => identity match 0."
        ),
    }
    verdict = evaluate_trial_admission(metrics, trial_policy=policy)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    consolidation_path = args.out_dir / "shadow-consolidation.json"
    metrics_path = args.out_dir / "trial-metrics.json"
    verdict_path = args.out_dir / "trial-admission.json"
    consolidation_path.write_text(
        json.dumps(consolidation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    metrics_path.write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    verdict_path.write_text(
        json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    summary = {
        "status": "shadow_fail_closed" if not verdict["live_influence_admitted"] else "admitted",
        "live_influence_admitted": verdict["live_influence_admitted"],
        "gw1_finished": event_summary["gw1_finished"],
        "finished_gameweeks": event_summary["finished_gameweeks"],
        "next_deadline": event_summary["next_deadline"],
        "rotowire_cited_fixtures": fixture_count,
        "consolidation_players": consolidation["player_count"],
        "unmapped_rotowire_fixtures": consolidation["unmapped_rotowire_fixture_count"],
        "artifacts": {
            "consolidation": str(consolidation_path),
            "metrics": str(metrics_path),
            "admission": str(verdict_path),
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if verdict["live_influence_admitted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
