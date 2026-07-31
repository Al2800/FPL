# 2026/27 daily official news research automation

**Status:** recipe ready — activate in Cursor Automations UI  
**Model:** Composer 2.5 (`composer-2.5`)  
**Schedule:** daily `0 8 * * *` UTC  
**Prompt:** `prompts/daily-news-research/v1.md`  
**Recipe:** `config/automations/2026-27-daily-news-research.json`

## Purpose

Run a scheduled web-search pass over the governed club-news catalogue so human
operators receive fresh **discovery leads**. Leads are not claims. Claim
admission remains manual citation under `official-club-communications`.

## Why Composer 2.5

Daily research is tool-heavy (many domain-restricted searches, careful metadata
capture, deterministic script hand-off). Composer 2.5 is assigned as the
automation model for agentic web research without promoting any LLM into the
deterministic scoring or approval path.

## Activate

Cursor Automations are configured in the product UI, not loaded automatically
from Git. Version the prompt here, then:

1. Open [cursor.com/automations](https://cursor.com/automations)
2. Create a **Scheduled** automation with cron `0 8 * * *` (UTC)
3. Set **Model** to **Composer 2.5**
4. Attach repository `Al2800/FPL`, branch `main`
5. Paste the full contents of `prompts/daily-news-research/v1.md`
6. Enable computer use / browsing, memories, and draft PR creation
7. Save and activate

After activation, store the automation UUID in the recipe's optional
`cursor_automation_uuid` field via a follow-up commit if useful for audits.

## Outputs

| Artifact | Path | Git |
|---|---|---|
| Search metadata | `data/live-shadow/news-discovery/YYYY-MM-DD/search-results.json` | ignored |
| Discovery ledger | `data/live-shadow/news-discovery/YYYY-MM-DD/news-discovery.json` | ignored |
| Cited originals packet | `data/live-shadow/news-discovery/YYYY-MM-DD/cited-originals.json` | ignored |
| Human briefing | `reports/news-discovery/YYYY-MM-DD.md` | may open draft PR |

## Boundaries

- Registry source stays citation-only; no HTML scrape collector
- Snippets and article bodies are discarded
- Empty successful search ≠ availability evidence
- No odds fabrication, no Sportradar, no unregistered analyst blogs
