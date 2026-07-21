# WP-06 status

**Scope this pass:** deterministic scoring + expanded validation against golden-case families (not yet full Opta-faithful BPS reconstruction — plan Section 5.5).

| Criterion | Status |
|---|---|
| Validator passes rule golden cases for implemented families | Met for squad/lineup/transfers/prices/chips/DC/bonus ties/captain fallback/autosub (see tests) |
| Scoring engine converts events/stats using versioned rules | Met — `src/scoring/engine.py` |
| Chip and autosub rules | Met for one-chip, first-half expiry, formation-preserving autosub |
| Official points reproduction within tolerance | Deferred — needs finalised GW samples post-launch; tolerance policy documented in Section 5.5 |

Next: wire golden-case YAML as a data-driven test runner; sample finalised Gameweeks once 2025/26 lock data is locally retained.
