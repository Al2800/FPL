"""Phase 1 walking skeleton — one historical Gameweek end-to-end (crude models)."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from src.forecasting.naive import naive_expected_points
from src.normalisation.players import filter_available, players_from_skeleton_fixture
from src.optimisation.io import fingerprint
from src.optimisation.simple_plan import no_transfer_plan
from src.orchestration.validated_plan import validate_and_freeze_plan
from src.reporting.decision_record import build_decision_record, write_decision_record
from src.scoring.rules_loader import load_rules, ruleset_sha256

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE = REPO_ROOT / "evals" / "golden-cases" / "skeleton-gw3-fixture.json"
DEFAULT_OUT = REPO_ROOT / "reports" / "gameweeks" / "skeleton-gw3"


def _stable_hash(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def run_skeleton(fixture_path: Path, out_dir: Path) -> dict[str, Any]:
    rules = load_rules()
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    deadline = fixture["deadline"]
    cutoff = fixture["decision_cutoff"]

    players = players_from_skeleton_fixture(fixture)
    players = filter_available(players, deadline)
    projected = naive_expected_points(players)

    squad_meta = fixture["squad"]
    # Merge club_id / purchase into projected rows for validation
    for row in squad_meta:
        pid = str(row["player_id"])
        mask = projected["player_id"] == pid
        projected.loc[mask, "purchase_price"] = row["purchase_price"]
        projected.loc[mask, "club_id"] = str(row["club_id"])

    plan = no_transfer_plan(squad_meta, projected)
    lineup = plan["lineup"]
    id_to_name = dict(zip(projected["player_id"], projected["web_name"]))
    rules_hash = ruleset_sha256()
    market = {
        str(row["player_id"]): {
            "player_id": str(row["player_id"]),
            "position": row["position"],
            "club_id": str(row["club_id"]),
            "now_cost": row["now_cost"],
        }
        for row in projected.to_dict(orient="records")
    }
    squad_by_id = {str(row["player_id"]): row for row in squad_meta}
    predecessor = {
        "policy_arm": "walking_skeleton",
        "season": fixture["season"],
        "gameweek": int(fixture["gameweek"]),
        "ruleset_id": rules["meta"]["ruleset_id"],
        "ruleset_sha256": rules_hash,
        "squad": [
            {
                "player_id": player_id,
                "position": market[player_id]["position"],
                "club_id": market[player_id]["club_id"],
                "purchase_price": squad_by_id[player_id]["purchase_price"],
            }
            for player_id in squad_by_id
        ],
        "bank": fixture["manager_state"]["bank"],
        "free_transfers": fixture["manager_state"]["free_transfers"],
        "chips_available": fixture["manager_state"]["chips_available"],
    }
    predecessor["content_sha256"] = fingerprint(predecessor)
    validated_plan = validate_and_freeze_plan(
        episode_id=f"walking-skeleton:{fixture['fixture_id']}",
        policy_arm="walking_skeleton",
        state=predecessor,
        candidate={
            "transfers": [],
            "bank_after": fixture["manager_state"]["bank"],
            "hit_cost": 0,
            "lineup": {
                "formation": lineup["formation"],
                "starting_xi_ids": [
                    str(player["player_id"]) for player in lineup["starting_xi"]
                ],
                "bench_ids": [
                    str(player["player_id"]) for player in lineup["bench"]
                ],
                "captain_id": lineup["captain_id"],
                "vice_captain_id": lineup["vice_captain_id"],
            },
        },
        decision_market=market,
        active_chip=None,
        frozen_at=cutoff,
        rules=rules,
        ruleset_sha256=rules_hash,
    )

    record = build_decision_record(
        {
            "gameweek": fixture["gameweek"],
            "season": fixture.get("season"),
            "fixture_id": fixture.get("fixture_id"),
            "decision_cutoff": cutoff,
            "deadline": deadline,
            "ruleset_id": rules["meta"]["ruleset_id"],
            "validated_plan": validated_plan,
            "data_quality": "Synthetic fixture; crude models; walking skeleton",
            "manager_state": fixture.get("manager_state"),
            "recommendation": {
                "strategy": plan["strategy"],
                "captain_name": id_to_name.get(lineup["captain_id"], lineup["captain_id"]),
                "vice_captain_name": id_to_name.get(lineup["vice_captain_id"], lineup["vice_captain_id"]),
                "validated_plan_sha256": validated_plan["content_sha256"],
            },
            "expected_advantage": "n/a (no-transfer baseline)",
            "confidence": "Low — walking skeleton",
            "principal_uncertainty": "Crude expected-minutes and points model",
            "validation": plan["validation"],
            "approval": "Pending human",
            "execution": "Manual in initial phase",
            "pipeline": {
                "components": [
                    "normalisation.players_from_skeleton_fixture",
                    "forecasting.naive_expected_points",
                    "optimisation.no_transfer_plan",
                    "scoring.validator",
                    "reporting.decision_record",
                ],
                "orchestration": "plain_python",
            },
        }
    )

    # Drop non-serialisable / unstable noise before hashing for reproducibility check
    hashable = {
        "gameweek": record["gameweek"],
        "deadline": record["deadline"],
        "ruleset_id": record["ruleset_id"],
        "recommendation": {
            "strategy": record["recommendation"]["strategy"],
            "captain_name": record["recommendation"]["captain_name"],
            "vice_captain_name": record["recommendation"]["vice_captain_name"],
            "starting_xi_ids": [p["player_id"] for p in lineup["starting_xi"]],
            "bench_ids": [p["player_id"] for p in lineup["bench"]],
            "expected_xi_points": lineup["expected_xi_points"],
        },
        "validation_ok": {
            "squad": record["validation"]["squad"]["ok"],
            "lineup": record["validation"]["lineup"]["ok"],
        },
    }
    record["repro_hash"] = _stable_hash(hashable)

    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "decision-record.json"
    write_decision_record(record, json_path)
    (out_dir / "repro-hash.txt").write_text(record["repro_hash"] + "\n", encoding="utf-8")
    projected.to_parquet(out_dir / "projections.parquet", index=False)
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Phase 1 walking skeleton")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    record = run_skeleton(args.fixture, args.out)
    print(f"Wrote decision record to {args.out / 'decision-record.json'}")
    print(f"repro_hash={record['repro_hash']}")
    print(f"squad_ok={record['validation']['squad']['ok']} lineup_ok={record['validation']['lineup']['ok']}")
    print(f"captain={record['recommendation']['captain_name']} plan={record['validated_plan']['content_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
