# 2026/27 daily agent-driven strategy loop

Architect map of hard stats, ledger join points and weighting:
`docs/architecture/2026-27-decision-data-flow.md`.

## Problem

Repeating a six-GW optimiser run each day is necessary but not sufficient.
Strong human FPL process also rebuilds **situational strategy understanding**
every day: chip paths, premium pivots, captain ladders, DEFCON/cheap-defence
gambles, fixture turns and early-Wildcard pressure. That understanding today
mostly lives in fast community posts (X/blogs/model screens), not in our
structured packet.

This lab therefore runs a **Composer 2.5 daily strategy research agent** as the
morning driver, then uses the deterministic checkpoint as the legality and
scoring spine.

## Daily sequence

```text
07:00 UTC  Composer 2.5 strategy research automation
           ├─ Lane A: official club/PL discovery (metadata only)
           └─ Lane B: strategy intelligence briefing (chips, premiums,
              captains, DEFCON, early WC) with citations
               → reports/strategy-research/YYYY-MM-DD.md

Morning     Human reads briefing; admits only decision-relevant official
            citations into the evidence protocol when justified

Capture     Immutable official snapshot (scheduler / manual)
            → data/snapshots/2026-27/preseason/<checkpoint>/

Checkpoint  scripts/run_initial_squad_checkpoint.py
            → six-GW live-faithful packet + deterministic/robust arms
            → diff vs previous checkpoint

Review      Human compares optimiser proposal with the day's strategy
            briefing (and any human/reference arm). Approval stays blocked
            until degradations are accepted and owner signs a named proposal.
```

## What the agent owns vs what code owns

| Concern | Owner |
|---|---|
| Chip-path hypotheses, community model splits, named watchlists | Daily strategy agent (Lane B) |
| Official injury/team-news lead discovery | Daily strategy agent (Lane A) → human citation |
| Six-GW EP / start / uncertainty vectors | `live-faithful` + prior (deterministic) |
| Legal 15, XI, captain, bench, objective | Initial-squad optimiser (deterministic) |
| Rules validity | Rules validator (deterministic) |
| Approval / manual entry | Owner only |

LLMs propose understanding and optional external arms. They never clear the
approval gate.

## Relationship to the X-post depth target

The briefing template in `prompts/daily-strategy-research/v1.md` is deliberately
shaped like strong preseason strategy notes:

1. chip and transfer path hypotheses + falsifiers;
2. premium / template pivots and model disagreement;
3. captain ladder;
4. DEFCON / cheap defence watch under manager uncertainty;
5. bench depth and FT-rolling fragility;
6. official leads worth citing;
7. watchlist for the next deterministic run.

Community numbers (EV gaps, ownership claims) must be **attributed or marked
unknown**. Inventing Review/Solio-style deltas is prohibited.

## Governance wall

- Lane B content is **not** registered evidence. It must not enter the live
  evidence ledger or silently adjust the forecast packet.
- Lane A can become a manual derived claim only through the existing citation
  protocol under admitted sources.
- Unregistered analyst/blog/X accounts remain barred from automated admission
  (`unregistered_analyst_or_blog_policy` in the evidence config).

## Activate

Recipe: `config/automations/2026-27-daily-strategy-research.json`  
Prompt: `prompts/daily-strategy-research/v1.md`  
UI: [cursor.com/automations](https://cursor.com/automations) — model
**Composer 2.5**, cron `0 7 * * *` UTC, repo `Al2800/FPL` @ `main`.

The narrower news-only recipe remains as the nested Lane A procedure; do not
run both automations as duplicate morning jobs.
