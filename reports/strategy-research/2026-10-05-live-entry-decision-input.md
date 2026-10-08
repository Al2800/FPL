# Live-entry decision input — 2026-10-05

- observed_at: 2026-10-05T07:25:52Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club and association sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded

## Executive decision

There is **no material decision change**. Make no transfer and activate no chip today.

New official workload evidence from 4 October: Haaland started Portugal 2-1 Norway and was replaced after 67 minutes. Bruno Fernandes started for Portugal and was replaced only in second-half stoppage time. Neither has a reported post-match issue and both remain unflagged in official FPL. The shorter Haaland workload supports, rather than weakens, the owned Haaland arm's existing **Haaland (C) / Bruno (VC)** order.

- **Entry 8522487:** start Diop ahead of foot-doubtful Van Hecke. João Pedro enters only after a normal-minutes clearance.
- **Entry 7337262:** Palmer, Semenyo, Rice, Isak and João Pedro remain at 75%; Obi remains unavailable. Keep Rogers (C) / Raya (VC) until Palmer receives a normal-minutes clearance. Compare transfers, hits and Wildcard only if at least three genuine XI holes survive the final press conferences.

Official FPL shows no owned-player price or availability change. Isak's mutable GW6 estimate has fallen from 5.8 to 3.8, but this is not a medical update. The governed evidence run `composer-2.5:2026-10-05T071500Z` admitted 0 claims and the ledger tip remains `fdc0e882…`.

The automated Kinsky/Cherki/Wissa reconstruction is advisory-only and is not either owned squad.

## Official entry state

GW5 is finished and data checked. The sampled top-1,000 boundary is **414**, re-polled from overall standings page 20.

| entry | arm | GW5 | total | current OR | gap to 414 |
|---|---|---:|---:|---:|---:|
| 8522487 | Haaland | 51 | 292 | 5,200,024 | 122 |
| 7337262 | no Haaland | 43 | 291 | 5,320,504 | 123 |

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
| official FPL bootstrap, fixtures and entry endpoints | observed 2026-10-05T07:25:52Z | no owned price/status change; deadline and public entry state current |
| Manchester City international roundup | published 2026-10-04T22:00:00Z | Haaland started and played 67 minutes; available with moderated workload |
| UEFA full-time report, Portugal 2-1 Norway | published 2026-10-04T23:59:07CET | Bruno started and was replaced in stoppage time; Haaland replaced at 67; no match-recorded injury substitution |
| Manchester City England roundup | published 2026-10-03T18:18:49Z | Guéhi 90 minutes; Anderson 79 minutes; positive availability plus workload |
| Liverpool Isak update | published 2026-09-27 | minor injury; returned for club assessment; no newer dated Liverpool clearance found |
| governed evidence ledger | observed 2026-10-05T07:15:00Z | 0 admits; tip unchanged `fdc0e882…` |
| decision packet | checkpoint 2026-08-11 | stale for live squads and availability; methodology context only |
| repository X community digest | observed 2026-10-02T08:15Z | challenge input only; no claim promoted |

No dated club publication after the prior cutoff clears Palmer, Semenyo, Rice, Isak, João Pedro, Van Hecke or van Ewijk. Silence is not a clearance. England play Czechia on 6 October, so Guéhi, Anderson, Rogers and Gibbs-White remain workload monitors.

Official FPL's mutable GW6 estimates include Haaland 8.0, Mitchell 7.7, Van Hecke 5.5, Semenyo 6.5, Guéhi/Raya 6.0, Rogers 5.3, Isak 3.8 and Bruno 2.0. These are directional game estimates, not medical evidence.

## Community challenge review

- RotoWire/Copilot Bruno-versus-Haaland captain framing: **retain Haaland (C)** for the owned Haaland arm; Haaland played fewer Sunday minutes and remains the safer leadership choice.
- WC6 drafts: **reject as default**; compare only if at least three owned holes survive the final pressers.
- Palmer KEEP and João Pedro specialist-treatment/ownership discussion: **defer**; none supplies an admissible return date.
- Bogle into Arsenal away and speculative differential defenders: **reject as actionable today**.

## Provisional GW6 teams

### 8522487 — Haaland arm

Verbruggen  
Mitchell, Castagne, Diop  
B.Fernandes, Gibbs-White, E.Le Fée, Dewsbury-Hall, Xhaka  
Thiago, Haaland

- Captain: **Haaland**
- Vice-captain: **B.Fernandes**
- Bench: Dubravka; 1 João Pedro, 2 Van Hecke, 3 van Ewijk
- If João Pedro receives a normal-minutes clearance, start him over Xhaka.
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

- **GW6:** wait for Tuesday's final England fixture, recovery reports and club pressers. Preserve transfers unless official evidence creates an XI hole or a clearly superior multiweek repair.
- **GW7:** Man City host Ipswich. Haaland is the probable captain anchor; compare Triple Captain rather than pre-committing. For entry 7337262, calculate the cheapest legal Haaland route only after authenticated free transfers and selling prices are known.
- **GW8:** Chelsea host Spurs and Man Utd host Bournemouth. Reassess Palmer, João Pedro and Bruno roles/minutes; retain premium flexibility.
- **GW9:** Man City host Brighton while Chelsea host Man Utd. Haaland is the early captain favourite; avoid spending transfers now on low-upside bench reshuffling.

## Host handoff

- Account writes: false
- Before the final GW6 recommendation, manually confirm on both authenticated transfer pages: exact free transfers, current bank/team value, purchase and selling prices, pending-transfer state and chip state.
- Owner approval remains required for any FPL action.
- Ledger tip: `fdc0e882…`

