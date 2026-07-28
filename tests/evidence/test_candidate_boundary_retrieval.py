from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from time import perf_counter

import pytest
import yaml

from src.evidence.candidate_boundary_retrieval import (
    CandidateBoundaryRetrievalError,
    build_candidate_boundary_packet,
    discover_candidate_boundaries,
)
from src.evidence.live_evidence_ledger import (
    append_live_evidence_claim,
    live_evidence_hash,
    new_live_evidence_ledger,
    project_live_evidence,
)
from src.forecasting.live_faithful import artifact_hash
from src.optimisation.io import fingerprint


ROOT = Path(__file__).resolve().parents[2]
COVERAGE = json.loads(
    (ROOT / "config/data_sources/2026-27-evidence-coverage.json").read_text()
)
EVIDENCE = json.loads(
    (ROOT / "config/data_sources/2026-27-evidence.json").read_text()
)
REGISTRY = yaml.safe_load(
    (ROOT / "control/sources/source-registry.yaml").read_text()
)


def engine() -> tuple[dict, dict]:
    players = [
        {
            "player_id": "p1",
            "web_name": "Owned Mid",
            "position": "MID",
            "club_id": "club:a",
            "now_cost": 7.0,
            "purchase_price": 7.0,
            "expected_points": 3.0,
            "start_probability": 0.95,
            "status": "a",
            "fixture_ids": ["fixture:1"],
        },
        {
            "player_id": "p2",
            "web_name": "Risk Defender",
            "position": "DEF",
            "club_id": "club:a",
            "now_cost": 4.5,
            "purchase_price": 4.5,
            "expected_points": 2.0,
            "start_probability": 0.5,
            "status": "d",
            "fixture_ids": ["fixture:1"],
        },
        {
            "player_id": "p3",
            "web_name": "Owned Forward",
            "position": "FWD",
            "club_id": "club:b",
            "now_cost": 7.5,
            "purchase_price": 7.5,
            "expected_points": 5.0,
            "start_probability": 0.9,
            "status": "a",
            "fixture_ids": ["fixture:2"],
        },
        {
            "player_id": "q1",
            "web_name": "External Mid",
            "position": "MID",
            "club_id": "club:c",
            "now_cost": 7.2,
            "expected_points": 6.0,
            "start_probability": 0.9,
            "status": "a",
            "fixture_ids": ["fixture:3"],
        },
        {
            "player_id": "q2",
            "web_name": "External Defender",
            "position": "DEF",
            "club_id": "club:d",
            "now_cost": 4.5,
            "expected_points": 5.0,
            "start_probability": 0.88,
            "status": "a",
            "fixture_ids": ["fixture:4"],
        },
        {
            "player_id": "q3",
            "web_name": "Unaffordable Mid",
            "position": "MID",
            "club_id": "club:e",
            "now_cost": 12.0,
            "expected_points": 9.0,
            "start_probability": 0.95,
            "status": "a",
            "fixture_ids": ["fixture:5"],
        },
    ]
    solver_input = {
        "season": "2026-27",
        "gameweek": 1,
        "decision_at": "2026-08-14T10:00:00Z",
        "ruleset_id": "2026-27-v1.0",
        "bank": 0.5,
        "free_transfers": 1,
        "squad_player_ids": ["p1", "p2", "p3"],
        "players": players,
        "horizon_gameweeks": 3,
        "discount_factors": [1.0, 0.9, 0.8],
    }

    def candidate(
        objective: float,
        *,
        transfer: tuple[str, str] | None = None,
        captain: str = "p3",
    ) -> dict:
        transfers = (
            []
            if transfer is None
            else [
                {
                    "player_out_id": transfer[0],
                    "player_in_id": transfer[1],
                }
            ]
        )
        squad = ["p1", "p2", "p3"]
        if transfer is not None:
            squad[squad.index(transfer[0])] = transfer[1]
        return {
            "objective": objective,
            "strategy": "no_transfer" if not transfers else "free_transfer",
            "transfers": transfers,
            "bank_after": 0.3 if transfer == ("p1", "q1") else 0.5,
            "hit_cost": 0,
            "lineup": {
                "starting_xi_ids": squad[:2],
                "bench_ids": squad[2:],
                "captain_id": captain,
                "vice_captain_id": squad[0],
            },
        }

    no_transfer = candidate(49.2)
    selected = candidate(50.0, transfer=("p1", "q1"))
    defender = candidate(49.8, transfer=("p2", "q2"))
    solver_output = {
        "solver_version": "fixture",
        "input_fingerprint": fingerprint(solver_input),
        "selected": selected,
        "plans": {"no_transfer": no_transfer},
        "all_candidates": [selected, defender, no_transfer],
    }
    return solver_input, solver_output


