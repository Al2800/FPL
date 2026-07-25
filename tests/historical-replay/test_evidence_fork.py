from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from src.orchestration.evidence_fork import (
    EvidenceForkError,
    run_isolated_evidence_fork,
    validate_reconstructed_bundle,
)


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "evals/evidence-forks/2025-26/gw-12/evidence-bundle.json"
CANONICAL = ROOT / "reports/benchmarks/2025-26"
EPISODES = ROOT / "data/benchmark-v0/episodes/v2/2025-26"


def _tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(item.read_bytes())
    return digest.hexdigest()


def test_reconstructed_bundle_rejects_post_deadline_publication() -> None:
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    invalid = deepcopy(bundle)
    invalid["sources"][0]["published_at"] = "2025-11-22T11:00:01Z"

    with pytest.raises(EvidenceForkError, match="published after decision cutoff"):
        validate_reconstructed_bundle(invalid)


def test_isolated_gw12_fork_is_deterministic_and_preserves_control(tmp_path: Path) -> None:
    canonical_before = _tree_hash(CANONICAL / "gw-12")
    output = tmp_path / "fork"

    first = run_isolated_evidence_fork(
        season="2025-26",
        gameweek=12,
        evidence_bundle_path=BUNDLE,
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        output_root=output,
    )
    first_hash = _tree_hash(output)
    second = run_isolated_evidence_fork(
        season="2025-26",
        gameweek=12,
        evidence_bundle_path=BUNDLE,
        canonical_root=CANONICAL,
        episode_root=EPISODES,
        output_root=output,
    )

    assert first == second
    assert _tree_hash(output) == first_hash
    assert _tree_hash(CANONICAL / "gw-12") == canonical_before
    assert first["canonical_gross_points"] == 29
    assert first["fork_gross_points"] == 43
    assert first["gross_points_delta"] == 14
    assert first["selected_transfer_names"] == [
        {
            "player_out": "Gabriel dos Santos Magalhães",
            "player_in": "Daniel Muñoz Mejía",
        }
    ]
    assert first["active_chip"] is None
    assert first["hit_cost"] == 0
    assert first["exploratory_only"] is True
    assert not (output / "gw-13").exists()

    plan = json.loads((output / "validated-plan.json").read_text(encoding="utf-8"))
    outcome = json.loads((output / "realised-outcome.json").read_text(encoding="utf-8"))
    assessment = json.loads(
        (output / "evidence-assessment.json").read_text(encoding="utf-8")
    )
    assert plan["frozen_at"] == "2025-11-22T11:00:00Z"
    assert outcome["plan_sha256"] == plan["content_sha256"]
    assert assessment["production_eligible"] is False
    assert assessment["exploratory_admissible"] is True
