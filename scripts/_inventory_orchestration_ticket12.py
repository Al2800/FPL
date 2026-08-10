"""One-shot inventory for ticket 12 (not a permanent entry point)."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
orch = root / "src" / "orchestration"
scripts = root / "scripts"

mods = sorted(p for p in orch.glob("*.py") if p.name != "__init__.py")
print(f"orchestration_modules={len(mods)}")

rows = []
for path in mods:
    text = path.read_text(encoding="utf-8", errors="replace")
    imports = re.findall(r"^(?:from|import)\s+(src\.[\w\.]+)", text, re.M)
    name = path.stem
    if any(
        token in name
        for token in (
            "replay",
            "genuine",
            "historical",
            "fork",
            "multiweek",
            "early_season",
            "evidence_fork",
            "episode",
        )
    ):
        kind = "replay_experiment"
    elif any(
        token in name
        for token in (
            "live_",
            "run_gameweek",
            "deadline",
            "freshness",
            "manager_state",
            "scheduled_agent",
            "walking_skeleton",
            "agent_arm",
            "hosted_response",
            "agent_trace",
        )
    ):
        kind = "live_path"
    else:
        kind = "mixed"
    rows.append((name, kind, len(imports), len(text.splitlines())))

print("by_kind", dict(Counter(kind for _, kind, _, _ in rows)))
for name, kind, nimp, nlines in sorted(rows, key=lambda row: (row[1], row[0])):
    print(f"{kind:18} {nlines:4}loc {nimp:2}imp  {name}")

forks = sorted(scripts.glob("run_gw*_agent_fork*.py"))
print("fork_runners", len(forks))
for path in forks:
    text = path.read_text(encoding="utf-8", errors="replace")
    print(path.name, "lines", len(text.splitlines()))

print("scripts_py", len(list(scripts.glob("*.py"))))
print("scripts_ps1", len(list(scripts.glob("*.ps1"))))
