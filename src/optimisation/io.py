"""Load/save solver inputs and outputs with stable JSON canonicalisation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.optimisation.types import SolverInput


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def fingerprint(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def load_solver_input(path: Path | str) -> SolverInput:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return SolverInput.from_dict(data)


def save_json(path: Path | str, obj: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
