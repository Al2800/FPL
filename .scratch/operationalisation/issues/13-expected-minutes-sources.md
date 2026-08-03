# 13 — Expected-minutes evidence sources: licensing and benchmarking

Status: ready-for-human
Type: task
Track: E (minutes evidence)

## Context

Expected minutes is the acknowledged weakest point (plan §7.1). The strongest external evidence — predicted line-ups (Fantasy Football Scout, Rotowire) and confirmed line-up feeds (Sofascore, Fotmob) — is registered but disabled pending terms review, as are Understat/FBref (xG/xA, defensive actions relevant to defensive-contribution scoring) and ClubElo (promoted-team priors).

## Human part (gates the rest)

Review terms for one predicted-line-up source and one confirmed-line-up feed (plus optionally Understat/FBref/ClubElo); record `licence_status`, `allowed_use` and collection method in `control/sources/source-registry.yaml`. Ground rule 2: no collection without registration.

## Agent part (after enablement)

- Implement the collector(s) per the acquisition contract, capturing pre-deadline with full point-in-time timestamps.
- Benchmark each start-probability source against the naive "started last Gameweek" baseline (WP-05 requirement) and against the official `chance_of_playing` flags before it feeds live decisions.
- Feed accepted sources into the minutes model as governed evidence, not silent overrides.

## Done when

- At least one line-up source is enabled with documented terms, its marginal accuracy over the naive baseline is measured and reported, and the minutes model consumes it through the evidence-adjustment policy.
