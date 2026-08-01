# Spec: deepen the frozen forecast packet for agent + human reasoning

## Goal

Make the initial-squad / strategy packet decision-grade enough that an agent
(and a human reviewer) can reason over **why** expected points look the way
they do — club, opponent, home/away, multipliers, minutes, set-piece role,
availability and market context — without reconstructing that story from
scattered captures.

## Non-goals

- Raising World Cup fatigue weight without an explicit calibration decision
- Scraping unregistered player-rating sites (FotMob / Sofascore / FBref)
- Treating The Odds API as a player-level xG source
- Account execution or rival modelling
- Fabricating odds, ratings or availability when sources are absent

## Problem statement (2026-08-02 checkpoint)

`weekly-2026-08-02` is `live_faithful_degraded`. Team and fixture strength
already move EP via Understat/ClubElo multipliers, but:

1. Player-level Understat xG/xA is captured (537 rows) and unused; `event_model_weight=0.0`.
2. Fixture context and per-week multipliers are not exposed on packet player rows.
3. Start probabilities are flat historical priors — not GW-specific and not
   blended with admitted availability / press evidence.
4. Set-piece roles are admitted but shadow-only.
5. Optional families (odds, ratings, transfers) still bound the packet quality.
6. Fatigue is useful but coarse; current under-use may be preferable to over-weighting.

## Sequencing

Prefer consuming already-captured, registry-approved artifacts before opening
new rights. Deterministic host code owns numerical effects; LLMs propose and
reason over an audit trail, never enforce.

## Success signal

A rebuilt checkpoint packet lets an agent answer, per shortlisted player-week:

- who they play, home/away, and the attack/defence/Elo/odds multipliers used;
- what minutes/start prior is assumed and which evidence would change it;
- whether set-piece / availability / fatigue / cold-start adjusted the view;
- which families remain explicitly degraded.
