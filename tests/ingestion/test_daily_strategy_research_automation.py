"""Daily Composer 2.5 strategy research recipe stays coherent."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECIPE = json.loads(
    (
        ROOT / "config/automations/2026-27-daily-strategy-research.json"
    ).read_text(encoding="utf-8")
)
PROMPT = (
    ROOT / "prompts/daily-strategy-research/v1.md"
).read_text(encoding="utf-8")
NEWS_RECIPE = json.loads(
    (
        ROOT / "config/automations/2026-27-daily-news-research.json"
    ).read_text(encoding="utf-8")
)


def test_strategy_recipe_assigns_composer_25_as_morning_driver() -> None:
    assert RECIPE["model"]["id"] == "composer-2.5"
    assert RECIPE["trigger"]["cron"] == "0 7 * * *"
    assert RECIPE["tools"]["web_search"] is True
    assert RECIPE["governance"]["community_content_lane"] == (
        "strategy_intelligence_only"
    )
    assert "six_gw_live_faithful_horizon" in RECIPE["governance"]["does_not_replace"]


def test_strategy_prompt_targets_chip_defcon_and_governance_wall() -> None:
    lowered = PROMPT.lower()
    assert "composer 2.5" in lowered
    assert "web search" in lowered
    assert "chip" in lowered
    assert "defcon" in lowered
    assert "haaland" in lowered or "premium" in lowered
    assert "lane b" in lowered
    assert "never" in lowered
    assert (ROOT / RECIPE["prompt"]["path"]).is_file()
    assert (ROOT / RECIPE["inputs"]["loop_doc_path"]).is_file()
    nested = RECIPE["nested_prompts"][0]["path"]
    assert (ROOT / nested).is_file()


def test_news_only_recipe_is_nested_not_parallel_morning_job() -> None:
    assert NEWS_RECIPE["status"] == "nested_lane_under_daily_strategy_research"
    assert NEWS_RECIPE["superseded_by"] == "fpl-daily-strategy-research"
