"""Load and query the source registry; enforce enabled-before-collect."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPO_ROOT / "control" / "sources" / "source-registry.yaml"

REQUIRED_FIELDS = [
    "source_id",
    "owner",
    "source_type",
    "authority",
    "terms_url",
    "licence_status",
    "allowed_use",
    "authentication",
    "collection_method",
    "expected_cadence",
    "max_staleness",
    "failure_policy",
    "retention_policy",
    "attribution",
    "enabled",
    "review_date",
]


def load_registry(path: Path | None = None) -> dict[str, Any]:
    registry_path = path or DEFAULT_REGISTRY
    with registry_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict) or "sources" not in data:
        raise ValueError(f"Invalid source registry: {registry_path}")
    return data


def get_source(source_id: str, path: Path | None = None) -> dict[str, Any]:
    registry = load_registry(path)
    for source in registry["sources"]:
        if source["source_id"] == source_id:
            missing = [f for f in REQUIRED_FIELDS if f not in source]
            if missing:
                raise ValueError(f"{source_id} missing fields: {missing}")
            return source
    raise KeyError(source_id)


def assert_collectable(source_id: str, path: Path | None = None) -> dict[str, Any]:
    source = get_source(source_id, path)
    if not source.get("enabled"):
        raise PermissionError(f"Source {source_id} is disabled in the registry")
    if source.get("licence_status") in {None, "prohibited"}:
        raise PermissionError(f"Source {source_id} has unresolved/prohibited licence_status")
    if not source.get("allowed_use"):
        raise PermissionError(f"Source {source_id} missing allowed_use")
    return source
