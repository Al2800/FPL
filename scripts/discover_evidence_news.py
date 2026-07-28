"""Run deterministic club-news discovery from an externally captured result file."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from src.ingestion.news_discovery import build_cited_original_packet, build_news_discovery_plan, execute_news_discovery_plan, write_immutable_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--search-results", type=Path, required=True, help="Externally captured search metadata; snippets are discarded.")
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--packet-output", type=Path)
    args = parser.parse_args()
    catalogue = yaml.safe_load(args.catalogue.read_text(encoding="utf-8"))
    config = json.loads(args.config.read_text(encoding="utf-8"))
    results = json.loads(args.search_results.read_text(encoding="utf-8"))
    plan = build_news_discovery_plan(catalogue, config=config, observed_at=args.observed_at)
    discovery = execute_news_discovery_plan(plan, search_results=results)
    write_immutable_json(args.output, discovery)
    if args.packet_output:
        write_immutable_json(args.packet_output, build_cited_original_packet(discovery))
    print(json.dumps({"status": discovery["status"], "lead_count": len(discovery["leads"]), "gaps": discovery["quality"]["gaps"], "content_sha256": discovery["content_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
