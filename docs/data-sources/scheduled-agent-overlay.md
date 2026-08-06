# Scheduled evidence/challenger overlay (ticket 11)

Deadline-relative agent stages run on the **subscription Codex sol** surface
(ADR-0021 / ADR-0024). They do not use API keys and must not enable web search
or workspace writes beyond sealed response artefacts.

| Checkpoint | Offset | Arms | Wall-clock (ADR-0016) |
| --- | --- | --- | --- |
| T-48h | 48h before deadline | evidence | ≤ 8 min |
| T-8h | 8h before deadline | evidence refresh | ≤ 8 min |
| T-2h | 2h before deadline | evidence + challenger | ≤ 8 + 5 min |
| T-90m | 90m before deadline | **hard stop** | deterministic plan + degraded GDR |

Policy: `control/policies/scheduled-agent-overlay-v1.json`.

## Offline / CI path

Forced-timeout degrade (no Codex invocation):

```powershell
python -m scripts.run_scheduled_agent_overlay `
  --deadline 2026-08-15T10:00:00Z `
  --now 2026-08-15T08:10:00Z `
  --code-commit <sha> `
  --deterministic-candidate path\to\candidate.json `
  --evidence-request path\to\evidence-request.json `
  --checkpoint T-2h `
  --force-timeout `
  --traces-dir reports\traces `
  --out data\live-shadow\agent-overlay\timeout-result.json
```

Pass the result into `run_gameweek(..., agent_overlay=...)`. The GDR records
`agent_overlay.status`, citations when completed, and degrade reasons on
timeout / T-90m.

## Unattended host path

1. Build a hash-bound request with `build_hosted_request` / fork adapters.
2. Invoke Codex **sol** with `approval_policy=never`, read-only attestation,
   **no** web search, writing only a hosted response JSON under
   `data/live-shadow/agent-overlay/`.
3. Materialise/validate with `python -m scripts.run_scheduled_agent_overlay`
   supplying `--evidence-response` / `--challenger-response`.
4. Call `run_gameweek` with the overlay result.

Traces land at `reports/traces/{run_id}.jsonl` (ADR-0010).
