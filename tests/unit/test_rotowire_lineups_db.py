"""Tests for Rotowire predicted-lineups DuckDB/Parquet load."""

from __future__ import annotations

import duckdb

from src.ingestion.rotowire_lineups import build_rotowire_predicted_lineup_pack
from src.ingestion.rotowire_lineups_db import (
    flatten_rotowire_predicted_lineup_pack,
    load_rotowire_predicted_lineup_pack_to_warehouse,
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


def test_flatten_and_load_to_duckdb(tmp_path):
    pack = build_rotowire_predicted_lineup_pack(
        fixtures=[
            {
                "home_code": "ARS",
                "away_code": "COV",
                "kickoff_at": "2026-08-21T15:00:00-04:00",
                "home_xi": _xi("ARS"),
                "away_xi": _xi("COV"),
                "home_injuries": [
                    {"name": "W. Saliba", "slot": "D", "status": "out"}
                ],
            }
        ],
        observed_at="2026-08-05T11:55:00Z",
        citation_url="https://www.rotowire.com/soccer/lineups.php",
        require_registry=True,
    )
    pack_path = tmp_path / "pack.json"
    pack_path.write_text(
        __import__("json").dumps(pack, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    frames = flatten_rotowire_predicted_lineup_pack(pack)
    assert len(frames["fixtures"]) == 1
    assert len(frames["xi_players"]) == 22
    assert len(frames["injury_notes"]) == 1

    warehouse = tmp_path / "warehouse"
    result = load_rotowire_predicted_lineup_pack_to_warehouse(
        pack_path,
        warehouse_dir=warehouse,
        require_registry=True,
    )
    assert result["duckdb"]["counts"]["xi_players"] == 22
    # Idempotent replace
    again = load_rotowire_predicted_lineup_pack_to_warehouse(
        pack_path,
        warehouse_dir=warehouse,
        require_registry=True,
    )
    assert again["duckdb"]["counts"]["xi_players"] == 22

    con = duckdb.connect(str(warehouse / "lab.duckdb"))
    try:
        n = con.execute(
            "SELECT COUNT(*) FROM rotowire_predicted_xi_players"
        ).fetchone()[0]
        assert n == 22
        fixture = con.execute(
            "SELECT home_code, away_code FROM rotowire_predicted_fixtures"
        ).fetchone()
        assert fixture == ("ARS", "COV")
    finally:
        con.close()
