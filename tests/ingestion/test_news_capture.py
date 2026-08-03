from __future__ import annotations

import json
from pathlib import Path

import yaml

from src.ingestion.news_capture import capture_search_candidates, validate_capture
from src.ingestion.news_discovery import build_news_discovery_plan


ROOT = Path(__file__).parents[2]
CATALOGUE = yaml.safe_load((ROOT / "control/sources/club-news-catalogue.yaml").read_text(encoding="utf-8"))
CONFIG = json.loads((ROOT / "config/data_sources/2026-27-news-discovery.json").read_text(encoding="utf-8"))
OBSERVED = "2026-08-20T12:00:00Z"


def _plan():
    return build_news_discovery_plan(CATALOGUE, config=CONFIG, observed_at=OBSERVED)


def test_broad_capture_retains_external_unknown_and_snippet_without_claim_admission():
    plan = _plan()
    results = {action["club_id"]: [] for action in plan["actions"]}
    results["arsenal"] = [
        {
            "url": "https://www.arsenal.com/news/team-news",
            "title": "Team news",
            "published_at": None,
            "publication_time_status": "unknown",
            "rank": 1,
            "snippet": "  Untrusted search text.  " * 100,
            "source_class": "official_candidate",
        },
        {
            "url": "https://example.com/arsenal-injury",
            "title": "External report",
            "published_at": "2026-08-20T10:00:00Z",
            "rank": 2,
            "snippet": "External candidate",
            "source_class": "external_candidate",
        },
    ]

    capture = capture_search_candidates(plan, search_results=results)
    assert capture["quality"]["candidate_count"] == 2
    assert capture["quality"]["source_class_counts"] == {"external_candidate": 1, "official_candidate": 1}
    assert capture["quality"]["publication_time_counts"] == {"known": 1, "unknown": 1}
    assert len(capture["candidates"][0]["snippet"]) <= 1000
    assert capture["candidates"][0]["quality_flags"]
    assert capture["candidates"][1]["quality_flags"]
    assert capture["raw_search_context_retained"] is True
    assert validate_capture(capture)


def test_broad_capture_marks_missing_search_without_discarding_other_rows():
    plan = _plan()
    results = {action["club_id"]: [] for action in plan["actions"]}
    results.pop("arsenal")
    capture = capture_search_candidates(plan, search_results=results)
    assert capture["status"] == "degraded"
    assert "club:arsenal:not_searched" in capture["quality"]["gaps"]
    assert capture["quality"]["candidate_count"] == 0
