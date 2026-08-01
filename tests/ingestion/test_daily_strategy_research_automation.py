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
    assert RECIPE["governance"]["role"] == "primary_advisory_decision_arm"
    assert RECIPE["governance"]["deterministic_arms_role"] == (
        "comparators_and_legality_stress_tests"
    )
    assert "host_rules_validation_and_rescoring" in RECIPE["governance"][
        "does_not_replace"
    ]


def test_strategy_prompt_is_primary_decision_arm() -> None:
    lowered = PROMPT.lower()
    assert "composer 2.5" in lowered
    assert "web search" in lowered
    assert "primary advisory" in lowered
    assert "recommended 15" in lowered
    assert "chip" in lowered
    assert "defcon" in lowered
    assert "comparator" in lowered
    assert "never" in lowered
    assert (ROOT / RECIPE["prompt"]["path"]).is_file()
    assert (ROOT / RECIPE["inputs"]["loop_doc_path"]).is_file()
    nested = RECIPE["nested_prompts"][0]["path"]
    assert (ROOT / nested).is_file()


def test_news_only_recipe_is_nested_not_parallel_morning_job() -> None:
    assert NEWS_RECIPE["status"] == "nested_lane_under_daily_strategy_research"
    assert NEWS_RECIPE["superseded_by"] == "fpl-daily-strategy-research"
