#!/usr/bin/env python3
"""Build a cutoff-safe live player-prior envelope from registered local history."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.forecasting.live_faithful import artifact_hash
from src.forecasting.player_priors import build_player_prior
from src.ingestion.registry import assert_collectable


DEFAULT_VAASTAV_ROOT = (
    REPO / "data" / "raw" / "vaastav" / "Fantasy-Premier-League"
)
DEFAULT_MODEL = REPO / "control" / "models" / "live-faithful-v1.feature-complete.json"


class LivePlayerPriorBuildError(ValueError):
    """Raised when local prior inputs cannot be admitted without guessing."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _deduplicate_exact_rows(
    rows: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    required = {"element", "fixture", "position"}
    missing = sorted(required - set(rows.columns))
    if missing:
        raise LivePlayerPriorBuildError(
            "Historical player rows are missing: " + ", ".join(missing)
        )

    duplicate_keys = 0
    duplicate_rows = 0
    for key, group in rows.groupby(
        ["element", "fixture"], sort=False, dropna=False
    ):
        if len(group) < 2:
            continue
        duplicate_keys += 1
        if len(group.drop_duplicates()) != 1:
            raise LivePlayerPriorBuildError(
                "Conflicting duplicate player-fixture rows: "
                f"element={key[0]}, fixture={key[1]}"
            )
        duplicate_rows += len(group) - 1

    return (
        rows.drop_duplicates(["element", "fixture"], keep="first").copy(),
        {
            "duplicate_player_fixture_keys": duplicate_keys,
            "exact_duplicate_rows_removed": duplicate_rows,
        },
    )


def build_prior_from_local_source(
    *,
    season: str,
    as_of: str,
    vaastav_root: Path = DEFAULT_VAASTAV_ROOT,
    model_config_path: Path = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Build a prior from local Vaastav bytes after the registry gate."""

    source = assert_collectable("vaastav-fpl")
    season_root = vaastav_root / "data" / season
    rows_path = season_root / "gws" / "merged_gw.csv"
    players_path = season_root / "players_raw.csv"
    if not rows_path.is_file() or not players_path.is_file():
        raise LivePlayerPriorBuildError(
            f"Missing registered {season} Vaastav inputs under {season_root}"
        )

    try:
        rows = pd.read_csv(rows_path, low_memory=False)
        players = pd.read_csv(players_path, low_memory=False)
        model = json.loads(model_config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise LivePlayerPriorBuildError(
            f"Unable to read local prior inputs: {exc}"
        ) from exc

    identity_columns = {"id", "code"}
    if not identity_columns <= set(players.columns):
        raise LivePlayerPriorBuildError(
            "Prior player catalogue must contain id and code columns"
        )
    if "price_bands" not in model:
        raise LivePlayerPriorBuildError("Live model config has no price_bands")

    input_row_count = len(rows)
    position_filtered = rows[
        rows["position"].astype(str).str.upper() != "AM"
    ].copy()
    excluded_position_rows = input_row_count - len(position_filtered)
    prepared, duplicate_stats = _deduplicate_exact_rows(position_filtered)
    identity_map = {
        "season": season,
        "players": [
            {"fpl_player_id": int(row.id), "fpl_code": int(row.code)}
            for row in players[["id", "code"]].itertuples(index=False)
        ],
    }

    prior = build_player_prior(
        season=season,
        as_of=as_of,
        rows=prepared.to_dict("records"),
        identity_map=identity_map,
        price_bands=model["price_bands"],
    )
    prior["source"].update(
        {
            "source_registry_id": str(source["source_id"]),
            "source_dataset": f"vaastav-fpl:data/{season}/gws/merged_gw.csv",
            "source_dataset_sha256": _sha256(rows_path),
            "identity_dataset": f"vaastav-fpl:data/{season}/players_raw.csv",
            "identity_dataset_sha256": _sha256(players_path),
            "input_row_count": input_row_count,
            "excluded_position_rows": excluded_position_rows,
            "duplicate_policy": (
                "deduplicate_exact_identical_player_fixture_rows_only"
            ),
            **duplicate_stats,
        }
    )
    prior["content_sha256"] = artifact_hash(prior)
    return prior


def _write_immutable(path: Path, value: dict[str, Any]) -> str:
    encoded = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise FileExistsError(
                f"Refusing to replace immutable player prior: {path}"
            )
        return "unchanged"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
    return "written"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build an immutable player prior from registered local history"
    )
    parser.add_argument("--season", default="2025-26")
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--vaastav-root", type=Path, default=DEFAULT_VAASTAV_ROOT)
    parser.add_argument("--model-config", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        prior = build_prior_from_local_source(
            season=args.season,
            as_of=args.as_of,
            vaastav_root=args.vaastav_root,
            model_config_path=args.model_config,
        )
        write_status = _write_immutable(args.output, prior)
    except (FileExistsError, LivePlayerPriorBuildError, OSError, PermissionError) as exc:
        parser.error(str(exc))

    print(
        json.dumps(
            {
                "output": str(args.output),
                "write": write_status,
                "season": prior["season"],
                "players": len(prior["players"]),
                "source": prior["source"],
                "content_sha256": prior["content_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
