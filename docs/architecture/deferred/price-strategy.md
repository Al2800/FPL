# Price-change strategy

**Phase:** 5 · **§19:** Price-change strategy

## Purpose

Optional transfers timed for value/price rises without violating budget or hit policy.

## Anticipated interfaces

- `price_predictions`: player_uid, predicted_delta, horizon_hours, model_version, available_at
- Optimiser objective term (optional flag): expected_points + λ·expected_value_delta − hits
- GDR: recommendation notes when a transfer is price-motivated

## Prerequisites

- Official price-change mechanics and any predictor data understood
- Selling-price rules already in validator (WP-06)

## Activation criteria

- Predictor source registered with licence/allowed_use
- Decision objective and λ documented (ties to risk preference ADR-0006)

## Non-goals (Phase 1)

- No price-speculation mode in the Phase 1 optimiser
