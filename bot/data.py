"""Free gold price data via Yahoo Finance (through the yfinance library).

GC=F is COMEX gold FUTURES. It is close to spot XAUUSD but not identical
(the gap is called the basis), and the free feed is delayed and unofficial.
Treat it as a guide, and use your broker's price to actually trade.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import yfinance as yf

SYMBOL = "GC=F"


class DataUnavailable(Exception):
    """No usable price came back from the data provider."""


@dataclass(frozen=True)
class Quote:
    symbol: str
    price: float
    time_utc: datetime

    def age_minutes(self, now_utc: datetime) -> float:
        return (now_utc - self.time_utc).total_seconds() / 60


def get_quote() -> Quote:
    """Latest 5-minute candle close. This blocks, so call it with asyncio.to_thread."""
    ticker = yf.Ticker(SYMBOL)
    candles = ticker.history(period="1d", interval="5m")
    if candles.empty:
        candles = ticker.history(period="5d", interval="5m")
    if candles.empty:
        raise DataUnavailable("Yahoo returned no candles for " + SYMBOL)

    last_time = candles.index[-1].to_pydatetime().astimezone(timezone.utc)
    last_price = float(candles["Close"].iloc[-1])
    return Quote(symbol=SYMBOL, price=last_price, time_utc=last_time)
