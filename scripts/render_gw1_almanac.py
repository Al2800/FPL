#!/usr/bin/env python3
"""Render a simple GW1 expected-vs-actual almanac HTML page.

Reads the sealed T-24h packet and a local official event-live capture.
Does not rewrite packets, ledgers, or the live 15. Regenerable after
Chelsea / bonus lock by pointing --event-live at a newer capture.
"""

from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
POS = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}

ADVISORY = {
    "id": "advisory",
    "title": "Haaland-in advisory",
    "note": "Live 15. Owner Bruno (C) / Haaland (VC). Bank £0.5m. No GW1 chip.",
    "ids": [
        "109",
        "497",
        "112",
        "204",
        "423",
        "259",
        "175",
        "426",
        "480",
        "542",
        "260",
        "544",
        "411",
        "165",
        "106",
    ],
    "xi": [
        "109",
        "423",
        "204",
        "112",
        "426",
        "480",
        "260",
        "542",
        "411",
        "106",
        "165",
    ],
    "bench": ["497", "544", "259", "175"],
    "captain": "426",
    "vice": "411",
}

ROBUST = {
    "id": "robust",
    "title": "Robust no-Haaland comparator",
    "note": "T-24h optimiser 15. Bruno (C) / Semenyo (VC). Bank £0.0. Not the live side.",
    "ids": [
        "1",
        "109",
        "13",
        "165",
        "248",
        "388",
        "397",
        "4",
        "40",
        "423",
        "426",
        "441",
        "481",
        "498",
        "61",
    ],
    "xi": [
        "1",
        "4",
        "388",
        "498",
        "61",
        "426",
        "397",
        "13",
        "40",
        "481",
        "165",
    ],
    "bench": ["109", "423", "248", "441"],
    "captain": "426",
    "vice": "397",
}


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _build_rows(
    *,
    packet: dict[str, Any],
    bootstrap: dict[str, Any],
    live: dict[str, Any],
    fixtures: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], set[int], str]:
    teams = {int(t["id"]): t["short_name"] for t in bootstrap["teams"]}
    els = {int(e["id"]): e for e in bootstrap["elements"]}
    live_by = {int(row["id"]): row for row in live.get("elements", [])}
    by_pkt = {str(p["player_id"]): p for p in packet["players"]}
    pending = {
        int(f["team_h"])
        for f in fixtures
        if f.get("event") == 1 and not f.get("started")
    } | {
        int(f["team_a"])
        for f in fixtures
        if f.get("event") == 1 and not f.get("started")
    }
    remaining = " · ".join(
        f"{teams.get(int(f['team_h']))} v {teams.get(int(f['team_a']))}"
        for f in fixtures
        if f.get("event") == 1 and not f.get("started")
    ) or "none"

    rows: dict[str, dict[str, Any]] = {}
    for pid, el in els.items():
        pkt = by_pkt.get(str(pid), {})
        ep_list = pkt.get("expected_points") or []
        sp_list = pkt.get("start_probability") or []
        stats = (live_by.get(pid) or {}).get("stats") or {}
        actual = stats.get("total_points")
        if actual is None:
            actual = el.get("event_points")
        rows[str(pid)] = {
            "id": str(pid),
            "name": el.get("web_name") or str(pid),
            "team": teams.get(int(el.get("team") or 0), "?"),
            "pos": POS.get(int(el.get("element_type") or 0), "?"),
            "our_ep": _num(ep_list[0]) if ep_list else None,
            "start_p": _num(sp_list[0]) if sp_list else None,
            "minutes": int(stats.get("minutes") or 0),
            "actual": actual,
            "xg": _num(stats.get("expected_goals")),
            "xa": _num(stats.get("expected_assists")),
            "xgi": _num(stats.get("expected_goal_involvements")),
            "goals": int(stats.get("goals_scored") or 0),
            "assists": int(stats.get("assists") or 0),
            "cs": int(stats.get("clean_sheets") or 0),
            "bonus": int(stats.get("bonus") or 0),
            "pen_miss": int(stats.get("penalties_missed") or 0),
            "pending": int(el.get("team") or 0) in pending,
        }
    return rows, pending, remaining


def _attach_official(
    rows: dict[str, dict[str, Any]], t24_bootstrap: dict[str, Any]
) -> None:
    els = {int(e["id"]): e for e in t24_bootstrap["elements"]}
    for pid, row in rows.items():
        el = els.get(int(pid))
        row["official_ep"] = _num(el.get("ep_next")) if el else None


