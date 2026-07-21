# Podcast / transcript ingestion

**Phase:** 4 · **§19:** Podcast/transcript ingestion

## Purpose

Turn permitted audio into timestamped transcripts that feed the same document → claim pipeline as articles.

## Anticipated interfaces

- `source_documents` with `media_type: audio|transcript`
- Passage offsets: start/end seconds on `document_passages`
- Transcription job metadata: model version, observed_at, error flags (bronze layer)

## Prerequisites

- Source registry entry with transcription allowed_use
- WP-08 claim extraction contracts

## Activation criteria

- Permitted source **and** reliable transcription quality on a pilot set
- Injection tests extended to transcript text (WP-08 patterns)

## Non-goals (Phase 1)

- No ASR pipeline; no podcast collectors
