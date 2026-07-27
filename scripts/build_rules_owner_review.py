"""Build a deterministic 2026/27 ruleset owner-review packet."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.scoring.rules_loader import (
    build_ruleset_activation,
    index_rules,
    load_rules,
    ruleset_semantic_diff,
    ruleset_sha256,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HISTORICAL = ROOT / "control" / "rules" / "2025-26.yaml"
DEFAULT_LIVE = ROOT / "control" / "rules" / "2026-27.yaml"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def artifact_hash(value: Mapping[str, Any]) -> str:
    payload = {key: item for key, item in value.items() if key != "content_sha256"}
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _timestamp(value: str, field: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return value


def build_owner_review(
    *,
    historical_path: Path = DEFAULT_HISTORICAL,
    live_path: Path = DEFAULT_LIVE,
    reviewed_at: str,
    status: str = "pending",
    approved_by: str | None = None,
    approved_at: str | None = None,
) -> dict[str, Any]:
    """Return a self-hashed review packet with a separate advisory approval gate."""

    if status not in {"pending", "approved"}:
        raise ValueError("Owner status must be pending or approved")
    _timestamp(reviewed_at, "reviewed_at")
    if status == "approved":
        if not approved_by or not approved_at:
            raise ValueError("Approved owner reviews require approver and approval time")
        _timestamp(approved_at, "approved_at")
    elif approved_by is not None or approved_at is not None:
        raise ValueError("Pending owner reviews cannot carry approval identity")

    historical = load_rules(historical_path)
    live = load_rules(live_path)
    historical_hash = ruleset_sha256(historical_path)
    live_hash = ruleset_sha256(live_path)
    activation = build_ruleset_activation(live, live_hash, mode="live")
    semantic_diff = ruleset_semantic_diff(
        historical,
        historical_hash,
        live,
        live_hash,
    )
    rules = index_rules(live)
    source_urls = sorted({str(rule["source_url"]) for rule in rules.values()})
    unresolved = sorted(
        rule_id
        for rule_id, rule in rules.items()
        if rule.get("status") != "confirmed"
    )
    missing_source_dates = sorted(
        rule_id
        for rule_id, rule in rules.items()
        if not rule.get("source_published_at") or not rule.get("verified_at")
    )
    if unresolved or missing_source_dates:
        raise ValueError("Owner packet cannot be built from unresolved source evidence")

    owner_review = {
        "status": status,
        "scope": "2026-27_ruleset_advisory_engine_use_only",
        "ruleset_id": activation["ruleset_id"],
        "ruleset_sha256": live_hash,
        "approved_by": approved_by,
        "approved_at": approved_at,
    }
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "reviewed_at": reviewed_at,
        "ruleset_activation": activation,
        "semantic_diff_from_2025_26": semantic_diff,
        "source_audit": {
            "rule_count": len(rules),
            "confirmed_rule_count": len(rules) - len(unresolved),
            "unresolved_rule_ids": unresolved,
            "missing_source_date_rule_ids": missing_source_dates,
            "unique_official_source_count": len(source_urls),
            "official_source_urls": source_urls,
        },
        "owner_review": owner_review,
        "advisory_use": (
            "approved" if status == "approved" else "blocked_pending_owner_signoff"
        ),
        "browser_execution_authorized": False,
        "fpl_account_writes_authorized": False,
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical", type=Path, default=DEFAULT_HISTORICAL)
    parser.add_argument("--live", type=Path, default=DEFAULT_LIVE)
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument("--status", choices=("pending", "approved"), default="pending")
    parser.add_argument("--approved-by")
    parser.add_argument("--approved-at")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = build_owner_review(
        historical_path=args.historical,
        live_path=args.live,
        reviewed_at=args.reviewed_at,
        status=args.status,
        approved_by=args.approved_by,
        approved_at=args.approved_at,
    )
    print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
