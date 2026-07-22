# Source profile: Betfair Historical Data

- Registry: `betfair-historical` (disabled).
- Use: timestamped exchange-price baseline selected strictly before the cutoff.
- Candidate package: BASIC, advertised as free with one-minute price intervals and
  no volume. This appears sufficient for cutoff-price features but must be tested.
- Required provenance: package, market and selection IDs, update timestamp,
  acquisition date and raw-file hash.
- Gate: confirm account/package cost, terms, permitted private retention and market
  coverage before acquisition.
- Fallback: football-data closing odds, explicitly labelled non-point-in-time.
