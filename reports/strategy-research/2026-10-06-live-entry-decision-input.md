# Live-entry decision input — 2026-10-06

- observed_at: 2026-10-06T08:05:03Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club and association sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded

## Executive decision

There is **no material owned-squad decision change**. Make no transfer and activate no chip today.

The governed evidence run admitted one new official claim: Nico O'Reilly withdrew from England and returned to Manchester City for assessment. O'Reilly is not owned by either tracked entry, so this changes the ledger tip but not either decision.

Official FPL shows no owned-player price, status, chance-of-playing or news-timestamp change since 5 October. Its mutable `ep_next` estimates moved materially — Semenyo 6.5 to 7.5, Mitchell 7.7 to 4.0, Verbruggen 5.7 to 7.0 and Haaland 8.0 to 7.5 — but these are directional game estimates rather than medical clearances.

- **Entry 8522487:** retain Haaland (C) / Bruno Fernandes (VC). Start Diop ahead of foot-doubtful Van Hecke. João Pedro enters only after a fresh normal-minutes clearance.
- **Entry 7337262:** Palmer, Semenyo, Rice, Isak and João Pedro remain at 75%; Obi remains unavailable. Retain Rogers (C) / Raya (VC) until Palmer receives a normal-minutes clearance. Compare free transfers, hits and Wildcard only if at least three genuine XI holes remain after the final club press conferences.

## Official entry state

GW5 is finished and data checked. Overall standings page 20 was re-polled; the sampled top-1,000 boundary remains **414 points** at rank 994.

| entry | arm | GW5 | total | current OR | gap to 414 |
|---|---|---:|---:|---:|---:|
| 8522487 | Haaland | 51 | 292 | 5,200,000 | 122 |
| 7337262 | no Haaland | 43 | 291 | 5,320,480 | 123 |

| entry | last-deadline value | bank | chips used |
|---|---:|---:|---|
| 8522487 | £99.6m | £0.2m | none |
| 7337262 | £99.8m | £0.0m | none |

Completed transfer history remains:

- 8522487: Wilson to Dewsbury-Hall in GW4; Shaw to Castagne in GW5.
- 7337262: Beto to Isak, B.Fernandes to Palmer and Senesi to Maatsen in GW4; Maatsen to Castagne in GW5.

Public endpoints do not expose current free transfers, pending transfers, purchase prices or selling prices. Those fields must not be inferred; manager state remains degraded.

## Authoritative squads, prices and flags

### Entry 8522487

- GKP: Verbruggen £4.5m; Dubravka £4.0m
- DEF: Van Hecke £4.9m (`d`, foot, 75%; FPL `news_added` 2026-09-30T16:00:09Z); Mitchell £4.5m; Castagne £4.5m; Diop £4.0m; van Ewijk £4.0m (`d`, hamstring, 75%; 2026-09-19T16:00:09Z)
- MID: B.Fernandes £11.9m; Gibbs-White £8.0m; E.Le Fée £5.7m; Dewsbury-Hall £6.6m; Xhaka £5.5m
- FWD: Thiago £7.8m; Haaland £15.6m; João Pedro £7.7m (`d`, knee, 75%; 2026-09-16T19:00:09Z)

### Entry 7337262

- GKP: Raya £6.1m; Verbruggen £4.5m
- DEF: Gabriel £8.0m; Guéhi £6.0m; Castagne £4.5m; Truffert £5.4m; Shaw £4.3m
- MID: Palmer £9.7m (`d`, muscular, 75%; 2026-09-21T13:00:09Z); Rogers £7.7m; Semenyo £8.4m (`d`, ankle, 75%; 2026-09-24T12:00:09Z); Rice £7.4m (`d`, unspecified, 75%; 2026-09-21T13:00:08Z); Anderson £6.3m
- FWD: Isak £9.1m (`d`, thigh, 75%; 2026-09-27T10:30:09Z); João Pedro £7.7m (`d`, knee, 75%; 2026-09-16T19:00:09Z); Obi £4.5m (`u`, loan, 0%)

## Evidence and source freshness

