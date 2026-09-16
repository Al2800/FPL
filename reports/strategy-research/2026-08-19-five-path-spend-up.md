# Spend-the-budget review — five GW1 paths

- packet_sha256: `53b889602cd7dbb8cb734c2890ed096d2f5f2faf605e9a7918c7fe5fb22b0e25`
- observed_at: `2026-08-19T13:28:05Z`
- rule: keep each path's 15-slot shape; spend leftover ITB on same-position upgrades
- account_writes: `false`

A and B already spend £100.0. C–E leave money on the table as unused bank.
This review force-spends that bank and host-scores the resulting 15 on the
same 19 August packet. It does not invent a sixth path.

| Path | Bank now | Best spend-up | Robust after | Δ vs current | Bank after |
|---|---:|---|---:|---:|---:|
| A-tight-ep-robust | 0.0 | already spent | 255.88 | 0 | 0.0 |
| B-loose-ep-deterministic | 0.0 | already spent | 255.63 | 0 | 0.0 |
| C-premium-override-advisory | 0.5 | Diop → Disasi (+£0.5, EP +6.58) | 236.52 | +2.20 | 0.0 |
| D-death-zone-playing-15 | 2.0 | Kinsky → Raya (+£1.5, EP +14.44); Calafiori → Guéhi (+£0.5, EP +6.36) | 251.74 | +11.45 | 0.0 |
| E-minutes-first | 1.0 | Truffert → Senesi (+£0.5, EP +2.95); E.Le Fée → Anderson (+£0.5, EP +2.84) | 252.46 | +4.95 | 0.0 |

## Per path

### A-tight-ep-robust
- current robust: `255.878647` · bank `0.0`
- weakest spend in the 15: Obi £4.5 EP 3.7 start_p 0.05 (bench), Beto £5.5 EP 10.6 start_p 0.41 (bench), Mitchell £4.5 EP 13.9 start_p 0.81 (bench), Pickford £5.5 EP 16.3 start_p 0.94 (bench)
- leftover pounds: none. Any money on the table is trapped in low-EP bench pieces, not ITB.

### B-loose-ep-deterministic
- current robust: `255.625166` · bank `0.0`
- weakest spend in the 15: Obi £4.5 EP 3.7 start_p 0.05 (bench), Beto £5.5 EP 10.6 start_p 0.41 (bench), Van Hecke £5.0 EP 15.5 start_p 0.81 (bench), Donnarumma £5.5 EP 17.2 start_p 0.91 (bench)
- leftover pounds: none. Any money on the table is trapped in low-EP bench pieces, not ITB.

### C-premium-override-advisory
- current robust: `234.320568` · bank `0.5`
- weakest spend in the 15: Diop £4.0 EP 5.5 start_p 0.26 (bench), van Ewijk £4.0 EP 5.9 start_p 0.30 (bench), Dubravka £4.0 EP 10.6 start_p 0.76 (bench), Xhaka £5.5 EP 14.1 start_p 0.74 (bench)
- best spend-up: Diop → Disasi (+£0.5, EP +6.58)
- robust after: `236.516906` (Δ +2.196)
- bank after: `0.0`
- captain / vice: B.Fernandes / Haaland
- XI: Verbruggen, Van Hecke, Shaw, Mitchell, B.Fernandes, Gibbs-White, E.Le Fée, Wilson, Haaland, Thiago, João Pedro
- bench: Dubravka, Xhaka, Disasi, van Ewijk
- other legal spends:
  - Diop → Cash (+£0.5, EP +7.00) → `236.454` (+2.133), bank 0.0
  - Diop → F.Kadıoğlu (+£0.5, EP +6.98) → `236.511` (+2.191), bank 0.0
  - Diop → Kayode (+£0.5, EP +6.81) → `236.354` (+2.033), bank 0.0

### D-death-zone-playing-15
- current robust: `240.284717` · bank `2.0`
- weakest spend in the 15: Kinsky £4.5 EP 4.1 start_p 0.19 (bench), Shaw £4.5 EP 12.9 start_p 0.85 (bench), Calvert-Lewin £6.0 EP 14.9 start_p 0.70 (bench), Truffert £5.5 EP 16.5 start_p 0.90 (bench)
- best spend-up: Kinsky → Raya (+£1.5, EP +14.44); Calafiori → Guéhi (+£0.5, EP +6.36)
- robust after: `251.738616` (Δ +11.454)
- bank after: `0.0`
- captain / vice: B.Fernandes / Gibbs-White
- XI: Raya, Guéhi, Tarkowski, Van Hecke, B.Fernandes, Gibbs-White, Semenyo, E.Le Fée, Wilson, Thiago, João Pedro
- bench: Verbruggen, Calvert-Lewin, Shaw, Truffert
- other legal spends:
  - Kinsky → Raya (+£1.5, EP +14.44); Calafiori → Senesi (+£0.5, EP +6.15) → `251.523` (+11.238), bank 0.0
  - Kinsky → Donnarumma (+£1.0, EP +13.11); Calafiori → Virgil (+£1.0, EP +6.59) → `250.805` (+10.520), bank 0.0
  - Kinsky → Pickford (+£1.0, EP +12.24); Calafiori → Virgil (+£1.0, EP +6.59) → `250.065` (+9.780), bank 0.0

### E-minutes-first
- current robust: `247.509262` · bank `1.0`
- weakest spend in the 15: Mitchell £4.5 EP 13.9 start_p 0.81 (bench), Calvert-Lewin £6.0 EP 14.9 start_p 0.70 (bench), Truffert £5.5 EP 16.5 start_p 0.90 (bench), Donnarumma £5.5 EP 17.2 start_p 0.91 (bench)
- best spend-up: Truffert → Senesi (+£0.5, EP +2.95); E.Le Fée → Anderson (+£0.5, EP +2.84)
- robust after: `252.461762` (Δ +4.952)
- bank after: `0.0`
- captain / vice: B.Fernandes / Gibbs-White
- XI: Raya, Virgil, Senesi, Van Hecke, B.Fernandes, Gibbs-White, Semenyo, Anderson, Xhaka, Thiago, João Pedro
- bench: Donnarumma, Calvert-Lewin, Shaw, Mitchell
- other legal spends:
  - Truffert → Tarkowski (+£0.5, EP +2.60); E.Le Fée → Anderson (+£0.5, EP +2.84) → `252.110` (+4.601), bank 0.0
  - Truffert → Guéhi (+£0.5, EP +3.16); Xhaka → Gravenberch (+£0.5, EP +1.96) → `251.417` (+3.908), bank 0.0
  - Truffert → Senesi (+£0.5, EP +2.95); Xhaka → Gravenberch (+£0.5, EP +1.96) → `251.199` (+3.689), bank 0.0

## Interpretation

- Spending leftover ITB is not the same as beating path A, except that
  D's £2.0 is large enough to buy A's premiums (Raya + Guéhi) and close
  most of the gap. That spend-up stops being a death-zone team.
- C's £0.5 only upgrades a junk defender; Haaland still costs ~19 vs A.
- E's £1.0 as Senesi + Anderson is the cleanest declared spend and
  becomes the closest alternative to A.
- A/B already spent £100.0; their leftover is Obi (start_p 0.05) and
  Beto minutes, not unused pounds.
- Owner approval is still required before any FPL entry.
