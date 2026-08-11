# ADR-0027: Committed derived decision artefacts

- Status: accepted
- Date: 2026-08-11

## Context

The daily strategy agent runs on an ephemeral cloud VM from the committed
tree. Two governance artefacts it depends on were previously local-only:

1. The sealed initial-squad checkpoint artefacts live under `reports/live/`
   (gitignored, ADR-0002 scale rationale). Every briefing therefore reported
   `bound_packet_sha256: unavailable` and had no deterministic comparator.
2. The model-evidence availability ledger written by
   `scripts/ingest_model_evidence_run.py` defaulted to `data/live-shadow/`
   (gitignored). Each cloud run started with `prior_ledger_sha256: none`, so
   admitted claims could never chain or accumulate across days, and cited
   claim IDs pointed at ledgers that vanished with the VM.

ADR-0002's exclusion targets raw capture bodies and bulk snapshots. The two
artefacts above are compact, derived, hash-bound decision surfaces with no
raw page content (the ingest policy is ephemeral fetch, hash then discard).

## Decision

Commit the derived decision surface; keep raw artefacts local-only.

1. `scripts/publish_decision_packet_summary.py` copies the recommendation,
   selection, gap panel, availability blend and checkpoint binding for a
   sealed checkpoint to `reports/strategy-research/packets/<checkpoint>.json`
   (committed). Full input packets, EP vector files and fixture audits stay
   under `reports/live/` and remain gitignored; the summary carries their
   binding hashes.
2. The daily strategy automation runs the model-evidence ingest with
   `--ledger-root reports/evidence-review/ledgers --output-root
   reports/evidence-review/ledgers` and commits the resulting
   content-addressed availability ledger and run audit alongside the review
   Markdown. The latest committed ledger is the prior for the next run, so
   `prior_ledger_sha256` chains across days and cited claim IDs stay
   resolvable from the repository alone.

## Consequences

- Briefings can bind `bound_packet_sha256` and quote deterministic comparator
  arms from the committed packet summary on any machine or VM.
- Admitted claims accumulate in an auditable chain under version control;
  reviews, audits and ledgers travel together in the same PR.
- Repository grows by roughly 300 KB per sealed checkpoint plus a few KB per
  model run; acceptable for a private repository, revisit if checkpoint
  frequency increases materially.
- Raw capture retention policy (ADR-0002) is unchanged.
