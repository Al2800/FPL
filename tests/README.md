# Testing

The authoritative offline quality gate is:

```bash
python -m pytest
```

`pyproject.toml` fixes test discovery to `tests/` and enables strict pytest
configuration and marker validation. GitHub Actions runs the same command on
Python 3.11, 3.12, 3.13 and 3.14 for every pull request and every push to
`main`.

## Per-bead testing

Each implementation bead follows the same progression:

1. Run the smallest relevant test module while changing the code.
2. Add or update regression, contract or golden-case tests for the behaviour.
3. Run `python -m pytest` before closing the bead.
4. Record the exact commands and results in the Beads completion comment.
5. Let GitHub Actions repeat the complete suite on all supported interpreters.

A bead is not complete when its focused tests pass but the complete suite fails.
Known failures that pre-date the bead must be recorded explicitly and tracked;
they must not be silently ignored or converted to unconditional skips.

## Offline boundary

The suite must be reproducible without credentials or live network access. It
may exercise collectors only through committed fixtures, fakes or mocks. CI
must never call live FPL endpoints, access authenticated manager state, control
a browser or write external account state.

Historical datasets and raw snapshots remain local and are not required for
the authoritative gate. Tests that cover them must use small committed fixtures
or fail with a clear opt-in prerequisite outside the default suite.
