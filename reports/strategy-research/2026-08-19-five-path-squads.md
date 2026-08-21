# Five GW1 paths — elevation models, not one “best 15”

**Date:** 19 August 2026  
**Bound packet:** 19 August live-faithful reconstruction `53b88960…`  
**Observed at:** 2026-08-19T13:28:05Z  
**Decision cutoff:** 2026-08-21T17:30:00Z  
**Account writes:** false. Owner approval still required.

These are five *ways of scoring the same problem* on **today’s** packet.
Paths A and B are the optimiser arms re-run on this packet. Paths C–E are
declared alternatives, rules-validated and host-scored against it.

The 11 August packet is not used. Prices, status and six-GW vectors are
from the 19 August official bootstrap plus the committed live-faithful
prior (official FDR team prior; no Understat; no availability blend).
Community Shield evidence is path colour, not a new expected-points layer.

Limitations that still sit on this packet: launch-context enrichment was
not admitted, so World Cup / new-signing shrinkage inside the forecaster
is off; Guehi / Rogers / Anderson therefore enter A/B unshrunk.

---

## The five elevations

| Path | Model of the problem | What it maximises | What it refuses |
|---|---|---|---|
| **A Tight EP** | Robust optimiser (`uncertainty_penalty` 0.35) | Six-GW EP after shrinkage and start-risk | Haaland; cheap non-playing bench as a thesis |
| **B Loose EP** | Deterministic optimiser (penalty 0.0) | Raw six-GW point forecast | The same, without Semenyo; Nunes is out of the packet (`d`) |
| **C Premium override** | Current advisory | Haaland *and* Bruno ownership | ~21.6 packet-EV vs A; a playing bench; BB1 |
| **D Death-zone spine** | Mid-price engine | The £6.5–8.5 band as the team | The £15.5 hole *and* £4.0 lottery enablers |
| **E Minutes-first** | Start probability over upside | Likely starters (Raya, Virgil, Xhaka not Wilson) | Haaland rust; Diop/van Ewijk; Obi |

---

## The five teams

### A — Tight expected points (robust)

**Objective 255.88** · SHA `3a937776…` · £100.0 · Bruno (C), Rice (VC)

| Pos | Players |
|---|---|
| GKP | Raya £6.0 (XI), Pickford £5.5 (bench) |
| DEF | Virgil £6.5, Tarkowski £6.0, **Guéhi £6.0**, **Senesi £6.0**, Mitchell £4.5 |
| MID | Bruno £12.0, Semenyo £8.5, **Rice £7.5**, **Rogers £7.5**, **Anderson £6.5** |
| FWD | João Pedro £7.5, Beto £5.5, Obi £4.5 |

XI 4-5-1: Raya; Guéhi, Virgil, Senesi, Tarkowski; Bruno, Rice, Semenyo, Rogers, Anderson; João Pedro.  
Bench: Pickford, Mitchell, Beto, Obi.

**Read:** today’s uncertainty-aware “do not buy Haaland” answer. City exposure is Guéhi + Semenyo + Anderson (club cap). Obi/Beto are the price of that midfield; this is not a BB pick.

### B — Loose expected points (deterministic)

**Objective 258.96** · SHA `e94a9b0e…` · £100.0 · Bruno (C), Gibbs-White (VC)

| Pos | Players |
|---|---|
| GKP | Raya, Donnarumma |
| DEF | Virgil, Tarkowski, Guéhi, Senesi, Van Hecke |
| MID | Bruno, Gibbs-White, Rice, Rogers, Anderson |
| FWD | João Pedro, Beto, Obi |

XI 4-5-1: Raya; Guéhi, Virgil, Senesi, Tarkowski; Bruno, Gibbs-White, Rice, Rogers, Anderson; João Pedro.  
Bench: Donnarumma, Van Hecke, Beto, Obi.

**Read:** the highest number on today’s packet. It drops Semenyo for Gibbs-White and swaps Pickford/Mitchell for Donnarumma/Van Hecke. Matheus Nunes is official-status `d` and is not in the packet, so he cannot appear.

### C — Premium override (current advisory)

**Host-scored today: 234.32 robust / 238.61 det** (−21.56 / −20.36 vs A/B) · £99.5 · Bruno (C), Haaland (VC)

| Pos | Players |
|---|---|
| GKP | Verbruggen £4.5, Dubravka £4.0 |
| DEF | Van Hecke, Mitchell, Shaw £4.5, **Diop £4.0**, **van Ewijk £4.0** |
| MID | Bruno, Gibbs-White, Le Fée, Wilson, Xhaka £5.5 |
| FWD | **Haaland £15.5**, João Pedro, Thiago |

XI 3-4-3: Verbruggen; Van Hecke, Mitchell, Shaw; Bruno, Gibbs-White, Le Fée, Wilson; Haaland, João Pedro, Thiago.  
Bench: Dubravka, Xhaka, Diop, van Ewijk.

**Read:** the live briefing 15 since 12 August, scored on today’s packet. You still pay a large six-GW haircut for Haaland + Bruno. Dead bench; no BB.

### D — Death-zone spine (playing 15)

**Host-scored today: 240.28 robust / 244.28 det** (−15.59 / −14.68 vs A/B) · £98.0 / £2.0 ITB · declared Bruno (C), Semenyo (VC)

