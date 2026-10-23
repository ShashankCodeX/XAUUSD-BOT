"""Position sizing and trade-plan maths for gold (XAUUSD).

Assumption: 1 standard lot = 100 troy ounces (true for most brokers, but
check yours). A $1 move in gold on 1 lot = $100.
Decimal is used so results like 0.29 lots are exact, not 0.28999999.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal


class RiskTooSmall(ValueError):
    """The risk amount is too small even for the smallest lot size."""


@dataclass(frozen=True)
class LotSize:
    lots: float
    ounces: float
    actual_risk: float
    risk_per_lot: float


@dataclass(frozen=True)
class Plan:
    side: str  # "buy" or "sell"
    risk_distance: float
    reward_distance: float
    rr: float


def lot_size(risk_usd: float, stop_usd: float, oz_per_lot: float = 100, min_lot: float = 0.01) -> LotSize:
    """Lots you can trade so that hitting your stop loses about `risk_usd`.

    stop_usd is the price distance between entry and stop in dollars
    (entry 2650.00, stop 2647.00 -> 3.00). Lots are rounded DOWN so you
    never risk more than you asked for.
    """
    if risk_usd <= 0 or stop_usd <= 0 or oz_per_lot <= 0:
        raise ValueError("Risk, stop distance and ounces per lot must all be above zero.")

    risk = Decimal(str(risk_usd))
    per_lot = Decimal(str(stop_usd)) * Decimal(str(oz_per_lot))
    lots = (risk / per_lot).quantize(Decimal("0.01"), rounding=ROUND_DOWN)

    if lots < Decimal(str(min_lot)):
        minimum_risk = Decimal(str(min_lot)) * per_lot
        raise RiskTooSmall(
            f"Too small: the minimum {min_lot} lot would risk ${minimum_risk:.2f} "
            f"with that stop. Raise your risk or tighten the stop."
        )

    return LotSize(
        lots=float(lots),
        ounces=float(lots * Decimal(str(oz_per_lot))),
        actual_risk=float(lots * per_lot),
        risk_per_lot=float(per_lot),
    )


def spread_share(spread: float, target_distance: float) -> float:
    """What fraction of your target the spread eats (0.10 = 10%)."""
    if spread < 0 or target_distance <= 0:
        raise ValueError("Spread must be 0 or more, and the target distance above 0.")
    return spread / target_distance


def plan_from_prices(entry: float, stop: float, target: float) -> Plan:
    """Work out buy/sell and reward:risk from three prices."""
    if target > entry > stop:
        return Plan("buy", entry - stop, target - entry, (target - entry) / (entry - stop))
    if target < entry < stop:
        return Plan("sell", stop - entry, entry - target, (entry - target) / (stop - entry))
    raise ValueError(
        "These prices don't make a valid trade. A buy needs stop < entry < target; "
        "a sell needs target < entry < stop."
    )
