"""Deterministic triage of high-recall news-capture candidates.

Ranks candidates for a human/agent verification pass. Never admits ledger
claims and never retains snippets on sealed triage outputs.
"""

from __future__ import annotations

from calendar import monthrange
from collections import Counter
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from src.ingestion.news_discovery import NewsDiscoveryError, artifact_hash

_YEAR_RE = re.compile(r"(?:19|20)\d{2}")
_URL_DATE_RE = re.compile(
    r"/((?:19|20)\d{2})/(\d{1,2}|[a-z]+)(?:/(\d{1,2}))?(?=/|$)"
)
_MONTH_NAMES = {
    name: index
    for index, name in enumerate(
        (
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ),
        start=1,
    )
}


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY_PATH = ROOT / "control" / "policies" / "news-capture-triage-v1.json"


class NewsTriageError(ValueError):
    """Raised when capture triage inputs are unsafe."""


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def load_triage_policy(path: Path | None = None) -> dict[str, Any]:
    import json

    policy_path = path or DEFAULT_POLICY_PATH
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise NewsTriageError("triage policy must be a JSON object")
    if payload.get("schema_version") != "news-capture-triage-v1":
        raise NewsTriageError("unsupported news triage schema")
    return payload


def _text_blob(candidate: Mapping[str, Any]) -> str:
    parts = [
        str(candidate.get("title") or ""),
        str(candidate.get("snippet") or ""),
        str(candidate.get("url") or ""),
    ]
    return " ".join(parts).casefold()


def _matched_terms(blob: str, terms: Sequence[str]) -> list[str]:
    return [term for term in terms if term.casefold() in blob]


def _topic_hits(blob: str, topic_tags: Mapping[str, Any]) -> list[str]:
    hits: list[str] = []
    for topic, terms in topic_tags.items():
        if not isinstance(terms, list):
            continue
        if any(str(term).casefold() in blob for term in terms):
            hits.append(str(topic))
    return sorted(hits)


def _observed_year(observed_at: str | None) -> int | None:
    if not observed_at or not isinstance(observed_at, str):
        return None
    try:
        parsed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.year


def _stale_scan_text(candidate: Mapping[str, Any], fields: Sequence[str]) -> str:
    parts = [str(candidate.get(field) or "") for field in fields]
    return " ".join(parts)


def _stale_year_hits(
    text: str,
    *,
    observed_year: int,
    grace_years: int,
) -> list[int]:
    hits: list[int] = []
    threshold = observed_year - max(0, grace_years)
    for match in _YEAR_RE.finditer(text):
        year = int(match.group(0))
        if 1990 <= year < threshold:
            hits.append(year)
    return sorted(set(hits))


def _historical_manager_hits(text: str, terms: Sequence[str]) -> list[str]:
    blob = text.casefold()
    return sorted({term for term in terms if term.casefold() in blob})