| Pos | Players |
|---|---|
| GKP | Verbruggen, **Kinsky £4.5** |
| DEF | Van Hecke, Tarkowski, **Calafiori £5.5**, Truffert, Shaw |
| MID | Bruno, Semenyo, Gibbs-White, Le Fée, Wilson |
| FWD | João Pedro, Thiago, Calvert-Lewin |

Declared XI 3-4-3. Host-optimal GW1 on this packet is **3-5-2 with Calvert-Lewin benched**.

**Read:** the mid-price band *is* the team. No Haaland, no £4.0 enablers. It still trails today’s robust A by ~16 points. **BB1 only if** Kinsky, Calafiori and Calvert-Lewin are confirmed starters.

### E — Minutes-first

**Host-scored today: 247.51 robust / 250.85 det** (−8.37 / −8.11 vs A/B) · £99.0 / £1.0 ITB · declared Bruno (C), Semenyo (VC)

| Pos | Players |
|---|---|
| GKP | Raya, Donnarumma |
| DEF | Virgil, Van Hecke, Truffert, Shaw, Mitchell |
| MID | Bruno, Semenyo, Gibbs-White, Le Fée, **Xhaka** |
| FWD | Thiago, João Pedro, Calvert-Lewin |

XI 3-5-2: Raya; Virgil, Van Hecke, Shaw; Bruno, Semenyo, Gibbs-White, Le Fée, Xhaka; Thiago, João Pedro.  
Bench: Donnarumma, Mitchell, Truffert, Calvert-Lewin.

**Read:** the closest *declared* alternative to today’s A (−8.37). It is not the optimiser 15: A prefers Rice/Rogers/Anderson/Guéhi over Xhaka/Truffert/Shaw.

---

## Side-by-side (19 August packet)

| | A Tight | B Loose | C Premium | D Death-zone | E Minutes |
|---|---|---|---|---|---|
| Robust 6-GW objective | **255.88** | 255.63 | 234.32 | 240.28 | 247.51 |
| Deterministic 6-GW | 259.12 | **258.96** | 238.61 | 244.28 | 250.85 |
| Δ vs A robust | 0 | −0.25 | **−21.56** | **−15.59** | **−8.37** |
| Haaland | no | no | **yes** | no | no |
| Semenyo | yes | no | no | yes | yes |
| City count | **3** (Guéhi, Semenyo, Anderson) | **3** (Donnarumma, Guéhi, Anderson) | 1 | 1 | 2 |
| £4.0 enablers | no (Obi 4.5) | no (Obi 4.5) | **Diop, van Ewijk, Dubravka** | no | no |
| Chip | hold | hold | hold | hold unless XI-confirmed BB | hold |

Shared across C–E still: **Bruno captain, Gibbs-White, Le Fée, João Pedro**. A/B on today’s packet keep Bruno and João Pedro but replace the old mid-price spine with Rice / Rogers / Anderson / Guéhi / Senesi.

---

## How to use this before Friday

1. If you want **today’s statistical recommendation**, pick **A**. B is the looser mean on the same packet; it does not include Nunes.
2. If you want the **current briefing 15**, you are on **C**. That is now a ~22-point six-GW haircut vs today’s A, not the old 11 August −25 vs a different 15.
3. **D** is still the mid-price rebuild; it trails A by ~16.
4. **E** is the smallest declared haircut (−8.37) if you do not want A’s City triple or Rice/Rogers.
5. Do not average them.
6. If the rule is **no pounds left in the bank**, spend C/D/E up (see below). A and B already spend £100.0.

## If we spend the leftover ITB

Same packet, same 15 slots, leftover bank forced into same-position upgrades.
Full write-up: `reports/strategy-research/2026-08-19-five-path-spend-up.md`.

| Path | Bank | Forced spend | Robust after | Δ vs that path |
|---|---:|---|---:|---:|
| A | 0.0 | already £100.0 | 255.88 | 0 |
| B | 0.0 | already £100.0 | 255.63 | 0 |
| C | 0.5 | Diop → Disasi | 236.52 | +2.20 |
| D | 2.0 | Kinsky → Raya; Calafiori → Guéhi | 251.74 | **+11.45** |
| E | 1.0 | Truffert → Senesi; Le Fée → Anderson | 252.46 | +4.95 |

D’s leftover is the only pile large enough to matter — and spending it buys A’s premiums, so it is no longer the death-zone 15. E’s £1.0 is the cleanest declared spend and becomes the closest alternative to A (252.46 vs 255.88). C’s £0.5 cannot fix Haaland’s haircut.

Falsifiers:

- Official City minutes cap on Guéhi / Anderson / Semenyo → A’s club-cap stack breaks; rebuild without the third City.
- Official Haaland-managed-again → leave C.
- Official Spurs Kinsky + Leeds / Arsenal XIs → D’s BB conversation.

Validation artefact: `reports/strategy-research/2026-08-19-five-path-squads.json`.  
Host-score artefact: `reports/strategy-research/2026-08-19-five-path-host-score.md`.  
Spend-up artefact: `reports/strategy-research/2026-08-19-five-path-spend-up.md`.  
All five squads and lineups passed `validate_squad` / `validate_lineup` on ruleset `2026-27-v1.0`.
