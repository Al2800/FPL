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
    "official-lineups-minutes",
    "statsbomb-open",
    "commercial-epl-event-data",
    "football-data-org",
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
        ["fpl-official-endpoints", "football-data-co-uk", "vaastav-fpl"]
    )


def test_benchmark_candidates_are_complete_and_disabled():
    registry = load_registry()
    by_id = {s["source_id"]: s for s in registry["sources"]}
    for source_id in BENCHMARK_CANDIDATE_IDS:
        assert source_id in by_id
        assert by_id[source_id]["enabled"] is False
        for field in REQUIRED_FIELDS:
            assert field in by_id[source_id], f"{source_id} missing {field}"


def test_statsbomb_is_prototyping_only_and_commercial_data_needs_ablation():
    registry = load_registry()
    by_id = {s["source_id"]: s for s in registry["sources"]}
    assert "method_prototyping" in by_id["statsbomb-open"]["allowed_use"]
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
