"""Static HTML render for live Gameweek Decision Records (ticket 14).

No server, no network, no execution controls. Optional Monte Carlo / price-risk
sections render as explicitly unavailable when absent. Status is always shown
with colour-independent text labels for accessibility.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from html import escape
import json
from pathlib import Path
from typing import Any


class GdrHtmlError(ValueError):
    """Raised when a GDR cannot be rendered safely."""


def _text(value: Any, *, default: str = "unavailable") -> str:
    if value is None or value == "":
        return default
    return str(value)


def _status_label(*, degraded: bool, data_quality: Any) -> str:
    if degraded:
        return f"DEGRADED — {_text(data_quality, default='degraded')}"
    return f"OK — {_text(data_quality, default='complete')}"


def _list_or_empty(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def scan_gameweek_records(gameweeks_root: Path) -> list[dict[str, Any]]:
    """Discover decision-record.json files under ``reports/gameweeks/``."""

    if not gameweeks_root.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(gameweeks_root.glob("*/decision-record.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        season = str(payload.get("season") or path.parent.name)
        try:
            gameweek = int(payload.get("gameweek") or 0)
        except (TypeError, ValueError):
            gameweek = 0
        rows.append(
            {
                "path": path,
                "dir": path.parent,
                "season": season,
                "gameweek": gameweek,
                "record_id": payload.get("record_id"),
                "has_outcome": payload.get("outcome") is not None,
                "has_retrospective": payload.get("retrospective") is not None,
                "degraded": bool(payload.get("degraded")),
                "html_name": "decision-record.html",
            }
        )
    rows.sort(key=lambda row: (row["season"], row["gameweek"], str(row["path"])))
    return rows


def render_season_index_html(
    entries: Sequence[Mapping[str, Any]],
    *,
    title: str = "Live Gameweek Decision Records",
) -> str:
    """Render a season index linking each GDR and outcome presence."""

    rows = []
    for entry in entries:
        rel = f"{Path(entry['dir']).name}/{entry.get('html_name') or 'decision-record.html'}"
        outcome = "attached" if entry.get("has_outcome") else "not attached"
        retrospective = (
            "attached" if entry.get("has_retrospective") else "not attached"
        )
        health = "DEGRADED" if entry.get("degraded") else "OK"
        rows.append(
            "<tr>"
            f"<td>{escape(str(entry.get('season')))}</td>"
            f"<td>{escape(str(entry.get('gameweek')))}</td>"
            f"<td><a href=\"{escape(rel)}\">{escape(_text(entry.get('record_id')))}</a></td>"
            f"<td><span class=\"status-text\" data-status=\"{escape(health)}\">{escape(health)}</span></td>"
            f"<td>{escape(outcome)}</td>"
            f"<td>{escape(retrospective)}</td>"
            "</tr>"
        )
    body_rows = "\n".join(rows) or (
        "<tr><td colspan=\"6\">No Gameweek Decision Records found.</td></tr>"
    )
    return _wrap_page(
        title=title,
        body=(
            f"<header><p class=\"eyebrow\">FPL Decision Laboratory</p>"
            f"<h1>{escape(title)}</h1>"
            "<p>Static index over local <code>reports/gameweeks/</code>. "
            "No execution controls.</p></header>"
            "<main><section aria-labelledby=\"index-heading\">"
            "<h2 id=\"index-heading\">Records</h2>"
            "<table>"
            "<caption>Available live Gameweek Decision Records</caption>"
            "<thead><tr>"
            "<th scope=\"col\">Season</th>"
            "<th scope=\"col\">GW</th>"
            "<th scope=\"col\">Record</th>"
            "<th scope=\"col\">Health</th>"
            "<th scope=\"col\">Outcome</th>"
            "<th scope=\"col\">Retrospective</th>"
            "</tr></thead>"
            f"<tbody>{body_rows}</tbody></table></section></main>"
        ),
    )


def render_gdr_html(record: Mapping[str, Any]) -> str:
    """Render one GDR to deterministic, self-contained HTML."""

    if "record_id" not in record:
        raise GdrHtmlError("GDR missing record_id")
    recommendation = _mapping(record.get("recommendation"))
    validation = _mapping(record.get("validation"))
    approval = record.get("approval")
    if isinstance(approval, Mapping):
        approval_text = (
            f"{_text(approval.get('status'))}"
            + (
                f" — {_text(approval.get('notes'), default='')}"
                if approval.get("notes")
                else ""
            )
            + (
                f" (journal: {_text(approval.get('journal_ref'))})"
                if approval.get("journal_ref")
                else ""
            )
        )
    else:
        approval_text = _text(approval)

    projections = _mapping(record.get("projections_summary"))
    freshness = _mapping(record.get("freshness"))
    capture = _mapping(freshness.get("capture"))
    evidence = _mapping(record.get("evidence"))
    baseline = _mapping(record.get("baseline_comparison"))
    validated = _mapping(record.get("validated_plan"))
    lineup = _mapping(validated.get("lineup"))
    provenance = _mapping(record.get("provenance"))

    degraded = bool(record.get("degraded"))
    health = _status_label(degraded=degraded, data_quality=record.get("data_quality"))
    reasons = _list_or_empty(record.get("degraded_reasons"))
    reason_text = ", ".join(str(item) for item in reasons) if reasons else "none"

    model_versions = _list_or_empty(projections.get("model_versions"))
    has_mc = bool(
        projections.get("p50") is not None
        or projections.get("simulation")
        or any(
            isinstance(plan, Mapping) and plan.get("points_distribution")
            for plan in _list_or_empty(record.get("candidate_plans"))
        )
    )
    price_risk = record.get("price_risk")
    has_price = price_risk is not None
    chip_ev = record.get("chip_distributional_ev")
    has_chip_ev = isinstance(chip_ev, Mapping)
    horizon = record.get("chip_horizon_policy_comparison")
    has_horizon = isinstance(horizon, Mapping)

    plan_rows = []
    for plan in _list_or_empty(record.get("candidate_plans")):
        if not isinstance(plan, Mapping):
            continue
        dist = _mapping(plan.get("points_distribution"))
        if dist:
            dist_text = (
                f"P10={dist.get('p10')} P50={dist.get('p50')} "
                f"P90={dist.get('p90')} mean={dist.get('mean')}"
            )
        else:
            dist_text = "unavailable (ticket 05 not attached)"
        plan_rows.append(
            "<tr>"
            f"<td>{escape(_text(plan.get('strategy')))}</td>"
            f"<td>{escape(_text(plan.get('objective')))}</td>"
            f"<td>{escape(_text(plan.get('hit_cost'), default='0'))}</td>"
            f"<td>{escape(dist_text)}</td>"
            "</tr>"
        )
    if not plan_rows:
        plan_rows.append(
            "<tr><td colspan=\"4\">No candidate plans on this record.</td></tr>"
        )

    support = _list_or_empty(evidence.get("supporting_claim_ids"))
    conflict = _list_or_empty(evidence.get("conflicting_claim_ids"))
    conflicts = _list_or_empty(evidence.get("conflict_ids"))
    evidence_block = (
        f"<p>Supporting claims: {escape(', '.join(map(str, support)) or 'none')}</p>"
        f"<p>Conflicting claims: {escape(', '.join(map(str, conflict)) or 'none')}</p>"
        f"<p>Conflicts: {escape(', '.join(map(str, conflicts)) or 'none')}</p>"
    )
    if not support and not conflict and not conflicts:
        evidence_block = "<p>Evidence citations unavailable on this record.</p>"

    mc_block = (
        "<p>"
        f"P10={escape(_text(projections.get('p10')))}, "
        f"P50={escape(_text(projections.get('p50')))}, "
        f"P90={escape(_text(projections.get('p90')))}"
        "</p>"
        if has_mc
        else "<p>Monte Carlo distributions unavailable (ticket 05).</p>"
    )
    price_block = (
        f"<pre>{escape(json.dumps(price_risk, indent=2, sort_keys=True))}</pre>"
        if has_price
        else "<p>Price-risk annotations unavailable (ticket 07).</p>"
    )
    if has_chip_ev:
        justification = _mapping(chip_ev.get("justification"))
        selected_vs = justification.get("selected_vs_later")
        if isinstance(selected_vs, Mapping):
            chip_ev_block = (
                "<p>"
                f"Selected {escape(_text(chip_ev.get('selected_active_chip'), default='no chip'))} "
                f"({escape(_text(chip_ev.get('selected_candidate_id')))}) "
                f"beats later control with probability "
                f"{escape(_text(selected_vs.get('prob_candidate_beats_alternative')))} "
                f"(mean Δ {escape(_text(selected_vs.get('mean_delta')))})."
                "</p>"
            )
        else:
            chip_ev_block = (
                "<p>Distributional chip annotation present; selected candidate is "
                "the later-control reference.</p>"
            )
    else:
        chip_ev_block = (
            "<p>Distributional chip EV unavailable (ticket 09 not attached).</p>"
        )
    horizon_block = (
        f"<pre>{escape(json.dumps(horizon, indent=2, sort_keys=True))}</pre>"
        if has_horizon
        else "<p>Horizon policy comparison unavailable (ticket 09).</p>"
    )

    squad_ok = _mapping(validation.get("squad")).get("ok")
    lineup_ok = _mapping(validation.get("lineup")).get("ok")
    validation_text = (
        f"squad={'OK' if squad_ok else 'FAIL' if squad_ok is False else 'unavailable'}; "
        f"lineup={'OK' if lineup_ok else 'FAIL' if lineup_ok is False else 'unavailable'}"
    )

    body = f"""
