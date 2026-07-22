# Cross-source identity resolution

Source records never join directly on display names. `src.data.identity_resolution`
maps a source entity into a stable player, team or fixture ID using the versioned
catalogue in `control/identities/source-aliases.yaml`.

Resolution first attempts an exact source identifier within the requested season
and effective-date interval. If no identifier matches, it tries a Unicode- and
punctuation-normalised exact alias. Fuzzy matching is deliberately excluded from
the automatic path.

One canonical candidate is `resolved`; multiple canonical candidates enter the
`review` queue; no candidate is `unresolved`. Decision-critical callers use
`require_resolved` and therefore fail closed on either non-resolved state. Reports
retain candidates plus resolved/review/unresolved counts and match rate.

The mapping hash excludes input order but includes catalogue version, season,
sources and resolution results. Replaying the same mapping set is therefore
deterministic and suitable for benchmark provenance.
