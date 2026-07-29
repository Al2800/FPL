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
observations. Records with `available_at >= deadline` are quarantined.

## Prerequisites

- Registered official FPL bootstrap and fixtures sources remain enabled.
- `control/rules/2026-27.yaml` is present and hashable.
- Optional families may be absent; the manifest must name each gap.
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

If the odds artifact is missing, or every quote has
`available_at >= deadline`, the checkpoint still admits mandatory official state
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
