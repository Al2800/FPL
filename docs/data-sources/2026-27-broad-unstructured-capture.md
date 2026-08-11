# 2026/27 broad unstructured capture

The daily capture lane is **freshness-first**: it still records official,
external, and feed candidates (including unknown publication times), but the
scheduled prompt prefers recent, dated official hits over archive volume.
Candidates remain research inputs, not evidence claims.

## Data contract

- `search-results.json` retains bounded result metadata and at most 1,000
  characters of untrusted search snippet in the gitignored live-shadow tree.
- `news-capture.json` preserves every supplied candidate and records
  `source_class`, publication-time status, and quality flags.
- The existing `news-discovery.json` remains the strict official admission
  view (`maximum_result_age_hours: 72`). It may have zero `leads` while the
  broad capture still contains useful undated candidates for triage/verify.
- Only a human-linked, timestamped official original can enter the governed
  evidence ledger.

## Agent behaviour (prompt)

- Prompt: `prompts/daily-news-research/v2-broad-capture-run.md`
- Recency bias (~14 days) on search where the engine allows it.
- Per-club retention cap (12; 8 official/feed + 4 external).
- Light page opens on top official hits to recover `published_at` metadata only.
- Optional post-capture triage via `scripts/run_news_capture_triage.py`.

## Signal workflow

The strategy-review lane reads the newest broad capture, clusters candidates by
club/player/topic, and reports repeated or decision-relevant signals. Prefer
known-time official candidates. It must state timestamp and corroboration
limitations, identify follow-up originals, and never convert snippets or
external reports into claims automatically.

## Operational tasks

- `FPL ChatGPT Unstructured Capture` uses
  `scripts/run_chatgpt_unstructured_capture_broad_task.ps1`.
- `FPL ChatGPT Strategy Review` uses
  `scripts/run_chatgpt_strategy_review_broad_task.ps1`.
- Each capture uses a UTC timestamped directory so reruns are immutable.
- Neither task may create branches, commits, pull requests, or FPL account
  actions.
