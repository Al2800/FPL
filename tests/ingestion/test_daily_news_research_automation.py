"""Daily Composer 2.5 news-research automation recipe stays coherent."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[2]
RECIPE = json.loads(
    (ROOT / "config/automations/2026-27-daily-news-research.json").read_text(
        encoding="utf-8"
    )
)
SCHEMA = json.loads(
    (ROOT / "prompts/daily-news-research/output.schema.json").read_text(
        encoding="utf-8"
    )
)
PROMPT = (
    ROOT / "prompts/daily-news-research/v1.md"
).read_text(encoding="utf-8")
CATALOGUE = yaml.safe_load(
    (ROOT / "control/sources/club-news-catalogue.yaml").read_text(encoding="utf-8")
)


def test_recipe_assigns_composer_25_on_daily_utc_schedule() -> None:
    assert RECIPE["model"]["id"] == "composer-2.5"
    assert RECIPE["model"]["assignment"] == "required"
    assert RECIPE["trigger"]["type"] == "schedule"
    assert RECIPE["trigger"]["cron"] == "0 8 * * *"
    assert RECIPE["trigger"]["timezone"] == "UTC"
    assert RECIPE["repository"]["repo"] == "Al2800/FPL"
    assert RECIPE["tools"]["web_search"] is True
    assert RECIPE["governance"]["raw_snippet_policy"] == "never_admit_or_retain"


def test_prompt_and_referenced_paths_exist() -> None:
    prompt_path = ROOT / RECIPE["prompt"]["path"]
    assert prompt_path.is_file()
    assert "Composer 2.5" in PROMPT
    assert "web search" in PROMPT.lower()
    assert "never" in PROMPT.lower()
    for key in (
        "catalogue_path",
        "discovery_config_path",
        "output_schema_path",
    ):
        assert (ROOT / RECIPE["inputs"][key]).is_file()
    assert (ROOT / "docs/data-sources/2026-27-daily-news-research-automation.md").is_file()


def test_output_schema_accepts_metadata_only_and_rejects_snippets() -> None:
    club_id = CATALOGUE["sources"][0]["club_id"]
    valid = {
        club_id: [
            {
                "url": "https://www.example.com/news/a",
                "title": "Team news",
                "published_at": "2026-08-20T10:00:00Z",
                "rank": 1,
            }
        ]
    }
    jsonschema.validate(valid, SCHEMA)
    invalid = {
        club_id: [
            {
                "url": "https://www.example.com/news/a",
                "title": "Team news",
                "published_at": "2026-08-20T10:00:00Z",
                "rank": 1,
                "snippet": "must not be retained",
            }
        ]
    }
    try:
        jsonschema.validate(invalid, SCHEMA)
        raise AssertionError("snippet field must be rejected")
    except jsonschema.ValidationError:
        pass
