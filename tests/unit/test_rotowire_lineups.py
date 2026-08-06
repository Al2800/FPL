"""Tests for Rotowire predicted-lineup citation sealing."""

from __future__ import annotations

import pytest

from src.ingestion.rotowire_lineups import (
    ROTOWIRE_SOURCE_ID,
    build_rotowire_predicted_lineup_pack,
    write_rotowire_predicted_lineup_pack,
)


def _xi(prefix: str):
    slots = [
        "GK",
        "DL",
        "DC",
        "DC",
        "DR",
        "DMC",
        "DMC",
        "AML",
        "AMC",
        "AMR",
        "FW",
    ]
    return [
        {"name": f"{prefix} {i}", "slot": slot, "status": "expected"}
        for i, slot in enumerate(slots, start=1)
    ]


def test_build_seals_predicted_lineup_pack():
    pack = build_rotowire_predicted_lineup_pack(
        fixtures=[
            {
                "home_code": "ARS",
                "away_code": "COV",
                "home_club": "Arsenal",
                "away_club": "Coventry City",
                "kickoff_at": "2026-08-21T15:00:00-04:00",
                "home_xi": _xi("ARS"),
                "away_xi": _xi("COV"),
                "home_injuries": [
                    {"name": "W. Saliba", "slot": "D", "status": "out"}
                ],
            }
        ],
        observed_at="2026-08-05T11:55:00+01:00",
        published_at="2026-08-05T00:00:00+01:00",
        citation_url="https://www.rotowire.com/soccer/lineups.php",
        gameweek=1,
        require_registry=True,
    )
    assert pack["source_id"] == ROTOWIRE_SOURCE_ID
    assert pack["fixture_count"] == 1
    assert pack["fixtures"][0]["home_xi"][0]["started"] is True
    assert pack["citation"]["url"] == "https://www.rotowire.com/soccer/lineups.php"
    assert len(pack["content_sha256"]) == 64


def test_write_is_create_only(tmp_path):
    pack = build_rotowire_predicted_lineup_pack(
        fixtures=[
            {
                "home_code": "ARS",
                "away_code": "COV",
                "kickoff_at": "2026-08-21T15:00:00-04:00",
                "home_xi": _xi("ARS"),
                "away_xi": _xi("COV"),
            }
        ],
        observed_at="2026-08-05T11:55:00Z",
        citation_url="https://www.rotowire.com/soccer/lineups.php",
        require_registry=True,
    )
    path = tmp_path / "lineups.json"
    assert write_rotowire_predicted_lineup_pack(pack, path) == "created"
    assert write_rotowire_predicted_lineup_pack(pack, path) == "identical"
    mutated = dict(pack)
    mutated["notes"] = "different"
    with pytest.raises(FileExistsError):
        write_rotowire_predicted_lineup_pack(mutated, path)


def test_rejects_non_eleven():
    with pytest.raises(Exception, match="exactly 11"):
        build_rotowire_predicted_lineup_pack(
            fixtures=[
                {
                    "home_code": "ARS",
                    "away_code": "COV",
                    "kickoff_at": "2026-08-21T15:00:00-04:00",
                    "home_xi": _xi("ARS")[:10],
                    "away_xi": _xi("COV"),
                }
            ],
            observed_at="2026-08-05T11:55:00Z",
            require_registry=False,
        )
