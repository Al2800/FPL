# 2026/27 daily agent-driven strategy loop

Architect map: `docs/architecture/2026-27-decision-data-flow.md`.

## Decision stance

The **Composer 2.5 web-search strategy agent is the primary advisory
decision**. That is where reasoning and strategising happen (chip paths,
structure, captains, DEFCON stacks, when to ignore pure EP).

Hard stats and the six-GW live-faithful packet are the **statistical base** the
agent must read. Deterministic / robust optimiser arms remain **comparators**
and legality stress tests. The host **rules-validates and rescores** the
agent’s declared 15. The owner still approves any real FPL entry.

LLMs never enforce rules, never execute account writes, and never silently
edit the frozen packet.

## Daily sequence

```text
07:00 UTC  Composer 2.5 strategy decision automation
           ├─ Lane A: official discovery + model evidence candidates
           ├─ Read latest frozen packet / comparator arms if present
           ├─ Lane B: web search (strategy debate)
           └─ PRIMARY ADVISORY DECISION
               recommended 15 + chips + captains + falsifiers
               concise decision rationale trace + host ledger audit
               → reports/strategy-research/YYYY-MM-DD.md

Capture     Immutable official snapshot (scheduler / manual)
            → data/snapshots/.../manifest.json

Checkpoint  scripts/run_initial_squad_checkpoint.py
            → freeze six-GW packet + deterministic/robust comparators

Handoff     Host validates/rescores the strategy agent’s declared 15
            against that frozen packet (human_reference / external proposal
            shape). Challenger may stress the rationale.
            Owner approval still required for manual entry.
```

When the checkpoint does not yet exist that morning, the agent still decides
from the best available packet/bootstrap and marks `bound_packet_sha256:
unavailable` with lower confidence. Re-bind after the checkpoint lands.

## What each layer owns

| Concern | Owner |
|---|---|
| Prices, priors, six-GW EP/start/uncertainty | Statistical base (deterministic) |
| Official injury/team-news leads | Lane A → model candidate → host validation → ledger |
| Chip path, squad thesis, named 15, captain | **Strategy agent (final advisory)** |
| Legal validation + objective rescoring | Deterministic host |
| Comparator EP-max / robust beams | Deterministic / robust arms |
| FPL site entry | Owner only |

## Governance wall

- Community/X content informs the strategy decision with citations; it is not
  auto-admitted to the evidence ledger.
- Registered official URLs may be visited ephemerally by the model run, but
  only the host admission script can append a structured claim.
- Model traces and host audit hashes remain visible in the committed briefing;
  raw pages are discarded.
- `ready_for_manual_entry` stays false until owner sign-off on a named,
  host-validated proposal hash.

## Activate

Recipe: `config/automations/2026-27-daily-strategy-research.json`  
Prompt: `prompts/daily-strategy-research/v1.md`  
UI: [cursor.com/automations](https://cursor.com/automations) — **Composer 2.5**,
cron `0 7 * * *` UTC, repo `Al2800/FPL` @ `main`.
