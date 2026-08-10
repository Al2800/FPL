"""Adapters that turn private Understat / ClubElo captures into team priors.

Understat feeds prior-season match xG into ``build_attack_defence_prior``.
ClubElo optionally supplies per-fixture expected-result scores.  Both are
optional: callers fall back to the official FDR baseline when captures are
absent.  Captures stay gitignored; only hashes and limitation tags enter the
decision packet.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.forecasting.team_attack_defence import (
    AttackDefenceParameters,
    TeamContextError,
    build_attack_defence_prior,
)
from src.forecasting.team_prior import EloParameters, _probabilities


class UnderstatTeamContextError(ValueError):
    """Raised when an Understat / ClubElo capture cannot be wired safely."""


# Understat EPL titles (season 2025 capture) → FPL bootstrap ``teams[].name``.
UNDERSTAT_TITLE_TO_FPL_NAME: dict[str, str] = {
    "Arsenal": "Arsenal",
    "Aston Villa": "Aston Villa",
    "Bournemouth": "Bournemouth",
    "Brentford": "Brentford",
    "Brighton": "Brighton",
    "Chelsea": "Chelsea",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Leeds": "Leeds",
    "Liverpool": "Liverpool",
    "Manchester City": "Man City",
    "Manchester United": "Man Utd",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Sunderland": "Sunderland",
    "Tottenham": "Spurs",
}

# ClubElo ``Club`` field (ENG Level 1) → FPL bootstrap ``teams[].name``.
CLUBELO_NAME_TO_FPL_NAME: dict[str, str] = {
    "Arsenal": "Arsenal",
    "Aston Villa": "Aston Villa",
    "Bournemouth": "Bournemouth",
    "Brentford": "Brentford",
    "Brighton": "Brighton",
    "Chelsea": "Chelsea",
    "Coventry": "Coventry City",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton",
    "Forest": "Nott'm Forest",
    "Fulham": "Fulham",
    "Hull": "Hull City",
    "Ipswich": "Ipswich Town",
    "Leeds": "Leeds",
    "Liverpool": "Liverpool",
    "Man City": "Man City",
    "Man United": "Man Utd",
    "Newcastle": "Newcastle",
    "Sunderland": "Sunderland",
    "Tottenham": "Spurs",
}


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    )


def _timestamp(value: Any, field: str, *, assume_utc_if_naive: bool = False) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise UnderstatTeamContextError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        if not assume_utc_if_naive:
            raise UnderstatTeamContextError(f"{field} must include a timezone")
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _as_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def fpl_team_identities(bootstrap: Mapping[str, Any]) -> list[dict[str, str]]:
    """Return ``{team_name, club_id}`` rows from an official bootstrap."""

    teams = bootstrap.get("teams")
    if not isinstance(teams, list) or not teams:
        raise UnderstatTeamContextError("bootstrap teams must be a non-empty list")
    rows: list[dict[str, str]] = []
    seen_names: set[str] = set()
    for raw in teams:
        if not isinstance(raw, Mapping):
            raise UnderstatTeamContextError("bootstrap team must be an object")
        try:
            name = str(raw["name"])
            club_id = str(int(raw["id"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise UnderstatTeamContextError(
                "bootstrap team requires integer id and name"
            ) from exc
        if name in seen_names:
            raise UnderstatTeamContextError(f"duplicate bootstrap team name: {name}")
        seen_names.add(name)
        rows.append({"team_name": name, "club_id": club_id})
    return rows


def understat_match_observations(
    capture: Mapping[str, Any],
    *,
    cutoff: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Extract cutoff-safe match xG observations mapped onto FPL team names.

    Matches involving clubs that do not map into the current FPL season
    (relegated sides in a prior-season capture) are skipped, not invented.
    """

    cutoff_time = _timestamp(cutoff, "cutoff")
    matches = capture.get("matches")
    if not isinstance(matches, list):
        raise UnderstatTeamContextError("understat capture matches must be a list")

    observations: list[dict[str, Any]] = []
    skipped_unmapped = 0
    skipped_not_result = 0
    skipped_after_cutoff = 0
    for raw in matches:
        if not isinstance(raw, Mapping):
            raise UnderstatTeamContextError("understat match must be an object")
        if not raw.get("isResult"):
            skipped_not_result += 1
            continue
        home_raw = raw.get("h")
        away_raw = raw.get("a")
        xg_raw = raw.get("xG")
        if not isinstance(home_raw, Mapping) or not isinstance(away_raw, Mapping):
            raise UnderstatTeamContextError("understat match sides are malformed")
        if not isinstance(xg_raw, Mapping):
            raise UnderstatTeamContextError("understat match xG is malformed")
        home_fpl = UNDERSTAT_TITLE_TO_FPL_NAME.get(str(home_raw.get("title", "")))
        away_fpl = UNDERSTAT_TITLE_TO_FPL_NAME.get(str(away_raw.get("title", "")))
        if home_fpl is None or away_fpl is None:
            skipped_unmapped += 1
            continue
        # Understat datetimes are naive wall-clock kickoffs; treat as UTC for
        # cutoff comparison only (completed 2025/26 matches precede GW1 by months).
        kickoff = _timestamp(
            raw.get("datetime"),
            "understat.match.datetime",
            assume_utc_if_naive=True,
        )
        if kickoff >= cutoff_time:
            skipped_after_cutoff += 1
            continue
        try:
            home_xg = float(xg_raw["h"])
            away_xg = float(xg_raw["a"])
        except (KeyError, TypeError, ValueError) as exc:
            raise UnderstatTeamContextError(
                "understat match xG values must be numeric"
            ) from exc
        observations.append(
            {
                "kickoff_time": _as_z(kickoff),
                "home_team": home_fpl,
                "away_team": away_fpl,
                "home_xg": home_xg,
                "away_xg": away_xg,
            }
        )

    meta = {
        "observation_count": len(observations),
        "skipped_unmapped_sides": skipped_unmapped,
        "skipped_not_result": skipped_not_result,
        "skipped_at_or_after_cutoff": skipped_after_cutoff,
        "capture_source_id": str(capture.get("source_id", "understat")),
        "capture_season": str(capture.get("season", "")),
        "capture_sha256": _sha256_json(
            {
                "season": capture.get("season"),
                "observed_at": capture.get("observed_at"),
                "available_at": capture.get("available_at"),
                "counts": capture.get("counts"),
                "matches": capture.get("matches"),
            }
        ),
    }
    if not observations:
        raise UnderstatTeamContextError(
            "understat capture produced no cutoff-safe mapped observations"
        )
    return observations, meta


