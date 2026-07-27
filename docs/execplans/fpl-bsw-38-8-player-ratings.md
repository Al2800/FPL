# FPL-bsw.38.8 — point-in-time player ratings

## Purpose

Add a reproducible, cutoff-safe player-ratings input without violating provider
terms or silently changing the shared forecast. The implementation must remain
useful when the selected open source has no current Premier League coverage.

## Decisions

- Select the preregistered `statsbomb-open` source for zero-cost research use.
- Disable automated FotMob and Sofascore collection because their current terms
  prohibit it.
- Automate only the deterministic transformation of an authorised local source
  envelope; do not add a network fetcher.
- Resolve identities only through explicit mappings. Quarantine rather than
  guess.
- Keep ratings shadow-only with no effect weights and byte-identical fallback.

## Work

- [x] Review the sealed feature-family preregistration and provider terms.
- [x] Define the source, cost, coverage and automation boundary.
- [x] Implement immutable snapshot, quarantine, ledger and feature payload.
- [x] Add a local idempotent capture CLI.
- [x] Add source configuration, operational manifest and documentation.
- [x] Run focused tests and address failures.
- [x] Run the complete repository suite.
- [x] Record results and close the Bead.`r`n- [x] Commit and push `main`.

## Validation log

- Initial ratings plus sealed-ablation set: 17 passed.
- Registry-gated ratings, registry and sealed-ablation set after governance and
  quarantine refinements: 26 passed.
- A temporal-provenance edit briefly broke the timestamp tuple contract; the
  focused suite caught it immediately. The helper was corrected and the same
  26-test set passed again.
- Ratings-only final focused set after quarantine-rate reporting: 8 passed.
- `compileall` passed for the ingestion module and local capture CLI.`r`n- Complete repository suite: 609 passed in 407.12 seconds.
- Bead FPL-bsw.38.8 closed after acceptance evidence was recorded.