def claim(
    claim_id: str,
    *,
    player_id: str,
    boundary_ids: list[str] | None = None,
    text: str = "The player remains a selection doubt.",
) -> dict:
    return {
        "claim_id": claim_id,
        "source_id": "official-club-communications",
        "document_id": f"doc:{claim_id}",
        "source_url": f"https://club.example/{claim_id}",
        "source_hash_sha256": hashlib.sha256(claim_id.encode()).hexdigest(),
        "claim_text": text,
        "claim_precision": "derived_claim",
        "claim_type": "player_availability",
        "value": {"status": "doubtful"},
        "confidence": 0.8,
        "published_at": "2026-08-14T08:00:00Z",
        "observed_at": "2026-08-14T08:05:00Z",
        "available_at": "2026-08-14T08:06:00Z",
        "expires_at": "2026-08-15T08:06:00Z",
        "identity_bindings": [
            {
                "entity_type": "player_uid",
                "stable_id": player_id,
                "source_label": player_id,
                "match_status": "manual_verified",
            }
        ],
        "decision_boundary_ids": boundary_ids or [],
        "estimated_impact_points": 6.0,
        "supersedes_claim_ids": [],
    }


def evidence_view(*rows: dict) -> dict:
    ledger = new_live_evidence_ledger(
        season="2026-27", created_at="2026-08-14T07:00:00Z"
    )
    for row in rows:
        ledger = append_live_evidence_claim(
            ledger,
            row,
            source_registry=REGISTRY,
            config=EVIDENCE,
        )
    return project_live_evidence(
        ledger, decision_at="2026-08-14T10:00:00Z"
    )


def test_discovers_owned_risks_and_only_engine_evaluated_external_candidates() -> None:
    solver_input, solver_output = engine()
    first = discover_candidate_boundaries(
        solver_input=solver_input,
        solver_output=solver_output,
        config=COVERAGE,
    )
    second = discover_candidate_boundaries(
        solver_input=solver_input,
        solver_output=solver_output,
        config=COVERAGE,
    )

    assert first == second
    assert first["content_sha256"] == artifact_hash(first)
    watched = {row["player_id"]: row for row in first["owned_watchlist"]}
    assert "availability_risk" in watched["p2"]["reasons"]
    assert "selected_transfer_out" in watched["p1"]["reasons"]
    assert {row["player_id"] for row in first["external_candidates"]} == {
        "q1",
        "q2",
    }
    assert "q3" not in first["expanded_entities"]["player_ids"]
    assert {
        row["decision_type"] for row in first["boundaries"]
    } >= {"transfer", "lineup", "captaincy"}


def test_engine_binding_and_outcome_blindness_fail_closed() -> None:
    solver_input, solver_output = engine()
    broken = deepcopy(solver_output)
    broken["input_fingerprint"] = "wrong"
    with pytest.raises(
        CandidateBoundaryRetrievalError, match="input fingerprint"
    ):
        discover_candidate_boundaries(
            solver_input=solver_input,
            solver_output=broken,
            config=COVERAGE,
        )
    leaked = deepcopy(solver_input)
    leaked["hidden_outcome"] = {"gross_points": 99}
    with pytest.raises(CandidateBoundaryRetrievalError, match="outcome field"):
        discover_candidate_boundaries(
            solver_input=leaked,
            solver_output=solver_output,
            config=COVERAGE,
        )

    historical = deepcopy(solver_input)
    historical["players"][0]["total_points"] = 42
    historical_output = deepcopy(solver_output)
    historical_output["input_fingerprint"] = fingerprint(historical)
    discover_candidate_boundaries(
        solver_input=historical,
        solver_output=historical_output,
        config=COVERAGE,
    )


def test_entity_join_retrieves_external_player_claim_and_records_irrelevance() -> None:
    solver_input, solver_output = engine()
    discovery = discover_candidate_boundaries(
        solver_input=solver_input,
        solver_output=solver_output,
        config=COVERAGE,
    )
    view = evidence_view(
        claim("external-relevant", player_id="q2"),
        claim("unrelated", player_id="outside"),
    )
    packet = build_candidate_boundary_packet(
        discovery=discovery,
        evidence_view=view,
        config=COVERAGE,
    )

    assert packet["status"] == "complete"
    assert [
        row["claim"]["claim_id"] for row in packet["evidence"]
    ] == ["external-relevant"]
    assert packet["evidence"][0]["match_basis"] == ["stable_entity"]
    assert packet["omitted"]["irrelevant_claim_ids"] == ["unrelated"]
    assert packet["engine_output_sha256"] == discovery[
        "engine_output_sha256"
    ]
    assert packet["context_contract"]["host_audit_only_fields"] == [
        "exclusion_counts",
        "omitted",
    ]
    assert packet["context_contract"][
        "prompt_must_exclude_host_audit_fields"
    ] is True
    assert "omitted" not in packet["context_contract"]["agent_visible_fields"]


