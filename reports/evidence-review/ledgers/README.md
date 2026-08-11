# Committed availability ledger chain

Content-addressed availability ledgers and model-run audits written by
`scripts/ingest_model_evidence_run.py` when the daily strategy automation
runs with `--ledger-root`/`--output-root` pointing here (ADR-0027).

- `availability-ledger-<sha256>.json` — one immutable ledger version per
  admission; the latest is the prior for the next run, so
  `prior_ledger_sha256` chains across days.
- `<run-id>.audit.json` — the host audit for each model evidence run.

These are derived, hash-bound claim records. Raw fetched page bodies are
never stored (ephemeral fetch, hash then discard). Do not edit or delete
files here; supersede by appending a new ledger version.
