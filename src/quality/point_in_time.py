"""Point-in-time filtering helpers (plan Sections 7.2, 11.4)."""

from __future__ import annotations

from typing import Any, Iterable


def usable_in_decision(record: dict[str, Any], deadline: str) -> bool:
    available = record.get("available_at")
    if available is None:
        return False
    return available <= deadline


def filter_by_deadline(records: Iterable[dict[str, Any]], deadline: str) -> list[dict[str, Any]]:
    return [r for r in records if usable_in_decision(r, deadline)]


def assert_no_lookahead(records: Iterable[dict[str, Any]], deadline: str) -> None:
    leaks = [r for r in records if not usable_in_decision(r, deadline)]
    if leaks:
        raise ValueError(f"{len(leaks)} record(s) have available_at > deadline {deadline}")
