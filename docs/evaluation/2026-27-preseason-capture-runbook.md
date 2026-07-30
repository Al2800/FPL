# 2026/27 preseason snapshot capture runbook

## What one checkpoint does

One invocation writes raw immutable official artifacts plus a sealed checkpoint
manifest under:

`data/snapshots/2026-27/preseason/<checkpoint-id>/`

The manifest binds source-registry version, `observed_at`, `available_at`,
deadline, artifact paths and SHA-256 digests, per-family
input/admitted/duplicate/quarantined/missing counts, quarantine reasons, source
gaps, code commit, ruleset hash and predecessor checkpoint hash.

The mutable index at `control/manifests/2026-27-preseason.json` records admitted
checkpoint hashes for downstream consumers (`FPL-guz`, `FPL-jm0`).

## Checkpoint IDs

| ID | Meaning |
|---|---|
| `launch` | First successful official launch-state capture |
| `weekly-YYYY-MM-DD` | Scheduled weekly capture until deadline week |
| `T-48h` | 48 hours before the official GW1 deadline |
| `T-24h` | 24 hours before the official GW1 deadline |
| `T-8h` | 8 hours before the official GW1 deadline |
| `T-2h` | 2 hours before the official GW1 deadline |
| `final` | Last successful pre-deadline capture (mapped from runner `final_pre_deadline`) |

Official GW1 deadline: **2026-08-21 18:30 Europe/London** (`2026-08-21T17:30:00Z`).

A missed checkpoint remains a recorded gap. Never backfill it from later
observations. Records whose `available_at` is later than the checkpoint's
`observed_at` are quarantined, even when they precede the GW1 deadline.

## Prerequisites

- Registered official FPL bootstrap and fixtures sources remain enabled.
- `control/rules/2026-27.yaml` is present and hashable.
- Optional families may be absent; the manifest must name each gap.
- Every binary optional artifact requires a JSON sidecar containing the exact
  registered `source_id`, `observed_at`, and `available_at`. The artifact and
  sidecar are copied into the checkpoint and independently hash-bound.
- Disabled, prohibited, unregistered, or rights-unresolved sources are rejected.
- No FPL account credentials are required or accepted.

## Successful launch (fixture / offline)

```bash
python scripts/capture_preseason_snapshot.py \
  --season 2026-27 \
  --checkpoint-id launch \
  --deadline 2026-08-21T17:30:00Z \
  --observed-at 2026-07-27T10:05:27Z \
  --output-root data/snapshots/2026-27/preseason \
  --bootstrap-file /path/to/bootstrap-static.json \
  --fixtures-file /path/to/fixtures.json \
  --no-network
```

Expected stdout includes `"status": "degraded"` when optional families are
absent, plus a `content_sha256` for the sealed checkpoint manifest. Re-running
the identical command returns the same hashes and performs no duplicate append.

The legacy live-shadow launch (`20260727T100527Z`, capture
`e2499ad7...2460`) remains the historical first capture; bind it by hash rather
than rewriting its raw bytes.

## Degraded optional odds

```bash
python scripts/capture_preseason_snapshot.py \
  --season 2026-27 \
  --checkpoint-id T-24h \
  --deadline 2026-08-21T17:30:00Z \
  --observed-at 2026-08-20T17:30:00Z \
  --output-root data/snapshots/2026-27/preseason \
  --bootstrap-file /path/to/bootstrap-static.json \
  --fixtures-file /path/to/fixtures.json \
  --odds-artifact /path/to/odds-or-empty.json \
  --no-network
```

If the odds artifact is missing, or every quote was first available after this
checkpoint's `observed_at`, the checkpoint still admits mandatory official state
and records `licensed_odds` under `source_gaps` with an explicit reason. It must
never invent zero odds.

## Failed mandatory official state

```bash
python scripts/capture_preseason_snapshot.py \
  --season 2026-27 \
  --checkpoint-id final \
  --deadline 2026-08-21T17:30:00Z \
  --observed-at 2026-08-21T17:25:00Z \
  --output-root data/snapshots/2026-27/preseason \
  --no-network
```

Expected: non-zero exit, stderr containing `Mandatory official state`, and no
admitted `manifest.json` under the checkpoint directory.

## Live network capture

Omit `--no-network` and the local official files only when registry-approved
live collection is intended. The CLI fetches `/api/bootstrap-static/` and
`/api/fixtures/` through the existing snapshot acquisition boundary. Never pass
secrets on the command line.

## Recovery and immutability

- Identical request → return existing artifact bytes and hashes.
- Different payload at the same immutable path → fail closed.
- Do not overwrite sealed 2025/26 artifacts or the legacy live-shadow launch
  tree.
- Downstream optimisers must read the index manifest hashes, not ad-hoc current
  files.

## Launch-context binding

Each checkpoint attempts to bind the reviewed launch context by default from:

- `control/identities/2026-27-launch-context.json`
- `control/identities/world-cup-2026-priors.csv`

This is a derived, local input, not a new collector: it does not enable the
manual `world-cup-2026` source or fetch any account/private data. The sealed
`launch_context` family is admitted only when all of the following hold:

- the context semantic `content_sha256` verifies;
- its `official_bootstrap.sha256` equals the exact raw official bootstrap in
  this checkpoint;
- its referenced World Cup CSV digest equals the supplied CSV bytes; and
- the context and official binding observations are not later than the
  checkpoint observation and remain strictly before the GW1 deadline.

On admission the checkpoint stores three independently content-addressed files:
the context JSON, World Cup CSV, and a generated provenance envelope. The family
records each path and hash, together with the bound official-bootstrap hash.

Use explicit overrides only for a separately reviewed successor context:

```bash
python scripts/capture_preseason_snapshot.py \
  --season 2026-27 \
  --checkpoint-id weekly-2026-08-03 \
  --deadline 2026-08-21T17:30:00Z \
  --observed-at 2026-08-03T12:00:00Z \
  --bootstrap-file /path/to/bootstrap-static.json \
  --fixtures-file /path/to/fixtures.json \
  --launch-context-path /path/to/reviewed-launch-context.json \
  --world-cup-priors-path /path/to/reviewed-world-cup-priors.csv \
  --no-network
```

A changed official player universe yields
`families.launch_context.status: "degraded"` with reason
`official_bootstrap_hash_mismatch`; it copies no context, World Cup, or
provenance bytes and cannot provide typed context downstream. Do not suppress the
gap or reuse the older context: create the reviewed successor through FPL-757.
A changed context or CSV at an existing checkpoint conflicts rather than
rewriting the immutable manifest.
