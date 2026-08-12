from __future__ import annotations

import json
from pathlib import Path

import yaml

from src.ingestion.news_triage import (
    load_triage_policy,
    triage_impact_summary,
    triage_news_capture,
)
from src.ingestion.news_verify import (
    admit_verified_into_discovery,
    apply_news_verifications,
    verified_rows_to_search_results,
)


ROOT = Path(__file__).parents[2]
CATALOGUE = yaml.safe_load(
    (ROOT / "control/sources/club-news-catalogue.yaml").read_text(encoding="utf-8")
)
CONFIG = json.loads(
    (ROOT / "config/data_sources/2026-27-news-discovery.json").read_text(encoding="utf-8")
)


def _capture() -> dict:
    return {
        "schema_version": "1.0",
        "capture_id": "news-capture:2026-27:2026-08-08T05:00:02Z",
        "season": "2026-27",
        "observed_at": "2026-08-08T05:00:02Z",
        "content_sha256": "capture-sha-test",
        "candidates": [
            {
                "candidate_id": "cand-ars",
                "club_id": "arsenal",
                "url": "https://www.arsenal.com/news/injury",
                "canonical_url": "https://www.arsenal.com/news/injury",
                "title": "Team news: midfielder ruled out",
                "snippet": "SECRET BODY MUST NOT LEAK",
                "published_at": None,
                "publication_time_status": "unknown",
                "rank": 1,
                "source_class": "official_candidate",
            },
            {
                "candidate_id": "cand-liv",
                "club_id": "liverpool",
                "url": "https://www.liverpoolfc.com/news/update",
                "canonical_url": "https://www.liverpoolfc.com/news/update",
                "title": "Squad update ahead of matchweek",
                "snippet": "more secret",
                "published_at": None,
                "publication_time_status": "unknown",
                "rank": 1,
                "source_class": "official_candidate",
            },
            {
                "candidate_id": "cand-ext",
                "club_id": "arsenal",
                "url": "https://www.bbc.co.uk/sport/football/articles/xyz",
                "canonical_url": None,
                "title": "Premier League injury round-up including Haaland",
                "snippet": "external body",
                "published_at": None,
                "publication_time_status": "unknown",
                "rank": 2,
                "source_class": "external_candidate",
            },
            {
                "candidate_id": "cand-noise",
                "club_id": "chelsea",
                "url": "https://www.chelseafc.com/en/news/shop",
                "canonical_url": "https://www.chelseafc.com/en/news/shop",
                "title": "New shirt available in store",
                "snippet": "shop",
                "published_at": None,
                "publication_time_status": "unknown",
                "rank": 5,
                "source_class": "official_candidate",
            },
        ],
    }


def test_triage_shortlist_excludes_snippets_and_prefers_official() -> None:
    policy = load_triage_policy()
    triage = triage_news_capture(_capture(), policy=policy)
    assert triage["shortlist_count"] >= 2
    assert all("snippet" not in item for item in triage["shortlist"])
    sealed = json.dumps(triage)
    assert "SECRET" not in sealed
    assert triage["shortlist"][0]["source_class"] == "official_candidate"
    assert triage["shortlist"][0]["club_id"] == "arsenal"
    assert any(item["source_class"] == "external_candidate" for item in triage["shortlist"])
    impact = triage_impact_summary(triage)
    assert impact["ledger_effect_without_verification"] == "none_zero_admitted_leads"
    assert impact["strategy_relevance"]["availability_general"] is True


