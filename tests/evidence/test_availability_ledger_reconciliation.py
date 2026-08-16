from __future__ import annotations

import json
from pathlib import Path

from src.evidence.availability_ledger import validate_availability_ledger
from src.forecasting.live_faithful import artifact_hash


ROOT = Path(__file__).resolve().parents[2]
LEDGERS = ROOT / "reports" / "evidence-review" / "ledgers"

PRIOR = "f2397d8fd295e2f630a2a9337d77abf2c8ca63f0d9fd14d501c4eddf60a4f777"
RESULT = "e065ec2649677864592d4b5b1501e05d8d64c267aa29305a90f845cf0a8fdf13"
PARALLEL = "4df25fc6ce68e4ecfe2ffd8cf32ea5be146991db7f78c9d267d5519a620d987a"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_2026_08_16_reconciliation_extends_canonical_15_august_tip() -> None:
    prior = _load(LEDGERS / f"availability-ledger-{PRIOR}.json")
    result = _load(LEDGERS / f"availability-ledger-{RESULT}.json")
    audit = _load(LEDGERS / "composer-2.5-2026-08-16T070218Z.audit.json")
    chain = _load(LEDGERS / "availability-ledger-chain-2026-08-16.json")

    validate_availability_ledger(prior)
    validate_availability_ledger(result)
    assert artifact_hash(result) == RESULT
    assert result["content_sha256"] == RESULT
    assert len(prior["claims"]) == 15
    assert len(result["claims"]) == 21
    assert result["claims"][:15] == prior["claims"]

    replayed = result["claims"][15:]
    assert len(replayed) == 6
    assert sum(bool(row.get("supersedes_claim_ids")) for row in replayed) == 5
    new_players = [
        row["player_uid"]
        for row in replayed
        if not row.get("supersedes_claim_ids")
    ]
    assert new_players == ["player:2026-27:165"]

    prior_ids = {row["claim_id"]: row["player_uid"] for row in prior["claims"]}
    for row in replayed:
        for superseded_id in row.get("supersedes_claim_ids", []):
            assert prior_ids[superseded_id] == row["player_uid"]

    assert audit["prior_ledger_sha256"] == PRIOR
    assert audit["resulting_ledger_sha256"] == RESULT
    assert audit["content_sha256"] == artifact_hash(audit)

    assert chain["status"] == "resolved"
    assert chain["canonical_tip_sha256"] == RESULT
    assert chain["sequence"][-1]["prior_ledger_sha256"] == PRIOR
    assert chain["sequence"][-1]["ledger_sha256"] == RESULT
    assert chain["superseded_parallel_tips"][0]["ledger_sha256"] == PARALLEL
    assert chain["content_sha256"] == artifact_hash(chain)
