# Daily FPL strategy decision — 2026-08-11 (Grok ad-hoc)

- observed_at: 2026-08-11T15:30:00Z
- model: Cursor Grok 4.5 (ad-hoc owner-requested run; normally Composer 2.5)
- role: primary_advisory_decision_arm (one-off; advisory only)
- prompt: prompts/daily-strategy-research/v1.md
- bound_packet_sha256: `93e783c3d0d0c4f619e249c3a2433e9fe1b34c70b49f7d2b9cc2873990cbe24e` (TRIAL A `input_packet_sha256`; full-data seal with Understat 2025/26 priors + ClubElo + availability citations + launch context)
- trial_recommendation_hashes:
  - TRIAL A (`world_cup_fatigue_weight=0.25`): recommendation `content_sha256` `974aba7421bede4c3b0dcdafe3d22d667e5aa3fe876f847e276db1348028c332`; selection `content_sha256` `af466fb9892d5e05c6719bfa49529a8097dce294af3c6e0772114212b12faee3`; selected proposal `proposal_sha256` `b2bca8cc056ecef966381ebee5fd888231876cf51a79a4ae76634718503602d9`; deterministic obj `280.316309` / robust obj `276.094376` (same 15)
  - TRIAL B (`world_cup_fatigue_weight=0.0`): recommendation `content_sha256` `f43e691ccc2ce3e1c1a9fb6fafdbbc71a9132f7249b0a18987c7e2923e0fb5d9`; selection `content_sha256` `b2fb866cf0f84f45949571a50ec8f7212b3b91ab3bfef25a528c08a91009b6a7`; selected (robust) proposal `proposal_sha256` `212e2460d7db8c6230397733d64ef577c23c2e138c5f53f023c389b3c5683652`; deterministic obj `298.406373` / robust obj `291.817437` (**15s diverge** — see below)
- committed midday packet (poorer; superseded analytically): `reports/strategy-research/packets/weekly-2026-08-11.json` — `input_packet_sha256` `c37b904feea84c45ce2564b32f08aa6c9b0b5642d1dee298a0b00e067defc389` (before Understat land)
- model_evidence_run_id: `composer:2026-08-11T07:02:32Z`
- model_evidence_audit: `data/live-shadow/availability/model-runs/composer:2026-08-11T07:02:32Z.audit.json` (model_run_sha256 `039e09ae3e32d6455be0370b5fb74d07d5276bf52c58105e98b30820e2e60a48`)
- model_evidence_review: `reports/evidence-review/2026-08-11-model-run.md` — **0 claims admitted**
- deterministic comparator present: yes (both trials)
- official discovery: complete (Lane A morning capture; 0 new ledger admits)
- decision_confidence: medium — full-data sealed packet bound; availability blend applied; `world_cup_return_fatigue` family still **unavailable** in gap panel (fatigue enters only via policy weight × launch_context flags); Community Shield (16 Aug) and GW1 PCs still ahead; cloud briefing of 07:02Z superseded

## Decision summary (final advisory)

- Chip path: hold all chips in GW1; roll free transfers; first Wildcard only when early data forces a rebuild (~GW5–8, not locked to WC7); Free Hit for blank/awkward; Bench Boost only when a true 15-man week is nailed (reject default BB1 / Scout BB2+WC3 Coventry-stack until bench evidence exists); Triple Captain held for a DGW unless post-Community Shield Haaland minutes + GW3 home vs Coventry look exceptional
- Squad thesis in one sentence: take the fatigue-aware no-Haaland Trial A 15 (Bruno captain hub + City/United mid attack + mid-price DEFCON/CS mix), treat Trial B’s WC-heavy uplift as a warning that `world_cup_fatigue_weight=0.25` is too blunt rather than proof that fatigue is fake, and keep Haaland as a priced force-in after 16 Aug rather than a day-one lock
- Key falsifiers: Community Shield XI/minutes (16 Aug) for Haaland/Semenyo/Gabriel; host re-seal at fatigue weight ∈ {0.10, 0.12, 0.15} that flips DEF/MID composition; human-admitted ledger claims moving Rice/Gabriel/Virgil/Gravenberch/Calafiori start_p; host-scored Haaland-in under this packet beating Trial A robust by enough to clear EO risk; Spurs/United GK minutes clarifying Lammens vs rivals

