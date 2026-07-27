#!/usr/bin/env python3
"""Build and replay the exploratory 2025/26 GW1 structured-prior seed."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import subprocess
from typing import Any

from scripts.prepare_replay_gameweek import prepare
from src.orchestration.genuine_replay import (
    finalise_historical_gameweek,
    run_historical_replay,
)
from src.orchestration.historical_seed_counterfactual import (
    build_candidate_pool,
    build_counterfactual_seed,
    decompose_seed_result,
)


REPO = Path(__file__).resolve().parents[1]
VAASTAV = REPO / "data" / "raw" / "vaastav" / "Fantasy-Premier-League" / "data"
EPISODES = REPO / "data" / "benchmark-v0" / "episodes" / "v2" / "2025-26"
CONTROL = REPO / "reports" / "benchmarks" / "2025-26"
EVAL = REPO / "evals" / "seed-forks" / "2025-26" / "gw-01"
BRANCH = REPO / "reports" / "benchmarks" / "2025-26-gw1-seed-counterfactual"
REPORT = CONTROL / "gw-01-seed-counterfactual.html"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_once(path: Path, value: dict[str, Any] | str) -> None:
    text = (
        value
        if isinstance(value, str)
        else json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise RuntimeError(f"Refusing to overwrite sealed artifact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _control_hash() -> dict[str, Any]:
    exclusions = {
        "evidence-early-season.html",
        "gw-01-seed-counterfactual.html",
    }
    digest = hashlib.sha256()
    count = 0
    for path in sorted(item for item in CONTROL.rglob("*") if item.is_file()):
        relative = path.relative_to(CONTROL).as_posix()
        if relative in exclusions:
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
        count += 1
    return {"file_count": count, "sha256": digest.hexdigest()}


def _render(
    result: dict[str, Any],
    seed: dict[str, Any],
    control_seed: dict[str, Any],
    control_hash: dict[str, Any],
) -> str:
    selected = {row["player_id"]: row for row in seed["squad"]}
    control_ids = {row["player_id"] for row in control_seed["squad"]}
    branch_ids = set(selected)
    added = [selected[player_id]["web_name"] for player_id in sorted(branch_ids - control_ids)]
    removed_names = {
        row["player_id"]: row["web_name"] for row in control_seed["squad"]
    }
    removed = [removed_names[player_id] for player_id in sorted(control_ids - branch_ids)]
    rows = "\n".join(
        "<tr>"
        f"<td>GW{row['gameweek']}</td>"
        f"<td>{row['control_net_points']}</td>"
        f"<td>{row['branch_net_points']}</td>"
        f"<td>{row['weekly_delta']:+d}</td>"
        f"<td>{row['cumulative_delta']:+d}</td>"
        f"<td>{row['control_transfers']} / {row['branch_transfers']}</td>"
        "</tr>"
        for row in result["weeks"]
    )
    squad_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['web_name'])}</td>"
        f"<td>{row['position']}</td><td>£{row['current_price']:.1f}m</td>"
        "</tr>"
        for row in seed["squad"]
    )
    decomposition = result["decomposition"]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GW1 seed counterfactual</title>
<style>
body{{font:16px/1.5 system-ui,sans-serif;max-width:1120px;margin:auto;padding:2rem;color:#172026}}
h1,h2{{line-height:1.15}} .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:1rem}}
.card{{border:1px solid #ccd5da;border-radius:12px;padding:1rem;background:#f8fafb}} .big{{font-size:2rem;font-weight:700}}
table{{border-collapse:collapse;width:100%}} th,td{{padding:.55rem;border-bottom:1px solid #dce3e7;text-align:left}}
.warning{{border-left:5px solid #b26a00;background:#fff6e5;padding:1rem}} code{{overflow-wrap:anywhere}}
</style></head><body>
<h1>2025/26 GW1 structured-prior seed counterfactual</h1>
<p class="warning"><strong>Exploratory and production-ineligible.</strong>
The launch pool is reconstructed after the season using a strict field whitelist.
This is a process test, not evidence that the branch could have been executed live.</p>
<div class="cards">
<div class="card"><div>GW1 seed delta</div><div class="big">{decomposition['gw1_initial_seed_realised_delta']:+d}</div></div>
<div class="card"><div>GW2–GW{result['stop_gameweek']} carried-policy delta</div><div class="big">{decomposition['gw2_to_stop_policy_and_carried_state_delta']:+d}</div></div>
<div class="card"><div>Total delta</div><div class="big">{decomposition['total_delta']:+d}</div></div>
<div class="card"><div>Budget / bank</div><div class="big">£{100-seed['bank']:.1f}m / £{seed['bank']:.1f}m</div></div>
</div>
<h2>What changed at the seed</h2>
<p><strong>Added:</strong> {html.escape(", ".join(added))}</p>
<p><strong>Removed:</strong> {html.escape(", ".join(removed))}</p>
<p>Captain: <strong>{html.escape(selected[seed['initial_plan']['captain_id']]['web_name'])}</strong>.
The policy ranks a six-Gameweek prior built from completed 2024/25 points and minutes,
availability shrinkage, reconstructed launch price/position/club, and GW1–GW6 fixture difficulty.</p>
<h2>Weekly trajectory</h2>
<table><thead><tr><th>Week</th><th>Scout control</th><th>Structured seed</th>
<th>Weekly Δ</th><th>Cumulative Δ</th><th>Transfers control / branch</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Alternative 15</h2>
<table><thead><tr><th>Player</th><th>Position</th><th>Price</th></tr></thead><tbody>{squad_rows}</tbody></table>
<h2>Interpretation boundaries</h2>
<ul>
<li>GW1 is the realised difference from starting squad, XI and captain.</li>
<li>GW2 onward mixes carried squad/finance with the same weekly engine; it is a seed × policy interaction, not a pure seed effect.</li>
<li>One realised season cannot establish expected-value superiority.</li>
<li>No GW1 injury news, press conferences, betting odds, ownership policy, or complete pre-deadline eligibility snapshot was available.</li>
<li>Luis Díaz was excluded using Liverpool's 30 July transfer announcement after the final export exposed him as a stale launch-row candidate.</li>
</ul>
<p>Frozen control tree (excluding derived comparison pages): <code>{control_hash['sha256']}</code>
across {control_hash['file_count']} files. Result hash: <code>{result['content_sha256']}</code>.</p>
</body></html>"""


