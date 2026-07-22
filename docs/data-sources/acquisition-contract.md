# Immutable acquisition contract

Every source adapter writes through `src.ingestion.acquisition`. The boundary
separates permission to contact a source from permission to exercise its adapter:

- `live` mode calls `assert_collectable` before the HTTP client is invoked;
- `fixture` mode requires a complete registry entry but never accepts a client or
  performs network access;
- both modes produce the same versioned source-snapshot manifest.

## Artefacts

Each acquisition stores the raw response, including an empty or error response,
and a sibling `*.meta.json` manifest. The manifest records source and origin,
registry version, observation time, acquisition mode and status, SHA-256 content
identity, byte count, bounded schema detection and structured failure evidence.

Body and manifest writes are immutable. An identical retry may reuse an existing
path only when its bytes match; different bytes at the same path fail rather than
overwrite evidence. `manifest_id` excludes collection time, so the same source,
origin, content, status and detected shape reproduce the same logical identity.

## Adapter rule

Adapters must call the acquisition gate before any external I/O. Disabled sources
may ship fixture-backed contract tests, but enabling their registry entry remains
a separate owner-controlled decision. CI uses only fixtures and mock transports;
it never contacts a live source or requires credentials.
