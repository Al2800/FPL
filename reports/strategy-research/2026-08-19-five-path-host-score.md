# Five-path host rescore — 2026-08-19

- packet_kind: `reconstructed_official_snapshot`
- packet_sha256: `53b889602cd7dbb8cb734c2890ed096d2f5f2faf605e9a7918c7fe5fb22b0e25`
- forecast_model_version: `live-faithful-v1.feature-complete`
- observed_at: `2026-08-19T13:28:05Z`
- decision_cutoff: `2026-08-21T17:30:00Z`
- bound_11_aug_packet_present: `False`
- account_writes: `False`

This is **not** a hash-bind of `65eba1fe…`. The 11 August live
input-packet is local-only and was not on this machine. A–E were
scored on a cutoff-safe reconstruction from the official bootstrap
and fixtures captured at `observed_at`, plus the committed player
prior. Published 11 August A/B objectives stay in the table for
reference; same-packet deltas use the reconstructed A/B scores.

| Path | Robust | Δ vs A robust | Deterministic | Δ vs A det | Bank | Notes |
|---|---:|---:|---:|---:|---:|---|
| A-tight-ep-robust | 251.531421 | +0.000000 | 254.909773 | +0.000000 | 0.0 | comparator A |
| B-loose-ep-deterministic | unscored (Nunes excluded, status d) |  | unscored (Nunes excluded, status d) |  | — | comparator B; Nunes may be absent if status ≠ a |
| C-premium-override-advisory | 234.320568 | -17.210853 | 238.606831 | -16.302942 | 0.5 | Haaland + Bruno; 12 Aug bound robust was 215.71 |
| D-death-zone-playing-15 | 240.284717 | -11.246704 | 244.282274 | -10.627499 | 2.0 | first host score |
| E-minutes-first | 247.509262 | -4.022159 | 250.852971 | -4.056802 | 1.0 | first host score |

## Host-optimal GW1 usage (robust mode)

### A-tight-ep-robust
- objective: `251.531421`
- proposal_sha256: `23f0a71dd3dfac8073142143d4419af457d1009ed798e85ca5dba87370b2d0ab`
- Captain / vice: B.Fernandes / Gibbs-White
- XI: Raya, Virgil, Tarkowski, Van Hecke, B.Fernandes, Gibbs-White, Semenyo, E.Le Fée, Wilson, Thiago, João Pedro
- Bench: Donnarumma, Mitchell, Truffert, Obi
- Formation: `{'DEF': 3, 'MID': 5, 'FWD': 2}`

### B-loose-ep-deterministic
- scorer: `Declared squad references unknown players: 389`

### C-premium-override-advisory
- objective: `234.320568`
- proposal_sha256: `fe34fd45b92dd4e7254f6502d79f4dd1f51f6d2cf2dde17b80c8b9236d21390a`
- Captain / vice: B.Fernandes / Haaland
- XI: Verbruggen, Van Hecke, Shaw, Mitchell, B.Fernandes, Gibbs-White, E.Le Fée, Wilson, Haaland, Thiago, João Pedro
- Bench: Dubravka, Xhaka, Diop, van Ewijk
- Formation: `{'DEF': 3, 'MID': 4, 'FWD': 3}`

### D-death-zone-playing-15
- objective: `240.284717`
- proposal_sha256: `4fa6127c8d650df381f16961b3b271957cb4bcaad4282b07b5236c87db40b3ee`
- Captain / vice: B.Fernandes / Gibbs-White
- XI: Verbruggen, Tarkowski, Van Hecke, Calafiori, B.Fernandes, Gibbs-White, Semenyo, E.Le Fée, Wilson, Thiago, João Pedro
- Bench: Kinsky, Calvert-Lewin, Shaw, Truffert
- Formation: `{'DEF': 3, 'MID': 5, 'FWD': 2}`

### E-minutes-first
- objective: `247.509262`
- proposal_sha256: `a88a9a1f4c3fdbba116d1d7caa3e229bc1fdea8fbd5b0d0ab77d7875c2c926f3`
- Captain / vice: B.Fernandes / Gibbs-White
- XI: Raya, Virgil, Van Hecke, Shaw, B.Fernandes, Gibbs-White, Semenyo, E.Le Fée, Xhaka, Thiago, João Pedro
- Bench: Donnarumma, Calvert-Lewin, Mitchell, Truffert
- Formation: `{'DEF': 3, 'MID': 5, 'FWD': 2}`

## Interpretation

- Rank on this reconstruction, robust mode: **A 251.53 > E 247.51 > D 240.28 > C 234.32**. B is unscored because Matheus Nunes (id 389) is official-status `d`.
- C remains the most expensive override. The 12 August bound-packet haircut was ~25 points; this reconstruction still leaves it last among legal paths.
- Owner approval is still required before any FPL entry.
- Do not average the five paths.
