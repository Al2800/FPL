# Live-entry review — 2026-10-10

- observed_at: 2026-10-10T07:06:23Z
- companion input: `reports/strategy-research/2026-10-10-live-entry-decision-input.md`
- companion advisory: `reports/strategy-research/2026-10-10.md`
- model_evidence_run: `composer-2.5:2026-10-10T070623Z`
- ledger tip: `7208a3ee9bff218a7a8e0cf9e75d04c0fd231f28270ed87f908b3be686a96364`
- account writes: false

## Verdict

Both tracked entries should **prefer roll** into GW6 (~3h to deadline). Availability moved in the owners’ favour on Van Hecke and Pedro (and Palmer on the no-Haaland arm), while Isak/Gakpo hardened to **unavailable** for City.

| entry | action | confidence |
|---|---|---|
| 8522487 | Lineup only: Van Hecke XI, Diop bench; Haaland (C) / Bruno (VC); no FT | medium-high |
| 7337262 | Prefer roll; Palmer (C) restored; accept Isak blank → Pedro autosub; WC only if owner counts ≥3 holes | medium |

## Evidence that changed the call

- Spurs: Van Hecke available `model:d71e4802…` (admitted)
- LFC: Isak unavailable `model:abd411a7…`; Gakpo unavailable `model:0cc3c0b4…` (admitted)
- Chelsea Pedro/Palmer: bootstrap `a`/100% + Alonso page text; **not** ledger-admitted (host HTTP 500)

## Risks

- ~3h deadline pressure — avoid speculative FTs
- 7337262 Obi remains `u` — second bench after Pedro is weak if Pedro also blanks
- Semenyo/Rice still doubtful on 7337262
- Packet bind remains predecessor `weekly-2026-08-11`