def load_clubelo_ratings_csv(
    path: Path,
    *,
    country: str = "ENG",
    level: str = "1",
) -> tuple[dict[str, float], str]:
    """Load ClubElo rankings mapped onto FPL team names."""

    text = path.read_text(encoding="utf-8")
    body_hash = _sha256_bytes(text.encode("utf-8"))
    lines = text.splitlines()
    if not lines:
        raise UnderstatTeamContextError("clubelo ranking CSV is empty")
    header = [cell.strip() for cell in lines[0].split(",")]
    required = {"Club", "Country", "Level", "Elo"}
    if not required.issubset(set(header)):
        raise UnderstatTeamContextError(
            "clubelo ranking CSV missing Club/Country/Level/Elo columns"
        )
    index = {name: header.index(name) for name in header}
    ratings: dict[str, float] = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        cells = line.split(",")
        if len(cells) < len(header):
            continue
        if cells[index["Country"]].strip() != country:
            continue
        if cells[index["Level"]].strip() != level:
            continue
        club = cells[index["Club"]].strip()
        fpl_name = CLUBELO_NAME_TO_FPL_NAME.get(club)
        if fpl_name is None:
            continue
        try:
            ratings[fpl_name] = float(cells[index["Elo"]].strip())
        except ValueError as exc:
            raise UnderstatTeamContextError(
                f"clubelo Elo for {club} is not numeric"
            ) from exc
    if not ratings:
        raise UnderstatTeamContextError("clubelo CSV produced no ENG Level-1 mappings")
    return ratings, body_hash


def clubelo_expected_scores(
    *,
    fixtures: Sequence[Mapping[str, Any]],
    team_name_by_club_id: Mapping[str, str],
    ratings_by_fpl_name: Mapping[str, float],
    elo_params: EloParameters,
) -> tuple[dict[tuple[int, str], float], list[str]]:
    """Derive per-fixture expected-result scores from ClubElo ratings."""

    scores: dict[tuple[int, str], float] = {}
    missing: list[str] = []
    for fixture in fixtures:
        fixture_id = int(fixture["fixture_id"])
        home_club = str(fixture["home_club_id"])
        away_club = str(fixture["away_club_id"])
        home_name = team_name_by_club_id[home_club]
        away_name = team_name_by_club_id[away_club]
        home_rating = ratings_by_fpl_name.get(home_name)
        away_rating = ratings_by_fpl_name.get(away_name)
        if home_rating is None:
            missing.append(home_name)
            continue
        if away_rating is None:
            missing.append(away_name)
            continue
        p_home, p_draw, p_away = _probabilities(home_rating, away_rating, elo_params)
        scores[(fixture_id, home_club)] = p_home + 0.5 * p_draw
        scores[(fixture_id, away_club)] = p_away + 0.5 * p_draw
    return scores, sorted(set(missing))


