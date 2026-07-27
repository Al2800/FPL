#!/usr/bin/env python3
"""Render the sealed GW2-GW11 evidence replay as a standalone HTML audit."""

from __future__ import annotations

from html import escape
import json
from pathlib import Path

from src.orchestration.evidence_fork import _read, _write_once


REPO = Path(__file__).resolve().parents[1]
SUMMARY = (
    REPO
    / "reports/benchmarks/2025-26-early-evidence/early-season-summary.json"
)
EVAL_SUMMARY = (
    REPO / "evals/evidence-forks/2025-26/early-season-summary.json"
)
OUTPUT = REPO / "reports/benchmarks/2025-26/evidence-early-season.html"


def _transfers(rows: list[dict]) -> str:
    if not rows:
        return "Bank"
    return "<br>".join(
        f"{escape(str(row['player_out']))} → {escape(str(row['player_in']))}"
        for row in rows
    )


def main() -> int:
    summary = _read(SUMMARY)
    _write_once(EVAL_SUMMARY, summary)
    isolated = {int(row["gameweek"]): row for row in summary["isolated_weeks"]}
    longitudinal = {
        int(row["gameweek"]): row for row in summary["longitudinal_weeks"]
    }
    canonical = {
        int(row["gameweek"]): row
        for row in summary["frozen_no_evidence_shadow"]["weeks"]
    }
    rows = []
    for gameweek in range(2, 12):
        direct = isolated[gameweek]["same_state_attribution"][
            "agent_evidence_delta"
        ]
        carried = (
            int(longitudinal[gameweek]["agent_fork_gross_points"])
            - int(canonical[gameweek]["net_points"])
        )
        rows.append(
            "<tr>"
            f"<td>GW{gameweek}</td>"
            f"<td><span class='pill {escape(isolated[gameweek]['agent_decision'])}'>"
            f"{escape(isolated[gameweek]['agent_decision'])}</span></td>"
            f"<td>{_transfers(isolated[gameweek]['selected_transfer_names'])}</td>"
            f"<td>{escape(str(isolated[gameweek]['captain']))}</td>"
            f"<td>{canonical[gameweek]['net_points']}</td>"
            f"<td>{longitudinal[gameweek]['agent_fork_gross_points']}</td>"
            f"<td class='delta {'negative' if direct < 0 else 'positive' if direct > 0 else ''}'>"
            f"{direct:+d}</td>"
            f"<td class='delta {'negative' if carried < 0 else 'positive' if carried > 0 else ''}'>"
            f"{carried:+d}</td>"
            "</tr>"
        )
    bridge = summary["gw12_bridge"]
    protocol = summary["protocol_metrics"]
    canonical_total = summary["frozen_no_evidence_shadow"]["net_points"]
    fork_total = summary["longitudinal_net_points"]
    season_delta = fork_total - canonical_total
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FPL early-season evidence replay</title>
<style>
:root{{--bg:#081019;--panel:#101c28;--panel2:#142536;--text:#e8f0f7;--muted:#91a6b8;
--line:#294052;--cyan:#6ee7f2;--green:#5ee0a0;--red:#ff7d86;--amber:#f2c66d}}
*{{box-sizing:border-box}} body{{margin:0;background:linear-gradient(145deg,#07101a,#0b1722);
color:var(--text);font:15px/1.55 Inter,Segoe UI,system-ui,sans-serif}}
main{{max-width:1180px;margin:auto;padding:48px 24px 72px}} h1{{font-size:42px;line-height:1.05;
letter-spacing:-1.5px;margin:0 0 12px}} h2{{margin:42px 0 14px;font-size:23px}}
p{{color:var(--muted);max-width:900px}} .eyebrow{{color:var(--cyan);text-transform:uppercase;
letter-spacing:2px;font-size:12px;font-weight:700}} .cards{{display:grid;
grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:28px 0}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px}}
.card b{{display:block;font-size:29px;margin-top:5px}} .label{{color:var(--muted);font-size:12px;
text-transform:uppercase;letter-spacing:1px}} table{{border-collapse:collapse;width:100%;
background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden}}
th,td{{padding:12px 11px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
th{{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.8px;
background:var(--panel2)}} tr:last-child td{{border-bottom:0}} .pill{{display:inline-block;
padding:3px 8px;border-radius:99px;background:#203344;color:var(--muted);font-size:12px}}
.pill.applied{{background:#163c36;color:var(--green)}} .pill.degraded_fallback{{background:#44351c;
color:var(--amber)}} .delta{{font-variant-numeric:tabular-nums}} .negative{{color:var(--red)}}
.positive{{color:var(--green)}} .finding{{background:var(--panel);border-left:3px solid var(--cyan);
padding:16px 18px;margin:10px 0;border-radius:0 12px 12px 0}} code{{color:var(--cyan)}}
.hash{{font:12px/1.5 ui-monospace,Consolas,monospace;word-break:break-all;color:var(--muted)}}
@media(max-width:850px){{.cards{{grid-template-columns:1fr 1fr}} table{{font-size:12px}}}}
</style>
</head>
<body><main>
<div class="eyebrow">Benchmark v0 · 2025/26 · exploratory only</div>
<h1>Early-season evidence replay</h1>
<p>GW2–GW11, starting from the unchanged official Scout seed. Evidence decisions
are compared both from the same weekly state and as an independently carried
trajectory. Retrospective sources are never promoted to production evidence.</p>
<div class="cards">
<div class="card"><span class="label">Frozen no-evidence</span><b>{canonical_total}</b>GW2–GW11 net points</div>
<div class="card"><span class="label">Evidence trajectory</span><b>{fork_total}</b>GW2–GW11 net points</div>
<div class="card"><span class="label">Trajectory delta</span><b class="negative">{season_delta:+d}</b>realised points</div>
<div class="card"><span class="label">Protocol</span><b>{protocol['evidence_completed']}/{protocol['week_count']}</b>evidence and challenger pairs complete</div>
</div>
<h2>Week-by-week</h2>
<table><thead><tr><th>Week</th><th>Evidence gate</th><th>Isolated decision</th>
<th>Captain</th><th>Control</th><th>Carried fork</th><th>Direct evidence Δ</th>
<th>Vs canonical Δ</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>What moved the result</h2>
<div class="finding"><strong>GW7 is the causal event.</strong> Gabriel's reported
fitness doubt reduced start probability from 0.9227 to 0.7227. That moved the
optimiser away from Murillo → Gabriel. The evidence plan scored 32 versus 40
from the same state: <span class="negative">−8</span>.</div>
<div class="finding"><strong>GW9 changed the projection, not the score.</strong>
The second Gabriel doubt was admitted and applied, but produced zero direct
realised-point delta.</div>
<div class="finding"><strong>Carried state recovered one point.</strong> By GW11,
the evidence trajectory made different transfers and scored one point more that
week, leaving the GW12 bridge seven points behind overall.</div>
<div class="finding"><strong>Five sources correctly did nothing.</strong> GW2,
GW5, GW8, GW10 and GW11 were context-only or duplicated structured signals.
GW3, GW4 and GW6 proposals were blocked by confidence-downgrade review. Porro's
GW6 player binding was suppressed because the stored passage mentioned only
Palmer.</div>
<h2>Engine implications</h2>
<div class="finding"><strong>Add transfer hysteresis and uncertainty valuation.</strong>
A modest doubt should not automatically veto a strong multiweek transfer. The
engine needs an explicit option-value comparison: buy now under an uncertainty
distribution, defer one week, or choose an alternative—rather than turning a
single adjusted mean into a categorical route switch.</div>
<div class="finding"><strong>Separate appearance probability from conditional
points.</strong> The current adapter applies one ratio to start probability,
expected minutes and expected points. That is deterministic and compatible with
later-season tests, but too coarse for partial fitness, bench risk and substitute
appearances. Calibrate minutes distributions first.</div>
<div class="finding"><strong>Judge evidence ex ante, not from one realised week.</strong>
Gabriel's GW7 report described genuine uncertainty. His eventual return does not
make the source false. Promotion requires calibration across repeated cases,
decision regret, and a frozen no-evidence shadow—not hindsight reward for this
single path.</div>
<h2>GW12 bridge</h2>
<div class="cards">
<div class="card"><span class="label">Cumulative points Δ</span><b class="negative">{bridge['cumulative_points_delta']:+d}</b></div>
<div class="card"><span class="label">Bank Δ</span><b>{bridge['bank_delta']:+.1f}</b></div>
<div class="card"><span class="label">Free transfers</span><b>{bridge['fork_free_transfers']}</b>control {bridge['canonical_free_transfers']}</div>
<div class="card"><span class="label">Squad difference</span><b>{len(bridge['squad_symmetric_difference'])}</b>player IDs in symmetric difference</div>
</div>
<p>The bridge is comparison-only and was not spliced into the accepted
GW12–GW38 trajectory. Canonical artifacts remained byte-identical.</p>
<p class="hash">Summary: {escape(summary['content_sha256'])}<br>
Canonical tree: {escape(summary['canonical_artifacts']['tree_sha256_after'])}</p>
</main></body></html>"""
    OUTPUT.write_text(html, encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "canonical_net_points": canonical_total,
                "fork_net_points": fork_total,
                "delta": season_delta,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