def _parse_observed_date(observed_at: str | None) -> date | None:
    if not observed_at or not isinstance(observed_at, str):
        return None
    try:
        return datetime.fromisoformat(observed_at.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def derive_published_on(candidate: Mapping[str, Any]) -> tuple[date | None, str | None]:
    """Best-effort publication date: capture metadata first, URL path second.

    Month-only URL dates resolve to the last day of that month so freshness
    exclusion stays conservative (a candidate is only excluded when the whole
    month is outside the window).
    """

    published = candidate.get("published_at")
    if published:
        try:
            parsed = datetime.fromisoformat(str(published).replace("Z", "+00:00"))
            return parsed.date(), "published_at"
        except ValueError:
            pass
    for field in ("canonical_url", "url"):
        url = str(candidate.get(field) or "").casefold()
        match = _URL_DATE_RE.search(url)
        if not match:
            continue
        year = int(match.group(1))
        month_raw = match.group(2)
        month = (
            int(month_raw)
            if month_raw.isdigit()
            else _MONTH_NAMES.get(month_raw)
        )
        if not month or not 1 <= month <= 12:
            continue
        day_raw = match.group(3)
        if day_raw and 1 <= int(day_raw) <= monthrange(year, month)[1]:
            return date(year, month, int(day_raw)), "url_path"
        return date(year, month, monthrange(year, month)[1]), "url_path_month"
    return None, None


def _section_exclusion_marker(
    candidate: Mapping[str, Any],
    freshness_policy: Mapping[str, Any],
) -> str | None:
    url_blob = " ".join(
        str(candidate.get(field) or "")
        for field in ("canonical_url", "url")
    ).casefold()
    for marker in freshness_policy.get("url_section_exclusions") or []:
        if str(marker).casefold() in url_blob:
            return str(marker)
    title = str(candidate.get("title") or "").casefold()
    for marker in freshness_policy.get("title_section_exclusions") or []:
        pattern = (
            r"(?<![a-z0-9])" + re.escape(str(marker).casefold()) + r"(?![a-z0-9])"
        )
        if re.search(pattern, title):
            return str(marker)
    return None


def score_candidate(
    candidate: Mapping[str, Any],
    policy: Mapping[str, Any],
    *,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Return a sealed scoring row without copying snippets into the output."""

    blob = _text_blob(candidate)
    watch_terms = [str(term) for term in policy.get("watch_terms") or []]
    matched = _matched_terms(blob, watch_terms)
    topics = _topic_hits(blob, policy.get("topic_tags") or {})
    source_class = str(candidate.get("source_class") or "")
    club_id = str(candidate.get("club_id") or "")
    prefer = set(policy.get("prefer_source_classes") or [])
    priority_clubs = set(policy.get("priority_clubs") or [])

    score = 0
    reasons: list[str] = []
    if source_class in prefer:
        score += 40
        reasons.append("preferred_source_class")
    elif source_class == "external_candidate":
        score += 5
        reasons.append("external_challenge_only")
    if club_id in priority_clubs:
        score += 20
        reasons.append("priority_club")
    score += min(25, 5 * len(matched))
    if matched:
        reasons.append("watch_term_hit")
    score += min(20, 5 * len(topics))
    if topics:
        reasons.append("topic_hit")
    if candidate.get("publication_time_status") == "known" and candidate.get(
        "published_at"
    ):
        score += 15
        reasons.append("publication_time_already_known")
    else:
        reasons.append("needs_publication_time_verification")

    rank = candidate.get("rank")
    try:
        rank_i = int(rank)
        if 1 <= rank_i <= 3:
            score += 4 - rank_i
            reasons.append("high_search_rank")
    except (TypeError, ValueError):
        pass

    stale = policy.get("stale_markers") or {}
    if isinstance(stale, Mapping):
        fields = [str(f) for f in stale.get("scan_fields") or ["title", "url", "canonical_url"]]
        scan_text = _stale_scan_text(candidate, fields)
        year = _observed_year(observed_at or str(candidate.get("observed_at") or ""))
        stale_years: list[int] = []
        if year is not None:
            stale_years = _stale_year_hits(
                scan_text,
                observed_year=year,
                grace_years=int(stale.get("grace_years") or 0),
            )
            if stale_years:
                score -= int(stale.get("year_penalty") or 0)
                reasons.append("stale_year_stamp")
        manager_hits = _historical_manager_hits(
            scan_text,
            [str(term) for term in stale.get("historical_manager_terms") or []],
        )
        if manager_hits:
            score -= int(stale.get("historical_manager_penalty") or 0)
            reasons.append("historical_manager_marker")
    else:
        stale_years = []
        manager_hits = []

    return {
        "candidate_id": str(candidate.get("candidate_id") or ""),
        "club_id": club_id,
        "source_class": source_class,
        "url": str(candidate.get("canonical_url") or candidate.get("url") or ""),
        "title": str(candidate.get("title") or ""),
        "rank": candidate.get("rank"),
        "published_at": candidate.get("published_at"),
        "publication_time_status": candidate.get("publication_time_status"),
        "matched_watch_terms": matched,
        "topic_hits": topics,
        "stale_year_hits": stale_years,
        "historical_manager_hits": manager_hits,
        "triage_score": score,
        "reasons": sorted(set(reasons)),
        "verification_status": "pending",
        "impact_hypothesis": (
            "May inform "
            + (", ".join(topics) if topics else "general availability/team-news review")
        ),
    }


def triage_news_capture(
    capture: Mapping[str, Any],
    *,
    policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Rank capture candidates into a verification shortlist."""

    loaded = dict(policy or load_triage_policy())
    if capture.get("schema_version") not in {"1.0", 1, "1"}:
        # captures use schema_version 1.0
        pass
    candidates = capture.get("candidates")
    if not isinstance(candidates, list):
        raise NewsTriageError("capture candidates must be a list")

    observed_at = str(capture.get("observed_at") or "")
    mapped = [row for row in candidates if isinstance(row, Mapping)]
    scored = [
        score_candidate(row, loaded, observed_at=observed_at)
        for row in mapped
    ]

    all_scored = scored
    freshness_policy = loaded.get("freshness")
    excluded: list[dict[str, Any]] = []
    if isinstance(freshness_policy, Mapping):
        observed_date = _parse_observed_date(observed_at)
        max_age_days = int(freshness_policy.get("max_age_days") or 14)
        exclude_known = bool(
            freshness_policy.get("exclude_known_dates_older_than_max_age", True)
        )
        exclude_stale_years = bool(
            freshness_policy.get("exclude_stale_year_stamps", True)
        )
        kept: list[dict[str, Any]] = []
        for candidate, row in zip(mapped, scored):
            published_on, derived_from = derive_published_on(candidate)
            row["derived_published_on"] = (
                published_on.isoformat() if published_on else None
            )
            row["derived_published_from"] = derived_from
            if published_on and observed_date:
                age_days = (observed_date - published_on).days
                row["freshness_status"] = (
                    "fresh" if age_days <= max_age_days else "stale"
                )
            else:
                row["freshness_status"] = "unknown"

            reason: str | None = None
            section_marker = _section_exclusion_marker(candidate, freshness_policy)
            if section_marker:
                reason = f"excluded_section:{section_marker}"
            elif exclude_known and row["freshness_status"] == "stale":
                reason = f"stale_beyond_{max_age_days}_days"
            elif exclude_stale_years and row.get("stale_year_hits"):
                reason = "stale_year_stamp"
            if reason:
                excluded.append(
                    {
                        "candidate_id": row["candidate_id"],
                        "url": row["url"],
                        "reason": reason,
                    }
                )
            else:
                kept.append(row)
        scored = kept

    scored.sort(
        key=lambda row: (
            -int(row["triage_score"]),
            str(row["source_class"]) != "official_candidate",
            str(row["club_id"]),
            str(row["url"]),
        )
    )

    limit = int(loaded.get("shortlist_limit") or 24)
    max_external = int(loaded.get("max_external_on_shortlist") or 0)
    shortlist: list[dict[str, Any]] = []
    external_count = 0
    for row in scored:
        if row["source_class"] == "external_candidate":
            if not loaded.get("allow_external_for_challenge_only", True):
                continue
            if external_count >= max_external:
                continue
            external_count += 1
        shortlist.append(row)
        if len(shortlist) >= limit:
            break

    topic_counts = Counter(
        topic for row in shortlist for topic in row.get("topic_hits") or []
    )
    demoted = sum(
        1
        for row in all_scored
        if "stale_year_stamp" in (row.get("reasons") or [])
        or "historical_manager_marker" in (row.get("reasons") or [])
    )
    fresh_known = sum(
        1 for row in shortlist if row.get("freshness_status") == "fresh"
    )
    return _seal(
        {
            "schema_version": "news-capture-triage-result-v1",
            "policy_id": loaded.get("policy_id"),
            "capture_id": capture.get("capture_id"),
            "capture_sha256": capture.get("content_sha256"),
            "observed_at": capture.get("observed_at"),
            "candidate_count": len(mapped),
            "shortlist_count": len(shortlist),
            "demoted_candidate_count": demoted,
            "excluded_candidate_count": len(excluded),
            "freshness_excluded_count": sum(
                1
                for row in excluded
                if str(row["reason"]).startswith("stale")
            ),
            "section_excluded_count": sum(
                1
                for row in excluded
                if str(row["reason"]).startswith("excluded_section")
            ),
            "excluded_candidates": excluded,
            "shortlist_freshness": {
                "fresh_known": fresh_known,
                "unknown": sum(
                    1
                    for row in shortlist
                    if row.get("freshness_status", "unknown") == "unknown"
                ),
                "freshness_rate": (
                    round(fresh_known / len(shortlist), 4) if shortlist else 0.0
                ),
            },
            "shortlist": shortlist,
            "topic_counts": dict(sorted(topic_counts.items())),
            "claim_policy": loaded.get("claim_policy"),
            "notes": (
                "Shortlist only. Verification must confirm page identity and "
                "ISO published_at before discovery admission. Snippets used for "
                "scoring are not retained on this artifact. Candidates with a "
                "derivable date outside the freshness window, prior-year "
                "stamps, or excluded sections are hard-excluded when the "
                "policy freshness block is present; undatable candidates are "
                "kept for verification."
            ),
            "account_writes": False,
        }
    )


def triage_impact_summary(triage: Mapping[str, Any]) -> dict[str, Any]:
    """Summarise how a shortlist could affect strategy watch items."""

    shortlist = list(triage.get("shortlist") or [])
    by_topic: dict[str, list[str]] = {}
    for row in shortlist:
        for topic in row.get("topic_hits") or ["untagged"]:
            by_topic.setdefault(str(topic), []).append(str(row.get("title") or row.get("url")))
    return {
        "schema_version": "news-triage-impact-v1",
        "shortlist_count": len(shortlist),
        "official_on_shortlist": sum(
            1 for row in shortlist if row.get("source_class") == "official_candidate"
        ),
        "topics": {key: values[:5] for key, values in sorted(by_topic.items())},
        "strategy_relevance": {
            "haaland_minutes": bool(by_topic.get("haaland_minutes")),
            "bruno_minutes": bool(by_topic.get("bruno_minutes")),
            "availability_general": bool(by_topic.get("availability_general")),
            "team_news": bool(by_topic.get("team_news")),
        },
        "ledger_effect_without_verification": "none_zero_admitted_leads",
        "notes": (
            "Impact is potential only until verification supplies published_at "
            "and discovery admission succeeds."
        ),
    }
