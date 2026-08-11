"""Apply verification records and optionally admit through discovery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.ingestion.news_verify import (  # noqa: E402
    admit_verified_into_discovery,
    apply_news_verifications,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--triage", type=Path, required=True)
    parser.add_argument("--verifications", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--admit-discovery", action="store_true")
    parser.add_argument(
        "--catalogue",
        type=Path,
        default=REPO / "control" / "sources" / "club-news-catalogue.yaml",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO / "config" / "data_sources" / "2026-27-news-discovery.json",
    )
    parser.add_argument("--discovery-out", type=Path, default=None)
    args = parser.parse_args(argv)

    triage = json.loads(args.triage.read_text(encoding="utf-8"))
    payload = json.loads(args.verifications.read_text(encoding="utf-8"))
    rows = payload.get("verifications") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise SystemExit("verifications must be a list or {verifications: [...]}")

    result = apply_news_verifications(triage, rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(args.out)
    print(f"verified_ready={len(result['verified_ready_for_discovery'])}")

    if args.admit_discovery:
        catalogue = yaml.safe_load(args.catalogue.read_text(encoding="utf-8"))
        config = json.loads(args.config.read_text(encoding="utf-8"))
        bridge = admit_verified_into_discovery(
            catalogue=catalogue,
            config=config,
            verification=result,
        )
        discovery_out = args.discovery_out or args.out.with_name(
            args.out.stem + "-discovery.json"
        )
        discovery_out.write_text(
            json.dumps(bridge, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(discovery_out)
        print(f"admitted_leads={bridge['admitted_lead_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
