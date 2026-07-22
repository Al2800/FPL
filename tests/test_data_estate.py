"""Data estate inventory / warehouse smoke tests."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_inventory_json_exists_and_has_sources() -> None:
    path = REPO / "docs" / "data-sources" / "data-estate" / "inventory.json"
    assert path.exists(), "Run: PYTHONPATH=. python3 -m scripts.inventory_data_estate"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["total_bytes"] > 0
    assert data["vaastav"]["present"] is True
    assert data["football_data"]["present"] is True
    assert len(data["football_data"]["files"]) >= 6


def test_warehouse_readme_documents_growth_options() -> None:
    text = (REPO / "docs" / "data-sources" / "data-estate" / "README.md").read_text(
        encoding="utf-8"
    )
    assert "Deepen what we have" in text
    assert "understat.com" in text
