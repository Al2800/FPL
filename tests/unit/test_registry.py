"""WP-02 registry completeness and collectability gate."""

from src.ingestion.registry import REQUIRED_FIELDS, assert_collectable, get_source, load_registry


TIER1_SOURCE_IDS = [
    "fpl-official-endpoints",
    "fpl-official-rules-news",
    "fpl-authenticated-manager-state",
    "official-club-communications",
    "official-competition-schedules",
]

BENCHMARK_CANDIDATE_IDS = [
    "betfair-historical",
    "clubelo",
    "commercial-epl-event-data",
    "football-data-org",
    "sportradar-soccer",
]


def test_tier1_sources_registered_with_all_fields():
    registry = load_registry()
    by_id = {s["source_id"]: s for s in registry["sources"]}
    for source_id in TIER1_SOURCE_IDS:
        assert source_id in by_id
        for field in REQUIRED_FIELDS:
            assert field in by_id[source_id], f"{source_id} missing {field}"


def test_only_assessment_sources_enabled():
    registry = load_registry()
    enabled = sorted(s["source_id"] for s in registry["sources"] if s["enabled"])
    assert enabled == sorted(
        [
            "fpl-official-endpoints",
            "football-data-co-uk",
            "official-club-communications",
            "official-lineups-minutes",
            "rotowire-lineups",
            "statsbomb-open",
            "the-odds-api",
            "vaastav-fpl",
        ]
    )


def test_official_lineups_enabled_for_manual_citation_only():
    source = get_source("official-lineups-minutes")
    assert source["enabled"] is True
    assert source["collection_method"] == "manual_citation"
    assert source["licence_status"] == "restricted"
    assert "citation" in source["allowed_use"]
    assert assert_collectable("official-lineups-minutes")["source_id"] == (
        "official-lineups-minutes"
    )


def test_rotowire_lineups_enabled_for_manual_citation_only():
    source = get_source("rotowire-lineups")
    assert source["enabled"] is True
    assert source["collection_method"] == "manual_citation"
    assert source["licence_status"] == "restricted"
    assert "citation" in source["allowed_use"]
    assert "crawl" in source["activation_approval"]["terms"]
    assert assert_collectable("rotowire-lineups")["source_id"] == "rotowire-lineups"


def test_official_club_communications_enabled_for_manual_citation_only():
    source = get_source("official-club-communications")
    assert source["enabled"] is True
    assert source["collection_method"] == "manual_citation"
    assert source["licence_status"] == "restricted"
    assert "citation" in source["allowed_use"]
    assert source["activation_approval"]["scope"] == (
        "manual_citation_capture_no_paid_provider_no_redistribution_no_html_scrape"
    )
    assert assert_collectable("official-club-communications")["source_id"] == (
        "official-club-communications"
    )


def test_benchmark_candidates_are_complete_and_disabled():
    registry = load_registry()
    by_id = {s["source_id"]: s for s in registry["sources"]}
    for source_id in BENCHMARK_CANDIDATE_IDS:
        assert source_id in by_id
        assert by_id[source_id]["enabled"] is False
        for field in REQUIRED_FIELDS:
            assert field in by_id[source_id], f"{source_id} missing {field}"


def test_sportradar_trial_source_is_disabled_after_cost_reversal():
    source = get_source("sportradar-soccer")
    assert source["enabled"] is False
    assert source["allowed_use"] == "private_trial_local_retention_pending_review"
    assert source["retention_policy"] == "none_until_owner_review"
    assert source["activation_approval"]["terms"] == "pending"



def test_statsbomb_is_prototyping_only_and_commercial_data_needs_ablation():
    registry = load_registry()
    by_id = {s["source_id"]: s for s in registry["sources"]}
    assert "method_prototyping" in by_id["statsbomb-open"]["allowed_use"]
    assert by_id["statsbomb-open"]["enabled"] is True
    assert by_id["statsbomb-open"]["activation_approval"]["cost"] == (
        "approved_zero"
    )
    commercial = by_id["commercial-epl-event-data"]
    assert commercial["licence_status"] == "unknown"
    assert "ablation" in commercial["notes"].lower()


def test_disabled_sources_have_alternative_or_gap_note():
    registry = load_registry()
    for source in registry["sources"]:
        if source["enabled"]:
            continue
        notes = (source.get("notes") or "").lower()
        assert "alternative" in notes or "gap" in notes, source["source_id"]


def test_assert_collectable_allows_enabled_fpl():
    source = assert_collectable("fpl-official-endpoints")
    assert source["allowed_use"]
    assert source["licence_status"] != "prohibited"


def test_assert_collectable_blocks_disabled():
    try:
        assert_collectable("fpl-authenticated-manager-state")
        assert False, "expected PermissionError"
    except PermissionError:
        pass



def test_free_results_alternative_does_not_bypass_governance():
    source = get_source("football-data-org")
    assert source["enabled"] is False
    assert source["authentication"] == "api_token"
    assert "odds" in source["notes"].lower()
