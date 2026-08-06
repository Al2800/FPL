#!/usr/bin/env python3
"""Load a sealed Rotowire predicted-lineups citation pack into DuckDB + Parquet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from src.ingestion.rotowire_lineups_db import (
    DEFAULT_DB_NAME,
    DEFAULT_WAREHOUSE_DIR,
    load_rotowire_predicted_lineup_pack_to_warehouse,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--warehouse", type=Path, default=DEFAULT_WAREHOUSE_DIR)
    parser.add_argument("--db-name", default=DEFAULT_DB_NAME)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = load_rotowire_predicted_lineup_pack_to_warehouse(
        args.pack,
        warehouse_dir=args.warehouse,
        db_name=args.db_name,
    )
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
