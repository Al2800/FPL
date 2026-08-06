"""Load sealed Rotowire predicted-lineup citation packs into DuckDB + Parquet.

Analytical only. Does not scrape, does not alter the sealed JSON citation, and
does not admit rows into the live expected-minutes forecast path.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from src.ingestion.registry import assert_collectable
from src.ingestion.rotowire_lineups import ROTOWIRE_CITATION_SCHEMA, ROTOWIRE_SOURCE_ID


class RotowireLineupsDbError(ValueError):
    """Raised when a sealed pack cannot be loaded into the analytical store."""


DEFAULT_WAREHOUSE_DIR = Path("data/warehouse")
DEFAULT_DB_NAME = "lab.duckdb"


def _require_pack(pack: Mapping[str, Any]) -> dict[str, Any]:
    if pack.get("schema_version") != ROTOWIRE_CITATION_SCHEMA:
        raise RotowireLineupsDbError(
            f"unsupported schema_version {pack.get('schema_version')!r}"
        )
    if pack.get("source_id") != ROTOWIRE_SOURCE_ID:
        raise RotowireLineupsDbError(
            f"source_id must be {ROTOWIRE_SOURCE_ID}, got {pack.get('source_id')!r}"
        )
    digest = str(pack.get("content_sha256") or "")
    if len(digest) != 64:
        raise RotowireLineupsDbError("content_sha256 is required on sealed pack")
    fixtures = pack.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        raise RotowireLineupsDbError("sealed pack has no fixtures")
    return dict(pack)


def load_sealed_pack(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise RotowireLineupsDbError("pack must be a JSON object")
    return _require_pack(payload)


def flatten_rotowire_predicted_lineup_pack(
    pack: Mapping[str, Any],
) -> dict[str, pd.DataFrame]:
    """Expand one sealed pack into analytical frames."""

    sealed = _require_pack(pack)
    pack_hash = sealed["content_sha256"]
    citation = sealed.get("citation") or {}
    packs_rows = [
        {
            "pack_content_sha256": pack_hash,
            "source_id": sealed["source_id"],
            "provider_id": sealed.get("provider_id"),
            "schema_version": sealed["schema_version"],
            "season": sealed.get("season"),
            "gameweek": sealed.get("gameweek"),
            "window_label": sealed.get("window_label"),
            "observed_at": sealed.get("observed_at"),
            "available_at": sealed.get("available_at"),
            "citation_url": citation.get("url"),
            "publisher": citation.get("publisher"),
            "published_at": citation.get("published_at"),
            "capture_method": citation.get("capture_method"),
            "fixture_count": sealed.get("fixture_count"),
            "identity_mapping_status": sealed.get("identity_mapping_status"),
            "notes": sealed.get("notes"),
        }
    ]

    fixture_rows: list[dict[str, Any]] = []
    player_rows: list[dict[str, Any]] = []
    injury_rows: list[dict[str, Any]] = []

    for fixture in sealed["fixtures"]:
        fixture_id = str(fixture["provider_fixture_id"])
        fixture_rows.append(
            {
                "pack_content_sha256": pack_hash,
                "provider_fixture_id": fixture_id,
                "kickoff_at": fixture.get("kickoff_at"),
                "home_code": fixture.get("home_code"),
                "away_code": fixture.get("away_code"),
                "home_club": fixture.get("home_club"),
                "away_club": fixture.get("away_club"),
                "prediction_kind": fixture.get("prediction_kind"),
            }
        )
        for side, club_code in (
            ("home", fixture.get("home_code")),
            ("away", fixture.get("away_code")),
        ):
            xi_key = f"{side}_xi"
            for index, player in enumerate(fixture.get(xi_key) or [], start=1):
                player_rows.append(
                    {
                        "pack_content_sha256": pack_hash,
                        "provider_fixture_id": fixture_id,
                        "side": side,
                        "club_code": club_code,
                        "xi_slot_order": index,
                        "provider_player_id": player.get("provider_player_id"),
                        "name": player.get("name"),
                        "slot": player.get("slot"),
                        "status": player.get("status"),
                        "role": player.get("role"),
                        "started": bool(player.get("started")),
                    }
                )
            notes_key = f"{side}_injury_notes"
            for note in fixture.get(notes_key) or []:
                injury_rows.append(
                    {
                        "pack_content_sha256": pack_hash,
                        "provider_fixture_id": fixture_id,
                        "side": side,
                        "club_code": club_code,
                        "provider_player_id": note.get("provider_player_id"),
                        "name": note.get("name"),
                        "slot": note.get("slot"),
                        "status": note.get("status"),
                        "role": note.get("role"),
                    }
                )

    return {
        "packs": pd.DataFrame(packs_rows),
        "fixtures": pd.DataFrame(fixture_rows),
        "xi_players": pd.DataFrame(player_rows),
        "injury_notes": pd.DataFrame(injury_rows),
    }


def write_rotowire_lineups_parquet(
    frames: Mapping[str, pd.DataFrame],
    out_dir: Path,
) -> dict[str, str]:
    """Write analytical parquet snapshots via DuckDB (no pyarrow required)."""

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}
    con = duckdb.connect()
    try:
        for name, frame in frames.items():
            path = out_dir / f"rotowire_predicted_{name}.parquet"
            view = f"rw_{name}_export"
            con.register(view, frame)
            # DuckDB needs forward slashes on Windows paths in COPY.
            target = path.resolve().as_posix()
            con.execute(f"COPY {view} TO '{target}' (FORMAT PARQUET)")
            written[name] = str(path)
    finally:
        con.close()
    return written


def upsert_rotowire_lineups_duckdb(
    frames: Mapping[str, pd.DataFrame],
    *,
    db_path: Path,
    pack_content_sha256: str,
) -> dict[str, Any]:
    """Idempotently replace one pack's rows in the analytical DuckDB."""

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS rotowire_predicted_packs (
                pack_content_sha256 VARCHAR PRIMARY KEY,
                source_id VARCHAR,
                provider_id VARCHAR,
                schema_version VARCHAR,
                season VARCHAR,
                gameweek INTEGER,
                window_label VARCHAR,
                observed_at VARCHAR,
                available_at VARCHAR,
                citation_url VARCHAR,
                publisher VARCHAR,
                published_at VARCHAR,
                capture_method VARCHAR,
                fixture_count INTEGER,
                identity_mapping_status VARCHAR,
                notes VARCHAR
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS rotowire_predicted_fixtures (
                pack_content_sha256 VARCHAR,
                provider_fixture_id VARCHAR,
                kickoff_at VARCHAR,
                home_code VARCHAR,
                away_code VARCHAR,
                home_club VARCHAR,
                away_club VARCHAR,
                prediction_kind VARCHAR
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS rotowire_predicted_xi_players (
                pack_content_sha256 VARCHAR,
                provider_fixture_id VARCHAR,
                side VARCHAR,
                club_code VARCHAR,
                xi_slot_order INTEGER,
                provider_player_id VARCHAR,
                name VARCHAR,
                slot VARCHAR,
                status VARCHAR,
                role VARCHAR,
                started BOOLEAN
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS rotowire_predicted_injury_notes (
                pack_content_sha256 VARCHAR,
                provider_fixture_id VARCHAR,
                side VARCHAR,
                club_code VARCHAR,
                provider_player_id VARCHAR,
                name VARCHAR,
                slot VARCHAR,
                status VARCHAR,
                role VARCHAR
            )
            """
        )

        for table in (
            "rotowire_predicted_packs",
            "rotowire_predicted_fixtures",
            "rotowire_predicted_xi_players",
            "rotowire_predicted_injury_notes",
        ):
            con.execute(
                f"DELETE FROM {table} WHERE pack_content_sha256 = ?",
                [pack_content_sha256],
            )

        con.register("packs_df", frames["packs"])
        con.register("fixtures_df", frames["fixtures"])
        con.register("xi_df", frames["xi_players"])
        con.register("inj_df", frames["injury_notes"])
        con.execute("INSERT INTO rotowire_predicted_packs SELECT * FROM packs_df")
        con.execute(
            "INSERT INTO rotowire_predicted_fixtures SELECT * FROM fixtures_df"
        )
        con.execute(
            "INSERT INTO rotowire_predicted_xi_players SELECT * FROM xi_df"
        )
        con.execute(
            "INSERT INTO rotowire_predicted_injury_notes SELECT * FROM inj_df"
        )

        counts = {
            "packs": int(
                con.execute(
                    "SELECT COUNT(*) FROM rotowire_predicted_packs "
                    "WHERE pack_content_sha256 = ?",
                    [pack_content_sha256],
                ).fetchone()[0]
            ),
            "fixtures": int(
                con.execute(
                    "SELECT COUNT(*) FROM rotowire_predicted_fixtures "
                    "WHERE pack_content_sha256 = ?",
                    [pack_content_sha256],
                ).fetchone()[0]
            ),
            "xi_players": int(
                con.execute(
                    "SELECT COUNT(*) FROM rotowire_predicted_xi_players "
                    "WHERE pack_content_sha256 = ?",
                    [pack_content_sha256],
                ).fetchone()[0]
            ),
            "injury_notes": int(
                con.execute(
                    "SELECT COUNT(*) FROM rotowire_predicted_injury_notes "
                    "WHERE pack_content_sha256 = ?",
                    [pack_content_sha256],
                ).fetchone()[0]
            ),
        }
    finally:
        con.close()

    return {
        "db_path": str(db_path),
        "pack_content_sha256": pack_content_sha256,
        "counts": counts,
    }


def load_rotowire_predicted_lineup_pack_to_warehouse(
    pack_path: Path,
    *,
    warehouse_dir: Path = DEFAULT_WAREHOUSE_DIR,
    db_name: str = DEFAULT_DB_NAME,
    require_registry: bool = True,
) -> dict[str, Any]:
    """Seal-aware analytical load: Parquet snapshots + DuckDB upsert."""

    if require_registry:
        assert_collectable(ROTOWIRE_SOURCE_ID)

    pack = load_sealed_pack(pack_path)
    frames = flatten_rotowire_predicted_lineup_pack(pack)
    warehouse_dir = Path(warehouse_dir)
    parquet_dir = warehouse_dir / "rotowire_predicted_lineups"
    parquet_paths = write_rotowire_lineups_parquet(frames, parquet_dir)
    db_result = upsert_rotowire_lineups_duckdb(
        frames,
        db_path=warehouse_dir / db_name,
        pack_content_sha256=str(pack["content_sha256"]),
    )
    return {
        "status": "loaded",
        "source_id": ROTOWIRE_SOURCE_ID,
        "pack_path": str(pack_path),
        "pack_content_sha256": pack["content_sha256"],
        "fixture_count": pack.get("fixture_count"),
        "citation_url": (pack.get("citation") or {}).get("url"),
        "parquet": parquet_paths,
        "duckdb": db_result,
        "influence_policy": "analytical_store_only_no_live_forecast_admission",
    }
