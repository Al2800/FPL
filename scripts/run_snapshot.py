#!/usr/bin/env python3
"""CLI entry: python -m scripts.run_snapshot"""

from src.ingestion.snapshot_fpl import main

if __name__ == "__main__":
    raise SystemExit(main())
