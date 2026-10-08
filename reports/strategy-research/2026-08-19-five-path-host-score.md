# Five-path host rescore — 2026-08-19

- packet_kind: `weekly_2026-08-19_live_faithful`
- packet_sha256: `53b889602cd7dbb8cb734c2890ed096d2f5f2faf605e9a7918c7fe5fb22b0e25`
- forecast_model_version: `live-faithful-v1.feature-complete`
- observed_at: `2026-08-19T13:28:05Z`
- decision_cutoff: `2026-08-21T17:30:00Z`
- account_writes: `False`

Bound packet is the 19 August live-faithful reconstruction from that
day's official bootstrap and fixtures. A and B are the optimiser arms
on this packet. C–E are declared alternatives scored against it.
The 11 August packet is not used.

| Path | Robust | Δ vs A robust | Deterministic | Δ vs B det | Bank | Notes |
|---|---:|---:|---:|---:|---:|---|
| A-tight-ep-robust | 255.878647 | +0.000000 | 259.116819 | +0.152938 | 0.0 | today's robust optimiser |
| B-loose-ep-deterministic | 255.625166 | -0.253481 | 258.963881 | +0.000000 | 0.0 | today's deterministic optimiser |
| C-premium-override-advisory | 234.320568 | -21.558079 | 238.606831 | -20.357050 | 0.5 | Haaland + Bruno advisory |
| D-death-zone-playing-15 | 240.284717 | -15.593930 | 244.282274 | -14.681607 | 2.0 | declared mid-price spine |
| E-minutes-first | 247.509262 | -8.369385 | 250.852971 | -8.110910 | 1.0 | declared minutes-first |

## Host-optimal GW1 usage (robust mode)

### A-tight-ep-robust
- objective: `255.878647`
- proposal_sha256: `3a9377765eddb3440cf319cb2dd760dd4d8877065c18edf20babb058cbc204ff`
- Captain / vice: B.Fernandes / Rice
- XI: Raya, Guéhi, Virgil, Senesi, Tarkowski, B.Fernandes, Rice, Semenyo, Rogers, Anderson, João Pedro
- Bench: Pickford, Mitchell, Beto, Obi
- Formation: `{'DEF': 4, 'MID': 5, 'FWD': 1}`

### B-loose-ep-deterministic
- objective: `255.625166`
- proposal_sha256: `9056be933e74aa8fd015b5b680861fe8062cd10db31c62a861eea46a108b1c68`
- Captain / vice: B.Fernandes / Gibbs-White
- XI: Raya, Guéhi, Virgil, Senesi, Tarkowski, B.Fernandes, Gibbs-White, Rice, Rogers, Anderson, João Pedro
- Bench: Donnarumma, Van Hecke, Beto, Obi
- Formation: `{'DEF': 4, 'MID': 5, 'FWD': 1}`

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

- Rank on this packet, robust mode: **A 255.88 > E 247.51 > D 240.28 > C 234.32**.
- A and B are today's optimiser 15s. They are not the 11 August squads.
- C remains the most expensive override (~21.6 vs A).
- Owner approval is still required before any FPL entry.
- Do not average the five paths.
