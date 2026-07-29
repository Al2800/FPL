# FPL Copilot comparative research review

**Bead:** `FPL-uc1`  
**Access date:** 2026-07-29  
**Terms reviewed:** https://fplcopilot.com/terms — last updated 2 June 2026  
**Scope:** Publicly accessible product pages and vendor/editorial claims only. No
authentication bypass, private API reverse engineering, or scraping beyond
ordinary page retrieval.

## Subjects distinguished

Two differently named products appear in public FPL AI discourse. This note
treats them separately.

| Product | Public home | Relationship to this lab |
| --- | --- | --- |
| **FPL Copilot** (third-party) | https://fplcopilot.com/ | Primary subject of this bead |
| **Fantasy Premier League Companion powered by Copilot** (official) | Microsoft / Premier League editorial (27 Jul 2026) | Adjacent official conversational companion; not the same product |

## Method and evidence classes

| Class | Meaning |
| --- | --- |
| **Observed** | Visible on a public page retrieved on the access date |
| **Vendor claim** | Stated by the product owner or marketing copy; not independently verified here |
| **Inference** | Research hypothesis only; not verified capability |

---

## A. Third-party FPL Copilot (`fplcopilot.com`)

### A.1 Publicly observable surface (Observed)

Retrieved 2026-07-29 from public routes including `/`, `/guides`,
`/blog/transfer-planning-guide`, `/blog/chip-strategy-guide`,
`/blog/expected-points-explained`, `/about`, `/support`, `/copilot`,
and `/terms`:

