# Automatic transfers

**Phase:** 7/8 · **§19:** Automatic transfers

## Purpose

Execute approved transfer list with hit costs already validated.

## Anticipated interfaces

- Same `executions` record family with step list: confirm selling prices → place transfers → read-back squad
- Hard stop if live prices diverge from decision snapshot beyond tolerance

## Prerequisites

- Stronger controls than line-up-only: dual confirmation or typed approve phrase
- Selling-price and club-limit validator pass on intended post-transfer squad

## Activation criteria

- Explicit approval covering transfers (not inherited from line-up-only approval)
- Dry-run transfer path successful on a throwaway/test context where possible

## Non-goals (Phase 1)

- No transfer automation
