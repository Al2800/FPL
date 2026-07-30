# W4 persistent availability challenger

`availability-persistence-v1` is a named, default-disabled projection
challenger. It receives only accepted claims from the immutable live-evidence
ledger, copied into an append-only availability ledger with the original source
hash, exact player identity and temporal fields. It can reduce only its own
solver-input copy; structured and frozen no-evidence controls remain unchanged.

An official `i`/`s`/`u` status suppresses the challenger projection, `d` applies
the configured bounded start-probability reduction, and `a` creates an explicit
recovery that supersedes unresolved negative state and restores the structured
baseline. Exact duplicate intake is idempotent; a changed duplicate ID, invalid
identity, unknown source, conflicting state or post-cutoff claim fails closed.

Run the historical qualification report with:

```powershell
C:\Users\Alastair\FPL\.venv\Scripts\python.exe -m scripts.evaluate_w4_historical_availability
```

The tracked GW33--GW36 evidence bundles are deliberately not injected: their
source material was recovered after the historical deadlines, source IDs are
not live-registry entries, publication precision is not exact and immutable
source hashes are unavailable. The resulting report is a useful no-leakage
qualification, not a claim that the challenger was historically scored.

Promotion remains blocked: live claims must accumulate through the official
capture/ledger path, the V2 policy must be explicitly enabled by a reversible
policy-data change, and an owner-approved ADR is required.
