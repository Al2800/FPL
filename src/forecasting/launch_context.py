"""Validate and apply prospective 2026/27 cold-start context."""

from __future__ import annotations

from copy import deepcopy
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


class LaunchContextError(ValueError):
    """Raised when launch context is ambiguous, inconsistent, or temporally late."""


FATIGUE_TIERS = ("none", "moderate", "high", "extreme")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def artifact_hash(value: Mapping[str, Any]) -> str:
    payload = {key: item for key, item in value.items() if key != "content_sha256"}
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise LaunchContextError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise LaunchContextError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _integer_set(values: Any, field: str) -> set[int]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise LaunchContextError(f"{field} must be a list")
    parsed = [int(value) for value in values]
    if len(parsed) != len(set(parsed)):
        raise LaunchContextError(f"{field} contains duplicate identities")
    return set(parsed)


def load_launch_context(path: Path) -> dict[str, Any]:
    """Load a self-hashed launch-context artifact."""

    value = json.loads(path.read_text(encoding="utf-8"))
    expected = str(value.get("content_sha256", ""))
    if len(expected) != 64 or artifact_hash(value) != expected:
        raise LaunchContextError("Launch-context content hash mismatch")
    return value


def load_world_cup_priors(path: Path) -> list[dict[str, str]]:
    """Load the World Cup ledger without performing permissive name joins."""

    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def world_cup_csv_hash(rows: Sequence[Mapping[str, Any]]) -> str:
    """Canonical CSV hash helper for synthetic and generated ledgers."""

    if not rows:
        return hashlib.sha256(b"").hexdigest()
    fields = list(rows[0])
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return hashlib.sha256(output.getvalue().encode("utf-8")).hexdigest()


def _validated_context(
    bootstrap: Mapping[str, Any],
    context: Mapping[str, Any],
    *,
    cutoff: datetime,
) -> tuple[set[int], set[int], set[int], dict[str, float], dict[str, Any]]:
    source = context.get("source_bindings", {}).get("official_bootstrap", {})
    _, observed = _timestamp(source.get("observed_at"), "official_bootstrap.observed_at")
    if observed >= cutoff:
        raise LaunchContextError(
            "Official launch context must be observed strictly before decision cutoff"
        )
    if len(str(source.get("sha256", ""))) != 64:
        raise LaunchContextError("Official bootstrap binding has no valid SHA-256")

    raw_players = list(bootstrap.get("elements", []))
    player_codes = [int(row["code"]) for row in raw_players]
    if len(player_codes) != len(set(player_codes)):
        raise LaunchContextError("Official bootstrap contains duplicate player codes")
    official_teams = {int(row["id"]): row for row in bootstrap.get("teams", [])}
    team_ids = set(official_teams)

    promoted_rows = list(context.get("promoted_teams", []))
    promoted = {int(row["team_id"]) for row in promoted_rows}
    if len(promoted) != len(promoted_rows):
        raise LaunchContextError("Promoted-team identities are duplicated")
    if not promoted or not promoted <= team_ids:
        raise LaunchContextError("Promoted-team identities are empty or unknown")
    for row in promoted_rows:
        official = official_teams[int(row["team_id"])]
        if int(row.get("team_code", -1)) != int(official.get("code", -2)):
            raise LaunchContextError("Promoted-team stable code does not match official team")
        if str(row.get("name", "")) != str(official.get("name", "")):
            raise LaunchContextError("Promoted-team name does not match official team")

    new = _integer_set(context.get("new_player_codes", []), "new_player_codes")
    transferred = _integer_set(
        context.get("transferred_player_codes", []), "transferred_player_codes"
    )
    known_codes = set(player_codes)
    if not new or not new <= known_codes:
        raise LaunchContextError("New-player identities are empty or unknown")
    if not transferred or not transferred <= known_codes:
        raise LaunchContextError("Transferred-player identities are empty or unknown")

    policy = context.get("classification_policy", {})
    precedence = list(policy.get("precedence", []))
    expected_precedence = [
        "promoted_team",
        "new_to_fpl",
        "transferred_player",
        "established",
    ]
    if precedence != expected_precedence:
        raise LaunchContextError("Cold-start precedence is not the registered policy")
    risk = {
        str(key): float(value)
        for key, value in context.get("cold_start_risk", {}).items()
    }
    if set(risk) != set(expected_precedence):
        raise LaunchContextError("Cold-start risk is incomplete")
    if any(value < 0.0 or value > 1.0 for value in risk.values()):
        raise LaunchContextError("Cold-start risk must be between zero and one")

    return promoted, new, transferred, risk, deepcopy(dict(policy))