def test_only_boundary_relevant_conflicts_are_agent_visible() -> None:
    solver_input, solver_output = engine()
    discovery = discover_candidate_boundaries(
        solver_input=solver_input,
        solver_output=solver_output,
        config=COVERAGE,
    )
    view = evidence_view(claim("external-relevant", player_id="q2"))
    view["conflicts"] = [
        {
            "subject_key": "player_availability|player_uid:q2",
            "claim_ids": ["q2-a", "q2-b"],
            "resolution": "exclude_pending_explicit_supersession",
        },
        {
            "subject_key": "player_availability|player_uid:outside",
            "claim_ids": ["outside-a", "outside-b"],
            "resolution": "exclude_pending_explicit_supersession",
        },
    ]
    view["content_sha256"] = live_evidence_hash(view)

    packet = build_candidate_boundary_packet(
        discovery=discovery,
        evidence_view=view,
        config=COVERAGE,
    )

    assert [row["subject_key"] for row in packet["conflicts"]] == [
        "player_availability|player_uid:q2"
    ]


def test_packet_caps_are_deterministic_and_list_character_budget_omissions() -> None:
    solver_input, solver_output = engine()
    discovery = discover_candidate_boundaries(
        solver_input=solver_input,
        solver_output=solver_output,
        config=COVERAGE,
    )
    bounded = deepcopy(COVERAGE)
    bounded["retrieval"]["maximum_claim_characters"] = 45
    view = evidence_view(
        claim("a-first", player_id="q1", text="A" * 40),
        claim("b-second", player_id="q2", text="B" * 40),
    )
    packet = build_candidate_boundary_packet(
        discovery=discovery,
        evidence_view=view,
        config=bounded,
    )

    assert packet["limits"]["selected_claims"] == 1
    assert packet["omitted"]["character_budget_claim_ids"] == ["b-second"]
    assert build_candidate_boundary_packet(
        discovery=discovery,
        evidence_view=view,
        config=bounded,
    ) == packet

def test_candidate_discovery_and_retrieval_p95_stay_within_local_guardrail() -> None:
    solver_input, solver_output = engine()
    view = evidence_view(claim("latency-relevant", player_id="q1"))
    elapsed_ms: list[float] = []
    for _ in range(30):
        started = perf_counter()
        discovery = discover_candidate_boundaries(
            solver_input=solver_input,
            solver_output=solver_output,
            config=COVERAGE,
        )
        build_candidate_boundary_packet(
            discovery=discovery,
            evidence_view=view,
            config=COVERAGE,
        )
        elapsed_ms.append((perf_counter() - started) * 1000)
    p95 = sorted(elapsed_ms)[int(len(elapsed_ms) * 0.95) - 1]
    assert p95 < COVERAGE["retrieval"]["maximum_packet_latency_ms"]

def test_large_active_ledger_still_yields_bounded_packet_within_guardrail() -> None:
    solver_input, solver_output = engine()
    discovery = discover_candidate_boundaries(
        solver_input=solver_input,
        solver_output=solver_output,
        config=COVERAGE,
    )
    claims = []
    for index in range(2000):
        player_id = "q1" if index % 200 == 0 else f"outside:{index}"
        claims.append(
            {
                "claim_id": f"scale-{index:04d}",
                "source_id": "official-club-communications",
                "claim_text": "Bounded availability claim.",
                "confidence": 0.8,
                "available_at": "2026-08-14T08:06:00Z",
                "decision_boundary_ids": [],
                "estimated_impact_points": 6.0,
                "identity_bindings": [
                    {
                        "entity_type": "player_uid",
                        "stable_id": player_id,
                    }
                ],
                "source_rights": {"authority": "canonical"},
            }
        )
    view = {
        "schema_version": "1.0",
        "ledger_id": "live-evidence:2026-27",
        "ledger_sha256": "a" * 64,
        "decision_at": "2026-08-14T10:00:00Z",
        "accepted": claims,
        "conflicts": [],
        "excluded": {
            "future": [],
            "expired": [],
            "superseded": [],
            "quarantined": [],
        },
    }
    view["content_sha256"] = live_evidence_hash(view)

    started = perf_counter()
    packet = build_candidate_boundary_packet(
        discovery=discovery,
        evidence_view=view,
        config=COVERAGE,
    )
    elapsed_ms = (perf_counter() - started) * 1000

    assert packet["limits"]["selected_claims"] <= 12
    assert packet["limits"]["selected_claim_characters"] <= 12000
    assert len(packet["omitted"]["irrelevant_claim_ids"]) == 1990
    assert elapsed_ms < COVERAGE["retrieval"]["maximum_packet_latency_ms"]
