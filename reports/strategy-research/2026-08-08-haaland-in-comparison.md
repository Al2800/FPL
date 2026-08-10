# Haaland-in host-scored comparison — 2026-08-08

- bound_packet / checkpoint: `weekly-2026-08-08`
- packet sha: `d430ba7670a7a98bea636ea6830d2ec3197e565415905e1fea8ab912b2cff422`
- Haaland: id `411`, £15.5m
- search tried: `251` legal candidates; scorer rejects: `46`
- verdict: `haaland_in_does_not_beat_robust`

## Baselines

- Robust objective: `257.441115` (`83f0bfc5bd945eda…`)
- Deterministic objective: `259.191879`

## Best Haaland-in (robust-mode score)

- Robust-mode objective: `250.412541` (delta vs robust `-7.028574`)
- Deterministic-mode objective: `253.895143` (delta vs deterministic `-5.296736`)
- Bank: `0.0`
- Dropped from robust: João Pedro, Semenyo, B.Fernandes
- Fillers added: Szoboszlai, Groß
- Captain / vice: Haaland / Rice
- Proposal sha (robust mode): `8ab39bf2a230861854757d9eb55d8588761724221b5e7d753ef43c3ceb4bb616`

### 15

Raya, Verbruggen, Groß, Rice, Tarkowski, Beto, Virgil, Szoboszlai, Guéhi, Rogers, Haaland, Obi, Anderson, Senesi, Mukiele

### GW1

- XI: Raya, Mukiele, Guéhi, Virgil, Senesi, Tarkowski, Rice, Rogers, Anderson, Szoboszlai, Haaland
- Bench: Verbruggen, Groß, Beto, Obi
- Formation: 5-4-1

## Host handoff

- human_reference objective: `253.895143`
- human_reference proposal sha: `19a9e911772f5c66a391b5925ebcbedecebb2b9c173a078c6b4d89038ae79201`
- Account writes: false; owner approval still required

## Top alternatives (by robust-mode objective)

1. obj `250.412541` (Δ `-7.028574`) — drop João Pedro, Semenyo, B.Fernandes; add Szoboszlai, Groß
2. obj `250.412541` (Δ `-7.028574`) — drop João Pedro, Semenyo, B.Fernandes; add Groß, Szoboszlai
3. obj `250.128865` (Δ `-7.31225`) — drop João Pedro, Semenyo, B.Fernandes; add Wilson, Gravenberch
4. obj `250.128865` (Δ `-7.31225`) — drop João Pedro, Semenyo, B.Fernandes; add Gravenberch, Wilson
5. obj `249.89582` (Δ `-7.545295`) — drop João Pedro, Semenyo, B.Fernandes; add Wilson, E.Le Fée

## Best Haaland + Bruno (constrained, host-scored)

- verdict: `haaland_bruno_does_not_beat_robust`
- Robust-mode objective: `236.065839` (delta vs robust `-21.375276`)
- human_reference objective: `241.272039`
- Dropped from robust: João Pedro, Semenyo, Rogers, Mukiele
- Fillers: Hughes, Reed, Aznou
- Captain / vice: B.Fernandes / Haaland
- Proposal sha (robust mode): `b85e2c00ac91bf336110b1a4417e40146f732eb9fcf4a727e318d1d9840b1ced`
- 15: Raya, Verbruggen, Rice, Hughes, Tarkowski, Aznou, Beto, Reed, Virgil, Guéhi, Haaland, B.Fernandes, Obi, Anderson, Senesi
- XI: Raya, Guéhi, Virgil, Senesi, Tarkowski, Aznou, B.Fernandes, Rice, Anderson, Haaland, Beto
- Bench: Verbruggen, Hughes, Reed, Obi

### Strategy implication

On this packet, neither unconstrained Haaland-in nor Haaland+Bruno beats the robust comparator under the host scorer. Challenger `forced_re_run` is satisfied: the premium alternative was scored; robust remains preferred on objective.
