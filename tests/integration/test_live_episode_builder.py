"""End-to-end contracts for immutable live-shadow episode construction."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path

import httpx
import pytest
from jsonschema import Draft202012Validator, FormatChecker

from scripts.build_live_episode import main as build_cli_main
from scripts.capture_fpl_live_shadow import capture_live_shadow
from src.forecasting.live_capture import (
    LiveForecastCaptureError,
    artifact_hash as live_capture_hash,
    build_live_forecast_capture,
)
from src.ingestion.registry import load_registry
from src.orchestration.episode_builder import LiveEpisodeError, build_live_episode
from src.orchestration.manager_state import ManagerStateError
from src.orchestration.live_shadow import build_unstructured_evidence_capture
from src.scoring.rules_activation import RulesetActivationError


ROOT = Path(__file__).resolve().parents[2]
RULES = ROOT / "control/rules/2025-26.yaml"
LIVE_RULES = ROOT / "control/rules/2026-27.yaml"
CUTOFF = "2025-08-14T10:00:00Z"
DEADLINE = "2025-08-14T11:00:00Z"
OBSERVED = "2025-08-14T09:00:00Z"
COMMIT = "a" * 40
POSITIONS = ["GKP"] * 2 + ["DEF"] * 5 + ["MID"] * 5 + ["FWD"] * 3
PRICES = [4.5] * 2 + [4.5] * 5 + [8.0] * 5 + [9.5] * 3
CHIPS = [
    "wildcard_fh",
    "free_hit_fh",
    "triple_captain_fh",
    "bench_boost_fh",
    "wildcard_sh",
    "free_hit_sh",
    "triple_captain_sh",
    "bench_boost_sh",
]


def _bootstrap() -> dict:
    position_ids = {"GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}
    elements = []
    for index, (position, price) in enumerate(zip(POSITIONS, PRICES), start=1):
        elements.append(
            {
                "id": index,
                "code": 1000 + index,
                "web_name": f"Player {index}",
                "element_type": position_ids[position],
                "team": ((index - 1) % 5) + 1,
                "now_cost": int(price * 10),
                "selected_by_percent": f"{index + 0.5:.1f}",
                "status": "a",
                "news": "",
                "news_added": None,
                "chance_of_playing_this_round": None,
                "chance_of_playing_next_round": None,
            }
        )
    return {
        "events": [{"id": 1, "deadline_time": DEADLINE}],
        "element_types": [
            {"id": 1, "singular_name_short": "GKP"},
            {"id": 2, "singular_name_short": "DEF"},
            {"id": 3, "singular_name_short": "MID"},
            {"id": 4, "singular_name_short": "FWD"},
        ],
        "teams": [{"id": index, "name": f"Team {index}"} for index in range(1, 6)],
        "elements": elements,
    }


def _fixtures() -> list[dict]:
    return [
        {
            "id": 1,
            "event": 1,
            "kickoff_time": "2025-08-14T12:30:00Z",
            "team_h": 1,
            "team_a": 2,
            "team_h_difficulty": 2,
            "team_a_difficulty": 4,
            "provisional_start_time": False,
            "finished": False,
            "started": False,
            "team_h_score": None,
            "team_a_score": None,
            "stats": [],
        }
    ]


def _client(*, fixtures_status: int = 200) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "authorization" not in request.headers
        assert "cookie" not in request.headers
        if request.url.path == "/api/bootstrap-static/":
            return httpx.Response(200, json=_bootstrap(), request=request)
        if request.url.path == "/api/fixtures/":
            return httpx.Response(
                fixtures_status,
                json=_fixtures() if fixtures_status == 200 else {"detail": "unavailable"},
                request=request,
            )
        raise AssertionError(f"Unexpected path: {request.url.path}")

    return httpx.Client(transport=httpx.MockTransport(handler))


def _capture(tmp_path: Path, *, observed_at: str = OBSERVED, fixtures_status: int = 200) -> Path:
    capture_root = tmp_path / "capture"
    with _client(fixtures_status=fixtures_status) as client:
        capture_live_shadow(
            out_dir=capture_root,
            base_url="https://fantasy.premierleague.com",
            observed_at=observed_at,
            client=client,
        )
    stamp = observed_at.replace(":", "").replace("-", "")
    return capture_root / stamp / "capture-summary.json"


def _manager_state() -> dict:
    squad = []
    for index, (position, price) in enumerate(zip(POSITIONS, PRICES), start=1):
        squad.append(
            {
                "player_id": str(index),
                "fpl_code": 1000 + index,
                "web_name": f"Player {index}",
                "position": position,
                "club_id": str(((index - 1) % 5) + 1),
                "purchase_price": price,
                "selling_price": price,
                "now_cost": price,
            }
        )
    return {
        "$schema_note": "Manual test input; no credentials.",
        "manager_id": "manager-fixture-1",
        "season": "2025-26",
        "gameweek": 1,
        "observed_at": OBSERVED,
        "available_at": "2025-08-14T09:01:00Z",
        "deadline": DEADLINE,
        "decision_cutoff": CUTOFF,
        "bank": 0.0,
        "free_transfers": 1,
        "chips_available": list(CHIPS),
        "chip_history": [],
        "squad": squad,
        "notes": "Fixture-only state",
    }


def _write_manager(tmp_path: Path, state: dict | None = None, *, name: str = "manager.json") -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state or _manager_state(), indent=2), encoding="utf-8")
    return path


def _build(tmp_path: Path, *, capture: Path | None = None, state: dict | None = None, rules: Path = RULES, out_name: str = "episode") -> dict:
    return build_live_episode(
        capture_summary_path=capture or _capture(tmp_path),
        manager_state_path=_write_manager(tmp_path, state),
        out_dir=tmp_path / out_name,
        rules_path=rules,
        code_commit=COMMIT,
    )


def _validate(schema_name: str, value: dict) -> None:
    schema = json.loads(
        (ROOT / "control/schemas/benchmark" / schema_name).read_text(encoding="utf-8")
    )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)


def test_complete_capture_and_manual_state_build_schema_valid_episode(tmp_path: Path):
    index = _build(tmp_path)
    out = tmp_path / "episode"
    manifest = json.loads((out / "episode-manifest.json").read_text())
    manager = json.loads((out / "manager-state.json").read_text())
    features = json.loads((out / "feature-view.json").read_text())
    pending = json.loads((out / "pending-outcome.json").read_text())

    _validate("episode-manifest.json", manifest)
    _validate("manager-state.json", manager)
    _validate("pending-outcome.json", pending)
    feature_schema = json.loads(
        (ROOT / "control/schemas/data/feature-view-manifest.json").read_text()
    )
    Draft202012Validator(feature_schema, format_checker=FormatChecker()).validate(features)

    assert index["mode"] == manifest["mode"] == "live_shadow"
    assert index["episode_id"] == manifest["episode_id"]
    assert len(index["observed_episode_sha256"]) == 64
    assert "squad" not in index
    assert "outcome" not in index
    assert manager["provenance"] == {
        "entry_method": "manual",
        "authentication": "none",
        "account_identifier_stored": False,
    }
    assert manager["team_purchase_value"] == 100.0
    assert manager["team_current_value"] == 100.0
    assert manager["team_selling_value"] == 100.0
    assert manager["squad"][0]["current_price"] == 4.5
    assert len(features["features"]) == 31
    assert set(manifest["observed"]["snapshot_ids"]) == {
        row["artifact_id"] for row in manifest["observed"]["source_artifacts"]
    }
    cutoff = datetime.fromisoformat(CUTOFF.replace("Z", "+00:00"))
    assert all(
        datetime.fromisoformat(row["available_at"].replace("Z", "+00:00")) <= cutoff
        for row in manifest["observed"]["source_artifacts"]
    )


def test_live_capture_freezes_launch_state_and_records_missing_market_degradation(
    tmp_path: Path,
):
    capture = _capture(tmp_path)
    summary = json.loads(capture.read_text())
    ref = summary["forecast_input_capture"]
    artifact = json.loads((capture.parent / ref["body_file"]).read_text())

    assert artifact["content_sha256"] == live_capture_hash(artifact)
    assert ref["content_sha256"] == artifact["content_sha256"]
    assert ref["status"] == "degraded"
    assert artifact["official_launch"]["players"][0] == {
        "availability": {
            "chance_of_playing_next_round": None,
            "chance_of_playing_this_round": None,
            "news": "",
            "news_added": None,
            "status": "a",
        },
        "available_at": OBSERVED,
        "cold_start_class": "established",
        "fpl_code": 1001,
        "launch_price": 4.5,
        "observed_at": OBSERVED,
        "player_id": 1,
        "position": "GKP",
        "source_sha256": summary["endpoints"][0]["content_hash_sha256"],
        "team_id": 1,
        "web_name": "Player 1",
    }
    assert artifact["market_evidence"]["required_slots"] == [
        "T-24h",
        "T-8h",
        "T-2h",
        "final",
    ]
    assert {row["slot"] for row in artifact["degraded_features"]} == {
        "T-24h",
        "T-8h",
        "T-2h",
        "final",
    }
    assert artifact["feature_contract"]["forecast_interface"] == "live-faithful-v1"


def test_complete_unstructured_evidence_is_bound_to_episode_and_raw_bytes(
    tmp_path: Path,
):
    capture = _capture(tmp_path)
    summary = json.loads(capture.read_text())
    content = "The player remains unavailable for selection."
    raw = {
        "source_id": "fixture-club-news",
        "document_id": "fixture-news-1",
        "url": "https://club.example/news/1",
        "title": "Team news",
        "published_at": "2025-08-14T08:00:00Z",
        "observed_at": "2025-08-14T08:05:00Z",
        "available_at": "2025-08-14T08:06:00Z",
        "content": content,
        "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
        "raw_file": "forecast-inputs/evidence-01.json",
    }
    raw_path = capture.parent / raw["raw_file"]
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(raw), encoding="utf-8")
    evidence = build_unstructured_evidence_capture(
        snapshots=[raw],
        source_registry={
            "sources": [
                {
                    "source_id": "fixture-club-news",
                    "enabled": True,
                    "licence_status": "restricted",
                    "allowed_use": "private_analysis",
                    "attribution": "Fixture club",
                }
            ]
        },
        decision_cutoff=CUTOFF,
    )
    evidence_path = capture.parent / "unstructured-evidence-capture.json"
    evidence_path.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary["unstructured_evidence_capture"] = {
        "body_file": evidence_path.name,
        "content_sha256": evidence["content_sha256"],
        "status": "complete",
        "snapshot_count": 1,
    }
    capture.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    _build(tmp_path, capture=capture)
    manifest = json.loads(
        (tmp_path / "episode/episode-manifest.json").read_text()
    )
    assert evidence["snapshots"][0]["snapshot_id"] in manifest["observed"][
        "snapshot_ids"
    ]
    assert {
        row["source_id"] for row in manifest["observed"]["source_artifacts"]
    } == {"fpl-official-endpoints", "fixture-club-news"}

    raw["content"] += " Tampered."
    raw_path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(LiveEpisodeError, match="raw content hash mismatch"):
        _build(tmp_path, capture=capture, out_name="tampered-evidence")


def test_launch_freeze_classifies_promoted_and_transferred_and_refuses_late_freeze(
    tmp_path: Path,
):
    context = tmp_path / "launch-context.json"
    context.write_text(
        json.dumps(
            {
                "promoted_team_ids": [1],
                "transferred_player_codes": [1002],
            }
        ),
        encoding="utf-8",
    )
    with _client() as client:
        summary = capture_live_shadow(
            out_dir=tmp_path / "early",
            base_url="https://fantasy.premierleague.com",
            observed_at=OBSERVED,
            launch_context_path=context,
            freeze_launch=True,
            client=client,
        )
    artifact = json.loads(
        (
            tmp_path
            / "early"
            / OBSERVED.replace(":", "").replace("-", "")
            / summary["forecast_input_capture"]["body_file"]
        ).read_text()
    )
    assert artifact["official_launch"]["status"] == "frozen"
    classes = {
        row["fpl_code"]: row["cold_start_class"]
        for row in artifact["official_launch"]["players"]
    }
    assert classes[1001] == "promoted_team"
    assert classes[1002] == "transferred_player"
    assert classes[1003] == "established"

    with _client() as client, pytest.raises(
        LiveForecastCaptureError, match="before the GW1 deadline"
    ):
        capture_live_shadow(
            out_dir=tmp_path / "late",
            base_url="https://fantasy.premierleague.com",
            observed_at=DEADLINE,
            decision_cutoff="2025-08-15T11:00:00Z",
            launch_context_path=context,
            freeze_launch=True,
            client=client,
        )


def test_market_evidence_requires_approval_hash_and_strict_pre_cutoff_time():
    registry = load_registry()
    registry["sources"].append(
        {
            "source_id": "fixture-live-odds",
            "enabled": True,
            "activation_approval": {"terms": "approved", "cost": "approved"},
        }
    )
    payload = {"markets": [{"fixture_id": 1, "home_win": 0.5}]}
    snapshot = {
        "source_id": "fixture-live-odds",
        "slot": "T-2h",
        "observed_at": "2025-08-14T08:00:00Z",
        "available_at": "2025-08-14T08:01:00Z",
        "payload": payload,
        "source_sha256": hashlib.sha256(
            json.dumps(
                payload, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest(),
    }
    bootstrap_hash = "a" * 64
    artifact = build_live_forecast_capture(
        bootstrap=_bootstrap(),
        bootstrap_manifest={"content_hash_sha256": bootstrap_hash},
        observed_at=OBSERVED,
        decision_cutoff=CUTOFF,
        launch_context=None,
        market_snapshots=[snapshot],
        source_registry=registry,
        freeze_launch=False,
    )
    assert artifact["market_evidence"]["snapshots"][0]["slot"] == "T-2h"
    assert "T-2h" not in {
        row["slot"]
        for row in artifact["degraded_features"]
        if row["reason"] == "no_approved_pre_cutoff_snapshot"
    }

    late = deepcopy(snapshot)
    late["available_at"] = CUTOFF
    disabled = deepcopy(snapshot)
    disabled["source_id"] = "betfair-historical"
    rejected = build_live_forecast_capture(
        bootstrap=_bootstrap(),
        bootstrap_manifest={"content_hash_sha256": bootstrap_hash},
        observed_at=OBSERVED,
        decision_cutoff=CUTOFF,
        launch_context=None,
        market_snapshots=[late, disabled],
        source_registry=registry,
        freeze_launch=False,
    )
    assert rejected["market_evidence"]["snapshots"] == []
    reasons = [row["reason"] for row in rejected["market_evidence"]["rejected"]]
    assert any("strictly before cutoff" in reason for reason in reasons)
    assert any("disabled" in reason for reason in reasons)


def test_pending_outcome_contains_no_future_values_and_is_reference_only(tmp_path: Path):
    _build(tmp_path)
    out = tmp_path / "episode"
    manifest = json.loads((out / "episode-manifest.json").read_text())
    pending = json.loads((out / "pending-outcome.json").read_text())

    assert pending["status"] == "pending"
    assert pending["contains_outcome_values"] is False
    assert pending["reveal_after"] == "proposal_frozen"
    forbidden = {"points", "realised_points", "scores", "results", "player_outcomes"}
    assert forbidden.isdisjoint(pending)
    assert set(manifest["hidden_outcome_ref"]) == {
        "outcome_id",
        "content_sha256",
        "reveal_after",
    }
    assert manifest["hidden_outcome_ref"]["content_sha256"] == pending["content_sha256"]


def test_identical_rerun_reuses_immutable_artifacts_and_hashes(tmp_path: Path):
    capture = _capture(tmp_path)
    state = _manager_state()
    first = _build(tmp_path, capture=capture, state=state)
    second = _build(tmp_path, capture=capture, state=state)
    assert second == first

    changed = deepcopy(state)
    changed["observed_at"] = "2025-08-14T09:00:30Z"
    with pytest.raises(FileExistsError, match="immutable"):
        _build(tmp_path, capture=capture, state=changed)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("selling_price", "selling price"),
        ("player_code", "code"),
        ("position", "position"),
        ("club", "club"),
        ("duplicate", "unique"),
        ("free_transfers", "free transfers"),
        ("fractional_gameweek", "gameweek must be an integer"),
        ("fractional_transfers", "free transfers must be an integer"),
        ("numeric_manager_id", "pseudonymous"),
        ("unsupported_manager_field", "unsupported fields"),
        ("unsupported_player_field", "unsupported fields"),
        ("chips", "chip"),
        ("deadline", "deadline"),
    ],
)
def test_invalid_manual_manager_state_fails_with_actionable_diagnostics(
    tmp_path: Path, mutation: str, message: str
):
    state = _manager_state()
    if mutation == "selling_price":
        state["squad"][0]["selling_price"] = 4.4
    elif mutation == "player_code":
        state["squad"][0]["fpl_code"] = 999999
    elif mutation == "position":
        state["squad"][0]["position"] = "MID"
    elif mutation == "club":
        state["squad"][0]["club_id"] = "99"
    elif mutation == "duplicate":
        state["squad"][1] = deepcopy(state["squad"][0])
    elif mutation == "free_transfers":
        state["free_transfers"] = 6
    elif mutation == "fractional_gameweek":
        state["gameweek"] = 1.5
    elif mutation == "fractional_transfers":
        state["free_transfers"] = 1.5
    elif mutation == "numeric_manager_id":
        state["manager_id"] = "1234567"
    elif mutation == "unsupported_manager_field":
        state["account_id"] = 1234567
    elif mutation == "unsupported_player_field":
        state["squad"][0]["session_token"] = "must-not-be-accepted"
    elif mutation == "chips":
        state["chips_available"].append("assistant_manager_fh")
    elif mutation == "deadline":
        state["deadline"] = "2025-08-14T11:01:00Z"

    with pytest.raises(ManagerStateError, match=message):
        _build(tmp_path, state=state)


def test_stale_or_post_cutoff_inputs_fail_closed(tmp_path: Path):
    stale = _manager_state()
    stale["observed_at"] = "2025-08-14T03:59:59Z"
    stale["available_at"] = "2025-08-14T09:01:00Z"
    with pytest.raises(ManagerStateError, match="stale"):
        _build(tmp_path, state=stale, out_name="stale")

    late_capture = _capture(
        tmp_path / "late", observed_at="2025-08-14T10:00:01Z"
    )
    with pytest.raises(LiveEpisodeError, match="cutoff"):
        _build(tmp_path / "late-build", capture=late_capture)


def test_capture_integrity_partial_failure_and_authentication_are_rejected(tmp_path: Path):
    capture = _capture(tmp_path / "tamper")
    run_dir = capture.parent
    bootstrap_path = run_dir / "api_bootstrap-static.json"
    bootstrap_path.write_bytes(bootstrap_path.read_bytes() + b"\n")
    with pytest.raises(LiveEpisodeError, match="hash"):
        _build(tmp_path / "tamper-build", capture=capture)

    partial = _capture(tmp_path / "partial", fixtures_status=503)
    with pytest.raises(LiveEpisodeError, match="complete"):
        _build(tmp_path / "partial-build", capture=partial)

    unauthenticated = _capture(tmp_path / "auth")
    summary = json.loads(unauthenticated.read_text())
    summary["authentication"] = "browser_session"
    altered = unauthenticated.parent / "altered-summary.json"
    altered.write_text(json.dumps(summary), encoding="utf-8")
    with pytest.raises(LiveEpisodeError, match="authentication"):
        _build(tmp_path / "auth-build", capture=altered)

    wrong_host = _capture(tmp_path / "wrong-host")
    summary = json.loads(wrong_host.read_text())
    summary["endpoints"][0]["request_url"] = "https://attacker.example/api/bootstrap-static/"
    summary["endpoints"][0]["origin"] = "https://attacker.example/api/bootstrap-static/"
    altered_host = wrong_host.parent / "altered-host-summary.json"
    altered_host.write_text(json.dumps(summary), encoding="utf-8")
    with pytest.raises(LiveEpisodeError, match="official FPL HTTPS host"):
        _build(tmp_path / "wrong-host-build", capture=altered_host)

    wrong_manifest = _capture(tmp_path / "wrong-manifest")
    summary = json.loads(wrong_manifest.read_text())
    summary["endpoints"][0]["manifest_id"] = "0" * 64
    altered_manifest = wrong_manifest.parent / "altered-manifest-summary.json"
    altered_manifest.write_text(json.dumps(summary), encoding="utf-8")
    with pytest.raises(LiveEpisodeError, match="manifest identity"):
        _build(tmp_path / "wrong-manifest-build", capture=altered_manifest)


def test_unconfirmed_live_rules_are_a_hard_preflight_gate(tmp_path: Path):
    state = _manager_state()
    state["season"] = "2026-27"
    with pytest.raises(RulesetActivationError, match="not activatable"):
        _build(tmp_path, state=state, rules=LIVE_RULES)


def test_cli_builds_offline_fixture_idempotently_and_keeps_live_rules_blocked(
    tmp_path: Path, capsys
):
    capture = _capture(tmp_path / "cli-capture")
    manager = _write_manager(tmp_path / "cli-input")
    out = tmp_path / "cli-episode"
    args = [
        "--capture-summary", str(capture),
        "--manager-state", str(manager),
        "--rules", str(RULES),
        "--out", str(out),
        "--code-commit", COMMIT,
    ]

    assert build_cli_main(args) == 0
    first = json.loads(capsys.readouterr().out)
    assert build_cli_main(args) == 0
    second = json.loads(capsys.readouterr().out)
    assert second == first
    assert json.loads((out / "episode-manifest.json").read_text())["mode"] == "live_shadow"

    blocked_args = list(args)
    blocked_args[blocked_args.index(str(RULES))] = str(LIVE_RULES)
    blocked_args[blocked_args.index(str(out))] = str(tmp_path / "blocked-live-episode")
    assert build_cli_main(blocked_args) == 2
    refused = capsys.readouterr()
    assert refused.out == ""
    assert "not activatable" in refused.err
    assert not (tmp_path / "blocked-live-episode").exists()
