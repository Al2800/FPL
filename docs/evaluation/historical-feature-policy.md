# Historical feature and market policy

## Purpose

Benchmark v0 must reproduce what a structured-data policy could have known at
each 2025/26 deadline. It must not improve a historical decision with a result,
price, registration or editorial fact learned later.

The adapter therefore consumes only `episode-manifest.json`, `observed.json`,
`identity-map.json`, the previous content-addressed feature state and, for
Gameweek 1 only, the governed official Scout seed. It has no hidden-outcome
parameter and does not read `hidden-outcome.json`.

## Chronology

An observed Gameweek `t` episode carries player fixture rows from completed
Gameweek `t-1`. Those rows are first combined into one record for each player
and Gameweek. Minutes, points and event counts are summed; `started` means the
player started at least one fixture. Only after this aggregation are rolling
features calculated.

This ordering is essential for Double Gameweeks. Two fixtures locked at the
same deadline are one information period: the first fixture cannot become a
feature for the second.

The resulting history is cumulative and content-addressed. Its lineage binds
the episode, observed partition, identity map, dataset, rules, previous feature
state and model specification. Reversing source-row order cannot change it.

## Market membership and blanks

The strict historical market contains players known through either:

1. the controlled Gameweek 1 seed; or
2. at least one completed prior-Gameweek observation.

Once known, a player remains in the market even when their club blanks or the
player has no row. Their most recent quote, position and club are carried
forward. A Blank Gameweek gives the player zero projected fixture points but
does not remove them, which preserves owned-player state and legal transfer
choices.

The final-season player catalogue is not used to introduce players early. It
contains end-of-season membership, status, cumulative outcomes and prices, so
using it as a launch market would leak later registrations. Players not yet
observed are an explicit limitation of this historical corpus.

## Historical prices

The vaastav `value` field is associated with a Gameweek, but the frozen corpus
does not prove that it was captured at that Gameweek's FPL deadline. It is
therefore an uncertain last-observed quote rather than a claimed exact
deadline price.

Every historical quote carries:

- `source_gameweek`;
- `age_gameweeks`; and
- `price_confidence=historical_post_gameweek_export`.

This is sufficient to exercise transfer finance and expose sensitivity, but
benchmark reports must not claim exact historical financial opportunity. The
2026/27 live process avoids this limitation by capturing immutable official
snapshots before each deadline.

## Projection baseline

The first replay projection is deliberately transparent:

- history is one row per completed player-Gameweek;
- the rolling window is the latest three completed Gameweeks;
- start probability blends the last start with rolling minutes;
- expected minutes are calculated per upcoming fixture;
- rolling realised points provide the per-fixture points baseline;
- Double Gameweek fixture projections are summed; and
- Blank Gameweeks receive zero fixture points.

Fixture difficulty is retained in the projection component but is not assigned
an arbitrary weight. Team Elo, odds and evidence-agent adjustments remain
separate inputs until their incremental value is calibrated through ablations.

## Gameweek 1

Gameweek 1 has no prior structured player history. Benchmark v0 therefore uses
the Premier League Scout's official 15-player selection published before the
deadline as a fixed shared seed. The frozen player rows map the published names
and £100.0m of launch prices to canonical player and club identifiers.

The seed is stored at
`control/seeds/2025-26/official-scout-gw1.json`. All policy arms begin from the
same seed and Gameweek 1 plan; policy divergence begins in Gameweek 2.

This is an experimental control for 2025/26, not the 2026/27 starting-squad
policy. The live season will use launch snapshots, pre-season priors and the
bounded evidence-agent process available at that time.

## Failure and degradation

The adapter fails closed for:

- a manifest, observed partition or identity-map hash mismatch;
- nonconsecutive feature-state advancement;
- a lag row from anything other than the exact prior Gameweek;
- outcome-like fields such as `xP`, `ep_next` or `player_outcomes`;
- conflicting price, position or team values within one player-Gameweek; or
- an owned player missing from the known market.

Historical price uncertainty, carried quotes, missing news, fixture-revision
limitations and the GW1 cold start remain visible in output artifacts. Missing
information is never silently interpreted as player availability.

## Sources

- Premier League, “Scout Selection: The best FPL squad for the opening
  Gameweeks”, 14 August 2025:
  https://www.premierleague.com/en/news/4373986
- Premier League, “Quick Fantasy tips: Your basic guide to Gameweek 1”,
  11 August 2025:
  https://www.premierleague.com/en/news/4373995/quick-fantasy-tips-your-basic-guide-to-gameweek-1
- Frozen Benchmark v0 dataset manifest:
  `control/manifests/datasets/benchmark-v0.json`
