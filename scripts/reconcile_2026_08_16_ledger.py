"""Deterministically reconcile the 2026-08-16 availability-ledger fork.

The 16 August model run was originally admitted against the stale 12 August
tip (b00a3606...) rather than the canonical 15 August tip (f2397d8f...).
This script replays the same six canonical claims against the correct prior,
using the repository's append/seal implementation, and publishes an explicit
chain record. It performs no network access and does not alter source claims.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

from src.evidence.availability_ledger import (
    append_availability_claim,
    validate_availability_ledger,
)
from src.forecasting.live_faithful import artifact_hash


ROOT = Path(__file__).resolve().parents[1]
LEDGER_DIR = ROOT / "reports" / "evidence-review" / "ledgers"
REVIEW_PATH = ROOT / "reports" / "evidence-review" / "2026-08-16-model-run-reconciled.md"
TEST_PATH = ROOT / "tests" / "evidence" / "test_availability_ledger_reconciliation.py"

B00 = "b00a36064f251c83f6fa48a43ad6f13852a32d4c96018c3b8aa1f9b87d3ae949"
LEDGER_14 = "62f5d4daebdb973e61ec4ab16630a73e85d5dbedfb81024f537d88da0bd3a790"
LEDGER_15 = "f2397d8fd295e2f630a2a9337d77abf2c8ca63f0d9fd14d501c4eddf60a4f777"
PARALLEL_16 = "4df25fc6ce68e4ecfe2ffd8cf32ea5be146991db7f78c9d267d5519a620d987a"
RECONCILED_16 = "e065ec2649677864592d4b5b1501e05d8d64c267aa29305a90f845cf0a8fdf13"

COMMIT_14 = "83ebe52e4dbaf8c851cc0af80b6352fb40faeb20"
COMMIT_15 = "e1f6c72c5fb3f25932ad69a95f7186e793540716"
COMMIT_16 = "92711d7a66af832b1edeb73f0da09c17118c6567"

PATH_14 = f"reports/evidence-review/ledgers/availability-ledger-{LEDGER_14}.json"
PATH_15 = f"reports/evidence-review/ledgers/availability-ledger-{LEDGER_15}.json"
PATH_PARALLEL = f"reports/evidence-review/ledgers/availability-ledger-{PARALLEL_16}.json"
PATH_RECONCILED = f"reports/evidence-review/ledgers/availability-ledger-{RECONCILED_16}.json"
AUDIT_PATH = "reports/evidence-review/ledgers/composer-2.5-2026-08-16T070218Z.audit.json"
CHAIN_PATH = "reports/evidence-review/ledgers/availability-ledger-chain-2026-08-16.json"

RUN_ID = "composer-2.5:2026-08-16T070218Z"
RUN_AVAILABLE_AT = "2026-08-16T07:02:18Z"
RESOLVED_AT = "2026-08-16T08:50:55Z"


def _git_show_json(commit: str, path: str) -> dict[str, Any]:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise TypeError(f"{commit}:{path} must contain a JSON object")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _latest_unsuperseded_match(
    ledger: Mapping[str, Any],
    incoming: Mapping[str, Any],
) -> str | None:
    source_ids = incoming.get("provenance", {}).get("source_ids", [])
    if len(source_ids) != 1:
        raise ValueError("incoming claim must bind exactly one source_id")
    source_id = str(source_ids[0])
    incoming_at = _parse(str(incoming["available_at"]))
    superseded = {
        str(claim_id)
        for claim in ledger["claims"]
        for claim_id in claim.get("supersedes_claim_ids", [])
    }
    matches: list[tuple[datetime, str]] = []
    for claim in ledger["claims"]:
        if (
            claim.get("player_uid") == incoming.get("player_uid")
            and claim.get("status") == incoming.get("status")
            and source_id in claim.get("provenance", {}).get("source_ids", [])
            and str(claim.get("claim_id")) not in superseded
            and _parse(str(claim["available_at"])) < incoming_at
        ):
            matches.append((_parse(str(claim["available_at"])), str(claim["claim_id"])))
    return max(matches)[1] if matches else None


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def _reconciled_audit(source_audit: Mapping[str, Any]) -> dict[str, Any]:
    audit = deepcopy(dict(source_audit))
    audit["prior_ledger_sha256"] = LEDGER_15
    audit["resulting_ledger_sha256"] = RECONCILED_16
    audit["content_sha256"] = artifact_hash(audit)
    return audit


def _chain_record(audit: Mapping[str, Any]) -> dict[str, Any]:
    record = {
        "schema_version": "1.0",
        "chain_id": "availability-ledger-chain:2026-27:2026-08-16",
        "season": "2026-27",
        "status": "resolved",
        "resolved_at": RESOLVED_AT,
        "canonical_tip_sha256": RECONCILED_16,
        "sequence": [
            {
                "ledger_sha256": B00,
                "path": f"reports/evidence-review/ledgers/availability-ledger-{B00}.json",
            },
            {
                "prior_ledger_sha256": B00,
                "ledger_sha256": LEDGER_14,
                "path": PATH_14,
            },
            {
                "prior_ledger_sha256": LEDGER_14,
                "ledger_sha256": LEDGER_15,
                "path": PATH_15,
            },
            {
                "prior_ledger_sha256": LEDGER_15,
                "ledger_sha256": RECONCILED_16,
                "path": PATH_RECONCILED,
            },
        ],
        "superseded_parallel_tips": [
            {
                "ledger_sha256": PARALLEL_16,
                "prior_ledger_sha256": B00,
                "path": PATH_PARALLEL,
                "status": "historical_noncanonical",
                "reason": (
                    "The 16 August claims were originally replayed against the "
                    "stale 12 August tip. The bytes are retained for audit only."
                ),
            }
        ],
        "reconciliation": {
            "run_id": RUN_ID,
            "audit_path": AUDIT_PATH,
            "accepted_claim_ids": list(audit["accepted_claim_ids"]),
            "appended_claim_count": 6,
            "supersession_count": 5,
            "new_player_claim_count": 1,
            "method": (
                "Replay the unchanged six canonical 16 August claims against "
                "the canonical 15 August ledger using repository append, "
                "supersession, ordering and content-hash semantics."
            ),
        },
    }
    return _seal(record)


def _review_markdown() -> str:
    return f"""# Model evidence run reconciliation — {RUN_ID}

