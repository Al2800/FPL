# Daily strategy research briefings

Composer 2.5 morning briefings that rebuild chip / premium / captain / DEFCON
situational understanding before the deterministic initial-squad checkpoint.

- Prompt: `prompts/daily-strategy-research/v1.md`
- Loop: `docs/evaluation/2026-27-daily-agent-strategy-loop.md`
- Recipe: `config/automations/2026-27-daily-strategy-research.json`

## Dry-run (before official cron)

One-shot subagent test against the thin `weekly-2026-07-31` packet:

- Prompt: `prompts/daily-strategy-research/dry-run-2026-08-01.md`
- Briefing: `reports/strategy-research/2026-08-01.md`

Do not activate the Cursor Automation until dry-run notes in that briefing are
reviewed and any agreed prompt tweaks land in `v1.md`.
