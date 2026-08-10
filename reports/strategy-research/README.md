# Daily strategy research briefings

Composer 2.5 morning briefings that rebuild chip / premium / captain / DEFCON
situational understanding before the deterministic initial-squad checkpoint.

- Prompt: `prompts/daily-strategy-research/v1.md`
- Loop: `docs/evaluation/2026-27-daily-agent-strategy-loop.md`
- Recipe: `config/automations/2026-27-daily-strategy-research.json`

## Dry-run (before official cron)

Subagent tests against the thin `weekly-2026-07-31` packet:

| Run | Prompt | Briefing |
|---|---|---|
| Composer 2.5 | `prompts/daily-strategy-research/dry-run-2026-08-01.md` | `reports/strategy-research/2026-08-01.md` |
| Grok 4.5 | `prompts/daily-strategy-research/dry-run-2026-08-01-grok.md` | `reports/strategy-research/2026-08-01-grok-4.5.md` |

Evidence stance: ADR-0022 (no invented start probs; hard team-news gather;
structure guided, content agnostic).

Do not activate the Cursor Automation until dry-run notes are reviewed and any
agreed prompt tweaks land in `v1.md`.
