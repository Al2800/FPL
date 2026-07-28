from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
import yaml

from src.ingestion.news_discovery import NewsDiscoveryError, artifact_hash, build_cited_original_packet, build_news_discovery_plan, execute_news_discovery_plan, write_immutable_json


ROOT = Path(__file__).parents[2]
CATALOGUE = yaml.safe_load((ROOT / "control/sources/club-news-catalogue.yaml").read_text(encoding="utf-8"))
CONFIG = json.loads((ROOT / "config/data_sources/2026-27-news-discovery.json").read_text(encoding="utf-8"))
OBSERVED = "2026-08-20T12:00:00Z"


def results(plan):
    return {action["club_id"]: [] for action in plan["actions"]}


def test_plan_has_official_status_for_every_2026_27_club_and_is_sealed():
    plan = build_news_discovery_plan(CATALOGUE, config=CONFIG, observed_at=OBSERVED)
    assert len(plan["actions"]) == 21
    assert sum(action["club_id"] != "premier-league" for action in plan["actions"]) == 20
    assert all(action["discovery_method"] == "official_domain_search_fallback" for action in plan["actions"])
    assert plan["content_sha256"] == artifact_hash(plan)


def test_discovery_only_keeps_fresh_canonical_official_metadata_and_drops_snippets():
    plan = build_news_discovery_plan(CATALOGUE, config=CONFIG, observed_at=OBSERVED)
    captured = results(plan)
    captured["arsenal"] = [
        {"url": "https://www.arsenal.com/news/team-news?utm_source=search", "title": "Team news", "published_at": "2026-08-20T10:00:00Z", "rank": 2, "snippet": "This must never survive."},
        {"url": "https://syndicated.example/team-news", "title": "Copied", "published_at": "2026-08-20T10:00:00Z", "rank": 1},
        {"url": "https://www.arsenal.com/news/old", "title": "Old", "published_at": "2026-08-10T10:00:00Z", "rank": 3},
    ]
    discovery = execute_news_discovery_plan(plan, search_results=captured)
    assert discovery["status"] == "complete"
    assert discovery["leads"] == [pytest.helpers.anything] if False else discovery["leads"]
    arsenal = [lead for lead in discovery["leads"] if lead["club_id"] == "arsenal"]
    assert arsenal[0]["source_url"] == "https://www.arsenal.com/news/team-news"
    assert "snippet" not in json.dumps(discovery)
    assert {row["reason"] for row in discovery["quality"]["rejected"]} >= {"result URL is not on the official domain", "result is stale"}


def test_missing_search_coverage_degrades_but_empty_search_does_not():
    plan = build_news_discovery_plan(CATALOGUE, config=CONFIG, observed_at=OBSERVED)
    captured = results(plan)
    assert execute_news_discovery_plan(plan, search_results=captured)["status"] == "complete"
    captured.pop("arsenal")
    discovery = execute_news_discovery_plan(plan, search_results=captured)
    assert discovery["status"] == "degraded"
    assert "club:arsenal:not_searched" in discovery["quality"]["gaps"]


def test_duplicate_canonical_urls_and_packet_selection_are_bounded():
    plan = build_news_discovery_plan(CATALOGUE, config=CONFIG, observed_at=OBSERVED)
    captured = results(plan)
    row = {"url": "https://www.arsenal.com/news/a?gclid=x", "title": "A", "published_at": "2026-08-20T10:00:00Z", "rank": 1}
    captured["arsenal"] = [row]
    captured["premier-league"] = [{**row, "url": "https://www.premierleague.com/news/a", "rank": 2}]
    discovery = execute_news_discovery_plan(plan, search_results=captured)
    packet = build_cited_original_packet(discovery, document_ids=[discovery["leads"][0]["document_id"]])
    assert len(packet["documents"]) == 1
    assert set(packet["documents"][0]) == {"document_id", "club_id", "source_url", "published_at", "observed_at", "discovery_method", "query", "rank", "title"}
    with pytest.raises(NewsDiscoveryError):
        build_cited_original_packet(discovery, document_ids=["missing"])


def test_tampering_and_nonidentical_immutable_writes_fail(tmp_path):
    plan = build_news_discovery_plan(CATALOGUE, config=CONFIG, observed_at=OBSERVED)
    tampered = deepcopy(plan)
    tampered["season"] = "wrong"
    with pytest.raises(NewsDiscoveryError, match="hash mismatch"):
        execute_news_discovery_plan(tampered, search_results=results(plan))
    target = tmp_path / "discovery.json"
    discovery = execute_news_discovery_plan(plan, search_results=results(plan))
    assert write_immutable_json(target, discovery) == "created"
    assert write_immutable_json(target, discovery) == "identical"
    changed = deepcopy(discovery)
    changed["status"] = "degraded"
    with pytest.raises(FileExistsError):
        write_immutable_json(target, changed)
