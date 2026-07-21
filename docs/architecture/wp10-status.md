# WP-10 status — deferred-feature designs

**Package:** WP-10  
**Done when (plan):** every §19 anticipated feature has an interface-only design note with prerequisites and activation criteria; no implementation code.

## Checklist

- [x] Index: `docs/architecture/deferred/README.md`
- [x] Notes for all §19 register rows (including cloud / distributed)
- [x] ADR-0015 — browser dry-run stability (Open Decision 11 — Proposed)
- [x] ADR-0016 — agent cost/latency budgets (Open Decision 13 — Proposed)
- [x] No new code under `src/agents/` or `src/execution/`

## Verify

```bash
PYTHONPATH=. python3 -m pytest tests/contracts/test_deferred_interfaces.py -q
```
