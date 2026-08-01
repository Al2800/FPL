# Daily FPL strategy decision — 2026-08-01

- observed_at: 2026-08-01T13:53:00Z
- model: Grok 4.5
- role: primary_advisory_decision_arm
- prompt: prompts/daily-strategy-research/v1.md
- bound_packet_sha256: 56275b67ebcf6f57771287e5e17608ca18fc080f2665e2ed316677698fa91905
- deterministic comparator present: yes (identical to robust after Understat wiring)
- official discovery: degraded (Lane A not re-run for every catalogue club_id in this dry-run; ledger/availability context taken from enablement note only)
- decision_confidence: medium — live_faithful_degraded packet; `event_model_weight=0.0` (player Understat xG/xA does not move EP); WC fatigue enters optimiser weights after forecast; Furo is a non-minutes enabler; Semenyo City identity verified on web but minutes still Pep/Maresca-rotation risk

## Decision summary (final advisory)

- Chip path: BB1 / FH3 / WC7 (BB1 only if the 4.5 FWD slot is upgraded to a minutes-backed option before deadline; otherwise hold BB for the post-WC7 rebuild)
- Squad thesis in one sentence: Pay the Haaland tax for captaincy insurance and early promoted homes, keep Bruno + Semenyo as the City/United attack spine, fund it with DEFCON-leaning cheap defenders and mid-price depth — overriding the robust arm’s fatigue-weighted Haaland omission without claiming he will not start.
- Key falsifiers (what would change this tomorrow): official City XI/minutes news that Semenyo is clearly rotated; Haaland or Bruno availability flag from a registered club/PL source; pre-season evidence that Kayode/Cash/Mitchell lose starts; a playable 4.5–5.0 FWD appearing that makes BB1 coherent without Furo; FH/BGW calendar resolving away from GW3.

## Recommended 15

| pos | player | club | price | role (XI/bench) | why |
|---|---|---|---|---|---|
| GKP | Raya | ARS | 6.0 | XI | Highest GKP 6GW EP in packet; dual-keeper BB path with Donna |
| GKP | Donnarumma | MCI | 5.5 | bench | Playable second keeper; City slot 1/3 with Semenyo + Haaland |
| DEF | Tarkowski | EVE | 6.0 | XI | DEFCON-friendly CB; high start_p in packet; follow comparator |
| DEF | Shaw | MUN | 4.5 | XI | Cheap United minutes + early fixtures; follow comparator |
| DEF | Mitchell | CRY | 4.5 | XI | High start_p (~0.81); restores pre-wiring cheap DEF depth |
| DEF | Kayode | BRE | 4.5 | bench | Packet start_p ~0.83 at 4.5 — better BB/autosub than dead DEF |
| DEF | Cash | AVL | 4.5 | bench | Playing-price enabler for BB depth; fixture-flexible |
| MID | B.Fernandes | MUN | 12.0 | XI | Premium mid; GW1–2 promoted fixtures; follow comparator core |
| MID | Semenyo | MCI | 8.5 | XI | #3 raw 6GW EP; City attack coverage without a second City DEF |
| MID | Szoboszlai | LIV | 7.0 | XI | Template mid-price; follow comparator |
| MID | Groß | BHA | 5.5 | XI | Value mid with multiple routes; pre-wiring robust favourite |
| MID | Ampadu | LEE | 5.5 | bench / cover | High start_p (~0.81) at 5.5; funds Haaland without 4.5 mid fodder |
| FWD | Haaland | MCI | 15.5 | XI (C) | #1 raw 6GW EP; override robust fatigue omission — see premiums |
| FWD | Calvert-Lewin | LEE | 6.0 | XI | Follow comparator third-forward band; playable vs Furo |
| FWD | Furo | BRE | 4.5 | bench | Enabler only (start_p≈0.05) — not a minutes claim |

ITB 0.0 / 100.0 spent (host must revalidate budget, formation and three-per-club).

**Semenyo identity:** Bootstrap lists Semenyo at Man City (club 15). Web evidence confirms the Jan 2026 Bournemouth→City transfer (BBC Sport / Premier League club notices). Treat as City asset; residual uncertainty is **minutes/rotation**, not club identity.

## GW1 XI, captain, vice, bench order

- XI (3-5-2): Raya — Tarkowski, Shaw, Mitchell — B.Fernandes, Semenyo, Szoboszlai, Groß, Ampadu — Haaland, Calvert-Lewin
- Captain / vice: Haaland / B.Fernandes (packet gw1_ep 7.47 vs 7.20; Bruno remains the GW1–2 fixture captaincy challenger if City sharpness looks poor in pre-season)
- Bench (1→4): Donnarumma → Kayode → Cash → Furo

