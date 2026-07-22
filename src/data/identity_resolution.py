"""Deterministic, season-aware resolution of source identities."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ALIASES = REPO_ROOT / "control" / "identities" / "source-aliases.yaml"


class IdentityResolutionError(ValueError):
    """Raised when decision-critical identities are not uniquely resolved."""


def normalise_name(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", ascii_value.casefold())


def load_alias_catalog(path: Path | None = None) -> dict[str, Any]:
    catalog_path = path or DEFAULT_ALIASES
    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("aliases"), list):
        raise ValueError(f"Invalid alias catalog: {catalog_path}")
    return data


def _as_date(value: str | None) -> date | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def _eligible(alias: dict[str, Any], *, season: str, effective_at: str | None) -> bool:
    seasons = alias.get("seasons") or []
    if seasons and season not in seasons:
        return False
    instant = _as_date(effective_at)
    if instant is None:
        return True
    valid_from = _as_date(alias.get("valid_from"))
    valid_to = _as_date(alias.get("valid_to"))
    return (valid_from is None or valid_from <= instant) and (valid_to is None or instant <= valid_to)


def _candidates(
    item: dict[str, Any], aliases: list[dict[str, Any]], *, season: str
) -> tuple[list[dict[str, Any]], str]:
    eligible = [
        alias
        for alias in aliases
        if alias.get("entity_type") == item.get("entity_type")
        and alias.get("source_id") == item.get("source_id")
        and _eligible(alias, season=season, effective_at=item.get("effective_at"))
    ]
    source_entity_id = str(item.get("source_entity_id", ""))
    by_id = [
        alias for alias in eligible if str(alias.get("source_entity_id", "")) == source_entity_id
    ]
    if source_entity_id and by_id:
        return by_id, "exact_source_id"
    source_name = normalise_name(str(item.get("source_name", "")))
    by_name = [alias for alias in eligible if normalise_name(str(alias.get("alias", ""))) == source_name]
    return by_name, "exact_alias"


def _stable_mapping_id(
    *, catalog_version: str, source_ids: list[str], season: str, records: list[dict[str, Any]]
) -> str:
    stable_records = [
        {key: value for key, value in record.items() if key != "input_index"}
        for record in records
    ]
    stable_records.sort(
        key=lambda row: (
            str(row.get("entity_type")),
            str(row.get("source_id")),
            str(row.get("source_entity_id")),
            str(row.get("source_name")),
        )
    )
    payload = json.dumps(
        {
            "catalog_version": catalog_version,
            "source_ids": sorted(source_ids),
            "season": season,
            "records": stable_records,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def resolve_identities(
    items: list[dict[str, Any]],
    *,
    season: str,
    catalog_path: Path | None = None,
) -> dict[str, Any]:
    """Resolve records into canonical IDs and retain reviewable failures."""

    catalog = load_alias_catalog(catalog_path)
    aliases = catalog["aliases"]
    records: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        candidates, method = _candidates(item, aliases, season=season)
        canonical_ids = sorted({str(candidate["canonical_id"]) for candidate in candidates})
        if len(canonical_ids) == 1:
            status = "resolved"
            canonical_id: str | None = canonical_ids[0]
            confidence = 1.0
        elif len(canonical_ids) > 1:
            status = "review"
            canonical_id = None
            confidence = 0.0
        else:
            status = "unresolved"
            canonical_id = None
            confidence = 0.0
        records.append(
            {
                "input_index": index,
                "entity_type": str(item.get("entity_type", "")),
                "source_id": str(item.get("source_id", "")),
                "source_entity_id": str(item.get("source_entity_id", "")),
                "source_name": str(item.get("source_name", "")),
                "status": status,
                "canonical_id": canonical_id,
                "resolution_method": method,
                "confidence": confidence,
                "candidates": canonical_ids,
            }
        )

    resolved = sum(record["status"] == "resolved" for record in records)
    review = sum(record["status"] == "review" for record in records)
    unresolved = len(records) - resolved - review
    source_ids = sorted({record["source_id"] for record in records})
    return {
        "mapping_version": "1.0",
        "mapping_id": _stable_mapping_id(
            catalog_version=str(catalog.get("catalog_version", "unknown")),
            source_ids=source_ids,
            season=season,
            records=records,
        ),
        "catalog_version": str(catalog.get("catalog_version", "unknown")),
        "season": season,
        "source_ids": source_ids,
        "records": records,
        "metrics": {
            "total": len(records),
            "resolved": resolved,
            "review": review,
            "unresolved": unresolved,
            "match_rate": resolved / len(records) if records else 1.0,
        },
    }


def require_resolved(report: dict[str, Any]) -> dict[str, Any]:
    """Fail closed when a decision-critical mapping is not unique."""

    failures = [record for record in report["records"] if record["status"] != "resolved"]
    if failures:
        summary = ", ".join(
            f"{record['entity_type']}:{record['source_id']}:{record['source_entity_id']}={record['status']}"
            for record in failures
        )
        raise IdentityResolutionError(f"Identity resolution incomplete: {summary}")
    return report
