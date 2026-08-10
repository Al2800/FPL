# Benchmark dataset roadmap

This roadmap orders integration by decision value, point-in-time integrity,
reliability and rights risk. Every stream below is part of the intended data
platform because it may contribute to a decision. A tier controls implementation
order, trust and degraded behaviour; it does not declare later data unnecessary.
Registration is not permission to collect: every collector still passes
`assert_collectable`, and unknown or restricted candidates remain disabled until
the owner approves a bounded acquisition.

## Tier 0 — canonical FPL episode spine

| Evidence | Source | Cutoff and cadence | Retention |
|---|---|---|---|
| Players, teams, prices, status, news, ownership | FPL bootstrap | Daily; T-48h, T-8h and T-2h | Immutable private raw snapshot + hash |
| Fixtures and revisions | FPL fixtures | Same cadence and on detected revision | Immutable raw snapshot + revision ledger |
| Scores, minutes and scoring events | FPL live | After deadline, during play and after corrections | Immutable outcome partition |
| Own squad, bank, purchase/selling price, free transfers and chips | Manual GDR initially | At episode cutoff and immediately after decision | Private manager-state snapshot |
| Picks, transfers, final points and rank | Public entry endpoints where permitted | Only after the relevant deadline/outcome | Private reconciliation snapshot |

These fields form the benchmark episode spine. Outcomes and post-deadline manager
observations are physically excluded from the observed partition. Authenticated
browser collection remains disabled; manual manager state is authoritative until
its terms and controls are approved.

## Tier 1 — low-dimensional market and strength baselines

| Candidate | Intended use | Point-in-time / rights constraint | State |
|---|---|---|---|
| football-data.co.uk | Results, simple Elo, closing-market comparator | Files do not establish a pre-FPL-deadline timestamp; no redistribution | Existing bounded local assessment |
| football-data.org | Independent fixtures/results/tables cross-check | Free tier is basic and rate-limited; registration and terms apply | Disabled |
| Betfair Historical Data | Last exchange update before the episode cutoff | Account/package, price and reuse terms require review; preserve update timestamp | Disabled |
| ClubElo | External team-strength comparator | Use only historical ratings demonstrably available at cutoff; national cups omitted; reuse terms unresolved | Disabled |

Tier 1 adapters are intended platform components, but remain feature-flagged until
their acquisition and temporal contracts pass. Their marginal contribution is
then measured against the fitted result-only Elo; a weak source may remain useful
for reconciliation without becoming a model dependency.

## Tier 2 — expected-minutes evidence

Use cited official evidence for line-ups and minutes, club injury updates and
press conferences, return-to-training, cup/European/international workload,
travel/rest, manager or formation changes and role competition. Store the source,
publication time, observation time, player identity, confidence and expiry. Never
rewrite historical evidence after the cutoff. Missing evidence degrades confidence;
it is not reconstructed from hindsight. The canonical interface and manual path
are first-class platform components; automated collection remains disabled until
each publisher's terms and method are approved.

See also the 2026-08-01 current-info source research note for the minutes / xG /
odds / WC-prior wiring map:
`docs/data-sources/2026-08-01-current-info-source-research.md`.

## Tier 3 — event-data ablation

StatsBomb open data provides the event-stream integration and feature-engineering
prototype where its competition coverage is suitable. It is not assumed to
represent target EPL episodes. The adapter and feature contract should therefore
exist even when a target episode has no event data. A commercial EPL event feed may
be activated only after a reproducible ablation demonstrates sufficient decision
value to justify licence, cost and retention constraints.

## Reliability architecture

Every stream moves through the same five boundaries:

1. immutable acquisition with request/file origin, collection time, registry
   version and content hash;
2. canonical player, team, fixture, competition and season identities;
3. temporal normalisation separating `event_time`, `published_at`, `observed_at`,
   `ingested_at`, `effective_at`, `finalised_at` and derived `available_at`;
4. quality monitoring for schema drift, coverage, freshness, duplicates, identity
   match rate, reconciliation and quarantine;
5. deadline-safe feature views that expose only records with
   `available_at <= episode_cutoff` and retain full lineage.

Collectors never write directly to model tables. Each feature declares its source
preference and fallback chain. A failed optional stream produces a recorded quality
or degraded-mode result, not silent imputation or total pipeline failure.

## Promotion gate

For every candidate: resolve licence and attribution; define episode-time
availability; profile coverage and identity joins; run a leakage audit; quantify
incremental calibration and decision utility with uncertainty; document cost and
failure mode; then approve a registry change. Integration contracts may be built
against fixtures while acquisition is disabled. Unknown or restricted sources do
not become collectable merely because an adapter exists.
