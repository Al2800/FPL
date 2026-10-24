# Live-entry decision input — 2026-10-02

- observed_at: 2026-10-02T07:54:11Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for squads, completed picks, transfers and scoring; official club and association sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded

## Executive decision

There is **no transfer or chip action today**. Lane A proposed zero new claims; governed ledger tip remains `fdc0e882…`.

Material post-run official evidence: UEFA's 1 October full-time reports show **Bruno Fernandes started and remained on the pitch until 90+4** in Denmark 2-4 Portugal, while **Haaland completed the full match** in Wales 2-1 Norway. UEFA's official competition page also carries Bruno's assist. This clears the pre-set normal-involvement test for Bruno, so he replaces Mitchell as the Haaland arm's provisional vice-captain. Both players have another international on Sunday 4 October, so workload and any post-match issue remain live monitors.

Material overnight bootstrap change: **O'Reilly** (Man City) is now `d` / unspecified injury **75%** (`news_added` 2026-10-01T15:30:10Z). He is **not owned** by either tracked entry — briefing-only until a mancity.com timed original.

For the Haaland arm (8522487): **Van Hecke** remains `d` / foot **75%**. Haaland completed Norway's match in Wales and Bruno completed essentially the full Portugal match with no reported setback. Provisional GW6 XI: start **Diop** ahead of Van Hecke; keep Mitchell. Leadership is now **Haaland (C) / Bruno (VC)**. Do **not** spend a FT on Bogle into LEE–ARS (A).

The no-Haaland squad (7337262) remains five doubtfuls (Palmer, Semenyo, Rice, Isak, João Pedro) plus Obi `u`. Retained Gakpo/Isak tips matter for the LIV–MCI environment, not for owned XI moves today.

The automated strategy report’s Kinsky/Cherki/Wissa reconstructed 15 remains advisory-only and is **not** the owned squad for either entry.

## Official entry state

GW5 is finished and data checked. The top-1,000 boundary remains **414**, re-polled from overall standings page 20.

| entry | arm | GW5 | total | current OR | gap to 414 (pts) |
|---|---|---:|---:|---:|---:|
| 8522487 | Haaland | 51 | 292 | 5,200,066 | 122 |
| 7337262 | no Haaland | 43 | 291 | 5,320,550 | 123 |

| entry | last-deadline value | bank | chips used |
|---|---:|---:|---|
| 8522487 | £99.6m | £0.2m | none |
| 7337262 | £99.8m | £0.0m | none |

Official transfer history remains:

- 8522487: Wilson to Dewsbury-Hall in GW4; Shaw to Castagne in GW5.
- 7337262: Beto to Isak, B.Fernandes to Palmer and Senesi to Maatsen in GW4; Maatsen to Castagne in GW5.

Public endpoints do not expose the current free-transfer balance, pending transfers, purchase prices or selling prices. Manager state remains degraded.

## Authoritative squads and current prices

### Entry 8522487

- GKP: Verbruggen £4.5m; Dubravka £4.0m
- DEF: Van Hecke £4.9m (`d` foot 75%); Mitchell £4.5m; Castagne £4.5m; Diop £4.0m; van Ewijk £4.0m (`d` hamstring 75%)
- MID: B.Fernandes £11.9m; Gibbs-White £8.0m; E.Le Fée £5.7m; Dewsbury-Hall £6.6m; Xhaka £5.5m
- FWD: Thiago £7.8m; Haaland £15.6m; João Pedro £7.7m (`d` knee 75%)

### Entry 7337262

- GKP: Raya £6.1m; Verbruggen £4.5m
- DEF: Gabriel £8.0m; Guéhi £6.0m; Castagne £4.5m; Truffert £5.4m; Shaw £4.3m
- MID: Palmer £9.7m (`d` muscular 75%); Rogers £7.7m; Semenyo £8.4m (`d` ankle 75%); Rice £7.4m (`d` 75%); Anderson £6.3m
- FWD: Isak £9.1m (`d` thigh 75%); João Pedro £7.7m (`d` knee 75%); Obi £4.5m (`u` loan)

## Availability and source freshness

