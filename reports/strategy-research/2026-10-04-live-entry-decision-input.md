# Live-entry decision input — 2026-10-04

- observed_at: 2026-10-04T07:38:24Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club and association sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded

## Executive decision

There is **no material decision change**. Make no transfer and activate no chip today.

New official workload evidence from 3 October: Guéhi played 90 minutes, Anderson played 79 minutes and Rogers scored after coming from the bench in England's 7-0 win over Croatia. This supports current availability for those players but adds no injury or GW6 minutes clearance. England play again on 6 October. Haaland and Bruno play for Norway and Portugal on 4 October, so their full-time involvement and any subsequent medical update remain live monitors.

Official FPL shows no overnight owned-player price or availability change. The governed evidence run `composer-2.5:2026-10-04T070133Z` admitted 0 claims and the ledger tip remains `fdc0e882…`.

- **Entry 8522487:** keep Haaland (C) / Bruno Fernandes (VC). Start Diop ahead of foot-doubtful Van Hecke. João Pedro only enters after a normal-minutes clearance.
- **Entry 7337262:** Palmer, Semenyo, Rice, Isak and João Pedro remain at 75%; Obi is unavailable. Keep Rogers (C) / Raya (VC) until Palmer receives a normal-minutes clearance. Compare transfers, hits and Wildcard only if at least three genuine XI holes survive the final press conferences.

The automated Kinsky/Cherki/Wissa reconstruction is advisory-only and is not either owned squad.

## Official entry state

GW5 is finished and data checked. The sampled top-1,000 boundary is **414**, re-polled from overall standings page 20.

| entry | arm | GW5 | total | current OR | gap to 414 |
|---|---|---:|---:|---:|---:|
| 8522487 | Haaland | 51 | 292 | 5,200,042 | 122 |
| 7337262 | no Haaland | 43 | 291 | 5,320,525 | 123 |

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
| official FPL bootstrap, fixtures and entry endpoints | observed 2026-10-04T07:38:24Z | no owned price/status change; deadline and public entry state current |
| Man City: England 7-0 Croatia | published 2026-10-03T18:18:49Z | Guéhi 90 minutes; Anderson 79 minutes; positive availability plus workload |
| England post-match report | published 2026-10-03 | Rogers scored after coming from the bench; positive availability, no GW6 clearance |
| Liverpool Isak update | published 2026-09-27 | minor injury; returned for club assessment; no newer dated Liverpool clearance found |
| Premier League international injury roundup | published 2026-10-03 | Isak thigh and Gakpo ankle concerns retained; no return date |
| governed evidence ledger | observed 2026-10-04T07:01:33Z | 0 admits; tip unchanged `fdc0e882…` |
| decision packet | checkpoint 2026-08-11 | stale for live squads and availability; methodology context only |
| repository X community digest | observed 2026-10-02T08:15Z | challenge input only; no claim promoted |

No dated club or association publication after the prior cutoff clears Palmer, Semenyo, Rice, Isak, João Pedro, Van Hecke or van Ewijk. Silence is not a clearance.

Official FPL's mutable GW6 estimates include Haaland 8.0, Mitchell 7.7, Van Hecke 5.5, Semenyo 6.5, Guéhi/Raya 6.0, Isak 5.8, Rogers 5.3 and Bruno 2.0. These are directional game estimates, not medical evidence.

## Community challenge review

- RotoWire/Copilot Bruno-versus-Haaland captain framing: **retain Haaland (C)** for the owned Haaland arm; the reconstructed advisory 15 does not override the live squad.
- WC6 drafts: **reject as default**; compare only if at least three owned holes survive the final pressers.
- Palmer KEEP and João Pedro ownership discussion: **defer**; neither resolves expected minutes.
- Bogle into Arsenal away and Timber/Vuskovic/Affengruber differentials: **reject as actionable today**.

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
- If João Pedro is unavailable, start Shaw. Rebuild the XI from the actual clearances rather than assuming all five doubts start.
- Transfer/chip: hold; rerun FT/hit/Wildcard only if at least three genuine holes persist.

## Rolling four-Gameweek plan

- **GW6:** wait for the remaining internationals, recovery reports and club pressers. Preserve transfers unless official evidence creates an XI hole or a clearly superior multiweek repair.
- **GW7:** Man City host Ipswich. Haaland is the probable captain anchor; compare Triple Captain rather than pre-committing. For entry 7337262, calculate the cheapest legal Haaland route only after authenticated free transfers and selling prices are known.
- **GW8:** Chelsea host Spurs and Man Utd host Bournemouth. Reassess Palmer, João Pedro and Bruno roles/minutes; retain premium flexibility.
- **GW9:** Man City host Brighton while Chelsea host Man Utd. Haaland is the early captain favourite; avoid spending transfers now on low-upside bench reshuffling.

## Host handoff

- Account writes: false
- Before the final GW6 recommendation, manually confirm on both authenticated transfer pages: exact free transfers, current bank/team value, purchase and selling prices, pending-transfer state and chip state.
- Owner approval remains required for any FPL action.
- Ledger tip: `fdc0e882…`

