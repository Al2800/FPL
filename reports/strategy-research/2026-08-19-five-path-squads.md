# Five GW1 paths — elevation models, not one “best 15”

**Date:** 19 August 2026  
**Bound packet:** `weekly-2026-08-11` / `65eba1fe…`  
**Decision cutoff:** 2026-08-21T17:30:00Z  
**Account writes:** false. Owner approval still required.

These are five *ways of scoring the same problem*. Paths A and B are the
frozen optimiser arms (11 August published objectives). Paths C–E are declared
alternatives, rules-validated in `scripts/score_five_path_initial_squads.py`
and host-rescored on 19 August in
`scripts/host_rescore_five_path_squads.py`.

Prices are the 11 August packet / current bootstrap figures used in the
18 August briefing. Community Shield evidence is used as *path colour*, not
as new expected-points.

The 11 August bound packet (`65eba1fe…`) is local-only and was not on this
machine. The 19 August host scores below are a **cutoff-safe reconstruction**
(`53b88960…`, `live-faithful-v1.feature-complete`, official FDR team prior,
no Understat, no availability blend). Same-packet deltas use reconstructed A,
not the published 240.72. C’s 12 August bound robust score (215.71) remains
the only `65eba1fe…` number for that 15.

---

## The five elevations

| Path | Model of the problem | What it maximises | What it refuses |
|---|---|---|---|
| **A Tight EP** | Robust optimiser (`uncertainty_penalty` 0.35) | Six-GW EP after shrinkage and start-risk | Haaland; cheap non-playing bench as a thesis |
| **B Loose EP** | Deterministic optimiser (penalty 0.0) | Raw six-GW point forecast | The same, but will spend on Nunes/Beto if the mean likes them |
| **C Premium override** | Current advisory | Haaland *and* Bruno ownership | ~25 packet-EV; a playing bench; BB1 |
| **D Death-zone spine** | Mid-price engine | The £6.5–8.5 band (Semenyo, MGW, JP, Thiago, Wilson) as the team | The £15.5 hole *and* £4.0 lottery enablers |
| **E Minutes-first** | Start probability over upside | Likely starters (Raya, Virgil, Xhaka not Wilson) | Haaland rust; Diop/van Ewijk; Obi |

ADR-0006 already says the default is balanced and the conservative /
aggressive alternatives should sit beside it. A is conservative. B is the
loose mean. C is the current balanced-aggressive override. D is a structural
alternative (BB-shaped). E is a minutes / low-variance alternative.

---

## The five teams

### A — Tight expected points (robust)

**Objective 240.72** · SHA `eafe0eda…` · £100.0 · Bruno (C), Semenyo (VC)

| Pos | Players |
|---|---|
| GKP | Raya £6.0 (XI), Donnarumma £5.5 (bench) |
| DEF | Virgil £6.5, Tarkowski £6.0, Van Hecke £5.0, Truffert £5.5, Mitchell £4.5 |
| MID | Bruno £12.0, Semenyo £8.5, Gibbs-White £8.0, Wilson £6.5, E.Le Fée £6.0 |
| FWD | Thiago £8.0, João Pedro £7.5, Obi £4.5 |

XI 3-5-2: Raya; Tarkowski, Virgil, Van Hecke; Bruno, Gibbs-White, Semenyo, Le Fée, Wilson; Thiago, João Pedro.  
Bench: Donnarumma, Mitchell, Truffert, Obi.

**Read:** the lab’s uncertainty-aware “do not buy Haaland” answer. City exposure is Semenyo + Donnarumma, which Community Shield *supports* (Semenyo 90). Obi is the price of the premium defence; he is not a BB pick.

### B — Loose expected points (deterministic)

**Objective 244.24** · SHA `56c936de…` · £100.0 · Bruno (C), Semenyo (VC)

| Pos | Players |
|---|---|
| GKP | Raya, Donnarumma |
| DEF | Virgil, Tarkowski, **Matheus N. £6.0**, Truffert, Mitchell |
| MID | Bruno, Semenyo, Gibbs-White, Wilson, Le Fée |
| FWD | João Pedro, **Calvert-Lewin £6.0**, **Beto £5.5** |

XI 3-5-2: Raya; Tarkowski, Virgil, Matheus N.; Bruno, Gibbs-White, Semenyo, Le Fée, Wilson; João Pedro, Calvert-Lewin.  
Bench: Donnarumma, Mitchell, Truffert, Beto.

**Read:** the highest published number. It is also the most dated: the 18 August briefing notes Matheus Nunes is bootstrap **`d` (75%)**. Three City players (Donnarumma, Semenyo, Nunes) sit on the club cap. Treat B as the loose-EP *shape*, not as a team to type in tomorrow.

### C — Premium override (current advisory)

**12 Aug bound packet: 215.71 robust / 220.01 det** (−25 / −24 vs A/B). **19 Aug reconstruction: 234.32 robust / 238.61 det** (−17.21 vs reconstructed A) · £99.5 · Bruno (C), Haaland (VC)

| Pos | Players |
|---|---|
| GKP | Verbruggen £4.5, Dubravka £4.0 |
| DEF | Van Hecke, Mitchell, Shaw £4.5, **Diop £4.0**, **van Ewijk £4.0** |
| MID | Bruno, Gibbs-White, Le Fée, Wilson, Xhaka £5.5 |
| FWD | **Haaland £15.5**, João Pedro, Thiago |

XI 3-4-3: Verbruggen; Van Hecke, Mitchell, Shaw; Bruno, Gibbs-White, Le Fée, Wilson; Haaland, João Pedro, Thiago.  
Bench: Dubravka, Xhaka, Diop, van Ewijk.