def _score_side(
    side: dict[str, Any], rows: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    xi_pts = 0
    cap = 0
    bench = 0
    pending_xi = 0
    xi_ep = 0.0
    for pid in side["xi"]:
        row = rows[pid]
        pts = int(row["actual"] or 0)
        if row["pending"]:
            pending_xi += 1
        else:
            xi_pts += pts
            if pid == side["captain"]:
                cap += pts
        if row["our_ep"] is not None:
            xi_ep += float(row["our_ep"])
    for pid in side["bench"]:
        row = rows[pid]
        if not row["pending"]:
            bench += int(row["actual"] or 0)
    cap_ep = rows[side["captain"]].get("our_ep") or 0.0
    return {
        "xi_pts": xi_pts,
        "cap": cap,
        "total": xi_pts + cap,
        "bench": bench,
        "pending_xi": pending_xi,
        "xi_ep": xi_ep,
        "plan": xi_ep + float(cap_ep),
    }


def _delta_cell(row: dict[str, Any]) -> str:
    if row["pending"] or row["our_ep"] is None or row["actual"] is None:
        return "—"
    delta = float(row["actual"]) - float(row["our_ep"])
    cls = "up" if delta > 0.25 else "down" if delta < -0.25 else "flat"
    return f'<span class="{cls}">{delta:+.2f}</span>'


def _player_table(
    side: dict[str, Any], rows: dict[str, dict[str, Any]], *, bench: bool
) -> str:
    ids = side["bench"] if bench else side["xi"]
    body = []
    for pid in ids:
        row = rows[pid]
        tags = []
        if pid == side["captain"]:
            tags.append("C")
        if pid == side["vice"]:
            tags.append("VC")
        badge = (
            "".join(f'<span class="badge">{escape(t)}</span>' for t in tags)
            if tags
            else ""
        )
        pending = ' class="pending"' if row["pending"] else ""
        actual = "pend" if row["pending"] else str(row["actual"] if row["actual"] is not None else "—")
        ep = "—" if row["our_ep"] is None else f"{row['our_ep']:.2f}"
        off = "—" if row["official_ep"] is None else f"{row['official_ep']:.2f}"
        note = []
        if row["pen_miss"]:
            note.append("missed pen")
        if row["goals"]:
            note.append(f"{row['goals']}G")
        if row["assists"]:
            note.append(f"{row['assists']}A")
        if row["cs"]:
            note.append("CS")
        if row["bonus"]:
            note.append(f"B{row['bonus']}")
        body.append(
            f"<tr{pending}>"
            f"<td>{escape(row['name'])}{badge}</td>"
            f"<td>{escape(row['team'])}</td>"
            f"<td>{escape(row['pos'])}</td>"
            f"<td class='num'>{row['minutes']}</td>"
            f"<td class='num'>{ep}</td>"
            f"<td class='num'>{off}</td>"
            f"<td class='num'>{actual}</td>"
            f"<td class='num'>{_delta_cell(row)}</td>"
            f"<td class='num'>{row['xgi']:.2f}</td>"
            f"<td>{escape(' · '.join(note))}</td>"
            "</tr>"
        )
    return "\n".join(body)


def _union_stats(
    sides: list[dict[str, Any]], rows: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    ids = sorted({pid for side in sides for pid in side["ids"]}, key=int)
    done = [
        rows[pid]
        for pid in ids
        if not rows[pid]["pending"] and rows[pid]["our_ep"] is not None
    ]
    if not done:
        return {"n": 0}
    our = [float(r["our_ep"]) for r in done]
    off = [float(r["official_ep"] or 0) for r in done]
    act = [float(r["actual"] or 0) for r in done]
    n = len(done)
    return {
        "n": n,
        "our": sum(our) / n,
        "off": sum(off) / n,
        "act": sum(act) / n,
        "bias_our": (sum(act) - sum(our)) / n,
        "mae_our": sum(abs(a - o) for a, o in zip(act, our)) / n,
        "bias_off": (sum(act) - sum(off)) / n,
        "mae_off": sum(abs(a - o) for a, o in zip(act, off)) / n,
    }


def render(html_path: Path, payload: dict[str, Any]) -> Path:
    adv = payload["advisory_score"]
    rob = payload["robust_score"]
    stats = payload["stats"]
    remaining = payload["remaining"] or "none"
    html = f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GW1 almanac — 2026/27</title>
  <style>
    :root {{
      --ink: #1c1917;
      --muted: #57534e;
      --line: #d6d3d1;
      --paper: #fafaf9;
      --card: #ffffff;
      --up: #166534;
      --down: #9f1239;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font: 15px/1.45 "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
      color: var(--ink);
      background: var(--paper);
    }}
    header, main, footer {{ max-width: 960px; margin: 0 auto; padding: 1.25rem 1rem; }}
    header {{ border-bottom: 2px solid var(--ink); }}
    h1 {{ font-size: 1.6rem; margin: 0 0 0.35rem; }}
    .meta {{ color: var(--muted); font-size: 0.92rem; }}
    .scoreboard {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.75rem;
      margin: 1.25rem 0;
    }}
    @media (max-width: 700px) {{ .scoreboard {{ grid-template-columns: 1fr; }} }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      padding: 0.9rem 1rem;
    }}
    .card h2 {{ margin: 0 0 0.2rem; font-size: 1.05rem; }}
    .big {{ font-size: 2.2rem; font-variant-numeric: tabular-nums; }}
    .sub {{ color: var(--muted); font-size: 0.9rem; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-variant-numeric: tabular-nums;
      font-size: 0.92rem;
    }}
    th, td {{ padding: 0.28rem 0.4rem; border-bottom: 1px solid var(--line); text-align: left; }}
    th {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.03em; color: var(--muted); }}
    td.num, th.num {{ text-align: right; }}
    tr.pending td {{ color: var(--muted); font-style: italic; }}
    .badge {{
      display: inline-block;
      margin-left: 0.35rem;
      padding: 0 0.3rem;
      border: 1px solid var(--ink);
      font-size: 0.7rem;
      letter-spacing: 0.04em;
    }}
    .up {{ color: var(--up); }}
    .down {{ color: var(--down); }}
    .flat {{ color: var(--muted); }}
    h3 {{ margin: 1.4rem 0 0.4rem; font-size: 1rem; }}
    .note {{ color: var(--muted); font-size: 0.9rem; margin: 0 0 0.5rem; }}
    .stance {{
      border-left: 3px solid var(--ink);
      padding: 0.6rem 0.8rem;
      margin: 1.2rem 0;
      background: #fff;
    }}
    footer {{ border-top: 1px solid var(--line); color: var(--muted); font-size: 0.82rem; }}
    code {{ font-size: 0.8rem; }}
  </style>
