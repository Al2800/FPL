"""Shared types for the Phase 1 optimiser."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SOLVER_VERSION = "wp07-safe-pool-v0.2"


@dataclass(frozen=True)
class TransferMove:
    player_out_id: str
    player_in_id: str

    def as_dict(self) -> dict[str, str]:
        return {"player_out_id": self.player_out_id, "player_in_id": self.player_in_id}


@dataclass
class SolverPlayer:
    player_id: str
    position: str
    club_id: str
    now_cost: float
    expected_points: float
    purchase_price: float | None = None
    web_name: str = ""
    status: str = "a"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SolverInput:
    """Canonical optimiser input — must round-trip through JSON unchanged in meaning."""

    season: str
    gameweek: int
    ruleset_id: str
    bank: float
    free_transfers: int
    squad_player_ids: list[str]
    players: list[dict[str, Any]]  # full market + ownership fields
    active_chip: str | None = None
    chips_available: list[str] = field(default_factory=list)
    horizon_gameweeks: int = 1
    discount_factors: list[float] = field(default_factory=lambda: [1.0])
    max_transfers: int = 3
    sell_pool_per_pos: int = 5
    buy_pool_per_pos: int = 8
    allow_hits: bool = True
    transfer_value_policy: str = "none"
    probability_extra_transfer_needed: float = 0.5
    future_transfer_discount: float = 0.9
    squad_contingency_policy: str = "none"
    appearance_calibration: dict[str, Any] | None = None
    search_candidate_budget: int | None = None
    search_deadline_ms: int | None = None
    ruleset_mismatch_policy: str = "fail_closed"
    availability_policy: str = "available_only"
    solver_version: str = SOLVER_VERSION

    def as_dict(self) -> dict[str, Any]:
        value = {
            "season": self.season,
            "gameweek": self.gameweek,
            "ruleset_id": self.ruleset_id,
            "bank": self.bank,
            "free_transfers": self.free_transfers,
            "squad_player_ids": list(self.squad_player_ids),
            "players": self.players,
            "active_chip": self.active_chip,
            "chips_available": list(self.chips_available),
            "horizon_gameweeks": self.horizon_gameweeks,
            "discount_factors": list(self.discount_factors),
            "max_transfers": self.max_transfers,
            "sell_pool_per_pos": self.sell_pool_per_pos,
            "buy_pool_per_pos": self.buy_pool_per_pos,
            "allow_hits": self.allow_hits,
            "ruleset_mismatch_policy": self.ruleset_mismatch_policy,
            "availability_policy": self.availability_policy,
            "solver_version": self.solver_version,
        }
        if self.transfer_value_policy != "none":
            value.update(
                {
                    "transfer_value_policy": self.transfer_value_policy,
                    "probability_extra_transfer_needed": (
                        self.probability_extra_transfer_needed
                    ),
                    "future_transfer_discount": self.future_transfer_discount,
                }
            )
        if self.squad_contingency_policy != "none":
            value.update(
                {
                    "squad_contingency_policy": self.squad_contingency_policy,
                    "appearance_calibration": self.appearance_calibration,
                }
            )
        if self.search_candidate_budget is not None:
            value["search_candidate_budget"] = self.search_candidate_budget
        if self.search_deadline_ms is not None:
            value["search_deadline_ms"] = self.search_deadline_ms
        return value

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SolverInput:
        return cls(
            season=str(data["season"]),
            gameweek=int(data["gameweek"]),
            ruleset_id=str(data["ruleset_id"]),
            bank=float(data["bank"]),
            free_transfers=int(data["free_transfers"]),
            squad_player_ids=[str(x) for x in data["squad_player_ids"]],
            players=list(data["players"]),
            active_chip=data.get("active_chip"),
            chips_available=[str(x) for x in data.get("chips_available", [])],
            horizon_gameweeks=int(data.get("horizon_gameweeks", 1)),
            discount_factors=[float(x) for x in data.get("discount_factors", [1.0])],
            max_transfers=int(data.get("max_transfers", 3)),
            sell_pool_per_pos=int(data.get("sell_pool_per_pos", 5)),
            buy_pool_per_pos=int(data.get("buy_pool_per_pos", 8)),
            allow_hits=bool(data.get("allow_hits", True)),
            transfer_value_policy=str(data.get("transfer_value_policy", "none")),
            probability_extra_transfer_needed=float(
                data.get("probability_extra_transfer_needed", 0.5)
            ),
            future_transfer_discount=float(
                data.get("future_transfer_discount", 0.9)
            ),
            squad_contingency_policy=str(
                data.get("squad_contingency_policy", "none")
            ),
            appearance_calibration=(
                dict(data["appearance_calibration"])
                if data.get("appearance_calibration") is not None
                else None
            ),
            search_candidate_budget=(
                int(data["search_candidate_budget"])
                if data.get("search_candidate_budget") is not None
                else None
            ),
            search_deadline_ms=(
                int(data["search_deadline_ms"])
                if data.get("search_deadline_ms") is not None
                else None
            ),
            ruleset_mismatch_policy=str(data.get("ruleset_mismatch_policy", "fail_closed")),
            availability_policy=str(data.get("availability_policy", "available_only")),
            solver_version=str(data.get("solver_version", SOLVER_VERSION)),
        )
