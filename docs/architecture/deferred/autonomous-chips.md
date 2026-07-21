# Autonomous chip use

**Phase:** 8 or later · **§19:** Autonomous chip use

## Purpose

Allow the system to activate Wildcard / Free Hit / Bench Boost / Triple Captain without a same-day human click — exceptional trust bar.

## Anticipated interfaces

- Separate policy file: `control/policies/chip-autonomy.yaml` (future)
- Chip recommendation already optional on GDR; autonomy adds `execution.chip_authorized_by`
- Irreversible actions require unique approval token per chip per Gameweek

## Prerequisites

- Exceptional reliability across prior automated line-up/transfer seasons
- Separate owner policy (not implied by transfer automation)

## Activation criteria

- Written policy + ADR superseding “human-gated chips”
- Kill-switch tested

## Non-goals (Phase 1–7)

- Chips remain human-gated recommendations only