- Landing emphasis on a **Solver** (“I'll find your best transfers. You just hit go.”).
- Guide index lists tools: Rate My Team, Compare Players, Solver, Chip Strategy,
  Expected Points, Mini-Leagues, Weekly Picks.
- Solver marketing asks for a Team ID and plans **1–10 gameweeks** of transfers.
- Chip strategy page describes ranking chip combinations across remaining GWs.
- Expected-points page describes editable minutes overrides.
- About page presents a single builder narrative and “free” positioning.
- Support page routes help through login / email follow-up.
- `/copilot` route: server-side render exposes navigation and page title
  ("FPL AI Chat: Free Squad Analysis & Transfer Advice") but **not** the
  interactive chat body; behind-login behaviour was not exercised.
- Terms of Service (last updated 2 June 2026): explicitly describe an opt-in
  **Autopilot** feature (§2 and §2a) that accepts FPL login credentials and
  can stage or execute transfers and chip plays on the user's behalf when
  enabled. Credential storage and deletion on disable are described in §2a.
  Terms also list acceptable-use prohibitions: no API reverse-engineering,
  scraping, or redistribution of data obtained from the Service (§4).

Unauthenticated retrieval did **not** expose live solver outputs, private
model weights, raw training corpora, or the Autopilot account-write controls
(which require authentication). The Autopilot capability is a **vendor claim**
in public Terms, not an independently exercised behaviour.

### A.2 Workflows and decision support (Vendor claim unless noted)

| Capability | Class | Public claim (paraphrased) |
| --- | --- | --- |
| Multi-GW transfer path optimisation | Vendor claim | MIP optimiser plans transfers across a horizon; maximises cumulative xPts after hits |
| Chip combination search | Vendor claim | Enumerates valid WC/FH/BB/TC combos with HiGHS MIP; ranks by total xPts |
| Expected points model | Vendor claim | Combines xG, xA, CS probability, minutes, bonus patterns; updates multiple times/week |
| Minutes override | Vendor claim | User can edit projected minutes; xPts recalculate |
| Conversational explanation | Vendor claim | Chat can explain why a solver path was chosen |
| Mini-league rivalry | Vendor claim | Rival squad visibility, win-probability simulation, differentials |
| Rate / roast team | Vendor claim | Team ID in → scored assessment and suggested fixes |
| Autopilot (opt-in account automation) | Vendor claim (Terms §2a, 2 Jun 2026) | Opt-in feature: user provides FPL credentials; service stages or executes transfers and chip plays on behalf of the user when enabled. Credentials encrypted at rest; deleted on disable. **Vendor-claimed public capability; not independently exercised by this review.** |

### A.3 Data inputs and provenance (mixed)

| Topic | Class | Notes |
| --- | --- | --- |
| Official FPL Team ID as squad input | Observed / vendor claim | Guides instruct users to enter Team ID |
| xG / xA / CS / minutes / bonus features | Vendor claim | EP explainer; underlying source licences not cited on reviewed pages |
| “50+ data points per player” / all PL players | Vendor claim | Not independently audited |
| Update cadence | Vendor claim | “Multiple times a week” |
| Point-in-time / deadline cutoffs | Unknown | No public contract analogous to this lab’s `available_at <= deadline` discipline was found |
| Redistribution / scraping terms | Vendor claim (Terms §4) | Terms §4 (Acceptable Use) prohibit reverse-engineering, scraping, or API abuse, and redistribution of data obtained from the Service. Broader licence compatibility with this lab’s source registry was not assessed. Do not assume redistribution rights. |

### A.4 Output structure, state, uncertainty, automation

| Topic | Class | Notes |
| --- | --- | --- |
| Output | Vendor claim | Transfer paths, chip rankings, EP tables, weekly picks, chat explanations |
| State handling | Vendor claim / inference | Team ID pulls current squad; multi-GW plan is recomputed; persistence model unknown |
| Uncertainty | Vendor claim | Minutes likelihood / rotation risk folded into EP; little public calibration reporting |
| Explanations | Vendor claim | Chat + pitch view of planned lineups |
| Automation boundary | Vendor claim (Terms §2a, 2 Jun 2026) | Public Terms explicitly describe an opt-in **Autopilot** that accepts FPL credentials and can stage or execute transfers and chip plays on behalf of the user. This is a vendor-claimed public capability, not an independently observed or exercised behaviour. The Autopilot execution path (authentication flow, FPL API interaction) was not verified in this review. |

### A.5 Limitations and unknowns

- Live product behaviour behind login was **not** exercised.
- Solver correctness, reproducibility and seed control were **not** verified.
- Feature provenance and licence compatibility with this lab’s source registry
  remain **unknown**.
- Marketing performance claims (e.g. manager rank anecdotes on `/about`) are
  **vendor claims**, not lab evaluation results.

---

## B. Official Fantasy Premier League Companion (Microsoft Copilot)

**Source:** Microsoft Source EMEA feature, Elliott Smith, **27 July 2026**  
https://news.microsoft.com/source/emea/features/fantasy-premier-league-companion-gives-managers-a-new-tool-for-success/

| Topic | Class | Notes |
| --- | --- | --- |
| Stack | Vendor claim | Microsoft Foundry; Azure OpenAI; “Chat GPT 5.4”; official Premier League / FPL data |
| Interaction | Vendor claim | Conversational Q&A for new and advanced managers |
| Data buckets | Vendor claim | Match data + FPL game data (ownership, captaincy, chip usage) |
| Autopilot | Vendor claim (explicit negative) | “Definitely not there to be an autopilot”; managers remain in control |
| Points prediction | Vendor claim (explicit negative) | “It will not predict FPL points” |
| Outputs | Vendor claim | Multiple options with supporting data and editorial links; not a single forced plan |

Useful contrast: the official Companion publicly rejects points prediction and
autopilot, while third-party FPL Copilot publicly centres an xPts optimiser.

---

## C. Comparison matrix vs this laboratory

| Pattern | FPL Copilot (3P) | Official Companion | This lab today | Adaptation hypothesis (not scheduled work) |
| --- | --- | --- | --- | --- |
| Multi-GW transfer MIP | Claimed core | Not claimed | Single-GW + multiweek challengers / option value | Separate bead: publish horizon + hit accounting as an explicit arm |
| Chip combination search | Claimed | Not claimed | Longitudinal chip policy experiments | Keep chip search deterministic and hash-bound |
| Conversational UX | Claimed chat | Core product | Agent envelopes / forks; host-owned prompts | Agents propose only; never enforce |
| Evidence / news minutes override | Manual minutes edit claimed | Real-time news claimed | Evidence ledger + availability claims | Align overrides with registry + cutoff admission |
| Rival / mini-league | Claimed | Not emphasised | Deferred (plan §19) | Remain deferred |
| Official PL/FPL data grounding | Unclear provenance | Explicit official data claim | Official endpoints + registry | Prefer registry-approved sources only |
| Autopilot / account write | Vendor-claimed opt-in Autopilot (Terms §2a); accepts FPL credentials; executes transfers/chips; **not independently exercised** | Explicitly rejected | Browser execution disabled | Keep disabled; advisory GDR only; vendor credential model must not be adopted |
| Point-in-time discipline | Unknown | Unknown | Core invariant | Non-negotiable |
| Evaluation / replay | Not public | Not public | Benchmark kernel, sealed forks | Keep sealed artefacts and arms |
| Uncertainty reporting | Partial (minutes risk) | Options not single answer | Contingency / appearance distributions | Separate calibration reporting bead |

---

## D. Gap register

| Gap | Severity for lab adoption |
| --- | --- |
| Data-source licence and redistribution rights for 3P features | High — blocks collection without registry entry |
| Provenance of xG/xA and update timestamps | High — needed for cutoff-safe replay |
| Reproducibility (seeds, solver versions, content hashes) | High — required for benchmark arms |
| FPL credential / account-write risk from 3P Autopilot | High — vendor-claimed opt-in Autopilot stores FPL credentials and executes transfers; must not be integrated, replicated, or wired to this lab’s execution path; browser execution remains disabled |
| Evaluation design (paired shadow, sealed outcomes) | High — marketing rank claims are not substitutes |
| Rights to reuse UX copy or proprietary solver logic | Absolute — adapt ideas only; no copying |

---

## E. Recommendations (research hypotheses only)

These are **not** implementation authorisations. Each would need its own bead.

1. **Hypothesis:** Multi-GW cumulative-xPts planning with explicit hit accounting
   is already directionally present; a named challenger arm with sealed
   fingerprints would make the comparison measurable.
2. **Hypothesis:** User-editable minutes are valuable only when admitted as
   evidence claims with `available_at` and source hashes.
3. **Hypothesis:** Official Companion’s “options + data, no autopilot, no points
   prediction” framing is a useful safety UX pattern for advisory outputs.
4. **Hypothesis:** Mini-league rivalry tooling should stay deferred until
   rights and evaluation design exist.
5. **Do not:** scrape FPL Copilot, embed its credentials, or treat vendor EP as
   an oracle inside sealed replays.
6. **Credential and account-write boundary:** vendor-claimed Autopilot collects
   FPL credentials and executes transfers on behalf of users. This pattern must
   not be replicated: this lab keeps browser execution disabled, issues
   advisory proposals only, and never stores or uses an FPL account password.
   The Terms' credential model is noted as a risk pattern, not an adaptation
   target.

---

## F. Closure checklist

- [x] Public capabilities/claims cited with access date 2026-07-29
- [x] Terms of Service (last updated 2 June 2026) reviewed for automation, credentials, and acceptable use
- [x] Observed / vendor claim / inference kept distinct
- [x] Autopilot vendor claim distinguished from independently exercised behaviour
- [x] `/copilot` route observed (SSR nav only; interactive chat body not in SSR)
- [x] "Terms not reviewed" replaced with narrow Terms §2a and §4 observation
- [x] Comparison matrix updated: Autopilot / account write row corrected
- [x] Gap register: credential/account-write risk rated High
- [x] Comparison matrix mapped to engine, evidence, arms, live-shadow
- [x] Provenance, state, reproducibility, safety, evaluation, rights gaps recorded
- [x] Recommendations are hypotheses only; implementation split to future beads
