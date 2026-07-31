# Testing

## Portable authoritative suite

The fresh-clone quality gate is:

```bash
python -m pytest -m "not artifact_backed"
```

GitHub Actions runs that command on **Python 3.13** for every pull request and
every push to `main`. It must pass without gitignored Benchmark v0 episode
trees or raw Vaastav dumps.

See `docs/evaluation/ci-artifact-test-boundary.md`.

## Artifact-backed integration suite

Tests marked `artifact_backed` exercise governed historical episode trees and
related local-only roots. Run them only when those artifacts are present:

```bash
python -m pytest -m artifact_backed
# or
FPL_ARTIFACT_ROOT=/path/to/approved-checkout python -m pytest -m artifact_backed
```

If the artifacts are missing, the command fails with a provisioning error. It
does not silently pass.

`python3 -m scripts.download_historical` restores registered raw history only;
it does not provision governed episode bundles.

## Local workflow

1. Run the smallest relevant portable test module while changing code.
2. Add or update regression, contract or golden-case tests.
3. Run `python -m pytest -m "not artifact_backed"` before opening a PR.
4. If you changed historical-integration behaviour and have approved local
   artifacts, also run `python -m pytest -m artifact_backed`.

## Offline boundary

The portable suite must be reproducible without credentials or live network
access. Collectors may be exercised only through committed fixtures, fakes or
mocks. CI must never call live FPL endpoints, access authenticated manager
state, control a browser or write external account state.