## Chip and transfer path

- Preferred path: **BB1 / FH3 / WC7**
  - **BB1:** Dual playable keepers + cheap DEF depth supports early BB (official Scout and community drafts still float GW1/GW2 BB). **Blocked in spirit by Furo** (start_p≈0.05). If Furo remains, do **not** force BB1 — hold BB for immediately after WC7 when the bench can be rebuilt with starters.
  - **FH3:** Targets City’s home vs Coventry (promoted) and/or a one-week attack stack without committing the Wildcard; aligns with early TC/FH debate around Haaland’s first promoted home.
  - **WC7:** Structural rebuild into the next fixture swing and City’s home vs Ipswich; natural window for TC7 on Haaland if owned, or to rebalance DEFCON/template drift. Matches community “early WC but not panic-GW2” banding (roughly GW4–8).
- Alternatives rejected:
  - **Pure robust/no-Haaland + BB1:** Maximises bench legality stress-test but fades ~70%+ ownership and the packet’s top raw EP without an availability veto — too large an early rank risk for this arm.
  - **Haaland + Bruno + Mbeumo triple United without Semenyo:** Viable, but Semenyo’s packet EP and City attack prior after Understat wiring outrank Mbeumo on this freeze.
  - **Save all chips for DGW/BGW only:** Sound for H2, but first-half chips expire; an intentional early BB/FH/WC sequence is still the majority opening plan in community guides.
- FT-rolling / early-WC pressure: With Haaland + Bruno locked, early price rises on Semenyo/cheap DEFs can force a GW4–8 WC anyway — WC7 is the planned release valve, not a failure state.

## Where this differs from the deterministic / robust arms

Comparator 15 (deterministic = robust on `weekly-2026-08-02` after wiring):  
Raya, Donnarumma, Tarkowski, Matheus N., Shaw, Truffert, Calafiori, Rice, Szoboszlai, Semenyo, B.Fernandes, Mbeumo, Furo, João Pedro, Calvert-Lewin.

- Followed: Raya / Donnarumma dual GK; Tarkowski + Shaw DEFCON/cheap spine; Semenyo + Bruno midfield premiums; Furo as 4.5 FWD enabler pattern; Szoboszlai mid-price; Calvert-Lewin in the forward band.
- Overrode (with reason + citations):
  1. **Haaland in, João Pedro / Matheus N. / Mbeumo / Rice / Truffert / Calafiori out (net restructuring).** Robust omits Haaland because `world_cup_fatigue=1.0` is applied **after** forecast into optimiser weights — not because start_p is low (0.81). Community + official Scout treat Haaland as the GW1 template lock and early TC magnet (promoted homes GW3/GW7). Fading him is a deliberate differential this arm rejects pre-deadline absent availability evidence. Sources: Premier League Scout must-haves; FPL Pilot template ownership (~73%); fpl.page note that Norway’s QF exit left enough rest for GW1 sharpness (untrusted blog — used only as debate, not ledger).
  2. **City three: Donna + Semenyo + Haaland** — drops Matheus N. so Haaland fits the club cap; prefers City attack over City DEF given Understat attack/defence team priors and Haaland’s EP lead.
  3. **Rice out** — packet WC fatigue 0.7 plus community GW1 England-return doubt; replace with Ampadu/Groß value rather than force Arsenal mid minutes.
  4. **Cheap DEF stack (Mitchell, Kayode, Cash)** — restores pre-wiring DEFCON/enabler logic (previous robust had Mitchell/Mukiele/Truffert) and funds Haaland; Calafiori start_p ~0.56 is a minutes risk this arm will not pretend is nailed.
- Could not verify against packet: exact BB1 EV vs post-WC BB; true GW1 line-ups; whether Cash/Kayode remain starters through August; player-level Understat xG impact (still weight 0).

**Understat / ClubElo team-context vs Haaland call:** Wiring replaces FDR with prior-season Understat attack/defence multipliers (+ optional ClubElo expected-result scores). That can modestly re-rank **team** attack/defence context (and helped move the robust 15 toward City/United assets vs the pre-wiring example). It does **not** move player xG/xA into EP while `event_model_weight=0.0`, and it does **not** remove Haaland’s post-forecast fatigue weight. Net: team-context wiring **does not reverse** the advisory Haaland-long call; if anything it is weakly supportive of keeping City attack (Haaland/Semenyo) rather than City DEF. The Haaland decision remains a **sharpness / opportunity-cost / ownership** judgement, not a non-start claim.

