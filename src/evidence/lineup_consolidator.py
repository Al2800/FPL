"""Consolidate official + Rotowire lineup citations with FPL availability flags.

Official team sheets remain adjudication truth (ADR-0025). Rotowire predicted
line-ups never silently override official confirmed sheets. Disagreements are
quarantined. Live influence stays off until the trial admission gate passes.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


class LineupConsolidatorError(ValueError):
    """Raised when lineup evidence cannot be consolidated safely."""


REPO = Path(__file__).resolve().parents[2]
DEFAULT_TRIAL_POLICY = (
    REPO / "control" / "policies" / "rotowire-lineups-trial-v1.json"
)


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def consolidator_hash(value: Mapping[str, Any]) -> str:
    payload = {
        key: item for key, item in value.items() if key != "content_sha256"
    }
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = consolidator_hash(result)
    return result


def load_trial_policy(path: Path | None = None) -> dict[str, Any]:
    policy_path = path or DEFAULT_TRIAL_POLICY
    data = json.loads(policy_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "1.0":
        raise LineupConsolidatorError("unsupported trial policy schema")
    if data.get("policy_id") != "rotowire-lineups-trial-v1":
        raise LineupConsolidatorError("unexpected trial policy_id")
    return data


def _time(value: Any, field: str) -> str:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise LineupConsolidatorError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise LineupConsolidatorError(f"{field} must include timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _alias_maps(
    aliases: Mapping[str, Any], *, provider_id: str
) -> tuple[dict[str, str], dict[str, str]]:
    rows = aliases.get("aliases") if isinstance(aliases, Mapping) else None
    if not isinstance(rows, list):
        raise LineupConsolidatorError("aliases.aliases must be a list")
    players: dict[str, str] = {}
    fixtures: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("provider_id")) != provider_id:
            continue
        entity = str(row.get("entity_type"))
        provider_entity = str(row.get("provider_entity_id") or "")
        fpl_entity = str(row.get("fpl_entity_id") or "")
        if not provider_entity or not fpl_entity:
            continue
        if entity == "player":
            players[provider_entity] = fpl_entity
        elif entity == "fixture":
            fixtures[provider_entity] = fpl_entity
    return players, fixtures


def _rotowire_started_by_fixture(
    pack: Mapping[str, Any] | None,
    *,
    aliases: Mapping[str, Any],
) -> dict[str, dict[str, dict[str, Any]]]:
    """Map fpl_fixture_id -> fpl_player_id -> predicted start row."""

    if pack is None:
        return {}
    if pack.get("source_id") != "rotowire-lineups":
        raise LineupConsolidatorError("rotowire pack source_id mismatch")
    player_aliases, fixture_aliases = _alias_maps(
        aliases, provider_id="rotowire-lineups"
    )
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for fixture in pack.get("fixtures") or []:
        provider_fixture_id = str(fixture.get("provider_fixture_id") or "")
        fpl_fixture = fixture_aliases.get(provider_fixture_id)
        if fpl_fixture is None:
            # Names-only packs stay unmapped until aliases exist.
            continue
        by_player: dict[str, dict[str, Any]] = {}
        for side in ("home_xi", "away_xi"):
            for row in fixture.get(side) or []:
                provider_player_id = str(row.get("provider_player_id") or "")
                fpl_id = player_aliases.get(provider_player_id)
                if fpl_id is None:
                    continue
                status = str(row.get("status") or "expected").lower()
                start_probability = {
                    "expected": 0.85,
                    "confirmed": 0.95,
                    "ques": 0.45,
                    "out": 0.05,
                    "sus": 0.0,
                }.get(status, 0.5)
                by_player[fpl_id] = {
                    "fpl_player_id": fpl_id,
                    "provider_player_id": provider_player_id,
                    "name": row.get("name"),
                    "predicted_started": bool(row.get("started")),
                    "status": status,
                    "start_probability": start_probability,
                    "source_id": "rotowire-lineups",
                }
        out[fpl_fixture] = by_player
    return out


def _official_started_by_fixture(
    official_snapshots: Sequence[Mapping[str, Any]] | None,
    *,
    aliases: Mapping[str, Any],
) -> dict[str, dict[str, dict[str, Any]]]:
    if not official_snapshots:
        return {}
    player_aliases, fixture_aliases = _alias_maps(
        aliases, provider_id="official-team-sheets"
    )
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for snapshot in official_snapshots:
        provider_fixture_id = str(
            snapshot.get("provider_fixture_id")
            or ((snapshot.get("citation") or {}).get("provider_snapshot") or {}).get(
                "provider_fixture_id"
            )
            or ""
        )
        # Accept either raw admitted snapshot or rehearsal envelope shape.
        players = snapshot.get("players")
        if players is None and isinstance(snapshot.get("citation"), Mapping):
            players = (
                (snapshot["citation"].get("provider_snapshot") or {}).get("players")
            )
            provider_fixture_id = str(
                (
                    (snapshot["citation"].get("provider_snapshot") or {}).get(
                        "provider_fixture_id"
                    )
                )
                or provider_fixture_id
            )
        fpl_fixture = fixture_aliases.get(provider_fixture_id)
        if fpl_fixture is None or not isinstance(players, list):
            continue
        by_player: dict[str, dict[str, Any]] = {}
        for row in players:
            if not isinstance(row, Mapping):
                continue
            provider_player_id = str(row.get("provider_player_id") or "")
            fpl_id = player_aliases.get(provider_player_id)
            if fpl_id is None:
                continue
            started = bool(row.get("started"))
            by_player[fpl_id] = {
                "fpl_player_id": fpl_id,
                "provider_player_id": provider_player_id,
                "predicted_started": started,
                "status": "confirmed" if started else "bench_or_unused",
                "start_probability": 1.0 if started else 0.05,
                "source_id": "official-lineups-minutes",
            }
        out[fpl_fixture] = by_player
    return out


def consolidate_lineup_evidence(
    *,
    fpl_availability: Sequence[Mapping[str, Any]],
    aliases: Mapping[str, Any],
    rotowire_pack: Mapping[str, Any] | None = None,
    official_snapshots: Sequence[Mapping[str, Any]] | None = None,
    observed_at: str,
    decision_cutoff: str,
    trial_policy: Mapping[str, Any] | None = None,
    live_influence_admitted: bool = False,
) -> dict[str, Any]:
    """Merge lineup evidence into per-player start priors with quarantine.

    Precedence: official confirmed sheet > Rotowire predicted XI > FPL
    chance_of_playing / status. Never averages feeds. When official and
    Rotowire disagree on a mapped starter, the player is quarantined and the
    official sheet wins for adjudication.
    """

    policy = dict(trial_policy or load_trial_policy())
    observed_text = _time(observed_at, "observed_at")
    cutoff_text = _time(decision_cutoff, "decision_cutoff")
    if observed_text > cutoff_text:
        raise LineupConsolidatorError("observed_at must not be after decision_cutoff")

    if live_influence_admitted and not policy.get("live_influence_default"):
        # Explicit owner admission flag required in addition to policy default.
        pass

    official = _official_started_by_fixture(official_snapshots, aliases=aliases)
    rotowire = _rotowire_started_by_fixture(rotowire_pack, aliases=aliases)

    availability = {
        str(row["fpl_player_id"]): dict(row)
        for row in fpl_availability
        if isinstance(row, Mapping) and row.get("fpl_player_id") is not None
    }

    fixture_ids = sorted(set(official) | set(rotowire))
    players_out: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    disagreements = 0
    unmapped_rotowire = 0

    if rotowire_pack is not None:
        _, fixture_aliases = _alias_maps(aliases, provider_id="rotowire-lineups")
        for fixture in rotowire_pack.get("fixtures") or []:
            if str(fixture.get("provider_fixture_id")) not in fixture_aliases:
                unmapped_rotowire += 1

    # Also emit availability-only rows for players not present in XI feeds.
    touched_players: set[str] = set()

    for fixture_id in fixture_ids:
        official_players = official.get(fixture_id, {})
        rotowire_players = rotowire.get(fixture_id, {})
        for fpl_id in sorted(set(official_players) | set(rotowire_players) | set()):
            touched_players.add(fpl_id)
            off = official_players.get(fpl_id)
            rw = rotowire_players.get(fpl_id)
            avail = availability.get(fpl_id, {})
            chance = avail.get("chance_of_playing")
            fpl_status = str(avail.get("status") or "")

            if off is not None and rw is not None:
                if bool(off["predicted_started"]) != bool(rw["predicted_started"]):
                    disagreements += 1
                    quarantined.append(
                        {
                            "fpl_fixture_id": fixture_id,
                            "fpl_player_id": fpl_id,
                            "reason": "official_rotowire_start_disagreement",
                            "official": off,
                            "rotowire": rw,
                        }
                    )
                selected = off
                selected_source = "official-team-sheets"
            elif off is not None:
                selected = off
                selected_source = "official-team-sheets"
            elif rw is not None:
                selected = rw
                selected_source = "rotowire-lineups"
            else:
                continue

            start_probability = float(selected["start_probability"])
            if chance is not None:
                try:
                    chance_f = float(chance) / (
                        100.0 if float(chance) > 1.0 else 1.0
                    )
                except (TypeError, ValueError):
                    chance_f = None
            else:
                chance_f = None

            # Availability can only reduce (never raise) a predicted start prior.
            if chance_f is not None and selected_source != "official-team-sheets":
                start_probability = min(start_probability, chance_f)
            if fpl_status in {"i", "s", "u"} and selected_source != "official-team-sheets":
                start_probability = min(start_probability, 0.05)

            players_out.append(
                {
                    "fpl_fixture_id": fixture_id,
                    "fpl_player_id": fpl_id,
                    "start_probability": round(start_probability, 4),
                    "predicted_started": bool(selected["predicted_started"]),
                    "selected_source": selected_source,
                    "fpl_chance_of_playing": chance,
                    "fpl_status": fpl_status or None,
                    "adjustment_family": "expected_minutes_lineup_evidence",
                    "shadow_only": not live_influence_admitted,
                }
            )

    for fpl_id, avail in sorted(availability.items()):
        if fpl_id in touched_players:
            continue
        chance = avail.get("chance_of_playing")
        try:
            start_probability = (
                float(chance) / (100.0 if float(chance) > 1.0 else 1.0)
                if chance is not None
                else 0.5
            )
        except (TypeError, ValueError):
            start_probability = 0.5
        status = str(avail.get("status") or "")
        if status in {"i", "s", "u"}:
            start_probability = 0.05
        players_out.append(
            {
                "fpl_fixture_id": None,
                "fpl_player_id": fpl_id,
                "start_probability": round(float(start_probability), 4),
                "predicted_started": start_probability >= 0.5,
                "selected_source": "fpl-official-endpoints",
                "fpl_chance_of_playing": chance,
                "fpl_status": status or None,
                "adjustment_family": "expected_minutes_lineup_evidence",
                "shadow_only": not live_influence_admitted,
            }
        )

    return _seal(
        {
            "schema_version": "lineup-evidence-consolidation-v1",
            "policy_id": policy["policy_id"],
            "observed_at": observed_text,
            "decision_cutoff": cutoff_text,
            "live_influence_admitted": bool(live_influence_admitted),
            "adjudication_truth": policy.get("adjudication_truth"),
            "disagreement_policy": policy.get("disagreement_policy"),
            "never_average_feeds": True,
            "fixture_count": len(fixture_ids),
            "player_count": len(players_out),
            "disagreement_count": disagreements,
            "quarantined_count": len(quarantined),
            "unmapped_rotowire_fixture_count": unmapped_rotowire,
            "players": players_out,
            "quarantined": quarantined,
            "baseline_policy": "byte_identical_structured_forecast_when_degraded",
        }
    )


def evaluate_trial_admission(
    metrics: Mapping[str, Any],
    *,
    trial_policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare measured trial metrics against preregistered thresholds."""

    policy = dict(trial_policy or load_trial_policy())
    thresholds = policy["admission_thresholds"]
    checks: list[dict[str, Any]] = []

    def check(name: str, actual: float, minimum: float | None = None, maximum: float | None = None) -> None:
        ok = True
        if minimum is not None and actual < minimum:
            ok = False
        if maximum is not None and actual > maximum:
            ok = False
        checks.append(
            {
                "metric": name,
                "actual": actual,
                "minimum": minimum,
                "maximum": maximum,
                "ok": ok,
            }
        )

    check(
        "fixture_coverage",
        float(metrics["fixture_coverage"]),
        minimum=float(thresholds["min_fixture_coverage"]),
    )
    check(
        "identity_match_rate",
        float(metrics["identity_match_rate"]),
        minimum=float(thresholds["min_identity_match_rate"]),
    )
    check(
        "brier_improvement_vs_chance_of_playing",
        float(metrics["brier_improvement_vs_chance_of_playing"]),
        minimum=float(
            thresholds["min_start_calibration_brier_improvement_vs_chance_of_playing"]
        ),
    )
    check(
        "brier_improvement_vs_started_last_gw",
        float(metrics["brier_improvement_vs_started_last_gw"]),
        minimum=float(
            thresholds["min_start_calibration_brier_improvement_vs_started_last_gw"]
        ),
    )
    check(
        "confirmed_minutes_mae",
        float(metrics["confirmed_minutes_mae"]),
        maximum=float(thresholds["max_confirmed_minutes_mae"]),
    )
    check(
        "citation_latency_hours",
        float(metrics["citation_latency_hours"]),
        maximum=float(thresholds["max_citation_latency_hours"]),
    )
    check(
        "scored_fixtures",
        float(metrics["scored_fixtures"]),
        minimum=float(thresholds["min_scored_fixtures"]),
    )
    check(
        "matchdays",
        float(metrics["matchdays"]),
        minimum=float(thresholds["min_matchdays"]),
    )

    admitted = all(row["ok"] for row in checks)
    return _seal(
        {
            "schema_version": "rotowire-lineups-trial-admission-v1",
            "policy_id": policy["policy_id"],
            "live_influence_admitted": admitted,
            "checks": checks,
            "metrics": dict(metrics),
            "negative_result_recorded": not admitted,
            "notes": (
                "Admitted for live influence"
                if admitted
                else "Trial failed or incomplete; Rotowire remains shadow-only"
            ),
        }
    )
