# 2026/27 broad unstructured capture

The daily capture lane is intentionally high-recall. It records official,
external, and feed candidates from the catalogue searches, including rows with
unknown or ambiguous publication times and rows outside the normal freshness
window. Candidates are research inputs, not evidence claims.

## Data contract

- `search-results.json` retains bounded result metadata and at most 1,000
  characters of untrusted search snippet in the gitignored live-shadow tree.
- `news-capture.json` preserves every supplied candidate and records
  `source_class`, publication-time status, and quality flags.
- The existing `news-discovery.json` remains the strict official admission
  view. It may have zero `leads` while the broad capture contains useful
  candidates.
- Only a human-linked, timestamped official original can enter the governed
  evidence ledger.

## Signal workflow

The strategy-review lane reads the newest broad capture, clusters candidates by
club/player/topic, and reports repeated or decision-relevant signals. It must
state timestamp and corroboration limitations, identify follow-up originals,
and never convert snippets or external reports into claims automatically.

## Operational tasks

- `FPL ChatGPT Unstructured Capture` uses
  `scripts/run_chatgpt_unstructured_capture_broad_task.ps1`.
- `FPL ChatGPT Strategy Review` uses
  `scripts/run_chatgpt_strategy_review_broad_task.ps1`.
- Each capture uses a UTC timestamped directory so reruns are immutable.
- Neither task may create branches, commits, pull requests, or FPL account
  actions.
