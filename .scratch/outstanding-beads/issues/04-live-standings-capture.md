# 04 — Capture 2026/27 official global standings snapshots

**What to build:** Prospective, point-in-time capture of official Overall-league
standings at immutable post-finalisation checkpoints for 2026/27 Gameweeks,
producing threshold rows the rank calibrator can label exact or bounded.
Collection stays registry-gated and off the pre-deadline decision path; missing
pages stay explicit gaps.

**Blocked by:** 02 — Approve historical overall-rank threshold source

**Status:** ready-for-agent

**Category:** enhancement

**Former bead:** `FPL-762`

- [ ] Registry entry with confirmed licence status and allowed use exists before enablement.
- [ ] Collector remains disabled by default until owner approval; every snapshot carries observed/available/finalisation metadata.
- [ ] Missing pages are recorded as gaps — never inferred from live standings.
- [ ] Focused ingestion tests cover the null/disabled and happy-path contracts without committing secrets.
