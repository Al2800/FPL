# WP-08 status — evidence pipeline

**Package:** WP-08  
**Done when (plan):** document/claim/signal/adjustment round-trip with citations and expiry; conflicts surfaced not merged; injection golden cases pass; challenger escalation enforced on approval.

## Checklist

- [x] Document → claim → signal → **proposed adjustment** interfaces (schemas + builders)
- [x] `proposed_adjustments` schema added to catalog (Section 9.4)
- [x] Citations + `expires_at` required on claims/adjustments
- [x] Conflicts recorded via `claim_conflicts`; `merge_claims_forbidden` preserves both
- [x] Challenger outcomes (§13.4) gate automatic approval (`evaluate_challenger_outcomes`)
- [x] Injection-resistant extraction golden case (`evals/golden-cases/evidence/injection-presser.json`)
- [x] ADR-0013 + `control/policies/evidence-adjustments.yaml` (Open Decision 10 — Proposed)
- [ ] Live LLM evidence/challenger agents — blocked on Open Decision 8 (provider + secrets)

## Run

```bash
PYTHONPATH=. python3 -m pytest tests/test_evidence_lifecycle.py tests/contracts/test_schemas.py -q
```
