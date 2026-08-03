"""High-recall capture adapter for unstructured news search results.

This layer deliberately preserves candidates and records quality flags instead
of dropping rows. It is not a claim or availability ledger: downstream code
must still use the strict official ``leads`` view before admitting evidence.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

from src.ingestion.news_discovery import (
    NewsDiscoveryError,
    _canonical_official_url,
    _positive_int,
    _timestamp,
    artifact_hash,
)


MAX_SNIPPET_CHARS = 1000
SOURCE_CLASSES = {"official_candidate", "external_candidate", "feed_candidate"}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _snippet(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    compact = " ".join(value.split())
    return compact[:MAX_SNIPPET_CHARS] or None


def _source_class(row: Mapping[str, Any], *, official: bool) -> str:
    value = str(row.get("source_class", "")).strip()
    if value in SOURCE_CLASSES:
        return value
    return "official_candidate" if official else "external_candidate"


def capture_search_candidates(
    plan: Mapping[str, Any],
    *,
    search_results: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    """Capture every supplied row, retaining bounded snippets and flags."""
    if plan.get("content_sha256") != artifact_hash(plan):
        raise NewsDiscoveryError("Discovery plan hash mismatch")
    observed_text, observed = _timestamp(plan.get("observed_at"), "plan.observed_at")
    max_age = _positive_int(plan.get("maximum_result_age_hours"), "plan.maximum_result_age_hours")
    if not isinstance(search_results, Mapping):
        raise NewsDiscoveryError("search_results must map club IDs to result lists")

    candidates: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    gaps: list[str] = []
    flags: Counter[str] = Counter()

    for action in plan.get("actions", []):
        club_id = str(action["club_id"])
        if club_id not in search_results:
            gaps.append(f"club:{club_id}:not_searched")
            coverage.append({"club_id": club_id, "status": "missing"})
            continue
        rows = search_results[club_id]
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            raise NewsDiscoveryError(f"search results for {club_id} must be a list")
        coverage.append({"club_id": club_id, "status": "searched", "result_count": len(rows)})
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                row = {}
                row_flags = ["result_not_object"]
            else:
                row_flags = []
            raw_url = row.get("url")
            raw_title = str(row.get("title", "")).strip()
            raw_published = row.get("published_at")
            try:
                rank = _positive_int(row.get("rank", index + 1), "result.rank")
            except NewsDiscoveryError:
                rank = index + 1
                row_flags.append("invalid_rank")

            canonical_url: str | None = None
            official = False
            try:
                canonical_url = _canonical_official_url(raw_url, str(action["official_domain"]))
                official = True
            except NewsDiscoveryError as exc:
                row_flags.append(str(exc))

            published_at: str | None = raw_published if isinstance(raw_published, str) else None
            publication_status = str(row.get("publication_time_status", "")).strip()
            if isinstance(raw_published, str) and raw_published:
                try:
                    published_at, published = _timestamp(raw_published, "result.published_at")
                    publication_status = "known" if publication_status not in {"ambiguous", "unknown"} else publication_status
                    if published > observed:
                        row_flags.append("result publication is after observation")
                    elif (observed - published).total_seconds() > max_age * 3600:
                        row_flags.append("result is stale")
                except NewsDiscoveryError as exc:
                    publication_status = "ambiguous"
                    row_flags.append(str(exc))
            else:
                publication_status = publication_status if publication_status in {"ambiguous", "unknown"} else "unknown"
                row_flags.append("missing publication time")
            if not raw_title:
                row_flags.append("result title is required")

            source_class = _source_class(row, official=official)
            bounded = _snippet(row.get("snippet"))
            candidate = {
                "candidate_id": hashlib.sha256(_canonical_bytes([club_id, raw_url, raw_title, rank, observed_text])).hexdigest(),
                "club_id": club_id,
                "url": raw_url if isinstance(raw_url, str) else None,
                "canonical_url": canonical_url,
                "title": raw_title,
                "published_at": published_at,
                "publication_time_status": publication_status,
                "observed_at": observed_text,
                "query": str(row.get("query", action.get("query", ""))),
                "rank": rank,
                "source_class": source_class,
                "snippet": bounded,
                "quality_flags": sorted(set(row_flags)),
            }
            candidates.append(candidate)
            flags.update(candidate["quality_flags"])

    class_counts = Counter(candidate["source_class"] for candidate in candidates)
    publication_counts = Counter(candidate["publication_time_status"] for candidate in candidates)
    return {
        "schema_version": "1.0",
        "capture_id": f"news-capture:{plan['season']}:{observed_text}",
        "season": str(plan["season"]),
        "observed_at": observed_text,
        "status": "complete" if not gaps else "degraded",
        "plan_sha256": str(plan["content_sha256"]),
        "raw_search_context_retained": any(candidate.get("snippet") for candidate in candidates),
        "candidates": sorted(candidates, key=lambda item: (item["club_id"], item["rank"], item["candidate_id"])),
        "coverage": coverage,
        "quality": {
            "gaps": sorted(gaps),
            "candidate_count": len(candidates),
            "source_class_counts": dict(sorted(class_counts.items())),
            "publication_time_counts": dict(sorted(publication_counts.items())),
            "flag_counts": dict(sorted(flags.items())),
        },
        "claim_policy": "manual_linked_derived_claim_only",
        "account_writes": False,
    }


def validate_capture(capture: Mapping[str, Any]) -> str:
    """Return the sealed hash for a capture, verifying its required shape."""
    if capture.get("schema_version") != "1.0":
        raise NewsDiscoveryError("Unsupported news capture schema")
    if not isinstance(capture.get("candidates"), list):
        raise NewsDiscoveryError("Capture candidates must be a list")
    return hashlib.sha256(_canonical_bytes(capture)).hexdigest()
