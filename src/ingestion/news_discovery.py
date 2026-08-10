"""Deterministic discovery of cited official club-news originals.

Search is deliberately an injected discovery input.  This module never fetches
or stores search snippets or article bodies: a lead becomes eligible only when
its canonical URL is on the catalogue's official domain and its publication
time is known at the recorded observation boundary.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class NewsDiscoveryError(ValueError):
    """Raised when a discovery plan or its supplied results are unsafe."""


_TRACKING_PARAMETER = re.compile(r"^(?:utm_[^=]*|gclid|fbclid)$", re.I)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def artifact_hash(value: Mapping[str, Any]) -> str:
    payload = {key: deepcopy(item) for key, item in value.items() if key != "content_sha256"}
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    if not isinstance(value, str) or not value:
        raise NewsDiscoveryError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise NewsDiscoveryError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise NewsDiscoveryError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise NewsDiscoveryError(f"{field} must be a positive integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise NewsDiscoveryError(f"{field} must be a positive integer") from exc
    if parsed < 1:
        raise NewsDiscoveryError(f"{field} must be a positive integer")
    return parsed


def _catalogue_sources(catalogue: Mapping[str, Any], *, season: str) -> list[dict[str, str]]:
    if catalogue.get("schema_version") != "1.0" or str(catalogue.get("season")) != season:
        raise NewsDiscoveryError("Catalogue schema or season does not match configuration")
    rows = catalogue.get("sources")
    if not isinstance(rows, list):
        raise NewsDiscoveryError("Catalogue sources must be a list")
    result: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_domains: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise NewsDiscoveryError(f"Catalogue source {index} must be an object")
        source = {field: str(row.get(field, "")).strip() for field in ("club_id", "club_name", "official_domain", "news_url", "source_status")}
        if not all(source.values()):
            raise NewsDiscoveryError(f"Catalogue source {index} has missing required fields")
        if source["club_id"] in seen_ids or source["official_domain"] in seen_domains:
            raise NewsDiscoveryError("Catalogue has duplicate club ID or official domain")
        parsed = urlsplit(source["news_url"])
        if parsed.scheme != "https" or parsed.hostname is None:
            raise NewsDiscoveryError(f"Catalogue source {source['club_id']} needs an HTTPS news URL")
        seen_ids.add(source["club_id"])
        seen_domains.add(source["official_domain"])
        result.append(source)
    club_rows = [row for row in result if row["club_id"] != "premier-league"]
    if len(club_rows) != 20 or len(result) != 21 or "premier-league" not in seen_ids:
        raise NewsDiscoveryError("Catalogue must contain Premier League plus exactly 20 clubs")
    return sorted(result, key=lambda row: row["club_id"])


def build_news_discovery_plan(catalogue: Mapping[str, Any], *, config: Mapping[str, Any], observed_at: str) -> dict[str, Any]:
    """Create a sealed, replayable daily discovery plan without network I/O."""
    if config.get("schema_version") != "1.0":
        raise NewsDiscoveryError("Unsupported news discovery config schema")
    season = str(config.get("season", ""))
    observed_text, _ = _timestamp(observed_at, "observed_at")
    template = str(config.get("query_template", ""))
    if "{official_domain}" not in template:
        raise NewsDiscoveryError("query_template must contain {official_domain}")
    maximum_age = _positive_int(config.get("maximum_result_age_hours"), "maximum_result_age_hours")
    maximum_leads = _positive_int(config.get("maximum_leads_per_source"), "maximum_leads_per_source")
    actions = []
    for source in _catalogue_sources(catalogue, season=season):
        status = source["source_status"]
        if status not in {"official_domain_search_fallback", "verified_rss_or_api"}:
            raise NewsDiscoveryError(f"Unsupported source status: {status}")
        actions.append({
            "club_id": source["club_id"], "official_domain": source["official_domain"],
            "news_url": source["news_url"], "source_status": status,
            "discovery_method": "rss_or_api" if status == "verified_rss_or_api" else "official_domain_search_fallback",
            "query": template.format(official_domain=source["official_domain"]),
        })
    return _seal({
        "schema_version": "1.0", "plan_id": f"news-discovery:{season}:{observed_text}",
        "season": season, "observed_at": observed_text,
        "maximum_result_age_hours": maximum_age, "maximum_leads_per_source": maximum_leads,
        "raw_search_context_retained": False, "search_result_policy": str(config.get("search_result_policy", "")),
        "actions": actions,
    })


def _canonical_official_url(value: Any, domain: str) -> str:
    if not isinstance(value, str):
        raise NewsDiscoveryError("result url must be a string")
    parsed = urlsplit(value)
    hostname = (parsed.hostname or "").lower()
    expected = domain.lower()
    if parsed.scheme != "https" or not hostname or not (hostname == expected or hostname.endswith("." + expected)):
        raise NewsDiscoveryError("result URL is not on the official domain")
    retained = [(key, val) for key, val in parse_qsl(parsed.query, keep_blank_values=True) if not _TRACKING_PARAMETER.fullmatch(key)]
    return urlunsplit(("https", parsed.netloc.lower(), parsed.path or "/", urlencode(retained, doseq=True), ""))


def execute_news_discovery_plan(plan: Mapping[str, Any], *, search_results: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
    """Admit official-domain metadata leads from externally captured results."""
    if plan.get("content_sha256") != artifact_hash(plan):
        raise NewsDiscoveryError("Discovery plan hash mismatch")
    observed_text, observed = _timestamp(plan.get("observed_at"), "plan.observed_at")
    max_age = _positive_int(plan.get("maximum_result_age_hours"), "plan.maximum_result_age_hours")
    limit = _positive_int(plan.get("maximum_leads_per_source"), "plan.maximum_leads_per_source")
    if not isinstance(search_results, Mapping):
        raise NewsDiscoveryError("search_results must map club IDs to result lists")
    leads: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    gaps: list[str] = []
    coverage: list[dict[str, Any]] = []
    for action in plan.get("actions", []):
        if not isinstance(action, Mapping):
            raise NewsDiscoveryError("plan actions must be objects")
        club_id = str(action["club_id"])
        if club_id not in search_results:
            gaps.append(f"club:{club_id}:not_searched")
            coverage.append({"club_id": club_id, "status": "missing"})
            continue
        rows = search_results[club_id]
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            raise NewsDiscoveryError(f"search results for {club_id} must be a list")
        coverage.append({"club_id": club_id, "status": "searched", "result_count": len(rows)})
        admitted_for_source: list[dict[str, Any]] = []
        for source_index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                rejected.append({"club_id": club_id, "reason": "result_not_object"})
                continue
            try:
                url = _canonical_official_url(row.get("url"), str(action["official_domain"]))
                published_text, published = _timestamp(row.get("published_at"), "result.published_at")
                rank = _positive_int(row.get("rank", source_index + 1), "result.rank")
                if published > observed:
                    raise NewsDiscoveryError("result publication is after observation")
                if (observed - published).total_seconds() > max_age * 3600:
                    raise NewsDiscoveryError("result is stale")
                title = str(row.get("title", "")).strip()
                if not title:
                    raise NewsDiscoveryError("result title is required")
            except NewsDiscoveryError as exc:
                rejected.append({"club_id": club_id, "reason": str(exc)})
                continue
            admitted_for_source.append({
                "document_id": hashlib.sha256(_canonical_bytes([club_id, url, published_text])).hexdigest(),
                "club_id": club_id, "source_url": url, "published_at": published_text,
                "observed_at": observed_text, "discovery_method": str(action["discovery_method"]),
                "query": str(action["query"]), "rank": rank, "title": title,
            })
        admitted_for_source.sort(key=lambda lead: (lead["rank"], lead["source_url"]))
        leads.extend(admitted_for_source[:limit])
    deduped: dict[str, dict[str, Any]] = {}
    for lead in sorted(leads, key=lambda item: (item["rank"], item["club_id"], item["source_url"])):
        prior = deduped.get(lead["source_url"])
        if prior is None:
            deduped[lead["source_url"]] = lead
        else:
            rejected.append({"club_id": lead["club_id"], "reason": "duplicate_canonical_official_url"})
    status = "complete" if not gaps else "degraded"
    return _seal({
        "schema_version": "1.0", "discovery_id": str(plan["plan_id"]), "season": str(plan["season"]),
        "observed_at": observed_text, "status": status, "plan_sha256": str(plan["content_sha256"]),
        "raw_search_context_retained": False, "leads": sorted(deduped.values(), key=lambda lead: (lead["club_id"], lead["rank"], lead["source_url"])),
        "coverage": coverage, "quality": {"gaps": sorted(gaps), "rejected": sorted(rejected, key=lambda row: (row["club_id"], row["reason"]))},
        "claim_policy": "model_derived_candidate_host_validated_claim", "account_writes": False,
    })


def build_cited_original_packet(discovery: Mapping[str, Any], *, document_ids: Sequence[str] | None = None) -> dict[str, Any]:
    """Return only bounded official-original metadata for downstream citation."""
    if discovery.get("content_sha256") != artifact_hash(discovery):
        raise NewsDiscoveryError("Discovery artifact hash mismatch")
    wanted = None if document_ids is None else set(document_ids)
    rows = [row for row in discovery.get("leads", []) if wanted is None or row.get("document_id") in wanted]
    if wanted is not None and {str(row.get("document_id")) for row in rows} != wanted:
        raise NewsDiscoveryError("Selected document ID is absent from discovery")
    safe_fields = ("document_id", "club_id", "source_url", "published_at", "observed_at", "discovery_method", "query", "rank", "title")
    return _seal({"schema_version": "1.0", "packet_id": f"cited-originals:{discovery['discovery_id']}", "discovery_sha256": str(discovery["content_sha256"]), "documents": [{field: row[field] for field in safe_fields} for row in rows], "raw_search_context_retained": False, "claim_policy": "model_derived_candidate_host_validated_claim"})


def write_immutable_json(path: str | Path, value: Mapping[str, Any]) -> str:
    """Create an immutable JSON artifact, accepting only byte-identical reruns."""
    target = Path(path)
    encoded = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if target.exists():
        if target.read_text(encoding="utf-8") != encoded:
            raise FileExistsError(f"Refusing to overwrite immutable artifact: {target}")
        return "identical"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(encoded, encoding="utf-8")
    return "created"
