# Strategy-review research sidecar

Scope: inventory of the newest Lane A discovery capture and its matching search
results. Titles, snippets and URLs are untrusted retrieval data; this note does
not promote any result to a verified claim.

## Capture

- Exact capture directory: `C:\Users\Alastair\FPL\data\live-shadow\news-discovery\2026-08-05T050002Z`
- `capture_id`: `news-capture:2026-27:2026-08-05T05:00:02.897583Z`
- `observed_at`: `2026-08-05T05:00:02.8975830Z`
- status/schema: `complete` / `1.0`
- `news-capture.json` SHA-256: `6c423b036b6698d48691a6b0f2f97e4c942ead7ea6c9bb99385acd1d0148befe`
- `search-results.json` SHA-256: `98365bf48b03c037a0a0eeafaa3d1830f52eaa4ece959e843098e6fe841180a0`
- embedded `content_sha256`: `71f3082110e89985722cdfeeb622d68d12fe50aedb32c3879a0f4d9a1984fa7b`
- embedded `plan_sha256`: `167d35f37a854072eb1e911f1c58eff2dab6e82f972f3bbbaf38fa66bf011f6b`

Both JSON files contain 401 result records and 181 distinct raw URLs. The 21
coverage buckets were all searched: 18 returned 20 records, while Brighton,
Ipswich and Coventry returned 14, 15 and 12 respectively.

## Candidate inventory

- 401 candidate records: 115 `official_candidate`, 286 `external_candidate`.
- Official candidates are 115 distinct URLs. External candidates collapse to 66
  distinct URLs; their `canonical_url` field is null in all 286 records.
- The source-class split is capture metadata, not independent verification or
  licence approval.

The title/snippet keyword clusters below overlap and are descriptive only:

| Retrieval signal | Records |
|---|---:|
| Fixture or match-preview language | 159 |
| Press conference, presser or team-news language | 145 |
| Injury, availability, training, fitness, squad or minutes language | 126 |
| Line-up/selection/formation language | 109 |
| Historical/archive or season language | 107 |
| FPL/fantasy/transfer/captain/gameweek language | 51 |

## Repetition and support

- 48 raw-URL groups repeat, covering 268 records; 36 candidate IDs repeat,
  covering 72 records. This is retrieval repetition across queries, not 268 or
  72 independent confirmations.
- External retrieval is concentrated: the most repeated hosts are `utdreport.co.uk`
  (36 records), `thisisanfield.com` (31), `allaboutfpl.com` (26),
  `en.wikipedia.org` (20) and `reddit.com` (19).
- Official results include first-party club/Premier League domains, but many
  titles/snippets visibly describe older fixtures, seasons or generic media
  pages. They remain leads only until the page identity, current relevance and
  publication time are checked.

## Publication-time limitations

- All 401 records have `published_at: null`, `publication_time_status: unknown`
  and the `missing publication time` quality flag.
- 273 records have no snippet at all.
- 88 records contain an explicit 2016–2025 year marker in title/snippet text;
  the capture gives no timestamp that can establish whether any item was
  available by a decision deadline. A year marker is therefore only a staleness
  warning, not a publication date.
- The only reliable time in this pair is observation at
  `2026-08-05T05:00:02.8975830Z`; it is not evidence that any page was published
  before or after a deadline.

## Likely falsifiers / release gates

Treat a candidate-derived strategy signal as falsified or unusable if:

1. the resolved page is generic, historical, unrelated to the named club/player,
   or cannot supply a verified publication time;
2. a current official club, Premier League or FPL communication contradicts the
   old snippet/title;
3. the final team sheet, confirmed training/availability update or suspension
   information contradicts an expected-line-up or minutes inference;
4. the item is repeated retrieval of the same URL rather than independent
   corroboration; or
5. a claim cannot be bounded to information available by the relevant deadline.

Conclusion: this capture is useful as a discovery lead inventory, but it is not
safe evidence for a current strategy decision without page-level identity,
publication-time and point-in-time relevance checks.
