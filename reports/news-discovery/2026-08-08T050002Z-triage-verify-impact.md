# News triage + verify impact — 2026-08-08T050002Z

Sealed capture → triage shortlist → sample verification → discovery bridge.

## Pipeline counts

| Stage | Count |
| --- | ---: |
| Capture candidates | 408 |
| Discovery leads (strict, pre-triage) | 0 |
| Triage shortlist | 24 |
| Sample verified with `published_at` | 1 |
| Discovery leads after verified admit | 0 |

## Strategy relevance (potential only)

From triage impact (before verification):

- `haaland_minutes`: true (2 shortlist titles)
- `bruno_minutes`: false
- `availability_general`: true
- `team_news`: true

Ledger effect without verification remains **none** (`none_zero_admitted_leads`).

## Sample verification outcomes

1. **City / Haaland fitness** — `needs_human`. Page identity OK; no ISO `published_at`. Body is FA Cup-era ankle/Rodri return, not 2026/27 GW1. Do not invent a date.
2. **United v Fulham team news** — `rejected`. URL dated 24 Feb 2024; page broken/stale.
3. **Liverpool injury news (Alisson et al.)** — `verified` with page date `2026-04-24T00:00:00Z`. Discovery bridge received it then rejected: `result is stale` under `maximum_result_age_hours: 72` → **0** admitted leads.
4. **Arsenal Gabriel/Calafiori** — `needs_human`. Identity OK; no published date; mid-season Fulham context.

## What triage changed

- Surfaced the **Haaland** watch topic that pure discovery (0 leads) hid.
- Showed most high-scoring official hits are **stale search debris**; verification + 72h gate correctly refuse ledger admission.
- Independent fresh look (not admitted): official City coverage around 7–8 Aug 2026 is Asia-tour / Maresca presser; Haaland post-World Cup holiday framing — **not** the old ankle article triage ranked #1.

## Artifacts

- `data/live-shadow/news-discovery/2026-08-08T050002Z/triage.json`
- `data/live-shadow/news-discovery/2026-08-08T050002Z/triage-impact.json`
- `data/live-shadow/news-discovery/2026-08-08T050002Z/verifications-sample.json`
- `data/live-shadow/news-discovery/2026-08-08T050002Z/verification-result.json`
- `data/live-shadow/news-discovery/2026-08-08T050002Z/verified-discovery-bridge.json`
- `reports/news-discovery/2026-08-08T050002Z-triage.md`
- Prompt: `prompts/news-triage-verify/v1.md`

## Open follow-ups

- Triage demotion for URL/title year stamps (e.g. `2024`) and obvious historical managers.
- Prefer fresh official City URLs (tour / presser) on next capture rather than keyword-only Haaland hits.
- Still no automatic forecast or owner-approval mutation from this path.
