#!/usr/bin/env python3
"""Render a self-contained HTML review from one committed replay checkpoint."""

from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
from typing import Any, Mapping


REPO = Path(__file__).resolve().parents[1]


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _short(value: str, length: int = 12) -> str:
    return f"{value[:length]}…"


def _player_card(
    player_id: str,
    *,
    names: Mapping[str, str],
    outcomes: Mapping[str, Mapping[str, Any]],
    captain_id: str,
    vice_id: str,
) -> str:
    row = outcomes[player_id]
    badges = []
    if player_id == captain_id:
        badges.append('<span class="badge captain">C</span>')
    if player_id == vice_id:
        badges.append('<span class="badge vice">V</span>')
    return (
        '<article class="player-card">'
        f'<div class="player-name">{escape(names[player_id])}'
        f'{"".join(badges)}</div>'
        f'<div class="player-meta">{escape(str(row["position"]))} · '
        f'{int(row["minutes"])} min</div>'
        f'<div class="player-points">{int(row["total_points"])}'
        '<span> pts</span></div>'
        "</article>"
    )


def _arm_label(arm: str) -> str:
    return arm.replace("_", " ").title()


def render_report(
    *,
    checkpoint_dir: Path,
    seed_path: Path,
    output_path: Path,
) -> Path:
    summary = _read(checkpoint_dir / "run-summary.json")
    seed = _read(seed_path)
    reference_arm = "naive_baseline"
    arm_dir = checkpoint_dir / reference_arm
    plan = _read(arm_dir / "validated-plan.json")
    outcome = _read(arm_dir / "realised-outcome.json")
    transition = _read(arm_dir / "state-transition.json")
    next_state = _read(arm_dir / "next-policy-state.json")

    names = {
        str(player["player_id"]): str(player["web_name"])
        for player in seed["squad"]
    }
    outcomes = {
        str(player["player_id"]): player
        for player in outcome["aggregated_players"]
    }
    lineup = plan["lineup"]
    captain_id = str(lineup["captain_id"])
    vice_id = str(lineup["vice_captain_id"])

    by_position: dict[str, list[str]] = {
        "GKP": [],
        "DEF": [],
        "MID": [],
        "FWD": [],
    }
    for player_id in lineup["starting_xi_ids"]:
        by_position[outcomes[player_id]["position"]].append(player_id)
    pitch_rows = "".join(
        '<div class="pitch-row">'
        + "".join(
            _player_card(
                player_id,
                names=names,
                outcomes=outcomes,
                captain_id=captain_id,
                vice_id=vice_id,
            )
            for player_id in by_position[position]
        )
        + "</div>"
        for position in ("GKP", "DEF", "MID", "FWD")
    )
    bench_cards = "".join(
        _player_card(
            player_id,
            names=names,
            outcomes=outcomes,
            captain_id=captain_id,
            vice_id=vice_id,
        )
        for player_id in lineup["bench_ids"]
    )
    arm_rows = "".join(
        "<tr>"
        f"<td>{escape(_arm_label(arm))}</td>"
        f"<td>{int(data['gross_points'])}</td>"
        f"<td>{int(data['transfers'])}</td>"
        f"<td>{int(data['free_transfers'])}</td>"
        f"<td><code>{escape(_short(data['plan_sha256']))}</code></td>"
        f"<td><code>{escape(_short(data['next_state_sha256']))}</code></td>"
        "</tr>"
        for arm, data in summary["arms"].items()
    )
    limitations = "".join(
        f"<li>{escape(item.replace('_', ' '))}</li>"
        for item in summary["limitations"]
    )
    chips = ", ".join(
        chip.replace("_", " ").title() for chip in next_state["chips_available"]
    )
    reveal_time = str(outcome["revealed_at"]).replace("T", " ").replace("Z", " UTC")
    deadline = str(plan["frozen_at"]).replace("T", " ").replace("Z", " UTC")

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FPL Benchmark · {escape(summary["season"])} · GW1</title>
  <style>
    :root {{
      --ink: #13231d;
      --muted: #5e6f67;
      --paper: #f3f1e9;
      --panel: rgba(255,255,255,.84);
      --line: #d6d9cf;
      --green: #0b6b4f;
      --green-dark: #084f3d;
      --lime: #d8f24a;
      --blue: #3157d5;
      --orange: #e47932;
      --shadow: 0 24px 70px rgba(19,35,29,.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 90% 0%, rgba(216,242,74,.45), transparent 26rem),
        radial-gradient(circle at 0% 40%, rgba(49,87,213,.12), transparent 28rem),
        var(--paper);
      font: 15px/1.5 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    .shell {{ width: min(1180px, calc(100% - 32px)); margin: 0 auto; }}
    header {{ padding: 64px 0 32px; }}
    .eyebrow {{
      display: inline-flex; gap: 9px; align-items: center;
      color: var(--green-dark); font-size: 12px; font-weight: 800;
      letter-spacing: .12em; text-transform: uppercase;
    }}
    .eyebrow::before {{ content: ""; width: 28px; height: 3px; background: var(--lime); }}
    h1 {{ font-size: clamp(40px, 8vw, 88px); line-height: .94; letter-spacing: -.065em; margin: 20px 0 24px; max-width: 900px; }}
    .lede {{ max-width: 760px; color: var(--muted); font-size: 18px; }}
    .hero-grid {{ display: grid; grid-template-columns: 1.15fr .85fr; gap: 18px; margin-top: 36px; }}
    .score-card {{
      min-height: 270px; border-radius: 26px; padding: 32px;
      background: var(--green-dark); color: white; box-shadow: var(--shadow);
      display: flex; flex-direction: column; justify-content: space-between;
      position: relative; overflow: hidden;
    }}
    .score-card::after {{
      content: ""; position: absolute; width: 240px; height: 240px; border: 44px solid rgba(216,242,74,.18);
      border-radius: 50%; right: -70px; top: -70px;
    }}
    .score-label, .metric-label {{ text-transform: uppercase; letter-spacing: .12em; font-size: 11px; font-weight: 800; opacity: .75; }}
    .score {{ font-size: 112px; line-height: .75; font-weight: 850; letter-spacing: -.08em; }}
    .score span {{ font-size: 18px; letter-spacing: 0; margin-left: 12px; opacity: .7; }}
    .score-note {{ width: 70%; color: rgba(255,255,255,.75); }}
    .metrics {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }}
    .metric {{
      border-radius: 20px; padding: 22px; background: var(--panel);
      border: 1px solid rgba(255,255,255,.8); box-shadow: 0 10px 30px rgba(19,35,29,.06);
    }}
    .metric-value {{ font-size: 32px; font-weight: 800; letter-spacing: -.04em; margin-top: 5px; }}
    section {{ padding: 34px 0; }}
    .section-head {{ display: flex; align-items: end; justify-content: space-between; gap: 20px; margin-bottom: 20px; }}
    h2 {{ font-size: clamp(27px, 4vw, 44px); letter-spacing: -.045em; margin: 0; }}
    .section-note {{ max-width: 500px; color: var(--muted); }}
    .panel {{ background: var(--panel); border: 1px solid rgba(255,255,255,.85); border-radius: 24px; padding: 24px; box-shadow: 0 14px 40px rgba(19,35,29,.07); }}
    .pitch {{
      padding: 34px 20px; border-radius: 22px;
      background:
        linear-gradient(rgba(255,255,255,.14) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.14) 1px, transparent 1px),
        linear-gradient(135deg, #117254, #09533e);
      background-size: 42px 42px, 42px 42px, auto;
      border: 4px solid rgba(255,255,255,.65);
    }}
    .pitch-row {{ display: flex; justify-content: center; gap: 12px; margin: 18px 0; flex-wrap: wrap; }}
    .player-card {{
      width: 142px; min-height: 108px; background: rgba(255,255,255,.94);
      border-radius: 14px; padding: 13px; color: var(--ink);
      box-shadow: 0 10px 24px rgba(0,0,0,.15); position: relative;
    }}
    .player-name {{ font-weight: 800; font-size: 14px; min-height: 42px; }}
    .player-meta {{ font-size: 11px; color: var(--muted); }}
    .player-points {{ margin-top: 3px; color: var(--green-dark); font-size: 25px; font-weight: 850; }}
    .player-points span {{ font-size: 11px; color: var(--muted); font-weight: 650; }}
    .badge {{ display: inline-grid; place-items: center; margin-left: 5px; width: 19px; height: 19px; border-radius: 50%; color: white; font-size: 10px; }}
    .captain {{ background: var(--orange); }} .vice {{ background: var(--blue); }}
    .bench {{ display: grid; grid-template-columns: repeat(4, 142px); justify-content: center; gap: 12px; margin-top: 18px; }}
    .bench .player-card {{ border: 1px solid var(--line); box-shadow: none; }}
    .bench-title {{ text-align: center; color: var(--muted); font-weight: 750; margin-top: 20px; }}
    .callout {{
      margin-top: 18px; padding: 17px 19px; border-left: 5px solid var(--orange);
      background: #fff4e9; border-radius: 0 14px 14px 0;
    }}
    .timeline {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; counter-reset: stage; }}
    .stage {{ background: var(--panel); border: 1px solid var(--line); border-radius: 18px; padding: 21px; }}
    .stage::before {{ counter-increment: stage; content: "0" counter(stage); display: block; color: var(--green); font-size: 12px; font-weight: 900; margin-bottom: 24px; }}
    .stage strong {{ display: block; font-size: 17px; margin-bottom: 7px; }}
    .stage p {{ margin: 0; color: var(--muted); font-size: 13px; }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 780px; }}
    th, td {{ padding: 14px 12px; text-align: left; border-bottom: 1px solid var(--line); }}
    th {{ color: var(--muted); text-transform: uppercase; letter-spacing: .08em; font-size: 10px; }}
    td:first-child {{ font-weight: 750; }} code {{ font: 12px/1.2 ui-monospace, SFMono-Regular, Consolas, monospace; }}
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
    .state-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 18px; }}
    .state-item {{ padding: 15px; border-radius: 14px; background: #edf3ee; }}
    .state-item strong {{ display: block; font-size: 23px; letter-spacing: -.03em; }}
    .limitations {{ columns: 2; padding-left: 20px; color: var(--muted); }}
    .limitations li {{ break-inside: avoid; margin: 0 0 9px; }}
    .hashes {{ display: grid; gap: 11px; }}
    .hash-row {{ display: grid; grid-template-columns: 150px 1fr; gap: 12px; padding-bottom: 10px; border-bottom: 1px solid var(--line); }}
    .hash-row span {{ color: var(--muted); }}
    .hash-row code {{ overflow-wrap: anywhere; }}
    footer {{ padding: 42px 0 70px; color: var(--muted); font-size: 12px; }}
    @media (max-width: 820px) {{
      .hero-grid, .two-col {{ grid-template-columns: 1fr; }}
      .timeline {{ grid-template-columns: 1fr 1fr; }}
      .bench {{ grid-template-columns: repeat(2, 142px); }}
      .limitations {{ columns: 1; }}
      .score {{ font-size: 90px; }}
    }}
    @media (max-width: 480px) {{
      .shell {{ width: min(100% - 20px, 1180px); }}
      header {{ padding-top: 40px; }}
      .metrics {{ grid-template-columns: 1fr 1fr; }}
      .timeline {{ grid-template-columns: 1fr; }}
      .player-card {{ width: 126px; }}
      .bench {{ grid-template-columns: repeat(2, 126px); }}
      .hash-row {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header class="shell">
    <div class="eyebrow">Benchmark V0 · Genuine historical replay</div>
    <h1>Gameweek 1<br>checkpoint review</h1>
    <p class="lede">A governed opening squad, frozen before the deadline, scored only after the official outcome was revealed, then advanced into five isolated policy states for Gameweek 2.</p>
    <div class="hero-grid">
      <article class="score-card">
        <div class="score-label">Official Scout seed · Net score</div>
        <div class="score">{int(transition["net_points"])}<span>points</span></div>
        <div class="score-note">One shared opening action. Five independently hashed benchmark arms. No hindsight correction.</div>
      </article>
      <div class="metrics">
        <article class="metric"><div class="metric-label">Transfers</div><div class="metric-value">{int(plan["finance"]["transfer_count"])}</div></article>
        <article class="metric"><div class="metric-label">Hit cost</div><div class="metric-value">−{int(plan["finance"]["hit_cost"])}</div></article>
        <article class="metric"><div class="metric-label">Autosubs</div><div class="metric-value">{len(outcome["substitutions"])}</div></article>
        <article class="metric"><div class="metric-label">GW2 free transfers</div><div class="metric-value">{int(next_state["free_transfers"])}</div></article>
      </div>
    </div>
  </header>

  <main>
    <section class="shell">
      <div class="section-head">
        <div><div class="eyebrow">The decision</div><h2>Starting XI and realised points</h2></div>
        <p class="section-note">The card values are raw FPL points. Palmer's three points are counted a second time through captaincy.</p>
      </div>
      <div class="panel">
        <div class="pitch">{pitch_rows}</div>
        <div class="bench-title">Ordered bench</div>
        <div class="bench">{bench_cards}</div>
        <div class="callout"><strong>Seven points stayed on the bench.</strong> Rodon returned 7, but every starting player appeared, so the engine correctly made no automatic substitution.</div>
      </div>
    </section>

    <section class="shell">
      <div class="section-head">
        <div><div class="eyebrow">Temporal boundary</div><h2>What the checkpoint proves</h2></div>
      </div>
      <div class="timeline">
        <article class="stage"><strong>Observed episode</strong><p>Only deadline-safe structured inputs and the governed Scout seed were visible.</p></article>
        <article class="stage"><strong>Plan frozen</strong><p>{escape(deadline)}. Exact XI, ordered bench, captain and chip state were hashed.</p></article>
        <article class="stage"><strong>Outcome revealed</strong><p>{escape(reveal_time)}. Official element IDs were resolved through the immutable identity map.</p></article>
        <article class="stage"><strong>State advanced</strong><p>Points, prices, bank, transfers and chips moved independently into opening GW2 state.</p></article>
      </div>
    </section>

    <section class="shell">
      <div class="section-head">
        <div><div class="eyebrow">Policy isolation</div><h2>Five arms, one controlled start</h2></div>
        <p class="section-note">The action is intentionally identical in GW1. Different hashes prove each arm owns its plan and successor state. Policy divergence begins in GW2.</p>
      </div>
      <div class="panel table-wrap">
        <table>
          <thead><tr><th>Policy arm</th><th>Points</th><th>Transfers</th><th>GW2 FT</th><th>Plan hash</th><th>Next-state hash</th></tr></thead>
          <tbody>{arm_rows}</tbody>
        </table>
      </div>
    </section>

    <section class="shell">
      <div class="two-col">
        <article class="panel">
          <div class="eyebrow">GW2 handoff</div>
          <h2>Ready, not decided</h2>
          <p>No Gameweek 2 proposal or outcome exists yet. This is the state each arm will start from before its policy is invoked.</p>
          <div class="state-grid">
            <div class="state-item"><span>Squad</span><strong>{len(next_state["squad"])} players</strong></div>
            <div class="state-item"><span>Bank</span><strong>£{float(next_state["bank"]):.1f}m</strong></div>
            <div class="state-item"><span>Free transfers</span><strong>{int(next_state["free_transfers"])}</strong></div>
            <div class="state-item"><span>Cumulative</span><strong>{int(next_state["cumulative_points"])} pts</strong></div>
          </div>
          <p><strong>Available chips:</strong> {escape(chips)}</p>
        </article>
        <article class="panel">
          <div class="eyebrow">Known constraints</div>
          <h2>Evidence limits</h2>
          <ul class="limitations">{limitations}</ul>
        </article>
      </div>
    </section>

    <section class="shell">
      <div class="section-head">
        <div><div class="eyebrow">Reproducibility</div><h2>Bound inputs and outputs</h2></div>
      </div>
      <div class="panel hashes">
        <div class="hash-row"><span>Code commit</span><code>{escape(summary["code_commit"])}</code></div>
        <div class="hash-row"><span>Observed episode</span><code>{escape(summary["observed_sha256"])}</code></div>
        <div class="hash-row"><span>Hidden outcome</span><code>{escape(summary["hidden_outcome_sha256"])}</code></div>
        <div class="hash-row"><span>Identity map</span><code>{escape(summary["identity_map_sha256"])}</code></div>
        <div class="hash-row"><span>Ruleset</span><code>{escape(summary["ruleset"]["content_sha256"])}</code></div>
        <div class="hash-row"><span>Feature state</span><code>{escape(summary["feature_state_sha256"])}</code></div>
        <div class="hash-row"><span>Run summary</span><code>{escape(summary["content_sha256"])}</code></div>
      </div>
    </section>
  </main>

  <footer class="shell">
    FPL Agentic Decision Laboratory · {escape(summary["episode_id"])} · Report generated from committed deterministic artifacts.
  </footer>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=REPO / "reports" / "benchmarks" / "2025-26" / "gw-01",
    )
    parser.add_argument(
        "--seed",
        type=Path,
        default=REPO
        / "control"
        / "seeds"
        / "2025-26"
        / "official-scout-gw1.json",
    )
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    output = args.out or args.checkpoint / "index.html"
    print(render_report(checkpoint_dir=args.checkpoint, seed_path=args.seed, output_path=output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