<header>
  <p class="eyebrow">FPL Decision Laboratory · advisory only</p>
  <h1>Gameweek Decision Record</h1>
  <p class="lede">Proposal <code>{escape(_text(record.get('record_id')))}</code>
  · season {escape(_text(record.get('season')))}
  · GW {escape(_text(record.get('gameweek')))}</p>
  <p><span class="status-text" data-status="{escape('DEGRADED' if degraded else 'OK')}">{escape(health)}</span></p>
</header>
<main>
  <section aria-labelledby="meta-heading">
    <h2 id="meta-heading">Cutoff, rules and provenance</h2>
    <dl>
      <dt>Decision cutoff</dt><dd>{escape(_text(record.get('decision_cutoff')))}</dd>
      <dt>Deadline</dt><dd>{escape(_text(record.get('deadline')))}</dd>
      <dt>Ruleset</dt><dd>{escape(_text(record.get('ruleset_id')))}</dd>
      <dt>Model versions</dt><dd>{escape(', '.join(map(str, model_versions)) or 'unavailable')}</dd>
      <dt>Provenance</dt><dd>{escape(json.dumps(provenance, sort_keys=True) if provenance else 'unavailable')}</dd>
      <dt>Approval journal</dt><dd>{escape(approval_text)}</dd>
    </dl>
  </section>

  <section aria-labelledby="health-heading">
    <h2 id="health-heading">Freshness and degraded state</h2>
    <p>Health: <span class="status-text" data-status="{escape('DEGRADED' if degraded else 'OK')}">{escape(health)}</span></p>
    <p>Degraded reasons: {escape(reason_text)}</p>
    <p>Capture freshness: {escape(_text(capture.get('status')))}
    · missed jobs: {escape(_text(capture.get('missed_job_count'), default='unavailable'))}
    · stale sources: {escape(_text(capture.get('stale_source_count'), default='unavailable'))}</p>
  </section>

  <section aria-labelledby="rec-heading">
    <h2 id="rec-heading">Recommendation</h2>
    <dl>
      <dt>Strategy</dt><dd>{escape(_text(recommendation.get('strategy')))}</dd>
      <dt>Objective</dt><dd>{escape(_text(recommendation.get('objective')))}</dd>
      <dt>Captain</dt><dd>{escape(_text(recommendation.get('captain_name')))}</dd>
      <dt>Vice-captain</dt><dd>{escape(_text(recommendation.get('vice_captain_name')))}</dd>
      <dt>Validated plan hash</dt><dd><code>{escape(_text(recommendation.get('validated_plan_sha256')))}</code></dd>
      <dt>Formation / XI</dt><dd>{escape(_text(lineup.get('formation')))} · starters {escape(', '.join(map(str, _list_or_empty(lineup.get('starting_xi_ids'))) or ['unavailable']))}</dd>
    </dl>
    <p>Baseline: do-nothing {escape(_text(baseline.get('do_nothing_objective')))}
    → recommended {escape(_text(baseline.get('recommended_objective')))}
    (advantage {escape(_text(baseline.get('expected_advantage')))})</p>
  </section>

  <section aria-labelledby="plans-heading">
    <h2 id="plans-heading">Candidate plans</h2>
    <table>
      <caption>Candidate plan objectives and optional Monte Carlo distributions</caption>
      <thead><tr>
        <th scope="col">Strategy</th>
        <th scope="col">Objective</th>
        <th scope="col">Hit cost</th>
        <th scope="col">Points distribution</th>
      </tr></thead>
      <tbody>
        {''.join(plan_rows)}
      </tbody>
    </table>
  </section>

  <section aria-labelledby="mc-heading">
    <h2 id="mc-heading">Monte Carlo summary</h2>
    {mc_block}
  </section>

  <section aria-labelledby="price-heading">
    <h2 id="price-heading">Price risk</h2>
    {price_block}
  </section>

  <section aria-labelledby="chip-ev-heading">
    <h2 id="chip-ev-heading">Distributional chip EV</h2>
    {chip_ev_block}
  </section>

  <section aria-labelledby="horizon-heading">
    <h2 id="horizon-heading">Horizon policy comparison</h2>
    {horizon_block}
  </section>

  <section aria-labelledby="evidence-heading">
    <h2 id="evidence-heading">Evidence</h2>
    {evidence_block}
  </section>

  <section aria-labelledby="validation-heading">
    <h2 id="validation-heading">Validation</h2>
    <p>{escape(validation_text)}</p>
  </section>

  <section aria-labelledby="outcome-heading">
    <h2 id="outcome-heading">Outcome and retrospective</h2>
    <p>Outcome: {escape('attached' if record.get('outcome') is not None else 'not attached')}</p>
    <p>Retrospective: {escape('attached' if record.get('retrospective') is not None else 'not attached')}</p>
  </section>
