"""WP-04 assessment reports exist and identity metrics are coherent."""

from pathlib import Path
import json

import yaml

REPO = Path(__file__).resolve().parents[2]
WP04 = REPO / "docs" / "data-sources" / "wp04"


def test_wp04_reports_present():
    for name in (
        "README.md",
        "vaastav-profile.md",
        "football-data-profile.md",
        "disabled-sources-profile.md",
        "news-recoverability.md",
        "training-targets.md",
        "summary.json",
    ):
        assert (WP04 / name).exists(), name


def test_summary_identity_rates_in_range():
    summary = json.loads((WP04 / "summary.json").read_text(encoding="utf-8"))
    assert summary["news_feasibility"] == "low_without_external_archives"
    assert len(summary["vaastav_seasons"]) >= 8
    assert summary["identity_matches"]
    for row in summary["identity_matches"]:
        assert 0.4 <= row["match_rate_of_earlier"] <= 0.9
        assert 0.4 <= row["match_rate_of_later"] <= 0.9


def test_tier2_sources_registered():
    registry = yaml.safe_load(
        (REPO / "control" / "sources" / "source-registry.yaml").read_text(encoding="utf-8")
    )
    ids = {s["source_id"] for s in registry["sources"]}
    for required in (
        "vaastav-fpl",
        "football-data-co-uk",
        "fbref",
        "understat",
        "clubelo",
        "fpl-core-insights",
        "world-cup-2026",
    ):
        assert required in ids


def test_world_cup_template_exists():
    assert (REPO / "control" / "identities" / "world-cup-2026-priors-template.csv").exists()
