# WP-04 Historical-data assessment

**Status:** Complete for Done-when criteria (local dumps gitignored; reports committed)

## Artifacts

| Report | Purpose |
|---|---|
| [vaastav-profile.md](vaastav-profile.md) | Coverage, gaps, licence, leakage, identity match rates |
| [football-data-profile.md](football-data-profile.md) | Results/odds CSV coverage and leakage notes |
| [disabled-sources-profile.md](disabled-sources-profile.md) | FBref, Understat, ClubElo, Core-Insights, World Cup |
| [news-recoverability.md](news-recoverability.md) | Evidence-dependent replay feasibility (§17.6) |
| [training-targets.md](training-targets.md) | Targets per model component |
| [summary.json](summary.json) | Machine-readable headline metrics |
| [world-cup-2026-priors-template.csv](../../control/identities/world-cup-2026-priors-template.csv) | Manual template for §7.7 priors |

## Reproduction

```bash
PYTHONPATH=. python3 scripts/download_historical.py
PYTHONPATH=. python3 scripts/profile_historical.py
```

Raw data stays under `data/raw/` (gitignored).

## Done-when checklist

| Criterion | Status |
|---|---|
| Each candidate dataset profiled (coverage, gaps, licence, leakage) | Met |
| Identity-match rates measured and reported | Met (~60–69% consecutive-season FPL `code` overlap) |
| Point-in-time news assessment | Met — feasibility **low** without external archives |
| Training targets recommended per component | Met |