def test_verification_admits_only_when_published_at_present() -> None:
    triage = triage_news_capture(_capture())
    result = apply_news_verifications(
        triage,
        [
            {
                "candidate_id": "cand-ars",
                "status": "verified",
                "page_identity_ok": True,
                "published_at": "2026-08-07T12:00:00Z",
                "verified_by": "test",
                "verified_at": "2026-08-08T12:00:00Z",
                "notes": "ok",
            },
            {
                "candidate_id": "cand-liv",
                "status": "verified",
                "page_identity_ok": True,
                "published_at": None,
                "verified_by": "test",
                "verified_at": "2026-08-08T12:00:00Z",
                "notes": "missing published_at",
            },
            {
                "candidate_id": "cand-ext",
                "status": "verified",
                "page_identity_ok": True,
                "published_at": "2026-08-07T09:00:00Z",
                "snippet": "FORBIDDEN",
                "verified_by": "test",
                "verified_at": "2026-08-08T12:00:00Z",
                "notes": "should strip snippet",
            },
        ],
    )
    assert len(result["verified_ready_for_discovery"]) == 2
    assert result["verified_ready_for_discovery"][0]["candidate_id"] == "cand-ars"
    assert "SECRET" not in json.dumps(result)
    assert "FORBIDDEN" not in json.dumps(result)
    search = verified_rows_to_search_results(result)
    assert "arsenal" in search
    assert search["arsenal"][0]["published_at"] == "2026-08-07T12:00:00Z"


def test_stale_year_and_manager_markers_demote_rank() -> None:
    capture = _capture()
    capture["candidates"].append(
        {
            "candidate_id": "cand-stale",
            "club_id": "manchester-united",
            "url": "https://www.manutd.com/en/news/detail/team-news-for-man-utd-v-fulham-on-24-february-2024",
            "canonical_url": "https://www.manutd.com/en/news/detail/team-news-for-man-utd-v-fulham-on-24-february-2024",
            "title": "Team news: United v Fulham | Erik ten Hag update",
            "snippet": "SECRET",
            "published_at": None,
            "publication_time_status": "unknown",
            "rank": 1,
            "source_class": "official_candidate",
        }
    )
    triage = triage_news_capture(capture)
    by_id = {row["candidate_id"]: row for row in triage["shortlist"]}
    from src.ingestion.news_triage import score_candidate

    stale = score_candidate(
        capture["candidates"][-1],
        load_triage_policy(),
        observed_at=capture["observed_at"],
    )
    fresh = score_candidate(
        capture["candidates"][0],
        load_triage_policy(),
        observed_at=capture["observed_at"],
    )
    assert "stale_year_stamp" in stale["reasons"]
    assert "historical_manager_marker" in stale["reasons"]
    assert 2024 in stale["stale_year_hits"]
    assert stale["triage_score"] < fresh["triage_score"]
    assert "cand-stale" not in by_id or by_id["cand-stale"]["triage_score"] < fresh["triage_score"]
    assert triage["demoted_candidate_count"] >= 1


