# ADR-0004: Minimum meaningful effect size for strategy comparisons

**Status:** Accepted
**Date:** 2026-07-21
**Decides:** the owner-preference half of the detectable-effect-size requirement (`docs/plan.md` Section 17.6)
**Accepted by:** project owner, 21 July 2026

## Context

Section 17.6 requires a detectable-effect-size estimate before any strategy difference is claimed. The threshold — the smallest per-Gameweek advantage worth caring about — is an owner preference; the sample-size mathematics that follows from it is delegable to an implementing agent.

## Decision

The minimum meaningful difference between strategies is **0.5 points per Gameweek** (about 19 points over a season). Smaller differences are treated as noise for decision-making purposes even if statistically detectable.

This threshold may be revised after the first formal power analysis if that analysis shows it is impractical or too coarse; until then it stands.

## Consequences

- WP-09's replay harness is sized to distinguish 0.5 points per Gameweek — expected to require hundreds of paired replayed decisions, reinforcing the cheap-per-run requirement.
- Claims of strategy superiority below this threshold are not made.
- The Phase 0/1 human task to "confirm the provisional effect size" is closed.
