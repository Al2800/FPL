# GW23-GW29 audited evidence review

This review covers the accepted experimental trajectory from the repaired GW22 `sol-v3` successor through terminal GW29. Historical evidence was recovered after the season and is exploratory; it is not eligible for headline agent-performance claims.

| GW | Accepted version | Evidence decision | Transfer | Captain | Fork | Canonical | Evidence delta |
|---:|:---|:---|:---|:---|---:|---:|---:|
| 23 | sol-v2 | Abstained | Bank | Haaland | 36 | 41 | 0 |
| 24 | sol-v1 | Abstained | Bruno Guimarães → Harry Wilson | Haaland | 45 | 60 | 0 |
| 25 | sol-v3 | Abstained | Foden → Bruno Fernandes | Bruno Fernandes | 73 | 58 | 0 |
| 26 | sol-v3 | Applied Mateta expected minutes 50.1 → 0 | Guiu → Mateus Mané | Gabriel | 64 | 68 | 0 |
| 27 | sol-v1 | Abstained | Bank | Haaland | 43 | 43 | 0 |
| 28 | sol-v1 | Applied Wirtz expected minutes 62.5 → 0 | Sánchez → Emi Martínez | Haaland | 82 | 67 | 0 |
| 29 | sol-v1 | Abstained | Chalobah → Guéhi | Semenyo | 67 | 53 | 0 |
| **Total** |  |  |  |  | **410** | **390** | **0** |

The block gained 20 points on the canonical trajectory. It entered GW23 four points behind the canonical cumulative comparison and therefore leaves GW29 sixteen points ahead. That gain is entirely attributable to the carried policy state and deterministic weekly choices, not the tested evidence. The paired same-state control matched the evidence plan and score in every gameweek.

The zero evidence delta is still informative. The positive or unresolved reports on Bruno Guimarães, Timber, and Haaland did not quantify a defensible change from the frozen baselines, so the agent correctly abstained. The strong Mateta and Wirtz absence reports did support large expected-minutes reductions, but neither player lay on the optimal transfer route before or after adjustment. The evidence pipeline therefore behaved conservatively and safely, but this seven-case sample did not test a decision boundary where evidence could flip a plan.

Five versions were deliberately rejected and preserved. GW23 `sol-v1` contained a future recovery timestamp. GW25 `sol-v1` used an invalid challenger enum and `sol-v2` expired its claim at the decision cutoff. GW26 `sol-v1` exceeded the 0.25 probability-delta cap and `sol-v2` returned an invalid challenger shape. These failures demonstrate that schema validation, expiry checks, delta bounds, write-once versioning, and independent gates are operational. They also show that the live orchestration needs automatic structured-output retries with explicit validator feedback.

Before the final GW30-GW38 block, the evidence sample should retain the same non-leakage rules but broaden beyond one hand-selected player per week. The live design should retrieve and extract all decision-relevant squad and candidate news, then let the bounded agent rank claims. For the historical experiment, at least one preregistered boundary case should target an owned player or near-tied transfer candidate; otherwise valid evidence can remain causally inert by construction.

The accepted state chain is byte-stable on rerun. Both agent gates completed for every accepted week, canonical tree hashes remained unchanged, failed versions have no comparison artifacts, and GW29 intentionally produced no successor or GW30 directory.
