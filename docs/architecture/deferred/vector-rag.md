# Vector database / RAG

**Phase:** 4 · **§19:** Vector database/RAG

## Purpose

Semantic retrieval over passages when SQL/full-text is insufficient for evidence assembly.

## Anticipated interfaces

- Embed against `document_passages` (passage_id, document_id, text, available_at)
- Retrieval API (conceptual): `search(query, available_at<=deadline, top_k) → passage_ids[]`
- Provenance on every hit: source_id, published_at, content_hash
- Index version recorded on `agent_runs` / Gameweek Decision Record pipeline block

## Prerequisites

- Article/passage corpus with point-in-time filters (WP-08)
- Ablation harness that can compare vector vs SQL/full-text on the same deadline slice

## Activation criteria

- Demonstrated benefit over SQL/full-text on golden evidence cases (plan §19)
- Cost/latency within agent budgets (ADR-0016)

## Non-goals (Phase 1)

- No vector DB dependency; schemas already allow later full-text/vector without blocking (WP-03)