def test_freshness_filter_excludes_dated_stale_and_sections() -> None:
    capture = _capture()
    capture["candidates"].extend(
        [
            {
                "candidate_id": "cand-old-url-date",
                "club_id": "fulham",
                "url": "https://www.fulhamfc.com/news/2026/july/15/first-day-back/",
                "canonical_url": "https://www.fulhamfc.com/news/2026/july/15/first-day-back/",
                "title": "First day back",
                "snippet": "SECRET",
                "published_at": None,
                "publication_time_status": "unknown",
                "rank": 1,
                "source_class": "official_candidate",
            },
            {
                "candidate_id": "cand-old-known",
                "club_id": "liverpool",
                "url": "https://www.liverpoolfc.com/news/old-injury-news",
                "canonical_url": "https://www.liverpoolfc.com/news/old-injury-news",
                "title": "Injury update",
                "snippet": "SECRET",
                "published_at": "2026-06-01T09:00:00Z",
                "publication_time_status": "known",
                "rank": 1,
                "source_class": "official_candidate",
            },
            {
                "candidate_id": "cand-women",
                "club_id": "arsenal",
                "url": "https://www.arsenal.com/women/news/team-news-cup-final",
                "canonical_url": "https://www.arsenal.com/women/news/team-news-cup-final",
                "title": "Team news: cup final",
                "snippet": "SECRET",
                "published_at": None,
                "publication_time_status": "unknown",
                "rank": 1,
                "source_class": "official_candidate",
            },
            {
                "candidate_id": "cand-prior-year",
                "club_id": "manchester-united",
                "url": "https://www.manutd.com/en/news/detail/team-news-v-fulham-24-february-2024",
                "canonical_url": "https://www.manutd.com/en/news/detail/team-news-v-fulham-24-february-2024",
                "title": "Team news: United v Fulham 2024",
                "snippet": "SECRET",
                "published_at": None,
                "publication_time_status": "unknown",
                "rank": 1,
                "source_class": "official_candidate",
            },
            {
                "candidate_id": "cand-fresh-known",
                "club_id": "chelsea",
                "url": "https://www.chelseafc.com/en/news/fitness-update",
                "canonical_url": "https://www.chelseafc.com/en/news/fitness-update",
                "title": "Fitness update ahead of the opener",
                "snippet": "SECRET",
                "published_at": "2026-08-06T10:00:00Z",
                "publication_time_status": "known",
                "rank": 1,
                "source_class": "official_candidate",
            },
        ]
    )
    triage = triage_news_capture(capture, policy=load_triage_policy())
    shortlist_ids = {row["candidate_id"] for row in triage["shortlist"]}
    excluded = {row["candidate_id"]: row["reason"] for row in triage["excluded_candidates"]}

    # Hard-excluded: URL-dated July page (>14 days), known old date,
    # women's section, prior-year stamp.
    assert excluded["cand-old-url-date"].startswith("stale_beyond_")
    assert excluded["cand-old-known"].startswith("stale_beyond_")
    assert excluded["cand-women"].startswith("excluded_section:")
    assert excluded["cand-prior-year"] == "stale_year_stamp"
    assert not shortlist_ids & set(excluded)

    # Kept: fresh known date and undatable candidates.
    assert "cand-fresh-known" in shortlist_ids
    assert "cand-ars" in shortlist_ids
    fresh_row = next(
        row for row in triage["shortlist"] if row["candidate_id"] == "cand-fresh-known"
    )
    assert fresh_row["freshness_status"] == "fresh"
    assert fresh_row["derived_published_on"] == "2026-08-06"

    assert triage["excluded_candidate_count"] == 4
    assert triage["freshness_excluded_count"] == 3
    assert triage["section_excluded_count"] == 1
    assert triage["shortlist_freshness"]["fresh_known"] >= 1
    assert "SECRET" not in json.dumps(triage)


def test_freshness_filter_absent_policy_block_keeps_all_candidates() -> None:
    policy = load_triage_policy()
    policy.pop("freshness", None)
    capture = _capture()
    capture["candidates"][0]["published_at"] = "2026-06-01T09:00:00Z"
    capture["candidates"][0]["publication_time_status"] = "known"
    triage = triage_news_capture(capture, policy=policy)
    assert triage["excluded_candidate_count"] == 0
    assert {row["candidate_id"] for row in triage["shortlist"]} >= {"cand-ars"}


def test_admit_verified_into_discovery_produces_leads() -> None:
    triage = triage_news_capture(_capture())
    verification = apply_news_verifications(
        triage,
        [
            {
                "candidate_id": "cand-ars",
                "status": "verified",
                "page_identity_ok": True,
                "published_at": "2026-08-07T12:00:00Z",
                "verified_by": "test",
                "verified_at": "2026-08-08T12:00:00Z",
                "notes": "ok",
            }
        ],
    )
    bridge = admit_verified_into_discovery(
        catalogue=CATALOGUE,
        config=CONFIG,
        verification=verification,
        observed_at="2026-08-08T05:00:02Z",
    )
    assert bridge["admitted_lead_count"] >= 1
    assert bridge["discovery"]["leads"]
