# Live-entry decision input — 2026-09-23

- observed_at: 2026-09-23T07:52:15Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST)
- scope: public entries 8522487 and 7337262
- authority: official FPL entry, history, picks, live and bootstrap endpoints
- account writes: false
- decision state: live_faithful_degraded

## Executive decision

There is **no material decision change** from 2026-09-22. Make no early transfer and activate no chip during the international break. The official-news lane found no new admissible club claim, while all four owned availability flags remain unchanged.

The automated strategy report in this branch is not authoritative for these entries. Its Kinsky/Cherki/Wissa reconstruction and one-free-transfer statement conflict with the official completed-GW picks or rely on private state that is not publicly exposed.

## Official entry state

GW5 is finished and data checked.

| entry | experiment arm | GW5 | total | current OR | sampled top-1k threshold | gap |
|---|---|---:|---:|---:|---:|---:|
| 8522487 | Haaland | 51 | 292 | 5,200,393 | 414 | 122 |
| 7337262 | no Haaland | 43 | 291 | 5,320,881 | 414 | 123 |

The small rank movement since 2026-09-22 is non-material. Entry summaries publicly expose the last-deadline value and bank, not the live authenticated transfer state:

| entry | last-deadline value | bank | chip history |
|---|---:|---:|---|
| 8522487 | £99.6m | £0.2m | none |
| 7337262 | £99.8m | £0.0m | none |

GW5 transfers were Shaw to Castagne for 8522487 and Maatsen to Castagne for 7337262. No-Haaland's Truffert autosub for João Pedro is confirmed.

## Authoritative live squads

### Entry 8522487, Haaland

Verbruggen; Dubravka  
Van Hecke; Mitchell; Castagne; Diop; van Ewijk  
B.Fernandes; Gibbs-White; E.Le Fée; Dewsbury-Hall; Xhaka  
Thiago; Haaland; João Pedro

### Entry 7337262, no Haaland

Raya; Verbruggen  
Gabriel; Guéhi; Castagne; Truffert; Shaw  
Palmer; Rogers; Semenyo; Rice; Anderson  
Isak; João Pedro; Obi

## Availability and freshness

| player | official FPL state | chance next round | news timestamp | freshness / implication |
|---|---|---:|---|---|
| Palmer | doubtful, muscular | 75% | 2026-09-21T13:00:09Z | unchanged; wait for Chelsea |
| Rice | doubtful, unspecified | 75% | 2026-09-21T13:00:08Z | unchanged; wait for Arsenal |
| João Pedro | doubtful, knee | 75% | 2026-09-16T19:00:09Z | stale; no timed Chelsea original found |
| van Ewijk | doubtful, hamstring | 75% | 2026-09-19T16:00:09Z | unchanged; bench-depth risk |
| Obi | unavailable, loan | 0% | 2026-09-14T18:30:08Z | non-playing third forward |
| Shaw | available | 100% | bootstrap current | available cover |
| all other owned players | available | 100% | bootstrap current | no new flag |

The 2026-09-23 repository discovery run searched all clubs but retained zero new official claims inside its 72-hour gate. Manchester City, Manchester United and Premier League retrieval remained partially degraded. This makes the absence of news a hold signal, not proof of fitness.

Current official `ep_next` rose to 9.2 for Haaland, 7.8 for Semenyo and Isak, and 7.2 for Bruno. These are mutable FPL game estimates rather than a frozen independent xP model. They strengthen the existing Haaland captain lean but do not justify an international-break transfer.

## Provisional GW6 decisions

### Entry 8522487

Verbruggen  
Van Hecke; Mitchell; Castagne  
B.Fernandes; Gibbs-White; E.Le Fée; Dewsbury-Hall; Xhaka  
Thiago; Haaland

- Captain: **Haaland**
- Vice-captain: **B.Fernandes**
- Bench: Dubravka; 1 Diop; 2 João Pedro; 3 van Ewijk
- If Chelsea clears João Pedro for normal minutes, start him and provisionally bench Xhaka.
- Transfer/chip: hold. Reassess after international minutes and club press conferences.

### Entry 7337262

Assuming Palmer, Rice and João Pedro recover:

Raya  
Gabriel; Castagne; Guéhi  
Rogers; Palmer; Semenyo; Rice; Anderson  
João Pedro; Isak

- Current risk-adjusted captain: **Rogers**
- Vice-captain: **Palmer**
- Restore Palmer as captain, with Rogers vice-captain, only if Chelsea clears him for normal minutes.
- Bench: Verbruggen; 1 Shaw; 2 Truffert; 3 Obi
- If João Pedro remains out, start Shaw in a 4-5-1.
- If Palmer, Rice and João Pedro all remain doubtful near the deadline, rerun the full transfer-versus-Wildcard comparison.

## Rolling four-Gameweek plan

- GW6: preserve information value through the break. No early transfer or chip.
- GW7: Manchester City versus Ipswich remains the likely Haaland captain focal point. Recalculate the no-Haaland route only with authenticated selling prices and free-transfer count.
- GW8–GW9: keep flexibility around Palmer, Bruno, João Pedro and premium structure. Do not pre-commit a Wildcard or hit schedule from current flags.
- Chip threshold: Wildcard only if late official evidence leaves at least three structural problems. Free Hit and Triple Captain remain unjustified today.

## Community challenge review

The 2026-09-22 community digest was reviewed. Price-rise discussion around Schade and Hall, unverified Ben White/Lavia availability claims, Wildcard drafts, and the model suggestion of Semenyo to Saka plus João Pedro to Barry are challenge inputs only. None has official support sufficient to change either live-entry decision.

## Manager-state degradation

Public endpoints cannot verify pending transfers, exact free transfers, purchase prices, selling prices or current authenticated team value. Before the GW6 deadline, manually confirm on each transfer page:

1. exact free-transfer count;
2. bank and current team value;
3. purchase and selling prices for every proposed mover;
4. whether a pending transfer exists;
5. chip availability and intended chip state.

No FPL account change was executed.

## Sources

- Official FPL bootstrap: https://fantasy.premierleague.com/api/bootstrap-static/
- Official entry 8522487: https://fantasy.premierleague.com/api/entry/8522487/
- Official entry 7337262: https://fantasy.premierleague.com/api/entry/7337262/
- Official GW5 picks: https://fantasy.premierleague.com/api/entry/8522487/event/5/picks/ and https://fantasy.premierleague.com/api/entry/7337262/event/5/picks/
- Official histories: https://fantasy.premierleague.com/api/entry/8522487/history/ and https://fantasy.premierleague.com/api/entry/7337262/history/
- Official England squad: https://www.englandfootball.com/england/mens-senior-team/squad