</main>
<footer>
  <p>Advisory only. No account writes. Approval remains a journal entry; execution remains manual.</p>
</footer>
"""
    return _wrap_page(title=f"GDR {_text(record.get('record_id'))}", body=body)


def _wrap_page(*, title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{escape(title)}</title>
  <style>
    :root {{
      --ink: #1a1a1a;
      --paper: #f7f4ef;
      --line: #cfc7bb;
      --muted: #5c564c;
      --panel: #fffdf8;
    }}
    body {{
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", Palatino, serif;
      color: var(--ink);
      background:
        linear-gradient(180deg, #ebe4d8 0%, var(--paper) 28%, #f3efe7 100%);
      line-height: 1.45;
    }}
    header, main, footer {{
      width: min(920px, calc(100% - 2rem));
      margin: 0 auto;
    }}
    header {{ padding: 2.5rem 0 1rem; }}
    .eyebrow {{ text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.75rem; color: var(--muted); }}
    h1, h2 {{ font-weight: 600; line-height: 1.15; }}
    h1 {{ font-size: clamp(1.8rem, 4vw, 2.6rem); margin: 0.4rem 0 0.8rem; }}
    h2 {{ font-size: 1.25rem; margin-top: 0; }}
    section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 2px;
      padding: 1rem 1.1rem 1.15rem;
      margin: 0 0 1rem;
    }}
    dl {{ display: grid; grid-template-columns: 12rem 1fr; gap: 0.35rem 1rem; margin: 0; }}
    dt {{ color: var(--muted); }}
    dd {{ margin: 0; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid var(--line); text-align: left; padding: 0.45rem 0.35rem; vertical-align: top; }}
    caption {{ caption-side: top; text-align: left; color: var(--muted); margin-bottom: 0.4rem; }}
    .status-text {{ font-weight: 700; }}
    .status-text[data-status="DEGRADED"]::before {{ content: "[DEGRADED] "; }}
    .status-text[data-status="OK"]::before {{ content: "[OK] "; }}
    code, pre {{ font-family: "Cascadia Code", "Consolas", monospace; font-size: 0.85rem; overflow-wrap: anywhere; }}
    footer {{ color: var(--muted); padding: 1rem 0 2.5rem; font-size: 0.9rem; }}
    a {{ color: var(--ink); }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""


def write_gdr_html(record: Mapping[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_gdr_html(record), encoding="utf-8", newline="\n")
    return path


def write_season_index(gameweeks_root: Path, output_path: Path) -> Path:
    entries = scan_gameweek_records(gameweeks_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_season_index_html(entries), encoding="utf-8", newline="\n"
    )
    return output_path
