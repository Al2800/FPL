# Approved article corpus

**Phase:** 4 · **§19:** Full approved article corpus

## Purpose

Retain rights-cleared news/article bodies (beyond Tier 1 FPL `news` fields) as `source_documents` for evidence agents.

## Anticipated interfaces

- Existing: `source_documents`, `document_passages` (`control/schemas/evidence/`)
- Registry: one entry per publisher in `control/sources/source-registry.yaml` with `licence_status` + `allowed_use`
- Storage: gitignored `data/raw/<source_id>/` snapshots; normalised rows reference `content_hash_sha256` only in Git

## Prerequisites

- WP-02 registry discipline; WP-08 document/claim lifecycle
- ADR-0001/0002 retention and non-redistribution

## Activation criteria

- Rights and retention confirmed per source (human gate)
- Collector remains `enabled: false` until registry row is complete

## Non-goals (Phase 1)

- No bulk scraping; no corpus download scripts beyond FPL Tier 1