def fixture_specs_from_official(
    fixtures: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Map official FPL fixture rows to attack/defence fixture specs."""

    specs: list[dict[str, Any]] = []
    for raw in fixtures:
        if not isinstance(raw, Mapping):
            raise UnderstatTeamContextError("fixture must be an object")
        if raw.get("event") is None:
            continue
        try:
            specs.append(
                {
                    "fixture_id": int(raw["id"]),
                    "home_club_id": str(int(raw["team_h"])),
                    "away_club_id": str(int(raw["team_a"])),
                }
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise UnderstatTeamContextError(
                "fixture requires id, team_h and team_a"
            ) from exc
    if not specs:
        raise UnderstatTeamContextError("no fixtures with assigned events")
    return specs


def discover_latest_understat_capture(root: Path) -> Path | None:
    """Return the newest ``understat-league.json`` under a capture root."""

    if not root.is_dir():
        return None
    candidates = sorted(root.rglob("understat-league.json"))
    return candidates[-1] if candidates else None


def discover_latest_clubelo_csv(root: Path) -> Path | None:
    """Return the newest ``clubelo-ranking.csv`` under a capture root."""

    if not root.is_dir():
        return None
    candidates = sorted(root.rglob("clubelo-ranking.csv"))
    return candidates[-1] if candidates else None


def build_understat_attack_defence_team_prior(
    *,
    bootstrap: Mapping[str, Any],
    fixtures: Sequence[Mapping[str, Any]],
    understat_capture: Mapping[str, Any],
    observed_at: str,
    decision_cutoff: str,
    season: str,
    promoted_team_names: Iterable[str] = (),
    clubelo_ratings_by_fpl_name: Mapping[str, float] | None = None,
    clubelo_body_sha256: str | None = None,
    odds_snapshots: Mapping[int, Mapping[str, Any]] | None = None,
    params: AttackDefenceParameters | None = None,
    elo_params: EloParameters | None = None,
) -> dict[str, Any]:
    """Build a separate attack/defence team prior from Understat (+ optional ClubElo/odds)."""

    identities = fpl_team_identities(bootstrap)
    name_by_club = {row["club_id"]: row["team_name"] for row in identities}
    observations, observation_meta = understat_match_observations(
        understat_capture,
        cutoff=observed_at,
    )
    specs = fixture_specs_from_official(fixtures)
    elo_scores: dict[tuple[int, str], float] | None = None
    elo_missing: list[str] = []
    if clubelo_ratings_by_fpl_name is not None:
        elo_scores, elo_missing = clubelo_expected_scores(
            fixtures=specs,
            team_name_by_club_id=name_by_club,
            ratings_by_fpl_name=clubelo_ratings_by_fpl_name,
            elo_params=elo_params
            or EloParameters(
                k=40.0,
                home_advantage=80.0,
                draw_factor=0.6,
                promoted_rating=1450.0,
                season_regression=1.0,
                fixture_scale=0.25,
            ),
        )
        if not elo_scores:
            elo_scores = None

    try:
        prior = build_attack_defence_prior(
            season=season,
            # Decision cutoff governs odds eligibility so a T-24h snapshot can
            # enter a packet whose official bootstrap observation is earlier.
            cutoff=decision_cutoff,
            team_identities=identities,
            fixtures=specs,
            observations=observations,
            promoted_teams=set(promoted_team_names),
            elo_expected_scores=elo_scores,
            odds_snapshots=odds_snapshots,
            params=params or AttackDefenceParameters(),
            lineage={
                "source_id": "understat",
                "client": str(understat_capture.get("client", "")),
                "capture_season": observation_meta["capture_season"],
                "capture_sha256": observation_meta["capture_sha256"],
                "observation_count": observation_meta["observation_count"],
                "skipped_unmapped_sides": observation_meta["skipped_unmapped_sides"],
                "observed_at": observed_at,
                "decision_cutoff": decision_cutoff,
                "clubelo_body_sha256": clubelo_body_sha256,
                "clubelo_missing_teams": elo_missing,
                "odds_fixture_count": (
                    len(odds_snapshots) if odds_snapshots is not None else 0
                ),
                "outcome_data_used": False,
                "prior_season_xg_only": True,
            },
        )
    except TeamContextError as exc:
        raise UnderstatTeamContextError(str(exc)) from exc
    return prior
