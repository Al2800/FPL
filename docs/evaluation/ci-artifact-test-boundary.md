# CI artifact test boundary

**Ticket:** `.scratch/outstanding-beads/issues/01-ci-artifact-boundary.md`  
**Status:** portable authoritative suite on Python 3.13

## Commands

Portable authoritative suite (fresh clone, no governed episodes/raw dumps):

```bash
python -m pytest -m "not artifact_backed"
```

Artifact-backed integration suite (requires approved local artifacts):

```bash
# default root is the repository checkout
python -m pytest -m artifact_backed

# or point at an approved artifact checkout
FPL_ARTIFACT_ROOT=/path/to/approved-checkout python -m pytest -m artifact_backed
```

If the artifact-backed suite is requested without `data/benchmark-v0/episodes`,
pytest fails with a clear provisioning error. It does not silently pass.

`python3 -m scripts.download_historical` restores registered raw history only.
It does **not** provision governed Benchmark v0 episode trees.

## Clean-clone inventory (31 July 2026)

Baseline before the boundary landed: **30 failed**, **22 skipped**, 803 passed
under undifferentiated `python -m pytest`.

| Class | Count | Disposition |
|---|---|---|
| Artifact-backed episode/raw dependency | 25 failures + prior skips | `artifact_backed` marker; excluded from portable CI |
| Portable CLI interpreter (`python` missing) | 4 failures | Fixed to `sys.executable` |
| Cross-platform sealed tree hash drift | 3 failures | Canonical POSIX/LF hasher + refreshed sealed expectations |
| Local knowledge-runtime path | 1 failure | `artifact_backed` (Windows-local tools path) |

No test was deleted. Marker membership is the classification record.

## CI

GitHub Actions runs only the portable command on Python 3.13 and prints the
deselected artifact-backed count via pytest's `-ra` summary.