## Fatigue-weight recommendation (feeds owner policy decision)

**Recommend `world_cup_fatigue_weight ≈ 0.12` (range 0.10–0.15), not 0.25 and not 0.0.**

| weight | what the sealed trials show | read |
|---|---|---|
| **0.25** (policy v1.0 / Trial A) | det=robust same 15; obj 280.3 → robust 276.1; `context_shrinkage_loss` ≈ 11.70 | Keeps out Gabriel/Virgil/Gravenberch/Thiago; aligns with “late WC return = managed minutes” discourse, but the single scalar is large enough to look like over-shrinkage once Understat+ClubElo priors are in |
| **0.0** (Trial B) | det obj **298.4** pulls Gabriel, Virgil, Gravenberch, Thiago (+ Obi/Truffert/Donnarumma on det); robust selects a different 15 (Lammens, O’Reilly, Welbeck, DCL; benches Virgil) | Proves the 0.25 penalty was binding on WC-tagged assets — but also shows that zeroing fatigue lets the optimiser treat deep-runners as fully fresh, which Scout/BBC/Fix community evidence rejects |
| **Haaland check** | Haaland raw six-GW EP **44.82** (`packet`, #1) yet **absent from both trials** | Exclusion is **budget-displacement**, not fatigue: zeroing the weight still does not buy him in |

Web evidence (Lane B, untrusted; not ledger):

- Scout pre-season: late-stage WC players (England/Argentina/France/Spain) have &lt;5 weeks to GW1; monitor returns and do not force fitness doubts ([premierleague.com](https://www.premierleague.com/en/news/4679613/what-to-look-out-for-in-pre-season-ahead-of-202627-fantasy)).
- BBC: PL starts 33 days after the final; finalists may get only ~12 days of club reintegration after mandatory three-week rest ([bbc.com](https://www.bbc.com/sport/football/articles/c87n3wydzjzo)).
- Fantasy Football Fix: City/Arsenal lead WC minute loads; avoid treating every WC name as equal — minute volume and return date matter ([fantasyfootballfix.com](https://www.fantasyfootballfix.com/blog-index/fpl-2026-27-world-cup-plans/)).
- Gap panel on this seal: `world_cup_return_fatigue` family state **unavailable** (`optional_world_cup_priors_not_supplied`) — so today’s weight is a blunt objective lever on launch_context flags, not a calibrated per-player minutes model.

**What would settle the weight:**

1. Admit player-level WC priors into the `world_cup_return_fatigue` family (gap currently degraded) and re-seal at 0.00 / 0.10 / 0.12 / 0.15 / 0.25.
2. After Community Shield + GW1–3 actual minutes, ablate realised points vs each weight’s selected 15 (especially Gabriel, Rice, Virgil, Gravenberch, O’Reilly, Semenyo).
3. Keep availability citations (Rogers/Guéhi/Senesi/Anderson) as the sharp minutes channel; do not ask the fatigue scalar to also do ledger work.

Until that ablation, **do not ship 0.0 into policy v1.x**. Prefer a mid weight and keep today’s advisory 15 on the Trial A composition (arms agree).

## Recommended 15

Follow **TRIAL A** robust/deterministic 15 (identical). Prices/`packet` from bound seal; bank £0.0.

| pos | player | club | price | role (XI/bench) | why |
|---|---|---|---|---|---|
| GKP | Raya | Arsenal | 6.0 | XI | Packet starter; Arsenal CS floor vs Coventry GW1 |
| GKP | Donnarumma | Man City | 5.5 | bench | City #1 route without forcing City DEF; Scout no-Haaland note prefers him over City CBs for DC reasons (`community`) |
| DEF | Tarkowski | Everton | 6.0 | XI | DEFCON + set-piece floor; arms agree |
| DEF | Matheus N. | Man City | 6.0 | XI | **XI override vs arm** — packet GW1 start_p 0.767 vs Calafiori 0.561; City early fixtures |
| DEF | Shaw | Man Utd | 4.5 | XI | Template £4.5; Hull/Ipswich openers (`community` + `packet`) |
| DEF | Truffert | Bournemouth | 4.5 | bench | High prior minutes / assist volume; pricey for a bench DEF but legal depth |
| DEF | Calafiori | Arsenal | 5.5 | bench | Kept in 15 (arms); benched today on rotation/`packet` start_p — Saliba absence helps Gabriel case more than Calafiori |
| MID | B.Fernandes | Man Utd | 12.0 | XI | Captain hub in no-Haaland structure; Hull A |
| MID | Semenyo | Man City | 8.5 | XI | Vice; pre-season starring role (Lane A discovery, not ledger); high six-GW EP without needing Haaland ownership |
| MID | Mbeumo | Man Utd | 8.0 | XI | United attack double with Bruno; friendly openers; Sesko fitness watch |
| MID | Rice | Arsenal | 7.5 | XI | Packet EP strong; **minutes watch** — England WC load (`community`); not removed because Trial A and six-GW EP still support |
| MID | Szoboszlai | Liverpool | 7.0 | XI | Template mid / pens case; GW1 Newcastle away is the tax |
| FWD | João Pedro | Chelsea | 7.5 | XI | Default non-Haaland premium forward; high EO |
| FWD | Calvert-Lewin | Leeds | 6.0 | XI | Mid-price FWD with packet EP; minutes not nailed — reassessment GW2–3 |
| FWD | Furo | Brentford | 4.5 | bench | Enabler only (`packet` start_p ≈ 0.05) |

Squad cost: £100.0m. Max-3 clubs respected (Arsenal 3, City 3, United 3).

## GW1 XI, captain, vice, bench order

- XI (3-5-2): Raya; Matheus N., Shaw, Tarkowski; B.Fernandes, Semenyo, Mbeumo, Rice, Szoboszlai; João Pedro, Calvert-Lewin
- Captain / vice: **B.Fernandes** (MUN vs HUL, A) / **Semenyo** (MCI vs BOU, H)
- Bench (1→4): Donnarumma; Calafiori; Truffert; Furo

## Chip and transfer path

- Preferred path: hold chips GW1 → FT-roll → Wildcard when structure fails on data (~GW5–8) → FH for blanks → BB on first true 15 → TC on DGW (aggressive alt: Haaland TC after force-in ahead of GW3 Coventry H, only if minutes clean post-Community Shield)
- Alternatives rejected:
  - **BB1 default** — bench has Furo (non-playing) + Calafiori rotation; not BB-ready
  - **Scout BB2 Coventry-stack then WC3 into Haaland** ([premierleague.com no-Haaland squad](https://www.premierleague.com/en/news/4686680/see-the-fpl-squad-you-could-pick-without-haaland)) — burns first-half BB on promoted minutes before evidence; keep as *contingent* plan only if owner later forces Haaland-out + promoted bench
  - **Trial B / fatigue=0.0 as today’s 15** — overfits missing WC priors; robust≠deterministic
  - **Cloud 07:02Z Haaland+Bruno+Gabriel spine** — poorer inputs; superseded by sealed trials + 08-08 host-scored Haaland-in loss
- FT-rolling notes: watch Semenyo↔Haaland pivot, Calafiori↔Gabriel, DCL↔Thiago/Welbeck/Brobbey, Rice minutes post-England return

## Where this differs from the deterministic / robust arms

- Followed: **Trial A 15 in full** (deterministic and robust identical); Bruno (C) / Semenyo (VC); no Haaland; hold-chips stance vs BB1/BB2 defaults
- Overrode:
  - **GW1 XI**: start Matheus N., bench Calafiori — packet start_p 0.767 vs 0.561 (`packet`), plus Calafiori rotation history (`community`)
  - **Trial B**: reject as today’s named 15; use only as fatigue-weight sensitivity
  - **Cloud briefing `reports/strategy-research/2026-08-11.md`**: reject Haaland-in / Verbruggen / Mitchell / Dubravka structure — that run lacked this sealed packet
  - **Community template (~74% Haaland)**: stay out of the 15 today (see override tree)
- Could not verify: licensed odds, player ratings, promoted_team_priors, transfers_and_signings, world_cup_return_fatigue family artefacts (all degraded/unavailable on gap panel); set-piece effect_weights still null (shadow-only)

### Trial arm snapshot (comparators)

| trial | arm | objective | 15 (web_names) |
|---|---|---:|---|
| A (wcf=0.25) | det = robust | 280.3 / 276.1 | Raya, Donnarumma, Tarkowski, Matheus N., Shaw, Truffert, Calafiori, Rice, Szoboszlai, Semenyo, B.Fernandes, Mbeumo, Furo, João Pedro, Calvert-Lewin |
| B (wcf=0.0) | deterministic | 298.4 | Raya, Donnarumma, Virgil, Matheus N., Gabriel, Shaw, Truffert, Rice, Szoboszlai, Gravenberch, Semenyo, B.Fernandes, Thiago, Furo, Obi |
| B (wcf=0.0) | robust (selected) | 291.8 | Raya, Lammens, Virgil, O’Reilly, Matheus N., Gabriel, Shaw, Rice, Szoboszlai, Gravenberch, Semenyo, B.Fernandes, Furo, Welbeck, Calvert-Lewin |

Note: the owner brief that “deterministic and robust agree on the 15 in each trial” holds for **Trial A only**; Trial B arms diverge on GK2/DEF/FWD fillers.

## Decision rationale trace

| boundary | decision | opportunity cost / alternatives rejected | supporting claim IDs | conflicting claim IDs | confidence | falsifiers |
|---|---|---|---|---|---|---|
| Packet bind | Bind Trial A `input_packet_sha256` `93e783c3…`; supersede midday committed packet `c37b904f…` and cloud 07:02Z briefing | Midday seal without Understat; cloud Haaland-in 15 | none (packet hashes) | none | high | Newer seal after Community Shield |
| Fatigue weight (policy) | Recommend **0.12** (0.10–0.15); keep advisory 15 on Trial A until re-seal | 0.25 (current policy) / 0.0 (Trial B) | none — WC family unavailable; blend claims are minutes not fatigue scalar | none | medium | Player-level WC priors admitted; GW1–3 ablation |
| Named 15 | Follow Trial A det=robust 15 | Trial B det/robust; cloud Haaland spine; BB2 Coventry stack | none new today; prior blend: `2026-27-preseason-guehi-late-city-return`, `2026-27-preseason-rogers-missed-chelsea-tour`, `2026-27-preseason-anderson-missed-asia-tour`, `2026-27-preseason-senesi-late-spurs-return` (none of the four are in the advisory 15 — they removed/doubted Guéhi, Rogers, Anderson, Senesi from the wider pool) | model-run admitted **0** claims today | medium | Re-seal at 0.12 flips DEF/MID; ledger admits on Rice/Gabriel |
| Haaland | **Stay out** of opening 15 (budget-displacement confirmed at wcf=0.0) | Force-in now; cloud Haaland-in; ~74% EO template | none (08-08 host score: Haaland-in lost ~7 obj) | none | medium–high on packet; medium on strategy | Community Shield minutes + host Haaland-in under this packet clears EO hurdle |
| Captain | Bruno (C), Semenyo (VC) | Haaland (C) requires ownership; Szoboszlai differential (C) | none | none | medium | Hull team news; Semenyo/Haaland CS minutes 16 Aug |
| GW1 XI | Matheus N. over Calafiori | Arm XI (Calafiori start) | none (`packet` start_p only) | none | medium | Arteta XI; City CB/FB confirmation |
| Chips | Hold all GW1 | BB1; BB2+WC3 Haaland re-entry | none | none | medium | Nailed 15-man bench; fixture DGW calendar |
| Lane A / ledger | No new model claims; do not treat community WC takes as ledger | Force Semenyo/Haaland minutes claims from bot-challenged City pages | none (0 admits on `composer:2026-08-11T07:02:32Z`) | none | high | Fetchable official PC with named watchlist player_uid |

## Premium / DEFCON / minutes calls

### Haaland — premium/captain override tree

Grounding: `reports/strategy-research/2026-08-08-haaland-in-comparison.md` (best Haaland-in robust-mode Δ ≈ **−7.03** vs robust; verdict `haaland_in_does_not_beat_robust`) + today’s sealed trials (still out at wcf 0.25 **and** 0.0) + Lane B EO (~74–75% Haaland; Scout must-have / captain default).

| branch | action | when / falsifiers |
|---|---|---|
| **A — Stay out (today’s pick)** | Keep Trial A 15; Bruno (C); Semenyo City attack without Haaland | Default until 16 Aug. Falsifier: Community Shield shows Haaland fully sharp **and** Semenyo clearly second fiddle / rotated, collapsing the Semenyo-without-Haaland thesis |
| **B — Captain-only pivot plan** | Cannot captain without owning. Path = FT or WC into Haaland, then (C). Preferred window: after CS minutes, before GW3 Coventry H (Scout TC bait). Funding: drop Semenyo + a mid FWD/DEF (host must re-score; do not invent prices). Chip: hold TC for that Coventry H only if minutes clean | Trigger: CS start + packet re-score Haaland-in ≥ Trial A robust − 2 obj (owner tolerance) **or** Semenyo blank + Haaland haul GW1 while out |
| **C — Force into 15 now** | Rejected today. 08-08 host score lost ~7 obj; today’s EP leadership (44.82) still loses the budget fight in both trials; forcing him implies BB2/WC3 recovery path per Scout no-Haaland article — we are not taking that chip burn pre-evidence | Revisit only if owner prioritises EO insurance over host objective |

**Verdict: stay out (branch A), with branch B as the planned pivot after Community Shield; do not force-in today.**

### Other premium / DEFCON / punts

- Bruno **long** as no-Haaland captain hub; Mbeumo **long** for GW1–2 promoted run (`community` pre-season pens/form — not a ledger claim).
- Gabriel **watch / soft long if fatigue weight drops** — Trial B det loves him; Saliba absence (`bootstrap` colour in morning briefing) strengthens the case; not in today’s 15 because Trial A arms agree without him under wcf=0.25.
- Cheap DEF / DEFCON: Shaw is the template £4.5 in this 15; community prefers Mitchell as differential £4.5 — **not overridden in** (would require funds from Tarkowski/Truffert and a new host score). Promoted £4.0s (van Ewijk/Thomas/Diop) left out — cold-start priors degraded; OneFPL-style “one enabler max” aligns with holding chips.
- Punts / reassess: Calafiori (GW1–2 XI news); Rice (England return minutes); DCL (Leeds role); Furo never a playing FWD; O’Reilly/Guéhi watched via blend claims `2026-27-preseason-guehi-late-city-return` + `2026-27-preseason-anderson-missed-asia-tour` (City late group) — neither is in the advisory 15.

## Minutes-risk matrix

Qualitative only — no invented xMins. Packet start_p quoted where used; otherwise low/med/high/unknown.

### Advisory 15 (Trial A base)

| player | club | risk | source tag | note |
|---|---|---|---|---|
| Raya | Arsenal | low | packet | GW1 start_p 0.920 |
| Donnarumma | Man City | low | packet / community | GW1 start_p 0.915; predicted City #1 |
| Tarkowski | Everton | low | packet | GW1 start_p 0.879 |
| Matheus N. | Man City | med | packet / community | start_p 0.767; City FB/CB rotation + WC club load |
| Shaw | Man Utd | low–med | packet / community | start_p 0.847; template £4.5; Hall rumour noise only |
| Truffert | Bournemouth | low–med | packet / community | start_p 0.901; new manager (Rose) scheme unknown |
| Calafiori | Arsenal | high | packet / community | start_p **0.561**; prior season minutes volatility; benched in advisory XI |
| B.Fernandes | Man Utd | low | packet / community | start_p 0.855; captain hub |
| Semenyo | Man City | med | packet / official / community | start_p 0.885; role strong in Asia tour report but City attack rotation real |
| Mbeumo | Man Utd | med | packet / community | start_p 0.753; competing with Cunha/Amad/Sesko |
| Rice | Arsenal | med–high | packet / community | start_p 0.842 but England late-stage WC discourse → managed minutes risk |
| Szoboszlai | Liverpool | low–med | packet / community | start_p 0.831; GW1 Newcastle away |
| João Pedro | Chelsea | med | packet / community | start_p 0.745; high EO, role not ironclad |
| Calvert-Lewin | Leeds | med–high | packet / community | start_p 0.696; promoted-attack minutes |
| Furo | Brentford | high | packet | start_p ≈ 0.05 — bench enabler only |

### Trial B / comparator names not in advisory 15

| player | club | risk | source tag | note |
|---|---|---|---|---|
| Gabriel | Arsenal | med | packet / community | start_p 0.676; Saliba out helps nailedness; Arsenal WC workload |
| Virgil | Liverpool | low–med | packet / community | start_p 0.902; age/minutes management watch |
| Gravenberch | Liverpool | med | packet / community | start_p 0.783; midfield competition |
| Thiago | Brentford | low–med | packet | start_p 0.879; Trial B det FWD |
| Obi | Man Utd | high | packet | start_p 0.050 — enabler only |
| Lammens | Man Utd | med | packet / community | start_p 0.743; #1 not fully settled in discourse |
| O’Reilly | Man City | med–high | packet / community / official | start_p 0.703; England WC minutes called out by Fix; City rotation |
| Welbeck | Chelsea | high | packet | start_p 0.588; age/rotation |
| Haaland | Man City | low–med | packet / community / official | start_p 0.815; EP 44.82; Asia XI omission is tour timing not injury; CS 16 Aug is the check |

## Official leads (Lane A) worth citation

From `reports/news-discovery/2026-08-11.md` (metadata only; 0 model claims admitted):

- manchester-city — Marmoush brace / Atletico Asia tour finale — https://www.mancity.com/news/mens/atletico-madrid-asia-tour-2026-report-63921855 — 2026-08-09T14:00:00Z — Semenyo starring; Haaland omitted from listed XI
- manchester-city — Marmoush reaction — https://www.mancity.com/citytv/mens/atleti-1-3-city-omar-marmoush-reaction-63921879 — 2026-08-09T14:40:00Z
- manchester-city — Maresca Atletico PC — https://www.mancity.com/citytv/mens/enzo-maresca-atletico-madrid-preview-seoul-asia-tour-63921768 — 2026-08-08T10:00:00Z
- fulham — Carabao Cup R2 draw / media features (10 Aug) — calendar/media only, not availability
- Morning unstructured capture `2026-08-11T050001Z`: 0 strict official admissions (publication-time gate)

Bootstrap-only watches (not Lane A claims): Saliba/Timber injury flags; Charlie Hughes out; Grealish doubtful — none in advisory 15.

## Model evidence and host admission

- Run ID / model / prompt: `composer:2026-08-11T07:02:32Z` / Composer 2.5 / prompt sha256 `31a62d37c7784957f15030ab61a196a9eac0af59b35e949a9a016da98572a856`
- Ledger hash before → after: none → `f76c71376bcc574ba34e80349085a9e3d3fcc2f40be33d620e2f56fbb8a23f85`
- Accepted claims: **none** (0 candidates)
- Rejected candidates: none
- Pre-existing availability citation ledger (4 claims; blended into Trial A/B start_p):  
  `2026-27-preseason-rogers-missed-chelsea-tour`,  
  `2026-27-preseason-guehi-late-city-return`,  
  `2026-27-preseason-senesi-late-spurs-return`,  
  `2026-27-preseason-anderson-missed-asia-tour`  
  (ledger `content_sha256` `9138dde2ab45db8199ab41d1009b6d22d1085d6f0615e48d8bdd327727ca4035`; blend view `3be3e8f313d700d913bc75bebc7ac2bf917699b6d8c79c11616dd4ef4e6b3f5a`)
- Coverage gaps: WC priors family unavailable; odds/ratings/promoted/transfers degraded; City ephemeral fetch bot-challenged for Semenyo claim emission
- Review report: `reports/evidence-review/2026-08-11-model-run.md`

## Citations (Lane B)

- FPL360 — https://fpl360.com/2026/08/09/fpl-template-team-gw1-the-blueprint-74-of-managers-follow/ — ~2026-08-09 — GW1 template / Haaland ~74% EO
- FPL Pilot — https://www.fplpilot.com/blog/fpl-gw1-captain-picks-2026-27 — GW1 captain framework Haaland / Bruno / Szoboszlai
- Premier League Scout — https://www.premierleague.com/en/news/4681709/the-scouts-must-haves-for-start-of-202627-fpl — Haaland / Bruno / João Pedro must-haves
- Premier League Scout — https://www.premierleague.com/en/news/4686680/see-the-fpl-squad-you-could-pick-without-haaland — no-Haaland Bruno/Mbeumo/Semenyo + BB2/WC3 path
- Premier League Scout — https://www.premierleague.com/en/news/4679613/what-to-look-out-for-in-pre-season-ahead-of-202627-fantasy — WC return monitoring
- BBC Sport — https://www.bbc.com/sport/football/articles/c87n3wydzjzo — World Cup hangover / 33-day turnaround
- Fantasy Football Fix — https://www.fantasyfootballfix.com/blog-index/fpl-2026-27-world-cup-plans/ — WC minutes to avoid / City+Arsenal load
- Fantasy Football Fix — https://www.fantasyfootballfix.com/blog-index/best-budget-fpl-defenders-gameweek-1/ — Shaw / Mitchell / DEFCON cheap DEF
- Yahoo / community tips — https://sports.yahoo.com/articles/fantasy-premier-league-2026-27-142000440.html — Gabriel/Rice WC caution; Saliba absence
- OneFPL — https://onefpl.com/blog/promoted-teams-fpl-guide-2026-27 — promoted enabler discipline
- All About FPL — https://allaboutfpl.com/2026/07/fpl-fixture-analysis-for-the-2026-27-fpl-season-pl-fixtures/ — United kind openers; Coventry tough start
- FPL Dashboard — https://fpl.page/article/fpl-gw1-predicted-lineups-2627 — predicted XIs (Donnarumma/Lammens/Shaw etc.)
- Repo — `reports/strategy-research/2026-08-08-haaland-in-comparison.md` — host-scored Haaland-in loss
- Repo — `control/policies/initial-squad-2026-27.json` — `world_cup_fatigue_weight: 0.25`

## Host handoff

- Declare this 15 for rules validation + rescoring against frozen packet `93e783c3d0d0c4f619e249c3a2433e9fe1b34c70b49f7d2b9cc2873990cbe24e`
- Trial hashes for audit: A `974aba7421bede4c3b0dcdafe3d22d667e5aa3fe876f847e276db1348028c332` / B `f43e691ccc2ce3e1c1a9fb6fafdbbc71a9132f7249b0a18987c7e2923e0fb5d9`
- Model-run: `composer:2026-08-11T07:02:32Z`; 0 admits; ledger → `f76c71376bcc574ba34e80349085a9e3d3fcc2f40be33d620e2f56fbb8a23f85`
- Policy ask for owner: move `world_cup_fatigue_weight` from **0.25 → ~0.12** and re-seal before treating Trial B assets as default
- Account writes: false
- Owner approval still required before any FPL entry
- `ready_for_manual_entry`: false
- This file is an ad-hoc working-tree briefing only — **not committed** by this agent
