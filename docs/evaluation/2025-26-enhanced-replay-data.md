# 2025/26 enhanced replay: data boundary and pre-flight review

## Outcome

The enhanced replay can be prepared, but it cannot honestly be described as a
strictly feature-complete historical simulation. It is an exploratory,
production-ineligible replay with a complete *accounting* of all intended
feature families.

The materialised index is
`evals/episodes/enhanced/2025-26/input-index.json`. Each Gameweek has its own
`input-pack.json`, bound to the canonical v2 episode by hashes. The pack never
contains an outcome payload, evidence text, or raw odds.

## Coverage

| Family | Strict | Degraded | Exploratory only | Unavailable | Interpretation |
|---|---:|---:|---:|---:|---|
| Official FPL state | 0 | 37 | 1 | 0 | Prior-GW outcomes are usable after a conservative completion bound; fixture revisions and exact deadline prices are not archived |
| Promoted/transfer context | 0 | 0 | 1 | 37 | GW1 retrospective candidate pool only; no immutable registration ledger |
| Team strength | 37 | 0 | 0 | 1 | Current-season results are safe from GW2; GW1 lacks a prior-season promoted-team pack |
| Player ratings | 0 | 0 | 0 | 38 | No verified point-in-time 2025/26 ratings source |
| Set-piece roles | 0 | 0 | 0 | 38 | No immutable historical official role snapshots |
| Odds | 0 | 0 | 38 | 0 | Sanitised pre-closing comparator exists locally; quote-level availability time is absent |
| Unstructured evidence | 0 | 0 | 38 | 0 | Publication predates deadlines, but project observation and case selection are retrospective |

“Strict” in this table applies to an entire family. A degraded family can still
contain strict observations; official state from GW2 onward has a strict
lagged-results observation alongside an exploratory final-export fixture
schedule.

## Areas most likely to make the replay fail or mislead

### 1. Retrospective evidence leakage

All recovered news and analyst evidence was observed by this project after the
historical decision. Its original publication date is retained, but it is not
substituted for `available_at`. It can be used only by a separately labelled
exploratory evidence arm. The continuously frozen no-evidence arm is mandatory.

### 2. Initial-15 hindsight

The reconstructed GW1 candidate pool has 689 players and excludes outcome
fields, but it is not an immutable launch snapshot. Player membership, prices,
and identity bridges still come from retrospective exports. The optimizer can
exercise the live-shaped selection process, but the result cannot establish
2026/27 skill. The official Scout seed remains the historical control.

### 3. Fixture and deadline precision

The episode deadline is reconstructed as first kickoff minus 90 minutes.
Fixture rows come from a final export, so later fixture revisions are not
recoverable. Packs retain the fixture payload hash but mark it exploratory,
rather than accepting the episode manifest's synthetic cutoff timestamp as
proof of historical availability.

### 4. Price and market-state precision

Vaastav Gameweek prices are post-Gameweek exports, not exact pre-deadline
quotes. Sale values and affordability can therefore differ from what a real
manager saw. The enhanced replay must preserve the existing price-confidence
labels and report any plan whose legality is sensitive to a £0.1m change.

### 5. Odds contamination

The raw Football-Data file contains results and closing odds as well as
pre-closing odds. The replay must never read that mixed file directly. The
builder creates a local, result-free comparator through
`normalise_football_data_csv`; committed packs retain only its hashes and
timing limitation. Closing odds remain outcome-side evaluation data.

### 6. Missing ratings and set-piece roles

Neither family has a trustworthy 2025/26 point-in-time source. Structured form
must not be renamed “player ratings”, and later penalty goals must not be used
to rewrite an earlier set-piece hierarchy. Both families fall back
byte-identically.

### 7. State and arm contamination

The input pack does not own manager state. The season runner must create
independent squad, bank, purchase-price, free-transfer, chip, and hit state for
every arm. No arm may start a Gameweek from another arm's state, even when their
previous plans were identical.

### 8. Canonical mutation

Only `episode-manifest.json`, `observed.json`, and `identity-map.json` are read.
The 114-file allowlisted tree hashes to
`a6c1bb9bb42ea2ac42af2d3d7045e4fae8fd661bea7ffb2bc7caaea1f029033e`.
The builder checks the hash before and after materialisation and writes only to
the separate enhanced tree.

## Replay setup required by FPL-bsw.38.13

Before GW1 is scored, the season runner must refuse to start unless:

1. all 38 pack hashes validate against the index;
2. the canonical allowlisted tree hash still matches;
3. every feature family has a declared status, gap, and fallback;
4. no strict observation has `available_at >= decision_cutoff`;
5. GW1 contains both the official Scout control seed and the separately
   labelled optimized-seed branch;
6. odds and retrospective evidence are isolated from the shared strict engine;
7. a frozen no-evidence arm is present;
8. every arm receives its own state chain;
9. hidden outcomes remain inaccessible until each proposal is frozen; and
10. output decomposition reports seed, weekly structured policy, evidence, and
    inherited-state interaction separately.

## Reproduction

From the repository root:

```powershell
.venv\Scripts\python.exe -m scripts.build_enhanced_replay_inputs
```

The command uses only already-acquired local data. It creates a local,
gitignored result-free odds comparator, writes the committed hash/reference
packs, accepts byte-identical reruns, and refuses conflicting overwrites. It
does not download data, mutate canonical episodes, or run the replay.
