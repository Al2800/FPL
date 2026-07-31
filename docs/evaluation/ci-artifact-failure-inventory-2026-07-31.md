# Clean-clone failure inventory — 31 July 2026

Captured when claiming ticket 01. Undifferentiated `python -m pytest` on a
clean Linux checkout: **30 failed**, **22 skipped**, 803 passed.

## Failures

| Test | Class | Disposition |
|---|---|---|
| `tests/agent-evals/test_agent_fork_adapter.py` (5) | artifact-backed episodes | `artifact_backed` |
| `tests/agent-evals/test_agent_fork_gw13_gw14.py` (2) | artifact-backed episodes | `artifact_backed` |
| `tests/agent-evals/test_agent_fork_gw15_gw17.py` (2) | artifact-backed episodes | `artifact_backed` |
| `tests/agent-evals/test_agent_fork_gw18_gw22.py::test_gw18_starts_from_actual_gw17_fork` | artifact-backed episodes | `artifact_backed` |
| `tests/agent-evals/test_agent_fork_gw18_gw22.py::test_degraded_sol_v1_archive_remains_byte_identical` | cross-platform hash | canonical hasher + refreshed expectations |
| `tests/agent-evals/test_agent_fork_gw18_gw22.py::test_partial_sol_v2_diagnostic_archive_remains_byte_identical` | cross-platform hash | canonical hasher + refreshed expectations |
| `tests/agent-evals/test_agent_fork_gw23_gw29.py` (2) | artifact-backed episodes | `artifact_backed` |
| `tests/agent-evals/test_agent_fork_gw30_gw38.py` (2) | artifact-backed episodes | `artifact_backed` |
| `tests/data/test_preseason_snapshot_capture.py` (3) | portable CLI (`python` missing) | `sys.executable` |
| `tests/forecasting/test_launch_context.py::test_successor_builder_cli_reports_paths_hashes_and_delta` | portable CLI (`python` missing) | `sys.executable` |
| `tests/historical-replay/test_chip_policy.py::test_partial_chip_inventory_builds_and_revalidates_weekly_decision` | artifact-backed episodes | `artifact_backed` |
| `tests/historical-replay/test_evidence_fork.py::test_isolated_gw12_fork_is_deterministic_and_preserves_control` | artifact-backed episodes | `artifact_backed` |
| `tests/historical-replay/test_evidence_fork.py::test_committed_longitudinal_fork_is_independent_and_preserves_control` | cross-platform hash | canonical span hasher + refreshed sealed report |
| `tests/historical-replay/test_gw2_setup.py::test_gw3_setup_uses_only_completed_history_and_arm_owned_state` | artifact-backed episodes | `artifact_backed` |
| `tests/historical-replay/test_weekly_evidence_programme.py::test_short_programme_separates_isolated_and_compounded_state` | artifact-backed episodes | `artifact_backed` |
| `tests/integration/test_fpl_knowledge_overlay.py::test_fpl_overlay_resolves_an_isolated_project_runtime` | local knowledge runtime | `artifact_backed` |
| `tests/orchestration/test_early_season_evidence_replay.py` (2) | artifact-backed episodes | `artifact_backed` |
| `tests/orchestration/test_historical_seed_counterfactual.py` (2) | artifact-backed episodes | `artifact_backed` |

## Prior skips (already artifact-shaped)

Squad contingency, genuine replay, GW2/GW3 setup, event challenger and
benchmark-evaluation skips for missing Vaastav/episodes were classified
`artifact_backed` and excluded from the portable suite.
