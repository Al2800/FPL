# Live-entry decision input — 2026-10-10

- observed_at: 2026-10-10T07:06:23Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST) — **~3h remaining**
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club and association sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-10-10.md` (reconstructed 15 is **not** either owned squad)

## Executive decision

**Haaland arm (8522487):** no transfer required for GW6. Restore **Van Hecke to the XI** (Spurs available `model:d71e4802…`; bootstrap `a`/100%) and bench Diop again. Keep **Haaland (C) / Bruno Fernandes (VC)** — do **not** flip owned captaincy to the advisory Bruno (C) lean. João Pedro is bootstrap-cleared (`a`/100%) and Alonso-ready (briefing; host fetch rejected) — optional elevation over a mid if wanting a 3-4-3, but not mandatory vs Thiago; prefer **roll**.

**No-Haaland arm (7337262):** Isak is now ledger **unavailable** for City (`model:abd411a7…`) and bootstrap `i`. Prefer **roll** and let **Pedro auto-sub** cover an Isak blank (Pedro now bootstrap `a`/100%) rather than panic-FT into a bad destination ~3h out — unless the owner already planned a structural repair. Palmer is bootstrap-cleared (`a`/100%) — restore **Palmer (C) / Rogers (VC)** (or Raya VC) once comfortable with minutes. Semenyo + Rice remain `d`/75%. Reject default WC unless the owner treats Isak+Semenyo+Rice as ≥3 holes.

## Official entry state

GW5 finished. Sampled overall ranks this morning: **8522487 ~5.20m** (292 pts); **7337262 ~5.32m** (291 pts). Top-1,000 boundary **414** re-polled on classic league 314 page 20.

| entry | arm | GW5 | total | current OR | gap to 414 (pts) |
|---|---|---:|---:|---:|---:|
| 8522487 | Haaland | 51 | 292 | ~5.20m | ~122 |
| 7337262 | no Haaland | 43 | 291 | ~5.32m | ~123 |

| entry | last-deadline value | bank | chips used |
|---|---:|---:|---|
| 8522487 | £99.6m | £0.2m | none |
| 7337262 | £99.8m | £0.0m | none |

Completed transfer history remains:

- 8522487: Wilson to Dewsbury-Hall in GW4; Shaw to Castagne in GW5.
- 7337262: Beto to Isak, B.Fernandes to Palmer and Senesi to Maatsen in GW4; Maatsen to Castagne in GW5.

Public endpoints do not expose current free transfers, pending transfers, purchase prices or selling prices. Manager state remains degraded.

## Authoritative squads, prices and flags (morning bootstrap)

### 8522487 — Haaland arm (GW5 picks template into GW6)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Verbruggen | BHA | 4.5 | a | XI |
| DEF | Van Hecke | TOT | 4.9 | a 100% | **restore XI** — tip `model:d71e4802…` |
| DEF | Mitchell | CRY | 4.5 | a | XI |
| DEF | Castagne | FUL | 4.5 | a | XI |
| MID | B.Fernandes | MUN | 11.9 | a | **VC** |
| MID | Gibbs-White | NFO | 8.0 | a | XI |
| MID | E.Le Fée | SUN | 5.7 | a | XI |
| MID | Dewsbury-Hall | EVE | 6.6 | a | XI |
| MID | Xhaka | SUN | 5.5 | a | XI |
| FWD | Thiago | BRE | 7.8 | a | XI |
| FWD | Haaland | MCI | 15.6 | a | **(C)** |
| BEN | Dubravka | TOT | 4.0 | a | |
| BEN | João Pedro | CHE | 7.7 | a 100% | optional elevate |
| BEN | Diop | IPS | 4.0 | a | provisional **bench** again |
| BEN | van Ewijk | COV | 4.0 | d 75% | |

### 7337262 — no-Haaland arm (GW5 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Raya | ARS | 6.1 | a | VC option |
| DEF | Gabriel | ARS | 8.0 | a | XI |
| DEF | Guéhi | MCI | 6.0 | a | XI |
| DEF | Castagne | FUL | 4.5 | a | XI |
| DEF | Truffert | BOU | 5.4 | a | XI |
| MID | Palmer | CHE | 9.7 | a 100% | **restore (C)** candidate |
| MID | Semenyo | MCI | 8.4 | d 75% | ankle — monitor |
| MID | Rice | ARS | 7.4 | d 75% | monitor |
| MID | Anderson | MCI | 6.3 | a | XI |
| MID | Rogers | CHE | 7.8 | a | VC / (C) if Palmer minutes capped |
| FWD | Isak | LIV | 9.1 | i 0% | **unavailable** tip `model:abd411a7…` — expect blank; Pedro auto-sub |
| BEN | Verbruggen | BHA | 4.5 | a | |
| BEN | João Pedro | CHE | 7.7 | a 100% | auto-sub cover |
| BEN | Shaw | MUN | 4.3 | a | |
| BEN | Obi | MUN | 4.5 | u 0% | unavailable — do not rely |

## Recommended owned actions (advisory only)

| entry | transfers | chip | captain / vice | XI note |
|---|---|---|---|---|
| 8522487 | **none / roll** | none | Haaland / Bruno | Start Van Hecke; bench Diop |
| 7337262 | **prefer roll**; FT Isak only if owner rejects Pedro autosub path | none / WC only if multi-hole | Palmer / Rogers (or Raya) | Isak blank expected; Pedro first outfield bench |

## Falsifiers before 10:00 UTC

- Van Hecke or Pedro omitted from matchday squads
- Palmer minutes capped despite clearance wording
- Owner on 7337262 has no valid autosub path and must FT Isak
- Fresh club news creates ≥3 holes on either arm
