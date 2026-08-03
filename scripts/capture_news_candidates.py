"""Capture broad unstructured news candidates without dropping uncertain rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from src.ingestion.news_capture import capture_search_candidates, validate_capture
from src.ingestion.news_discovery import build_news_discovery_plan, write_immutable_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--search-results", type=Path, required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    catalogue = yaml.safe_load(args.catalogue.read_text(encoding="utf-8"))
    config = json.loads(args.config.read_text(encoding="utf-8"))
    results = json.loads(args.search_results.read_text(encoding="utf-8"))
    plan = build_news_discovery_plan(catalogue, config=config, observed_at=args.observed_at)
    capture = capture_search_candidates(plan, search_results=results)
    capture["content_sha256"] = validate_capture(capture)
    write_immutable_json(args.output, capture)
    print(json.dumps({
        "status": capture["status"],
        "candidate_count": capture["quality"]["candidate_count"],
        "source_class_counts": capture["quality"]["source_class_counts"],
        "publication_time_counts": capture["quality"]["publication_time_counts"],
        "flag_counts": capture["quality"]["flag_counts"],
        "content_sha256": capture["content_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
