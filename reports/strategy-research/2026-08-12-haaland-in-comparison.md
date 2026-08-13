# Haaland-in host-scored comparison — 2026-08-12

- bound_packet / checkpoint: `weekly-2026-08-11`
- packet sha: `65eba1feb8c6f6f9707789e0cbf6533baf9fdffa57ac872e10b8bc6badcd3651`
- Haaland: id `411`, £15.5m
- search tried: `2426` legal candidates; scorer rejects: `53`
- verdict: `haaland_in_does_not_beat_robust`

## Baselines

- Robust objective: `240.724705` (`eafe0eda68a68456…`)
- Deterministic objective: `244.244457`

## Best Haaland-in (robust-mode score)

- Robust-mode objective: `230.309624` (delta vs robust `-10.415081`)
- Deterministic-mode objective: `234.052114` (delta vs deterministic `-10.192343`)
- Bank: `0.0`
- Dropped from robust: Thiago, Donnarumma, B.Fernandes
- Fillers added: Verbruggen, Groß
- Captain / vice: Gibbs-White / Raya
- Proposal sha (robust mode): `e3c0d9edbf2f42d7a054f899cc98d093024735e4a4886292212ab3d6e4aec32f`

### 15

Raya, Verbruggen, Van Hecke, Groß, João Pedro, Mitchell, Tarkowski, Wilson, Virgil, Semenyo, Haaland, Obi, Gibbs-White, E.Le Fée, Truffert

### GW1

- XI: Raya, Tarkowski, Virgil, Van Hecke, Gibbs-White, Semenyo, E.Le Fée, Wilson, Groß, Haaland, João Pedro
- Bench: Verbruggen, Mitchell, Truffert, Obi
- Formation: `{'DEF': 3, 'MID': 5, 'FWD': 2}`

## Host handoff

- human_reference objective: `234.052114`
- human_reference proposal sha: `d1b6348ef8281b7557166e1ebda8b99a3b8cd245d4cdb54b4248285ffbfe95b1`
- Account writes: false; owner approval still required

## Top alternatives (by robust-mode objective)

1. obj `230.309624` (Δ `-10.415081`) — drop Thiago, Donnarumma, B.Fernandes; add Verbruggen, Groß
2. obj `230.271713` (Δ `-10.452992`) — drop Thiago, Donnarumma, B.Fernandes; add Leno, Groß
3. obj `230.18776` (Δ `-10.536945`) — drop Thiago, Donnarumma, B.Fernandes; add Petrović, Groß
4. obj `230.094783` (Δ `-10.629922`) — drop Thiago, Wilson, B.Fernandes; add Groß, Ampadu
5. obj `230.094783` (Δ `-10.629922`) — drop Thiago, Wilson, B.Fernandes; add Ampadu, Groß

## Best Haaland + Bruno (constrained)

- candidates tried: `0`
- verdict: `no_legal_haaland_bruno_found`

No legal Haaland+Bruno 15 found in the bounded search.
