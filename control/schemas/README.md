# Canonical data model (WP-03)

Schemas live under `control/schemas/` as JSON Schema (draft 2020-12). Every entity named in plan Section 9 has a schema and at least one example under `control/schemas/examples/`.

## Layout

```text
control/schemas/
├── README.md                 (this file)
├── _defs.json                shared definitions (timestamps, ids, provenance)
├── catalog.yaml              entity → schema map and temporal flags
├── identity/                 Section 9.1
├── performance/              Section 9.2
├── manager/                  Section 9.3
├── evidence/                 Section 9.4
├── decisions/                Section 9.5
└── examples/
```

## Point-in-time

See [point-in-time-contract.md](../architecture/point-in-time-contract.md). Temporal entities declare which of the four timestamps they require in `catalog.yaml`.

## Identity resolution

Internal surrogate IDs (`player_uid`, `team_uid`) are stable across seasons. Source-specific IDs live on `player_identities` / `team_identities`. A worked cross-season example is in `examples/identity_resolution_cross_season.json`.

## Done-when (WP-03)

| Criterion | Evidence |
|---|---|
| Every Section 9 entity has a published schema | `catalog.yaml` + schema files |
| Temporal entities carry the four timestamps | `_defs.json` + per-entity `required` |
| Identity resolution demonstrated | `examples/identity_resolution_cross_season.json` |
| Each schema ships with a valid example | `examples/` + `tests/contracts/test_schemas.py` |
