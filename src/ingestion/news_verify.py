"""Apply verified publication metadata onto triage shortlists.

Verification records are operator/agent supplied. This module never fetches
pages and never stores article bodies. Successful rows can be reshaped into
``search_results`` for ``execute_news_discovery_plan``.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence

from src.ingestion.news_discovery import (
    NewsDiscoveryError,
    _timestamp,
    artifact_hash,
    build_news_discovery_plan,
    execute_news_discovery_plan,
)


class NewsVerifyError(ValueError):
    """Raised when verification inputs cannot safely admit a lead."""


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def apply_news_verifications(
    triage: Mapping[str, Any],
    verifications: Sequence[Mapping[str, Any]],
    *,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Merge verification outcomes onto the triage shortlist."""

    if triage.get("schema_version") != "news-capture-triage-result-v1":
        raise NewsVerifyError("triage artifact schema unsupported")
    if triage.get("content_sha256") != artifact_hash(triage):
        raise NewsVerifyError("triage content_sha256 mismatch")

    by_id = {
        str(row.get("candidate_id")): deepcopy(dict(row))
        for row in triage.get("shortlist") or []
        if isinstance(row, Mapping)
    }
    if not by_id:
        raise NewsVerifyError("triage shortlist is empty")

    observed = observed_at or str(triage.get("observed_at") or "")
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for raw in verifications:
        if not isinstance(raw, Mapping):
            rejected.append({"reason": "verification_not_object"})
            continue
        candidate_id = str(raw.get("candidate_id") or "")
        row = by_id.get(candidate_id)
        if row is None:
            rejected.append(
                {"candidate_id": candidate_id, "reason": "candidate_not_on_shortlist"}
            )
            continue
        status = str(raw.get("status") or "").strip()
        if status not in {"verified", "rejected", "needs_human"}:
            rejected.append(
                {"candidate_id": candidate_id, "reason": "unsupported_verification_status"}
            )
            continue
        updated = deepcopy(row)
        updated["verification_status"] = status
        updated["verified_by"] = raw.get("verified_by")
        updated["verified_at"] = raw.get("verified_at")
        updated["page_identity_ok"] = bool(raw.get("page_identity_ok"))
        updated["matched_players"] = list(raw.get("matched_players") or [])
        updated["verification_notes"] = str(raw.get("notes") or "")[:500]
        # Never retain body/excerpt fields if an agent accidentally supplies them.
        for banned in ("snippet", "body", "excerpt", "html", "content"):
            updated.pop(banned, None)
            if banned in raw:
                rejected.append(
                    {
                        "candidate_id": candidate_id,
                        "reason": f"forbidden_field_stripped:{banned}",
                    }
                )

        if status == "verified":
            if not updated["page_identity_ok"]:
                rejected.append(
                    {
                        "candidate_id": candidate_id,
                        "reason": "verified_requires_page_identity_ok",
                    }
                )
                continue
            try:
                published_text, _ = _timestamp(raw.get("published_at"), "published_at")
            except NewsDiscoveryError as exc:
                rejected.append(
                    {"candidate_id": candidate_id, "reason": str(exc)}
                )
                continue
            updated["published_at"] = published_text
            updated["publication_time_status"] = "known"
            accepted.append(updated)
        else:
            rejected.append(
                {
                    "candidate_id": candidate_id,
                    "reason": f"verification_{status}",
                    "notes": updated["verification_notes"],
                }
            )
        by_id[candidate_id] = updated

    return _seal(
        {
            "schema_version": "news-capture-verification-result-v1",
            "triage_sha256": triage.get("content_sha256"),
            "capture_id": triage.get("capture_id"),
            "observed_at": observed,
            "shortlist": sorted(
                by_id.values(),
                key=lambda row: (-int(row.get("triage_score") or 0), str(row.get("url"))),
            ),
            "verified_ready_for_discovery": accepted,
            "rejected": rejected,
            "claim_policy": "manual_linked_derived_claim_only",
            "account_writes": False,
            "notes": (
                "Verified rows have ISO published_at and may be converted into "
                "discovery search_results. They are still not ledger claims."
            ),
        }
    )


def verified_rows_to_search_results(
    verification: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Convert verified triage rows into discovery search_results shape."""

    results: dict[str, list[dict[str, Any]]] = {}
    for index, row in enumerate(verification.get("verified_ready_for_discovery") or []):
        club_id = str(row.get("club_id") or "")
        if not club_id:
            continue
        results.setdefault(club_id, []).append(
            {
                "url": str(row.get("url") or ""),
                "title": str(row.get("title") or ""),
                "published_at": str(row.get("published_at") or ""),
                "rank": int(row.get("rank") or index + 1),
            }
        )
    return results


def admit_verified_into_discovery(
    *,
    catalogue: Mapping[str, Any],
    config: Mapping[str, Any],
    verification: Mapping[str, Any],
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Run the strict discovery gate over verified official metadata only."""

    observed = observed_at or str(verification.get("observed_at") or "")
    plan = build_news_discovery_plan(catalogue, config=config, observed_at=observed)
    # Discovery requires every club key present for complete coverage; fill empties.
    search_results = {action["club_id"]: [] for action in plan["actions"]}
    verified = verified_rows_to_search_results(verification)
    for club_id, rows in verified.items():
        if club_id in search_results:
            search_results[club_id] = rows
    discovery = execute_news_discovery_plan(plan, search_results=search_results)
    return _seal(
        {
            "schema_version": "news-verified-discovery-bridge-v1",
            "verification_sha256": verification.get("content_sha256"),
            "discovery": discovery,
            "admitted_lead_count": len(discovery.get("leads") or []),
            "account_writes": False,
        }
    )
