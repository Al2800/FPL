# 2026/27 daily official news research automation

**Status:** nested Lane A under the daily strategy research automation  
**Prefer:** `config/automations/2026-27-daily-strategy-research.json`  
**Model:** Composer 2.5 (`composer-2.5`)  
**Prompt (Lane A only):** `prompts/daily-news-research/v1.md`  
**Strategy driver:** `prompts/daily-strategy-research/v1.md`

## Purpose

Official catalogue discovery remains the **governed lead** lane. The morning
driver is now the broader strategy research loop (chips, premiums, DEFCON,
captains, early Wildcard debate) documented in
`docs/evaluation/2026-27-daily-agent-strategy-loop.md`. Do not run this
news-only automation as a second morning job.

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

The model run is self-contained after activation: it writes candidates, runs
the host admission script and records the audit. No owner-side ledger editing
step is part of the operating loop.

After activation, store the automation UUID in the recipe's optional
`cursor_automation_uuid` field via a follow-up commit if useful for audits.

## Outputs

| Artifact | Path | Git |
|---|---|---|
| Search metadata | `data/live-shadow/news-discovery/YYYY-MM-DD/search-results.json` | ignored |
| Discovery ledger | `data/live-shadow/news-discovery/YYYY-MM-DD/news-discovery.json` | ignored |
| Cited originals packet | `data/live-shadow/news-discovery/YYYY-MM-DD/cited-originals.json` | ignored |
| Model evidence run | `data/live-shadow/evidence/model-runs/YYYY-MM-DD/model-evidence-run.json` | ignored |
| Host admission audit | `data/live-shadow/availability/model-runs/<run-id>.audit.json` | ignored |
| Content-addressed availability ledger | `data/live-shadow/availability/model-runs/availability-ledger-<hash>.json` | ignored |
| Deterministic evidence review | `reports/evidence-review/<run-id>.md` | committed |
| Model briefing + decision trace | `reports/news-discovery/YYYY-MM-DD.md` | may open draft PR |

## Boundaries

- Registry source stays citation-only; model path is one-URL ephemeral hashing,
  not a bulk HTML scrape collector
- Snippets and article bodies are discarded
- Empty successful search ≠ availability evidence
- The host, not the model, appends claims; rejected candidates and coverage
  gaps are retained in the audit
- No odds fabrication, no Sportradar, no unregistered analyst blogs
