# ADR-0007: Historical datasets are downloaded locally

**Status:** Accepted
**Date:** 2026-07-21
**Decides:** Open Decision 3 (`docs/plan.md` Section 25)

## Context

WP-04 profiling and baseline training need historical datasets (Section 6.1, Tier 2). The choice was between downloading them into the local data plane or referencing user-provided external paths.

## Decision

Historical raw datasets (for example vaastav, FPL-Core-Insights, football-data.co.uk) are downloaded into version-control-ignored local paths under `data/raw/` as needed, respecting each source's licence, terms and attribution per its registry entry. They are not committed to Git and not redistributed.

## Consequences

- WP-04 operates on local copies with recorded provenance: source, version or commit, and download date.
- Registry entries still gate which datasets may be fetched at all (AGENTS.md rule 2).