Pre-wiring robust example (contrast only): Raya, Donnarumma, Mitchell, Tarkowski, Virgil, Mukiele, Truffert, Groß, Wilson, Semenyo, B.Fernandes, Gibbs-White, Thiago, João Pedro, Obi — more Forest/Liverpool/Brentford mid-fwd balance, still no Haaland.

## Premium / DEFCON / minutes calls

- **Haaland: LONG from GW1.** Highest 6GW EP (44.82); start_p≈0.81; fatigue flag explains robust omission via optimiser weights. Issue is opportunity cost of £15.5m and early sharpness, not inventing a benching. Plan TC hooks at GW3 COV (H) and/or GW7 IPS (H) if form confirms.
- **Bruno: LONG.** Follow comparator; GW1–2 promoted run is the early captaincy alternative.
- **Semenyo: LONG as City MID.** Identity confirmed; minutes are the open risk (rotation in a deep City attack) — reassess by GW3–4.
- **Cheap DEF / DEFCON:** Tarkowski + Shaw core; Mitchell/Kayode/Cash as high start_p enablers. Prefer CBs/full-backs with packet start_p over status=`a` alone. Maguire-type low start_p premiums avoided despite DEFCON reputation.
- **Furo:** Enabler only. Obi is similarly ~0.05 start_p — swapping enablers does not fix BB1.
- **One-week punts / reassess:** Ampadu/Groß/Cash by GW3; Semenyo role by GW4; early WC pressure crystallises GW5–7 if Haaland blanks and mid-prices climb.

## Official leads (Lane A) worth citation

- Degraded this run — no fresh per-club catalogue scrape. Prior governed context only:
  1. Launch-context / WC priors admitted on checkpoint `weekly-2026-08-02` (Haaland fatigue 1.0 intentional in weights).
  2. Availability ledger note: Haaland omitted from doubtful list on purpose (enablement log).
  3. Premier League fixture/chip explainers (public FPL editorial) for BB early / TC on promoted homes — treat as official editorial, not live availability.
- Max 12 not filled; host should not promote community URLs into the evidence ledger.

## Citations (Lane B)

- Premier League / The Scout — https://www.premierleague.com/en/news/4681709/the-scouts-must-haves-for-start-of-202627-fpl — Haaland & Bruno must-haves, João Pedro ownership
- Premier League — https://www.premierleague.com/en/news/4675553/why-fernandes-and-haaland-look-like-must-haves-to-start-202627-fpl — fixtures, Semenyo/Cherki/City value, United doubles
- Premier League — https://www.premierleague.com/en/news/4679879/whats-happening-with-fpl-chips-in-202627 — BB1/early BB, TC on Haaland vs promoted, FH for blanks
- BBC Sport — https://www.bbc.co.uk/sport/football/articles/c801yv529z7o — Semenyo→Man City transfer (~Jan 2026)
- Premier League — https://www.premierleague.com/en/news/4515794/man-city-sign-semenyo-from-bournemouth — club identity confirmation
- FPL Pilot — https://www.fplpilot.com/blog/fpl-template-team-2026-27 — Haaland ~73% OW template; Bruno/Szobo core
- Fantasy Football Fix — https://www.fantasyfootballfix.com/blog-index/fpl-template-team-2026-27/ — early template Haaland/Bruno/Pedro/Szobo
- FPL Dashboard — https://fpl.page/article/fpl-chip-strategy-guide-2627 — BB1 vs post-WC BB; FH around early City/promoted weeks
- FPL Dashboard — https://fpl.page/article/fpl-gw1-absent-injured-missing-players-world-cup-2627 — Haaland GW1 rest narrative (untrusted; debate only)
- Onside — https://onsidearena.com/tips/fpl-wildcard-draft-2026-27 — WC GW4–8 banding; avoid panic GW2 WC
- Full90 FPL — https://full90fpl.com/haaland-bruno-gabriel-26-27/ — Haaland±Bruno premium trade-offs; early BB drafts
- All About FPL — https://allaboutfpl.com/2026/07/fpl-rotational-pairs-combinations-for-the-2026-27-fpl-season/ — DEFCON cheap DEF rotations (Shaw/Mitchell/Tarkowski patterns)

## Host handoff

- Declare this 15 for rules validation + rescoring against the frozen packet `56275b67ebcf6f57771287e5e17608ca18fc080f2665e2ed316677698fa91905` (checkpoint `weekly-2026-08-02`)
- Account writes: false
- Owner approval still required before any FPL entry
- LLM proposes only; approval gate uncleared; rules remain data in `control/rules/`