- status: **complete**
- issue: the original 16 August admission used stale prior ledger `{B00}`
- canonical prior ledger: `{LEDGER_15}`
- superseded parallel tip: `{PARALLEL_16}`
- reconciled canonical tip: `{RECONCILED_16}`
- claims replayed: 6
- claims superseding 15 August evidence: 5
- wholly new player claims: 1 (João Pedro)
- source claims, source hashes and canonical claim IDs changed: no

## Resolution

The six already-admitted 16 August claims were replayed without alteration
against the canonical 15 August ledger. Haaland, Rodri, Saka, Saliba and
Timber now explicitly supersede their corresponding 15 August claims.
João Pedro remains a new claim.

The superseded `{PARALLEL_16}` ledger is retained as historical evidence but
is not a canonical tip. The authoritative sequence is:

`{B00}` → `{LEDGER_14}` → `{LEDGER_15}` → `{RECONCILED_16}`

## Validation

- Repository ledger validation passes for the prior and reconciled ledgers.
- The first 15 claims of the reconciled ledger are byte-equivalent to the
  canonical 15 August claim history.
- Claims remain ordered by `available_at`.
- Every supersession points to an earlier claim for the same player.
- The reconciled ledger content hash recomputes to `{RECONCILED_16}`.
- The corrected audit binds prior `{LEDGER_15}` to result `{RECONCILED_16}`.
"""


def _test_source() -> str:
    return f"""from __future__ import annotations

import json
from pathlib import Path

from src.evidence.availability_ledger import validate_availability_ledger
from src.forecasting.live_faithful import artifact_hash


ROOT = Path(__file__).resolve().parents[2]
LEDGERS = ROOT / "reports" / "evidence-review" / "ledgers"

PRIOR = "{LEDGER_15}"
RESULT = "{RECONCILED_16}"
PARALLEL = "{PARALLEL_16}"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_2026_08_16_reconciliation_extends_canonical_15_august_tip() -> None:
    prior = _load(LEDGERS / f"availability-ledger-{{PRIOR}}.json")
    result = _load(LEDGERS / f"availability-ledger-{{RESULT}}.json")
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

    prior_ids = {{row["claim_id"]: row["player_uid"] for row in prior["claims"]}}
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
"""


def main() -> None:
    ledger_14 = _git_show_json(COMMIT_14, PATH_14)
    prior = _git_show_json(COMMIT_15, PATH_15)
    parallel = _git_show_json(COMMIT_16, PATH_PARALLEL)
    source_audit = _git_show_json(COMMIT_16, AUDIT_PATH)

    validate_availability_ledger(ledger_14)
    validate_availability_ledger(prior)
    validate_availability_ledger(parallel)
    if ledger_14["content_sha256"] != LEDGER_14:
        raise ValueError("14 August ledger hash mismatch")
    if prior["content_sha256"] != LEDGER_15:
        raise ValueError("15 August ledger hash mismatch")
    if parallel["content_sha256"] != PARALLEL_16:
        raise ValueError("parallel 16 August ledger hash mismatch")

    replay_claims = [
        deepcopy(claim)
        for claim in parallel["claims"]
        if claim.get("available_at") == RUN_AVAILABLE_AT
    ]
    if len(replay_claims) != 6:
        raise ValueError(f"expected six 16 August claims, found {len(replay_claims)}")

    ledger = deepcopy(prior)
    for claim in replay_claims:
        claim.pop("supersedes_claim_ids", None)
        supersedes = _latest_unsuperseded_match(ledger, claim)
        if supersedes:
            claim["supersedes_claim_ids"] = [supersedes]
        ledger = append_availability_claim(ledger, claim)

    validate_availability_ledger(ledger)
    if ledger["content_sha256"] != RECONCILED_16:
        raise ValueError(
            "reconciled ledger hash mismatch: "
            f"{ledger['content_sha256']} != {RECONCILED_16}"
        )
    if ledger["claims"][: len(prior["claims"])] != prior["claims"]:
        raise ValueError("reconciliation altered prior claim history")

    audit = _reconciled_audit(source_audit)
    chain = _chain_record(audit)

    _write_json(LEDGER_DIR / Path(PATH_14).name, ledger_14)
    _write_json(LEDGER_DIR / Path(PATH_15).name, prior)
    _write_json(LEDGER_DIR / Path(PATH_PARALLEL).name, parallel)
    _write_json(LEDGER_DIR / Path(PATH_RECONCILED).name, ledger)
    _write_json(ROOT / AUDIT_PATH, audit)
    _write_json(ROOT / CHAIN_PATH, chain)
    REVIEW_PATH.write_text(_review_markdown(), encoding="utf-8")
    TEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEST_PATH.write_text(_test_source(), encoding="utf-8")

    print(f"canonical prior: {LEDGER_15}")
    print(f"reconciled tip:  {RECONCILED_16}")
    print("replayed claims: 6; supersessions: 5; new player claims: 1")


if __name__ == "__main__":
    main()
