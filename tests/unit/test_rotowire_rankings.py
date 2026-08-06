"""Tests for Rotowire short-horizon rankings citation sealing."""

from __future__ import annotations

import pytest

from src.ingestion.rotowire_rankings import (
    ROTOWIRE_EDITORIAL_SOURCE_ID,
    build_rotowire_short_horizon_rankings_pack,
    write_rotowire_short_horizon_rankings_pack,
)


def _players():
    return [
        {
            "rank": 1,
            "name": "Erling Haaland",
            "team": "Man City",
            "team_code": "MCI",
            "position": "F",
            "price": 15.5,
            "adjusted_total": 37.7,
        },
        {
            "rank": 2,
            "name": "Bruno Fernandes",
            "team": "Man Utd",
            "team_code": "MUN",
            "position": "M",
            "price": 12.0,
            "adjusted_total": 31.1,
        },
    ]


def test_build_seals_short_horizon_rankings_pack():
    pack = build_rotowire_short_horizon_rankings_pack(
        players=_players(),
        observed_at="2026-08-05T11:00:00+01:00",
        published_at="2026-08-05T00:00:00+01:00",
        citation_title="FPL Gameweeks 1-5 Rankings",
        team_fixture_ranks=[
            {
                "rank": 1,
                "team": "Manchester City",
                "team_code": "MCI",
                "opening_5_read": "Elite",
            }
        ],
        narrative={"captaincy": "Haaland popular"},
        require_registry=True,
    )
    assert pack["source_id"] == ROTOWIRE_EDITORIAL_SOURCE_ID
    assert pack["player_count"] == 2
    assert pack["players"][0]["position"] == "FWD"
    assert pack["players"][1]["position"] == "MID"
    assert pack["citation"]["canonical_url_status"] == "pending_owner_url"
    assert pack["influence_policy"].startswith("editorial_prior_only")
    assert len(pack["content_sha256"]) == 64


def test_write_is_create_only(tmp_path):
    pack = build_rotowire_short_horizon_rankings_pack(
        players=_players(),
        observed_at="2026-08-05T11:00:00Z",
        citation_title="FPL Gameweeks 1-5 Rankings",
        citation_url="https://www.rotowire.com/soccer/example",
        require_registry=True,
    )
    path = tmp_path / "rankings.json"
    assert write_rotowire_short_horizon_rankings_pack(pack, path) == "created"
    assert write_rotowire_short_horizon_rankings_pack(pack, path) == "identical"
    mutated = dict(pack)
    mutated["notes"] = "different"
    with pytest.raises(FileExistsError):
        write_rotowire_short_horizon_rankings_pack(mutated, path)


def test_rejects_non_contiguous_ranks():
    players = _players()
    players[1]["rank"] = 3
    with pytest.raises(Exception, match="contiguous"):
        build_rotowire_short_horizon_rankings_pack(
            players=players,
            observed_at="2026-08-05T11:00:00Z",
            citation_title="x",
            require_registry=False,
        )
