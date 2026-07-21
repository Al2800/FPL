# ADR-0002: Local retention of raw snapshots

**Status:** Accepted
**Date:** 2026-07-21
**Decides:** Open Decision 2 (`docs/plan.md` Section 25)

## Context

The Premier League Terms of Use restrict reproduction and re-utilisation of site material (plan Section 6.3); public endpoint availability is not permission to archive or redistribute. The plan's point-in-time discipline nonetheless requires immutable local snapshots (Sections 7.2, 10.1), and day-one capture is the most time-critical asset in the plan (Section 17.6).

## Decision

Raw FPL JSON responses, fixture data and pre-deadline odds captures are retained locally, indefinitely, for private non-commercial research (ADR-0001). Nothing is redistributed or republished. Raw data, credentials and browser state stay out of version control. Third-party sources are retained only per their individual registry entries.

## Consequences

- The snapshotter may start as soon as the FPL-endpoint registry entry exists.
- `.gitignore` must exclude the data planes before any collection runs.
- Retention terms for each further source are a registry decision; this ADR does not cover them.
- Re-review if project scope changes (ADR-0001) or the relevant terms materially change.