</head>
<body>
  <header>
    <h1>Gameweek 1 almanac — 2026/27</h1>
    <p class="meta">
      {escape(payload["status"])} · observed {escape(payload["observed_at"])} ·
      remaining: {escape(remaining)} · packet T-24h
      <code>{escape(payload["packet_sha"][:16])}…</code>
    </p>
    <p class="meta">Record only. Not a transfer recommendation. Account writes: false.</p>
  </header>
  <main>
    <section class="scoreboard">
      <article class="card">
        <h2>Haaland-in advisory</h2>
        <div class="big">{adv["total"]}</div>
        <div class="sub">XI + captain so far · plan {adv["plan"]:.1f} · bench unused {adv["bench"]} · {adv["pending_xi"]} XI still to play</div>
        <p class="note">{escape(ADVISORY["note"])}</p>
      </article>
      <article class="card">
        <h2>Robust no-Haaland</h2>
        <div class="big">{rob["total"]}</div>
        <div class="sub">XI + captain so far · plan {rob["plan"]:.1f} · bench unused {rob["bench"]} · {rob["pending_xi"]} XI still to play</div>
        <p class="note">{escape(ROBUST["note"])}</p>
      </article>
    </section>

    <div class="stance">
      <strong>Owner stance.</strong> No change to the live 15. Do not retune
      weights from this week. Minutes/starts first; shrink returns.
      Official EP is a sense-check, not a new model.
    </div>

    <h3>Advisory XI</h3>
    <p class="note">Our EP is T-24h live-faithful GW1. Official is FPL <code>ep_next</code> on 20 Aug. Δ is actual − our EP.</p>
    <table>
      <thead><tr>
        <th>Player</th><th>Club</th><th>Pos</th>
        <th class="num">Min</th><th class="num">Our EP</th><th class="num">Off. EP</th>
        <th class="num">Act</th><th class="num">Δ</th><th class="num">xGI</th><th>Notes</th>
      </tr></thead>
      <tbody>
        {_player_table(ADVISORY, payload["rows"], bench=False)}
      </tbody>
    </table>
    <h3>Advisory bench</h3>
    <table>
      <thead><tr>
        <th>Player</th><th>Club</th><th>Pos</th>
        <th class="num">Min</th><th class="num">Our EP</th><th class="num">Off. EP</th>
        <th class="num">Act</th><th class="num">Δ</th><th class="num">xGI</th><th>Notes</th>
      </tr></thead>
      <tbody>
        {_player_table(ADVISORY, payload["rows"], bench=True)}
      </tbody>
    </table>

    <h3>Robust XI</h3>
    <table>
      <thead><tr>
        <th>Player</th><th>Club</th><th>Pos</th>
        <th class="num">Min</th><th class="num">Our EP</th><th class="num">Off. EP</th>
        <th class="num">Act</th><th class="num">Δ</th><th class="num">xGI</th><th>Notes</th>
      </tr></thead>
      <tbody>
        {_player_table(ROBUST, payload["rows"], bench=False)}
      </tbody>
    </table>
    <h3>Robust bench</h3>
    <table>
      <thead><tr>
        <th>Player</th><th>Club</th><th>Pos</th>
        <th class="num">Min</th><th class="num">Our EP</th><th class="num">Off. EP</th>
        <th class="num">Act</th><th class="num">Δ</th><th class="num">xGI</th><th>Notes</th>
      </tr></thead>
      <tbody>
        {_player_table(ROBUST, payload["rows"], bench=True)}
      </tbody>
    </table>

    <h3>Engine on these two 15s</h3>
    <p class="note">Completed players only (n={stats["n"]}). Whole-market figures stay in the markdown review; this page is the named sides.</p>
    <table>
      <thead><tr><th>Lens</th><th class="num">Mean</th><th class="num">Bias vs actual</th><th class="num">MAE</th></tr></thead>
      <tbody>
        <tr><td>Our EP</td><td class="num">{stats["our"]:.2f}</td><td class="num">{stats["bias_our"]:+.2f}</td><td class="num">{stats["mae_our"]:.2f}</td></tr>
        <tr><td>Official EP</td><td class="num">{stats["off"]:.2f}</td><td class="num">{stats["bias_off"]:+.2f}</td><td class="num">{stats["mae_off"]:.2f}</td></tr>
        <tr><td>Actual</td><td class="num">{stats["act"]:.2f}</td><td class="num">—</td><td class="num">—</td></tr>
      </tbody>
    </table>
  </main>
  <footer>
    Regenerated by <code>scripts/render_gw1_almanac.py</code>.
    Event-live: <code>{escape(payload["event_live_dir"])}</code>.
    Full write-up: <code>reports/strategy-research/2026-08-24-gw1-midweek-review.md</code>.
  </footer>
