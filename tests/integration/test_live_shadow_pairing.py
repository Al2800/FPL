"""End-to-end contracts for paired advisory-only live shadows."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.run_live_shadow_week import run_bundle
from src.orchestration.live_shadow import (
    LiveShadowError,
    build_unstructured_evidence_capture,
    freeze_live_shadow_week,
    reveal_live_shadow_week,
    shadow_hash,
    write_shadow_artifact,
)
from src.orchestration.policy_state import POLICY_ARMS, initialise_policy_states
from src.scoring.rules_loader import load_rules, ruleset_sha256
from src.scoring.validator import selling_price


ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "control/rules/2025-26.yaml"
POLICY_PATH = ROOT / "control/policies/live-shadow-candidate.json"
RULES = load_rules(RULES_PATH)
RULES_HASH = ruleset_sha256(RULES_PATH)
CUTOFF = "2025-08-14T10:00:00Z"
FROZEN = "2025-08-14T09:55:00Z"
REVEALED = "2025-08-18T09:00:00Z"


def _players() -> list[dict]:
    spec = (
        [(i, "GKP", 4.5) for i in (1, 2)]
        + [(i, "DEF", 4.5) for i in range(3, 8)]
        + [(i, "MID", 7.0) for i in range(8, 13)]
        + [(i, "FWD", 11.0) for i in range(13, 16)]
    )
    return [
        {
            "player_id": str(player_id),
            "position": position,
            "club_id": str(player_id),
            "purchase_price": price,
            "current_price": price,
            "selling_price": selling_price(price, price, RULES),
        }
        for player_id, position, price in spec
    ]


def _states() -> dict[str, dict]:
    return initialise_policy_states(
        {
            "seed_id": "live-shadow-fixture-gw1",
            "season": "2025-26",
            "gameweek": 1,
            "bank": 0.5,
            "free_transfers": 1,
            "chips_available": [
                "wildcard_fh",
                "free_hit_fh",
                "triple_captain_fh",
                "bench_boost_fh",
                "wildcard_sh",
                "free_hit_sh",
                "triple_captain_sh",
                "bench_boost_sh",
            ],
            "squad": _players(),
        },
        policy_arms=POLICY_ARMS,
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )


def _market(*, next_week: bool = False) -> dict[str, dict]:
    market = {}
    for player in _players():
        market[player["player_id"]] = {
            "player_id": player["player_id"],
            "position": player["position"],
            "club_id": player["club_id"],
            "now_cost": player["current_price"],
        }
    market["16"] = {
        "player_id": "16",
        "position": "DEF",
        "club_id": "16",
        "now_cost": 4.9 if next_week else 4.8,
    }
    return market


def _candidate(*, transfer: bool = False) -> dict:
    ids = [str(value) for value in range(1, 16)]
    transfers = []
    if transfer:
        ids[ids.index("3")] = "16"
        transfers = [{"player_out_id": "3", "player_in_id": "16"}]
    by_position = {
        position: sorted(
            (
                player_id
                for player_id in ids
                if _market()[player_id]["position"] == position
            ),
            key=int,
        )
        for position in ("GKP", "DEF", "MID", "FWD")
    }
    xi = (
        by_position["GKP"][:1]
        + by_position["DEF"][:3]
        + by_position["MID"][:4]
        + by_position["FWD"][:3]
    )
    bench = [
        player_id
        for position in ("GKP", "DEF", "MID", "FWD")
        for player_id in by_position[position]
        if player_id not in xi
    ]
    return {
        "transfers": transfers,
        "lineup": {
            "formation": {"DEF": 3, "MID": 4, "FWD": 3},
            "starting_xi_ids": xi,
            "bench_ids": bench,
            "captain_id": "8",
            "vice_captain_id": "9",
        },
    }


def _registry() -> dict:
    return {
        "sources": [
            {
                "source_id": "fixture-club-news",
                "enabled": True,
                "licence_status": "restricted",
                "allowed_use": "private_analysis",
                "attribution": "Fixture club",
            }
        ]
    }


def _evidence() -> dict:
    text = "Player 3 will miss the opening fixture."
    import hashlib

    return build_unstructured_evidence_capture(
        snapshots=[
            {
                "source_id": "fixture-club-news",
                "document_id": "club-news-1",
                "url": "https://club.example/news/1",
                "title": "Team news",
                "published_at": "2025-08-14T08:00:00Z",
                "observed_at": "2025-08-14T08:05:00Z",
                "available_at": "2025-08-14T08:06:00Z",
                "content": text,
                "content_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "raw_file": "forecast-inputs/evidence-01.json",
            }
        ],
        source_registry=_registry(),
        decision_cutoff=CUTOFF,
    )


def _episode() -> dict:
    return {
        "episode_id": "live-shadow:2025-26:gw01:fixture",
        "season": "2025-26",
        "gameweek": 1,
        "mode": "live_shadow",
        "cutoff": CUTOFF,
    }


def _policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _agent(candidate: dict, *, status: str = "completed") -> dict:
    return {
        "status": status,
        "validated_output": {} if status == "completed" else None,
        "selected_candidate": deepcopy(candidate),
        "content_sha256": "a" * 64,
    }


def _freeze(*, agent_status: str = "completed", frozen_at: str = FROZEN) -> dict:
    states = _states()
    baseline = _candidate()
    evidence = _candidate(transfer=True)
    return freeze_live_shadow_week(
        episode_manifest=_episode(),
        structured_context={"forecast_sha256": "b" * 64},
        decision_market=_market(),
        control_state=states["forecast_optimizer"],
        evidence_state=states["evidence_agent"],
        control_candidate=baseline,
        evidence_baseline_candidate=baseline,
        evidence_candidate=evidence,
        evidence_capture=_evidence(),
        agent_run=_agent(evidence, status=agent_status),
        frozen_at=frozen_at,
        rules=RULES,
        ruleset_sha256=RULES_HASH,
        policy=_policy(),
    )


def _outcome(plan: dict, points: int) -> dict:
    return {
        "outcome_id": f"fixture:{plan['content_sha256'][:12]}",
        "plan_sha256": plan["content_sha256"],
        "revealed_at": REVEALED,
        "gross_points": points,
        "content_sha256": str(points).zfill(64),
    }


def test_pair_freezes_same_structured_context_and_reproduces_byte_for_byte(
    tmp_path: Path,
):
    first = _freeze()
    second = _freeze()
    assert second == first
    assert first["content_sha256"] == shadow_hash(first)
    assert first["mode"] == "advisory_only"
    assert first["browser_actions"] is False
    assert first["account_writes"] is False
    assert {
        row["structured_context_sha256"]
        for row in first["arm_inputs"].values()
    } == {first["shared_structured_context_sha256"]}
    assert first["agent_gate"] == {
        "status": "completed",
        "reason": None,
        "run_sha256": "a" * 64,
    }

    path = tmp_path / "frozen-week.json"
    write_shadow_artifact(path, first)
    write_shadow_artifact(path, second)
    changed = deepcopy(first)
    changed["frozen_at"] = "2025-08-14T09:54:00Z"
    with pytest.raises(LiveShadowError, match="overwrite"):
        write_shadow_artifact(path, changed)


def test_incomplete_agent_falls_back_and_post_cutoff_freeze_is_refused():
    fallback = _freeze(agent_status="failed")
    assert fallback["agent_gate"]["status"] == "fallback_to_control_policy"
    assert fallback["agent_gate"]["reason"] == "agent_run_incomplete"
    assert (
        fallback["plans"]["evidence_actual"]
        == fallback["plans"]["evidence_state_no_evidence"]
    )
    with pytest.raises(LiveShadowError, match="freeze by"):
        _freeze(frozen_at="2025-08-14T10:00:01Z")


def test_reveal_advances_independent_states_and_attribution_is_additive():
    states = _states()
    frozen = _freeze()
    plans = frozen["plans"]
    result = reveal_live_shadow_week(
        frozen_week=frozen,
        control_state=states["forecast_optimizer"],
        evidence_state=states["evidence_agent"],
        control_outcome=_outcome(plans["deterministic_control"], 50),
        evidence_baseline_outcome=_outcome(
            plans["evidence_state_no_evidence"], 50
        ),
        evidence_actual_outcome=_outcome(plans["evidence_actual"], 56),
        decision_market=_market(),
        next_market=_market(next_week=True),
        rules=RULES,
        ruleset_sha256=RULES_HASH,
    )
    effects = result["attribution"]["effects"]
    assert effects == {
        "current_evidence": 6,
        "inherited_state": 0,
        "total_evidence_trajectory": 6,
        "identity": "total_evidence_trajectory=current_evidence+inherited_state",
    }
    control_next = result["next_states"]["forecast_optimizer"]
    evidence_next = result["next_states"]["evidence_agent"]
    assert control_next["previous_state_sha256"] == states["forecast_optimizer"][
        "content_sha256"
    ]
    assert evidence_next["previous_state_sha256"] == states["evidence_agent"][
        "content_sha256"
    ]
    assert control_next["content_sha256"] != evidence_next["content_sha256"]
    assert "3" in {row["player_id"] for row in control_next["squad"]}
    assert "16" in {row["player_id"] for row in evidence_next["squad"]}
    assert result["account_writes"] is False


def test_bundle_runner_completes_one_gameweek_and_reproduces_artifacts(
    tmp_path: Path,
):
    states = _states()
    baseline = _candidate()
    evidence = _candidate(transfer=True)
    bundle = {
        "episode_manifest": _episode(),
        "structured_context": {"forecast_sha256": "b" * 64},
        "decision_market": _market(),
        "next_market": _market(next_week=True),
        "control_state": states["forecast_optimizer"],
        "evidence_state": states["evidence_agent"],
        "control_candidate": baseline,
        "evidence_baseline_candidate": baseline,
        "evidence_candidate": evidence,
        "evidence_capture": _evidence(),
        "agent_run": _agent(evidence),
        "frozen_at": FROZEN,
        "outcomes": {
            "control": {
                "outcome_id": "fixture-control",
                "revealed_at": REVEALED,
                "gross_points": 50,
                "content_sha256": "1" * 64,
            },
            "evidence_baseline": {
                "outcome_id": "fixture-baseline",
                "revealed_at": REVEALED,
                "gross_points": 50,
                "content_sha256": "2" * 64,
            },
            "evidence_actual": {
                "outcome_id": "fixture-evidence",
                "revealed_at": REVEALED,
                "gross_points": 56,
                "content_sha256": "3" * 64,
            },
        },
    }
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    out = tmp_path / "out"
    first = run_bundle(
        bundle_path=bundle_path,
        out_dir=out,
        rules_path=RULES_PATH,
        policy_path=POLICY_PATH,
    )
    frozen_bytes = (out / "frozen-week.json").read_bytes()
    revealed_bytes = (out / "revealed-week.json").read_bytes()
    second = run_bundle(
        bundle_path=bundle_path,
        out_dir=out,
        rules_path=RULES_PATH,
        policy_path=POLICY_PATH,
    )
    assert second == first
    assert first["status"] == "revealed_and_transitioned"
    assert first["effects"]["total_evidence_trajectory"] == 6
    assert (out / "frozen-week.json").read_bytes() == frozen_bytes
    assert (out / "revealed-week.json").read_bytes() == revealed_bytes
