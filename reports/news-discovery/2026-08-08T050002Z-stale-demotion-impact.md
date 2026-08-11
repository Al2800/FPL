# Stale-marker demotion impact — 2026-08-08T050002Z

Compared `triage-before-stale-demotion.json` vs demotion-enabled `triage.json`.

## Policy

`control/policies/news-capture-triage-v1.json` → `stale_markers`:

- year stamps in title/URL older than observed year (`2026`): **−45**
- historical manager terms (Ten Hag, Tuchel, Lampard, …): **−25**
- demotion only — candidates are not deleted

## Counts

| Metric | Before | After |
| --- | ---: | ---: |
| Shortlist | 24 | 24 |
| Demoted across full capture | — | 143 |
| `arsenal_attack` on shortlist | 7 | 5 |
| `availability_general` | 23 | 21 |
| `haaland_minutes` | 2 | 2 |

## Dropped from shortlist (6)

- Team news: United v Fulham (URL `…-24-february-2024`)
- Tuchel Chelsea injury / Southampton pressers
- Frank Lampard Norwich injury update
- Wigan v Man City injury news (`…/2018/february/…`)
- Erik ten Hag West Ham press conference

## Newly promoted onto shortlist (6)

- Klopp: Salah in contention to face Brentford
- Watch Chelsea training live
- Injury update: Alisson, Isak, Mamardashvili, Salah and more
- Liverpool v Brentford: Team news
- Michael Carrick press conference
- The Presser: Emery analyses AZ Alkmaar

## Still needs verify

Top Haaland City hit remains #1 (no year in URL/title) — still FA Cup-era content; demotion does not invent dates. Fresh Asia-tour / holiday framing still requires a newer capture or manual verify of fresher official URLs.
