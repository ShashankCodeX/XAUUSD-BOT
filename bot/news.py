"""High-impact USD news, the main thing that spikes gold.

Source: a free public weekly calendar feed (Forex Factory-style data,
published by Fair Economy). It is unofficial and can change or disappear,
so every function fails safely and the bot tells you to check manually.
Do not scrape the Forex Factory website itself.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import requests

FEED_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
CACHE_SECONDS = 30 * 60  # be polite to the free feed

_cache: dict = {"at": 0.0, "events": None}


class NewsUnavailable(Exception):
    """The calendar could not be loaded."""


@dataclass(frozen=True)
class Event:
    title: str
    currency: str
    impact: str
    time_utc: datetime
    forecast: str = ""
    previous: str = ""


def parse_events(raw) -> list[Event]:
    events: list[Event] = []
    if not isinstance(raw, list):
        return events
    for item in raw:
        try:
            moment = datetime.fromisoformat(str(item["date"]))
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=timezone.utc)
            events.append(
                Event(
                    title=str(item["title"]),
                    currency=str(item.get("country", "")).upper(),
                    impact=str(item.get("impact", "")).title(),
                    time_utc=moment.astimezone(timezone.utc),
                    forecast=str(item.get("forecast") or ""),
                    previous=str(item.get("previous") or ""),
                )
            )
        except (KeyError, ValueError, TypeError, AttributeError):
            continue  # skip a broken row instead of crashing
    return sorted(events, key=lambda e: e.time_utc)


def fetch_events(force: bool = False) -> list[Event]:
    """Load this week's events (cached). Blocks, so use asyncio.to_thread."""
    cached = _cache["events"]
    now = time.monotonic()
    if cached is not None and not force and now - _cache["at"] < CACHE_SECONDS:
        return cached
    try:
        response = requests.get(
            FEED_URL, timeout=10, headers={"User-Agent": "xauusd-bot (open source)"}
        )
        response.raise_for_status()
        events = parse_events(response.json())
        if not events:
            raise NewsUnavailable("The calendar feed returned no events.")
    except (requests.RequestException, ValueError) as exc:
        if cached is not None:
            return cached
        raise NewsUnavailable(str(exc)) from exc
    _cache["at"], _cache["events"] = now, events
    return events


def high_impact_usd(events: list[Event]) -> list[Event]:
    return [e for e in events if e.currency == "USD" and e.impact == "High"]


def upcoming(events: list[Event], now_utc: datetime, hours: int = 24, lookback_minutes: int = 60) -> list[Event]:
    start = now_utc - timedelta(minutes=lookback_minutes)
    end = now_utc + timedelta(hours=hours)
    return [e for e in high_impact_usd(events) if start <= e.time_utc <= end]


def news_guard(events: list[Event], now_utc: datetime, minutes: int = 15) -> Event | None:
    """Return the high-impact USD event within +/- `minutes` of now, if any."""
    window = timedelta(minutes=minutes)
    for event in high_impact_usd(events):
        if abs(event.time_utc - now_utc) <= window:
            return event
    return None
