# Official FPL live-shadow capture

The live-shadow command records public official FPL state for future cutoff-safe
evaluation. It performs evidence collection only: there is no authentication,
browser interaction, manager-state read, squad mutation or model execution.

## Command

Run from the repository root with the dependency-complete environment:

    .venv/Scripts/python.exe -m scripts.capture_fpl_live_shadow

The default targets are the public bootstrap-static and fixtures endpoints. Raw
responses, endpoint manifests and a capture summary are written below
data/live-shadow/fpl and remain gitignored. A run uses one UTC observed_at value
for every endpoint so its evidence boundary is unambiguous.

## Immutability and repeatability

Each endpoint is persisted through the governed acquisition contract with its URL,
HTTP status, registry version, retrieval time, SHA-256 content identity and schema
shape. Existing files may only be reused when their bytes are identical. The
capture summary records endpoint manifest identities and refuses a conflicting
overwrite at the same observation time.

The command returns zero only when every configured endpoint succeeds. A partial
HTTP or transport failure is still persisted with structured evidence and returns
one so schedulers can alert without discarding the successful endpoint captures.
Registry refusal or an immutable-path conflict returns two.

## Scheduling boundary

The command is safe for a read-only scheduler. Recommended in-season cadence is
daily plus T-48h, T-8h and T-2h before a deadline. Scheduling itself remains an
operator decision; overlapping runs should use distinct seconds-resolution
observation times. No credentials or browser profile should be attached.

Captured evidence is private and local under ADR-0001, ADR-0002 and ADR-0018. Do
not redistribute source payloads.