**Read:** the live briefing since 12 August. Community Shield said Haaland *starts* and is *minutes-managed*. You pay for that with a dead bench and no BB. This is a rank-protection / FOMO path, not an EP path.

### D — Death-zone spine (playing 15)

**19 Aug reconstruction: 240.28 robust / 244.28 det** (−11.25 vs reconstructed A) · £98.0 / £2.0 ITB · declared Bruno (C), Semenyo (VC); host-optimal C/VC Bruno / Gibbs-White

| Pos | Players |
|---|---|
| GKP | Verbruggen, **Kinsky £4.5** |
| DEF | Van Hecke, Tarkowski, **Calafiori £5.5**, Truffert, Shaw |
| MID | Bruno, Semenyo, Gibbs-White, Le Fée, Wilson |
| FWD | João Pedro, Thiago, Calvert-Lewin |

XI 3-4-3: Verbruggen; Van Hecke, Tarkowski, Calafiori; Bruno, Semenyo, Gibbs-White, Le Fée, Wilson; João Pedro, Thiago.  
Bench: Kinsky, Shaw, Truffert, Calvert-Lewin.

**Read:** the mid-price band *is* the team. No Haaland, no £4.0 enablers. Shield-coloured (Calafiori, Semenyo 90, Kinsky as the Spurs No.1 hypothesis). £2.0 left can become Virgil, Raya, or Mbeumo after Thursday pressers. Host-optimal GW1 on the reconstruction is **3-5-2 with Calvert-Lewin benched**, so the declared 3-4-3 is not what the scorer starts. **BB1 is only legal as a conversation if** Kinsky, Calafiori and Calvert-Lewin are confirmed starters — do not pre-commit.

### E — Minutes-first

**19 Aug reconstruction: 247.51 robust / 250.85 det** (−4.02 vs reconstructed A) · £99.0 / £1.0 ITB · declared Bruno (C), Semenyo (VC); host-optimal C/VC Bruno / Gibbs-White

| Pos | Players |
|---|---|
| GKP | Raya, Donnarumma |
| DEF | Virgil, Van Hecke, Truffert, Shaw, Mitchell |
| MID | Bruno, Semenyo, Gibbs-White, Le Fée, **Xhaka** (Wilson out) |
| FWD | Thiago, João Pedro, Calvert-Lewin |

XI 3-5-2: Raya; Virgil, Van Hecke, Shaw; Bruno, Semenyo, Gibbs-White, Le Fée, Xhaka; Thiago, João Pedro.  
Bench: Donnarumma, Mitchell, Truffert, Calvert-Lewin.

**Read:** throw away upside that depends on a 0.25–0.73 start. No Haaland rust, no Diop, no van Ewijk, no Obi. Wilson’s role risk is the first thing this path deletes. Closest in spirit to A, and on the 19 August reconstruction it is the **closest scored alternative** (−4.02 vs A).

---

## Side-by-side

| | A Tight | B Loose | C Premium | D Death-zone | E Minutes |
|---|---|---|---|---|---|
| Published 11 Aug objective | **240.72** | **244.24** | **215.71** | — | — |
| 19 Aug reconstructed robust | **251.53** | unscored (Nunes `d`) | 234.32 | 240.28 | 247.51 |
| Δ vs reconstructed A | 0 | — | **−17.21** | **−11.25** | **−4.02** |
| Haaland | no | no | **yes** | no | no |
| Semenyo | yes | yes | no | yes | yes |
| Premium GK pair | yes | yes | no | no | yes |
| £4.0 enablers | no (Obi 4.5) | no | **Diop, van Ewijk, Dubravka** | no | no |
| Playing-15 / BB1 | no | no | no | **maybe** | weak maybe |
| City count | 2 | **3** | 1 | 1 | 2 |
| Main live risk | Obi blank | Nunes `d` | Haaland minutes + dead bench | Kinsky / DCL / Calafiori XI | Xhaka ceiling |
| Chip | hold | hold | hold | hold unless XI-confirmed BB | hold |

Shared core across all five: **Bruno captain, Gibbs-White, Le Fée, João Pedro**. Those are not the decision. The decision is Haaland vs Semenyo+defence, and whether the bench is allowed to be junk.

---

## How to use this before Friday

1. If you want the **lab’s statistical recommendation**, pick **A**. B cannot even be host-scored on the 19 August bootstrap: Matheus Nunes is official-status `d` and is excluded from the packet.
2. If you want the **current briefing**, you are already on **C**. The 12 August bound haircut was ~25 points; the 19 August reconstruction still leaves C last among scored paths (−17.21 vs A). Rank-protection / FOMO, not EP.
3. If the last two days of “look at the rest of the 15” pulled you away from City-only thinking, **D** is the rebuild: keep the mid-price spine, add Semenyo and a playing defence, leave Haaland. It still trails A by ~11 reconstructed points.
4. If you are losing sleep over Wilson / Diop / Haaland minutes, **E** is the calmer no-Haaland side and the smallest scored haircut (−4.02).
5. Do not average them. Averaging C and A produces an illegal or incoherent 15.

Thursday–Friday falsifiers that flip a path, not a player:

- Official City “Haaland managed again” → leave C, move to A or E.
- Official Spurs Kinsky + Leeds Wilson/DCL + Arsenal Calafiori → D becomes the BB conversation.
- Official Bruno limit → every path changes captain first; C may lose its reason to exist.

Validation artefact: `reports/strategy-research/2026-08-19-five-path-squads.json`.  
Host-score artefact: `reports/strategy-research/2026-08-19-five-path-host-score.md`.  
All five squads and lineups passed `validate_squad` / `validate_lineup` on ruleset `2026-27-v1.0`.