def _run_gw1_checkpoint(**kwargs: Any) -> dict[str, Any]:
    summary = Path(kwargs["output_root"]) / "gw-01" / "run-summary.json"
    if summary.exists():
        return _read(summary)
    return run_historical_replay(**kwargs)


def _prepare_checkpoint(**kwargs: Any) -> dict[str, Any]:
    root = Path(kwargs["output_root"]) / f"gw-{int(kwargs['gameweek']):02d}"
    completed = root / "run-summary.json"
    if completed.exists():
        return {"status": "already_completed"}
    prepared = root / "setup" / "forecast-review-summary.json"
    if prepared.exists():
        return _read(prepared)
    return prepare(**kwargs)


def run(*, stop_gameweek: int = 11, code_commit: str | None = None) -> dict[str, Any]:
    if not 1 <= stop_gameweek <= 11:
        raise ValueError("Historical seed branch is bounded to GW1-GW11")
    commit = code_commit or _git_commit()
    before = _control_hash()
    control_seed = _read(REPO / "control" / "seeds" / "2025-26" / "official-scout-gw1.json")
    pool = build_candidate_pool(
        gw1_path=VAASTAV / "2025-26" / "gws" / "gw1.csv",
        current_players_path=VAASTAV / "2025-26" / "players_raw.csv",
        previous_players_path=VAASTAV / "2024-25" / "players_raw.csv",
        identity_map_path=EPISODES / "gw-01" / "identity-map.json",
        episode_root=EPISODES,
    )
    seed = build_counterfactual_seed(pool, control_seed)
    seed_path = EVAL / "structured-prior-seed.json"
    _write_once(EVAL / "candidate-pool.json", pool)
    _write_once(seed_path, seed)
    _run_gw1_checkpoint(
        season="2025-26",
        episode_root=EPISODES,
        output_root=BRANCH,
        stop_after_gameweek=1,
        code_commit=commit,
        seed_path=seed_path,
    )
    for gameweek in range(2, stop_gameweek + 1):
        _prepare_checkpoint(
            season="2025-26",
            gameweek=gameweek,
            episode_root=EPISODES,
            output_root=BRANCH,
            previous_checkpoint_dir=BRANCH / f"gw-{gameweek - 1:02d}",
            code_commit=commit,
            seed_path=seed_path if gameweek == 2 else None,
        )
        finalise_historical_gameweek(
            season="2025-26",
            gameweek=gameweek,
            episode_root=EPISODES,
            output_root=BRANCH,
            code_commit=commit,
            reviewed_setup_dir=BRANCH / f"gw-{gameweek:02d}" / "setup",
        )
    result = decompose_seed_result(
        control_root=CONTROL,
        branch_root=BRANCH,
        stop_gameweek=stop_gameweek,
    )
    result["candidate_pool_sha256"] = pool["content_sha256"]
    result["seed_sha256"] = seed["content_sha256"]
    result["canonical_control_tree"] = before
    result["content_sha256"] = hashlib.sha256(
        json.dumps(
            {key: value for key, value in result.items() if key != "content_sha256"},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    _write_once(EVAL / "summary.json", result)
    _write_once(REPORT, _render(result, seed, control_seed, before))
    after = _control_hash()
    if after != before:
        raise RuntimeError("Canonical control tree changed during seed counterfactual")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stop-gameweek", type=int, default=11)
    args = parser.parse_args()
    print(json.dumps(run(stop_gameweek=args.stop_gameweek), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
