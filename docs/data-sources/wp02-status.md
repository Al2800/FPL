# WP-02 Source governance — status

**Package:** WP-02  
**Registry:** `control/sources/source-registry.yaml` (`0.1.0`)

## Done-when checklist (Section 6.1 Tier 1)

| Criterion | Status |
|---|---|
| Every Section 6.1 source has a complete Section 6.2 field set | Met |
| Collector `enabled` follows licence/allowed_use | Met — only `fpl-official-endpoints` enabled |
| Disabled sources document an alternative or accepted gap | Met — see `notes` on each entry |

## Enabled collectors

- `fpl-official-endpoints` — private local snapshots per ADR-0001/0002 (`licence_status: restricted`, not prohibited).

## Explicitly disabled (with alternatives)

| Source | Alternative / gap |
|---|---|
| Official rules/news HTML | Manual citation into `control/rules/` (WP-01) |
| Authenticated manager state | Manual entry (ADR-0005); public entry endpoints for cross-check later |
| Club communications | Manual linked evidence (WP-08) |
| Competition schedules | FPL fixtures endpoint + manual revision notes |

## Out of scope for this pass

Tier 2/3 sources (vaastav, FBref, odds, line-up services, etc.) are not yet registered. They remain disabled-by-default until individual terms reviews — do not enable collectors for them.
