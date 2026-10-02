# Live-entry decision input — 2026-10-02

- observed_at: 2026-10-02T07:15:00Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for squads, completed picks, transfers and scoring; official club and association sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded

## Executive decision

There is **no transfer or chip action today**. Lane A proposed zero new claims; governed ledger tip remains `fdc0e882…`.

Material overnight bootstrap change: **O'Reilly** (Man City) is now `d` / unspecified injury **75%** (`news_added` 2026-10-01T15:30:10Z). He is **not owned** by either tracked entry — briefing-only until a mancity.com timed original.

For the Haaland arm (8522487): **Van Hecke** remains `d` / foot **75%**. City’s 1 Oct official international roundup shows **Haaland involved for Norway** on Thursday — corroborates keeping Haaland (C). Provisional GW6 XI: start **Diop** ahead of Van Hecke; keep Mitchell. **Bruno** remains the key owned monitor (FPL still `a`); **Mitchell remains provisional vice-captain** until normal Bruno involvement is shown. Do **not** spend a FT on Bogle into LEE–ARS (A).

The no-Haaland squad (7337262) remains five doubtfuls (Palmer, Semenyo, Rice, Isak, João Pedro) plus Obi `u`. Retained Gakpo/Isak tips matter for the LIV–MCI environment, not for owned XI moves today.

The automated strategy report’s Kinsky/Cherki/Wissa reconstructed 15 remains advisory-only and is **not** the owned squad for either entry.

## Official entry state

GW5 is finished and data checked. Working top-1,000 boundary remains **414** (prior sample; not re-polled this morning).

| entry | arm | GW5 | total | current OR | gap to 414 (pts) |
|---|---|---:|---:|---:|---:|
| 8522487 | Haaland | 51 | 292 | ~5.20m | 122 |
| 7337262 | no Haaland | 43 | 291 | ~5.32m | 123 |

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
| Haaland | City Norway involvement confirmed on 1 Oct club roundup; FPL `a` | FPL `a` | mancity.com listing 2026-10-01T20:50:00Z; tip `model:2cb641ec…` | 2026-10-02T07:15:00Z | keep (C) on Haaland arm; Anfield away still monitored |
| Van Hecke | foot injury; returned from Netherlands camp | 75% | KNVB 2026-09-30; FPL `news_added` 2026-09-30T16:00:09Z | 2026-10-02T07:15:00Z | unchanged; bench behind Diop |
| Bruno Fernandes | FPL unflagged `a` | FPL unflagged | Man Utd 2026-09-28 page outside today's 72h gate | 2026-10-02T07:15:00Z | keep in XI; Mitchell provisional VC |
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
- Captain / vice: Haaland / Mitchell
- Chip: none; FT: roll/bank unless multi-hole after remaining pressers

### 7337262 (no-Haaland arm)

- XI lean: Raya; Gabriel, Guéhi, Castagne, Truffert; Rogers, Anderson; (Palmer/Semenyo/Rice minutes pending); Isak or João Pedro only if cleared
- Fallback captaincy while Palmer doubtful: Rogers (C) / Raya (VC); restore Palmer (C) only after normal-minutes clearance
- Reject automated Isak (C) while thigh-flagged
- Chip: none; WC only if ≥3 holes persist into the final GW6 pressers

## Host handoff

- Account writes: false
- Owner approval still required
- Ledger tip: `fdc0e882…`
- Model run: `composer-2.5:2026-10-02T070041Z`