| input | published / observed | accepted implication |
|---|---|---|
| official FPL bootstrap, fixtures and entry endpoints | observed 2026-10-06T08:05:03Z | no owned price/status/chance/news change; deadline and public entry state current |
| England squad update | published 2026-10-05 | O'Reilly returned to City for assessment; Scott and Konsa also withdrew; none is owned |
| Manchester City Lewis call-up report | published 2026-10-04T13:30:00Z | corroborates O'Reilly withdrawal; no owned-player effect |
| Chelsea pre-Brentford team news | published 2026-09-18 | Alonso expected João Pedro to use the break to target Bournemouth; positive target, but too old to prove current fitness or normal minutes |
| Premier League João Pedro pointer | published 2026-10-05 | republishes the aged Chelsea target; not a fresh medical update |
| governed evidence ledger | observed 2026-10-06T07:15:00Z | O'Reilly doubtful admitted; tip `fdc0e882…` to `5d89db69…` |
| decision packet | checkpoint 2026-08-11 | stale for live squads and availability; methodology context only |
| repository X community digest | observed 2026-10-05T08:00:00Z | challenge input only; no claim promoted |

No fresh timed club original clears Palmer, Semenyo, Rice, Isak, João Pedro, Van Hecke or van Ewijk. Silence is not a clearance. England host Czechia at 19:45 BST on 6 October, making completed minutes and any post-match issues for Guéhi, Anderson, Rogers and Gibbs-White the next owned-player evidence checkpoint.

## Accepted, rejected and deferred claims

- **Accepted, non-owned:** O'Reilly is doubtful after returning to Manchester City for assessment.
- **Retained:** Haaland and Bruno completed their 4 October international involvement without a reported problem; Haaland remains the owned arm's captain and Bruno vice-captain.
- **Deferred:** João Pedro's old Bournemouth return target increases the plausibility of a return but does not satisfy the normal-minutes clearance test.
- **Rejected:** treating FPL `ep_next` movement as injury evidence; default WC6; an early hit; clearing any flagged player from community optimism or absence of news.
- **Community challenge only:** early Wildcard drafts, Saka/Bruno buying pressure, unverified Havertz and Haaland injury chatter, and Alex Scott timelines do not change either owned squad today.

## Provisional GW6 teams

### 8522487 — Haaland arm

Verbruggen  
Mitchell, Castagne, Diop  
B.Fernandes, Gibbs-White, E.Le Fée, Dewsbury-Hall, Xhaka  
Thiago, Haaland

- Captain: **Haaland**
- Vice-captain: **B.Fernandes**
- Bench: Dubravka; 1 João Pedro, 2 Van Hecke, 3 van Ewijk
- If João Pedro receives a fresh normal-minutes clearance, start him over Xhaka.
- Transfer/chip: hold; no chip.

### 7337262 — no-Haaland arm

If all five doubtful players receive normal-minutes clearances:

Raya  
Gabriel, Guéhi, Castagne  
Rogers, Palmer, Semenyo, Rice, Anderson  
João Pedro, Isak

- Current risk-adjusted captain: **Rogers**
- Vice-captain: **Raya**
- Restore Palmer (C) / Rogers (VC) only after a normal-minutes clearance.
- Bench: Verbruggen; 1 Shaw, 2 Truffert, 3 Obi.
- If João Pedro is unavailable, start Shaw. Rebuild the XI from actual clearances rather than assuming all five doubts start.
- Transfer/chip: hold; rerun FT/hit/Wildcard only if at least three genuine holes persist.

## Rolling four-Gameweek plan

- **GW6:** record Tuesday's England minutes and wait for Wednesday–Friday club press conferences. Preserve transfers unless official evidence creates a real XI hole or clearly superior multiweek repair.
- **GW7:** Manchester City host Ipswich. Haaland is the probable captain anchor; compare Triple Captain rather than pre-committing. For entry 7337262, calculate the cheapest legal Haaland route only after authenticated free transfers and selling prices are known.
- **GW8:** Chelsea host Spurs and Manchester United host Bournemouth. Reassess Palmer, João Pedro and Bruno roles/minutes; retain premium flexibility.
- **GW9:** Manchester City host Brighton while Chelsea host Manchester United. Haaland is the early captain favourite; avoid spending transfers now on low-upside bench reshuffling.

## Host handoff

- Account writes: false
- Before the final GW6 recommendation, manually confirm on both authenticated transfer pages: exact free transfers, current bank/team value, purchase and selling prices, pending-transfer state and chip state.
- Owner approval remains required for any FPL action.
- Ledger tip: `5d89db69…`

