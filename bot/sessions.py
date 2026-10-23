"""Forex / gold trading sessions.

Session hours are defined in each city's local time, so daylight saving
changes (London, New York, Sydney) are handled automatically.
All functions take a timezone-aware datetime. Inside the code we think in
UTC and only convert to your own time zone when showing a message.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Session:
    name: str
    tz: str
    start: time
    end: time


SESSIONS = (
    Session("Sydney", "Australia/Sydney", time(7, 0), time(16, 0)),
    Session("Tokyo", "Asia/Tokyo", time(9, 0), time(18, 0)),
    Session("London", "Europe/London", time(8, 0), time(17, 0)),
    Session("New York", "America/New_York", time(8, 0), time(17, 0)),
)


def _require_aware(moment: datetime) -> None:
    if moment.tzinfo is None:
        raise ValueError("Use a timezone-aware datetime (for example datetime.now(timezone.utc)).")


def is_open(session: Session, now_utc: datetime) -> bool:
    """True if the session is open at this moment (Mon-Fri in that city)."""
    _require_aware(now_utc)
    local = now_utc.astimezone(ZoneInfo(session.tz))
    if local.weekday() >= 5:  # Saturday or Sunday in that city
        return False
    return session.start <= local.time() < session.end


def active_sessions(now_utc: datetime) -> list[str]:
    return [s.name for s in SESSIONS if is_open(s, now_utc)]


def is_market_break(now_utc: datetime) -> bool:
    """Approximate weekend break for gold: Friday 22:00 UTC to Sunday 22:00 UTC.

    Brokers differ by an hour or so, so treat this as a guide, not a rule.
    """
    _require_aware(now_utc)
    utc = now_utc.astimezone(ZoneInfo("UTC"))
    wd, hour = utc.weekday(), utc.hour  # Monday = 0
    return (wd == 4 and hour >= 22) or wd == 5 or (wd == 6 and hour < 22)


def hours_in_zone(session: Session, now_utc: datetime, display_tz: str) -> str:
    """Session opening hours shown in your own time zone, e.g. '13:30-22:30'."""
    _require_aware(now_utc)
    tz = ZoneInfo(session.tz)
    out = ZoneInfo(display_tz)
    today = now_utc.astimezone(tz).date()
    start = datetime.combine(today, session.start, tzinfo=tz).astimezone(out)
    end = datetime.combine(today, session.end, tzinfo=tz).astimezone(out)
    return f"{start:%H:%M}-{end:%H:%M}"


def describe_sessions(now_utc: datetime, display_tz: str = "Asia/Kolkata") -> str:
    _require_aware(now_utc)
    local_now = now_utc.astimezone(ZoneInfo(display_tz))
    lines = [f"Time now: {local_now:%a %d %b, %H:%M} ({display_tz})"]

    if is_market_break(now_utc):
        lines.append("Gold market: weekend break (roughly Fri 22:00 to Sun 22:00 UTC).")
    else:
        active = active_sessions(now_utc)
        if active:
            lines.append("Open sessions: " + ", ".join(active))
        else:
            lines.append("Open sessions: none (a quiet gap between sessions)")
        if "London" in active and "New York" in active:
            lines.append("London + New York overlap: usually the busiest, fastest window for gold.")

    lines.append("")
    lines.append(f"Session hours in your time ({display_tz}):")
    for s in SESSIONS:
        lines.append(f"  {s.name}: {hours_in_zone(s, now_utc, display_tz)}")
    return "\n".join(lines)