def apply_launch_context(
    *,
    bootstrap: Mapping[str, Any],
    context: Mapping[str, Any],
    world_cup_rows: Sequence[Mapping[str, Any]],
    official_bootstrap_source_sha256: str,
    world_cup_source_sha256: str,
    decision_cutoff: str,
    gameweek: int,
) -> dict[str, Any]:
    """Classify the official universe and attach cutoff-safe World Cup priors."""

    cutoff_text, cutoff = _timestamp(decision_cutoff, "decision_cutoff")
    if gameweek < 1:
        raise LaunchContextError("gameweek must be positive")
    promoted, new, transferred, class_risk, policy = _validated_context(
        bootstrap, context, cutoff=cutoff
    )
    bindings = context.get("source_bindings", {})
    if official_bootstrap_source_sha256 != str(
        bindings.get("official_bootstrap", {}).get("sha256", "")
    ):
        raise LaunchContextError("Official bootstrap source hash mismatch")
    if world_cup_source_sha256 != str(
        bindings.get("world_cup_priors", {}).get("sha256", "")
    ):
        raise LaunchContextError("World Cup prior source hash mismatch")

    world_policy = context.get("world_cup_policy", {})
    tier_scores = {
        str(key): float(value)
        for key, value in world_policy.get("fatigue_tier_score", {}).items()
    }
    if set(tier_scores) != set(FATIGUE_TIERS):
        raise LaunchContextError("World Cup fatigue tiers are incomplete")
    fades = [float(value) for value in world_policy.get("gameweek_fade", [])]
    if not fades or any(value < 0.0 or value > 1.0 for value in fades):
        raise LaunchContextError("World Cup gameweek fade is invalid")
    fade = fades[gameweek - 1] if gameweek <= len(fades) else 0.0

    official_codes = {int(row["code"]) for row in bootstrap.get("elements", [])}
    world_by_code: dict[int, dict[str, Any]] = {}
    seen_world_codes: set[int] = set()
    degraded: list[dict[str, Any]] = []
    coverage = {
        "ledger_rows": len(world_cup_rows),
        "matched_rows": 0,
        "blank_code_rows": 0,
        "non_current_code_rows": 0,
        "late_rows": 0,
        "missing_return_to_training_rows": 0,
    }
    for index, raw in enumerate(world_cup_rows, start=2):
        row = dict(raw)
        code_text = str(row.get("fpl_code", "")).strip()
        if not code_text:
            coverage["blank_code_rows"] += 1
            degraded.append(
                {
                    "feature": "world_cup_prior",
                    "row": index,
                    "reason": "blank_stable_fpl_code_no_name_join",
                }
            )
            continue
        try:
            code = int(code_text)
        except ValueError as exc:
            raise LaunchContextError(
                f"World Cup stable code is not an integer at row {index}: {code_text}"
            ) from exc
        if code in seen_world_codes:
            raise LaunchContextError(f"Duplicate World Cup stable code: {code}")
        seen_world_codes.add(code)
        if code not in official_codes:
            coverage["non_current_code_rows"] += 1
            degraded.append(
                {
                    "feature": "world_cup_prior",
                    "fpl_code": code,
                    "reason": "stable_code_not_in_current_official_universe",
                }
            )
            continue
        observed_text, observed = _timestamp(
            row.get("observed_at"), f"world_cup_rows[{index}].observed_at"
        )
        if observed >= cutoff:
            coverage["late_rows"] += 1
            degraded.append(
                {
                    "feature": "world_cup_prior",
                    "fpl_code": code,
                    "reason": "observed_at_or_after_decision_cutoff",
                }
            )
            continue
        tier = str(row.get("fatigue_prior", ""))
        if tier not in tier_scores:
            raise LaunchContextError(
                f"Unknown World Cup fatigue tier for stable code {code}: {tier}"
            )
        return_date = str(row.get("return_to_training_date", "")).strip() or None
        if return_date is None:
            coverage["missing_return_to_training_rows"] += 1
        world_by_code[code] = {
            "status": "matched",
            "fatigue_tier": tier,
            "fatigue_score": tier_scores[tier],
            "gameweek_fade": fade,
            "effective_fatigue": round(tier_scores[tier] * fade, 6),
            "wc_minutes": (
                int(row["wc_minutes"]) if str(row.get("wc_minutes", "")).strip() else None
            ),
            "elimination_date": str(row.get("elimination_date", "")) or None,
            "return_to_training_date": return_date,
            "observed_at": observed_text,
        }
        coverage["matched_rows"] += 1

    players: list[dict[str, Any]] = []
    class_counts = {
        "promoted_team": 0,
        "new_to_fpl": 0,
        "transferred_player": 0,
        "established": 0,
    }
    for row in bootstrap.get("elements", []):
        code = int(row["code"])
        team_id = int(row["team"])
        cold_class = (
            "promoted_team"
            if team_id in promoted
            else "new_to_fpl"
            if code in new
            else "transferred_player"
            if code in transferred
            else "established"
        )
        class_counts[cold_class] += 1
        players.append(
            {
                "player_id": int(row["id"]),
                "fpl_code": code,
                "team_id": team_id,
                "cold_start_class": cold_class,
                "cold_start_risk": class_risk[cold_class],
                "is_new_to_fpl": code in new,
                "changed_club": code in transferred,
                "world_cup": world_by_code.get(
                    code,
                    {
                        "status": "not_in_admitted_ledger",
                        "fatigue_tier": None,
                        "fatigue_score": 0.0,
                        "gameweek_fade": fade,
                        "effective_fatigue": 0.0,
                    },
                ),
            }
        )

    expected = {
        str(key): int(value)
        for key, value in policy.get("expected_class_counts", {}).items()
    }
    if expected and class_counts != expected:
        raise LaunchContextError(
            f"Official universe no longer matches frozen class counts: {class_counts}"
        )
    if sum(class_counts.values()) != len(players):
        raise LaunchContextError("Not every official player received exactly one class")

    result: dict[str, Any] = {
        "schema_version": "1.0",
        "season": str(context.get("season", "")),
        "decision_cutoff": cutoff_text,
        "gameweek": gameweek,
        "classification_policy": policy,
        "class_counts": class_counts,
        "world_cup_coverage": coverage,
        "degraded_features": degraded,
        "players": sorted(players, key=lambda item: item["player_id"]),
        "source_bindings": deepcopy(dict(context.get("source_bindings", {}))),
    }
    result["content_sha256"] = artifact_hash(result)
    return result
