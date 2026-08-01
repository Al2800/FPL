# ADR-0022: Strategy-prompt stance on start probs, team news, and guidance

**Status:** Proposed  
**Date:** 2026-08-01  
**Owners:** Project owner  
**Related:** ADR-0013, `docs/architecture/2026-27-decision-data-flow.md`,
`prompts/daily-strategy-research/v1.md`

## Context

The strategy agent is the primary advisory chooser (Plane D). The statistical
packet is thin in preseason: start probabilities are often proxies, odds and
ratings are degraded, and unstructured evidence is absent. Before official
daily automation we need a clear prompt stance on:

1. whether the agent should produce **start probabilities**;
2. how hard to push **team news** gathering;
3. how much to **guide** chip/premium/structure theses vs stay **agnostic**.

Open-source and community practice splits cleanly:

| Approach | What they do | Why |
|---|---|---|
| **Sertalp / open-fpl-solver** | Open optimiser; **bring your own** EP/xMins (often FPL Review) | Keep forecasting separate from legality/search |
| **OpenFPL (daniegr)** | Public FPL + Understat only; **no proprietary xMins**; use FPL API **availability tags** | Reproducible baseline without paywalled minutes |
| **fpl-predict / SmartPlay-style ML** | Train own minutes/points models; scrape or API-adjust for transfers | Own the forecast stack end-to-end |
| **LLM assistants (e.g. fantasy-ai)** | Read FPL `status` / `chance_of_playing` / `news`, then narrate transfers | Cheap minutes signal from official API without inventing xMins |

Commercial stacks win on minutes fidelity via expert xMins. Open stacks that
stay honest either (a) import external projections, (b) train their own, or
(c) refuse to invent minutes and use availability categories.

Our lab already chose (c) for the LLM plane: degrade visibly; ledger-capped
adjustments only for structured rates (ADR-0013); community EV never blends
into `points_per_90`.

## Decision

### Start probabilities

The strategy agent **must not invent numeric start probabilities or xMins**.

It **may and should**:

- quote packet `start_probability` / expected-minutes when present;
- quote frozen bootstrap `status`, `chance_of_playing_*`, and `news` strings
  with `news_added` when present;
- give a **qualitative** minutes-risk label (`low` / `med` / `high` /
  `unknown`) with an evidence tier tag.

Numeric start-prob edits remain a **host / ledger** concern (Plane C → B),
not a free-text invention in Plane D.

### Team news

Yes — **gather team news hard**, but in Lane A form:

- official club / PL / FPL URLs as metadata leads;
- bootstrap news fields as packet-bound structured status;
- community minutes takes only as Lane B citations that inform selection,
  never as governed ledger claims.

The prompt should require coverage of minutes risk for every recommended
player and every dropped comparator pick. It should **not** ask the model to
emit a parallel start-prob table that looks like forecast output.

### Guidance vs agnostic

**Guide structure; stay content-agnostic.**

Require:

- evidence tiers;
- comparator follow/override accounting;
- minutes-risk matrix;
- premium/captain override tree when a dominant premium is absent;
- falsifiers and confidence degradation when data is thin.

Do **not** bake preferred chip recipes, DEFCON dogma, or “must own Haaland”
into the prompt. Those theses may appear in web debate; the agent weighs them
against the packet and official status, it does not inherit them as policy.

## Consequences

- Prompt enhancements emphasise bootstrap availability + official discovery,
  not fabricated xMins.
- Dry-runs (Composer, Grok, etc.) are comparable on evidence hygiene, not on
  who invents sharper minutes numbers.
- Host rescoring stays meaningful: the declared 15 is still scored on the
  frozen packet.
- Future work can still train or import open minutes models into Plane B
  without changing the LLM’s role.

## Open questions

1. Should a future open minutes model (OpenFPL-style or internal) become an
   optional packet family, or stay outside the live default?
2. When bootstrap `chance_of_playing_next_round` is present, should the
   forecaster ingest it automatically (W7) before the strategy agent runs?
