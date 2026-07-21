# WP-03 status

**Done when** criteria:

| Criterion | Status |
|---|---|
| Every Section 9 entity has a published schema | Met — 45 schemas in `control/schemas/` + `catalog.yaml` |
| Temporal entities carry point-in-time fields | Met — contract in `docs/architecture/point-in-time-contract.md`; temporal schemas require `observed_at` / `available_at` |
| Identity resolution demonstrated | Met — `control/schemas/examples/identity_resolution_cross_season.json` |
| Each schema ships with a valid example | Met — `examples/*.json` validated in `tests/contracts/test_schemas.py` |
