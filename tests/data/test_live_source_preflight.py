from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from scripts.preflight_live_sources import build_live_source_preflight


ROOT = Path(__file__).resolve().parents[2]
ODDS_CONFIG = json.loads(
    (ROOT / "config/data_sources/2026-27-live-odds-provider.json").read_text(
        encoding="utf-8"
    )
)
LINEUPS_CONFIG = json.loads(
    (ROOT / "config/data_sources/2026-27-lineups-minutes.json").read_text(
        encoding="utf-8"
    )
)


def test_absent_odds_key_is_safe_degraded_result_with_no_network() -> None:
    report = build_live_source_preflight(
        odds_config=ODDS_CONFIG,
        lineups_config=LINEUPS_CONFIG,
        environ={},
    )

    assert report["preflight_status"] == "degraded"
    assert report["network_actions"] is False
    assert report["account_writes"] is False
    assert report["families"][0] == {
        "family": "odds",
        "source_id": "the-odds-api",
        "credential_environment": "THE_ODDS_API_KEY",
        "credential_checked": True,
        "credential_present": False,
        "status": "degraded",
        "reason": "missing_credential_no_network",
        "network_actions": False,
        "value_redacted": True,
    }
    assert report["eligible_source_families"] == []


def test_present_key_is_verified_structurally_but_never_serialised() -> None:
    secret = "fixture-odds-secret-that-must-not-appear"
    report = build_live_source_preflight(
        odds_config=ODDS_CONFIG,
        lineups_config=LINEUPS_CONFIG,
        environ={"THE_ODDS_API_KEY": secret},
    )

    odds = report["families"][0]
    assert odds["status"] == "ready_structural"
    assert odds["credential_present"] is True
    assert report["eligible_source_families"] == ["odds"]
    assert secret not in json.dumps(report, sort_keys=True)


def test_null_lineups_selection_does_not_inspect_candidate_credentials() -> None:
    candidate_secret = "fixture-lineups-secret-that-must-not-appear"
    report = build_live_source_preflight(
        odds_config=ODDS_CONFIG,
        lineups_config=LINEUPS_CONFIG,
        environ={
            "THE_ODDS_API_KEY": "fixture-odds-secret",
            "API_FOOTBALL_KEY": candidate_secret,
        },
    )

    lineups = report["families"][1]
    assert lineups == {
        "family": "lineups_minutes",
        "selected_provider": None,
        "credential_checked": False,
        "credential_present": None,
        "status": "degraded",
        "reason": "no_provider_selected",
        "network_actions": False,
    }
    encoded = json.dumps(report, sort_keys=True)
    assert candidate_secret not in encoded
    assert "API_FOOTBALL_KEY" not in encoded


def test_selected_provider_key_is_checked_only_after_selection() -> None:
    lineups = deepcopy(LINEUPS_CONFIG)
    lineups["selected_provider"] = "api-football"
    provider = next(
        item for item in lineups["providers"] if item["provider_id"] == "api-football"
    )
    provider["registry_enabled"] = True
    provider["rights_approved"] = True
    provider["owner_approved"] = True
    secret = "fixture-selected-lineups-secret"

    report = build_live_source_preflight(
        odds_config=ODDS_CONFIG,
        lineups_config=lineups,
        environ={"API_FOOTBALL_KEY": secret},
    )

    selected = report["families"][1]
    assert selected["selected_provider"] == "api-football"
    assert selected["credential_checked"] is True
    assert selected["credential_present"] is True
    assert selected["status"] == "ready_structural"
    assert secret not in json.dumps(report, sort_keys=True)


def test_unknown_selected_provider_is_reported_as_degraded_not_fetched() -> None:
    lineups = deepcopy(LINEUPS_CONFIG)
    lineups["selected_provider"] = "unregistered-provider"

    report = build_live_source_preflight(
        odds_config=ODDS_CONFIG,
        lineups_config=lineups,
        environ={},
    )

    selected = report["families"][1]
    assert selected["credential_checked"] is False
    assert selected["reason"] == "selected_provider_not_registered"
    assert selected["network_actions"] is False