</body>
</html>
"""
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
    return html_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--packet",
        type=Path,
        default=REPO / "reports/live/2026-27/initial-squad/T-24h/input-packet.json",
    )
    parser.add_argument(
        "--event-live-dir",
        type=Path,
        default=REPO / "data/live-shadow/fpl/event-live/20260824T103200Z",
    )
    parser.add_argument(
        "--t24-bootstrap",
        type=Path,
        default=REPO
        / "data/snapshots/2026-27/preseason/_live_fetch/20260820T112217Z/api_bootstrap-static.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO / "reports/strategy-research/almanac/gw1-2026-27.html",
    )
    args = parser.parse_args(argv)

    wrap = _read(args.packet)
    packet = wrap.get("packet") or wrap
    live_dir = args.event_live_dir
    live = _read(live_dir / "event-1-live.json")
    bootstrap = _read(live_dir / "api_bootstrap-static.json")
    fixtures = _read(live_dir / "api_fixtures-event-1.json")
    if not isinstance(fixtures, list):
        fixtures = fixtures.get("fixtures") or []
    t24 = _read(args.t24_bootstrap)
    meta = {}
    meta_path = live_dir / "meta.json"
    if meta_path.is_file():
        meta = _read(meta_path)

    rows, _pending, remaining = _build_rows(
        packet=packet, bootstrap=bootstrap, live=live, fixtures=fixtures
    )
    _attach_official(rows, t24)
    adv = _score_side(ADVISORY, rows)
    rob = _score_side(ROBUST, rows)
    stats = _union_stats([ADVISORY, ROBUST], rows)
    packet_sha = str(
        wrap.get("content_sha256")
        or packet.get("content_sha256")
        or "879221d6efd7084734d16586accbc5279d7052177f545a03b8d49eba03f07d24"
    )
    payload = {
        "status": "provisional mid-GW1" if remaining else "GW1 complete (bonus may still move)",
        "observed_at": str(meta.get("observed_at") or "unknown"),
        "remaining": remaining,
        "packet_sha": packet_sha,
        "event_live_dir": str(live_dir.relative_to(REPO)).replace("\\", "/"),
        "rows": rows,
        "advisory_score": adv,
        "robust_score": rob,
        "stats": stats,
    }
    out = render(args.out, payload)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