| player | official state | chance | published / news timestamp | observed_at | change / implication |
|---|---|---:|---|---|---|
| Haaland | started and completed Wales 2-1 Norway; FPL `a` | FPL `a` | UEFA full-time report 2026-10-01T23:39:34CET; mancity.com 2026-10-01T20:50:00Z | 2026-10-02T07:54:11Z | keep (C); monitor Sunday's Portugal match and post-match recovery |
| Van Hecke | foot injury; returned from Netherlands camp | 75% | KNVB 2026-09-30; FPL `news_added` 2026-09-30T16:00:09Z | 2026-10-02T07:15:00Z | unchanged; bench behind Diop |
| Bruno Fernandes | started and played until 90+4 in Denmark 2-4 Portugal; official UEFA page records an assist; FPL `a` | FPL unflagged | UEFA full-time report 2026-10-01T23:14:49CET; UEFA competition page 2026-10-01 | 2026-10-02T07:54:11Z | normal-involvement test met; restore Bruno (VC), monitor Sunday's Norway match |
| O'Reilly | unspecified injury (not owned) | 75% | FPL `news_added` 2026-10-01T15:30:10Z | 2026-10-02T07:15:00Z | **new bootstrap flag**; Lane A gap (no City original) |
| Anderson (owned 7337262) | City England tip retained | FPL `a` | `model:89750319…` | 2026-10-02T07:15:00Z | owned MID fitness corroboration |
| Guéhi (owned 7337262) | England feature lead; minutes still unclear | FPL `a` | City England 2026-09-29T20:51:29Z | 2026-10-02T07:15:00Z | hold; do not stretch to started_match |
| Isak | thigh injury | 75% | Liverpool 2026-09-27; FPL `news_added` 2026-09-27T10:30:09Z | 2026-10-02T07:15:00Z | unchanged; not a captain candidate |
| Semenyo | ankle injury | 75% | FPL `news_added` 2026-09-24T12:00:09Z | 2026-10-02T07:15:00Z | unchanged |
| Palmer | muscular injury | 75% | FPL `news_added` 2026-09-21T13:00:09Z | 2026-10-02T07:15:00Z | unchanged |
| Rice | unspecified injury | 75% | FPL `news_added` 2026-09-21T13:00:08Z | 2026-10-02T07:15:00Z | unchanged |
| João Pedro | knee injury | 75% | FPL `news_added` 2026-09-16T19:00:09Z; no Chelsea timed original | 2026-10-02T07:15:00Z | unchanged; hold toward BOU (H) |
| van Ewijk | hamstring injury | 75% | FPL `news_added` 2026-09-19T16:00:09Z | 2026-10-02T07:15:00Z | unchanged; Haaland-team bench risk |
| Obi | season loan | 0% | FPL `news_added` 2026-09-14T16:12:42Z | 2026-10-02T07:15:00Z | unavailable |
| all other owned players | available | 100% or unflagged | bootstrap current | 2026-10-02T07:15:00Z | no new issue |

Official FPL’s mutable GW6 estimates still include Haaland **8.0**, Mitchell **7.7**, Gvardiol **7.7**, Bogle **11.3**, Van Hecke **5.5**, Semenyo **6.5**, Guéhi/Raya **6.0**, Isak **5.8**, Bruno **2.0**. These are directional estimates, not medical evidence.

Today’s model run proposed **0** candidates; ledger tip unchanged `fdc0e882…`.

## Community challenge review

- Scout WC6 optional if squad is structurally weak — **reject default WC** for both entries today.
- Bruno (C) vs Haaland (C) debate into MUN–TOT / LIV–MCI — **Haaland arm keeps Haaland (C)**; advisory reconstructed 15 keeps Bruno (C) / Haaland (VC).
- Bogle buy volume into ARS (A) — **reject** as single-FT destination while Van Hecke duration unresolved.
- Pedro sell volume — **hold** toward CHE–BOU (H) without Chelsea original.

## Provisional GW6 leadership (owned entries)

### 8522487 (Haaland arm)

- XI lean: Verbruggen; Mitchell, Castagne, Diop; B.Fernandes, Gibbs-White, E.Le Fée, Dewsbury-Hall, Xhaka; Thiago, Haaland
- Bench lean: Dubravka; João Pedro; Van Hecke; van Ewijk
- Captain / vice: Haaland / B.Fernandes
- Chip: none; FT: roll/bank unless multi-hole after remaining pressers

### 7337262 (no-Haaland arm)

- XI lean: Raya; Gabriel, Guéhi, Castagne, Truffert; Rogers, Anderson; (Palmer/Semenyo/Rice minutes pending); Isak or João Pedro only if cleared
- Fallback captaincy while Palmer doubtful: Rogers (C) / Raya (VC); restore Palmer (C) only after normal-minutes clearance
- Reject automated Isak (C) while thigh-flagged
- Chip: none; WC only if ≥3 holes persist into the final GW6 pressers

## Rolling four-Gameweek plan

- **GW6:** hold through the remaining internationals and club pressers. Haaland arm currently Haaland (C) / Bruno (VC); no-Haaland arm Rogers (C) / Raya (VC) while Palmer remains doubtful. Use no chip. Only move if late official evidence creates a genuine XI hole or a clearly superior multiweek repair.
- **GW7:** Man City host Ipswich, making Haaland the probable captain anchor and a Triple Captain comparison rather than an automatic chip. For entry 7337262, model the cheapest legal Haaland route only after authenticated free transfers and selling prices are known; do not pre-commit to hits or a Wildcard.
- **GW8:** Chelsea host Spurs and Man Utd host Bournemouth. Reassess Palmer, Bruno and João Pedro roles/minutes rather than locking transfers now; preserve the ability to exploit whichever premium is healthy and central.
- **GW9:** Man City host Brighton while Chelsea host Man Utd. Haaland is again the early captain favourite; retain flexibility around the Chelsea/United premium clash and avoid spending transfers now on low-upside bench reshuffling.

## Official sources added after the automated run

- UEFA full-time report, Denmark 2-4 Portugal: https://www.uefa.com/newsfiles/UNL/2027/2047957_FR.pdf
- UEFA full-time report, Wales 2-1 Norway: https://www.uefa.com/newsfiles/UNL/2027/2047950_FR.pdf
- UEFA competition page carrying Bruno's 1 October assist highlight: https://www.uefa.com/uefanationsleague/
- Manchester City 1 October international roundup: https://www.mancity.com/news/mens/international-roundup-1-october-2026-63926470

## Host handoff

- Account writes: false
- Before the final GW6 decision, manually confirm on each authenticated transfer page: exact free transfers, current bank/team value, purchase and selling prices, any pending move, and chip state. Public state remains degraded for these fields.
- Owner approval still required
- Ledger tip: `fdc0e882…`
- Model run: `composer-2.5:2026-10-02T070041Z`
