from datetime import datetime, timezone

import pytest

from bot import sessions


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def test_overlap_in_winter_and_summer():
    assert {"London", "New York"} <= set(sessions.active_sessions(utc(2026, 1, 15, 14, 0)))
    assert {"London", "New York"} <= set(sessions.active_sessions(utc(2026, 7, 15, 14, 0)))


def test_daylight_saving_shifts_london_open():
    # London opens 08:00 local: 08:00 UTC in winter, 07:00 UTC in summer.
    assert "London" not in sessions.active_sessions(utc(2026, 1, 15, 7, 30))
    assert "London" in sessions.active_sessions(utc(2026, 7, 15, 7, 30))


def test_asian_hours_early_utc():
    active = sessions.active_sessions(utc(2026, 1, 15, 3, 0))
    assert "Tokyo" in active
    assert "London" not in active and "New York" not in active


def test_weekend_break():
    assert sessions.is_market_break(utc(2026, 1, 17, 12, 0))   # Saturday
    assert sessions.is_market_break(utc(2026, 1, 16, 23, 0))   # Friday night
    assert not sessions.is_market_break(utc(2026, 1, 18, 23, 0))  # Sunday reopening
    assert not sessions.is_market_break(utc(2026, 1, 15, 12, 0))


def test_naive_datetime_rejected():
    with pytest.raises(ValueError):
        sessions.active_sessions(datetime(2026, 1, 15, 12, 0))


def test_hours_shown_in_kolkata():
    london = next(s for s in sessions.SESSIONS if s.name == "London")
    assert sessions.hours_in_zone(london, utc(2026, 1, 15, 12, 0), "Asia/Kolkata") == "13:30-22:30"


def test_describe_runs():
    text = sessions.describe_sessions(utc(2026, 1, 15, 14, 0), "Asia/Kolkata")
    assert "overlap" in text and "London" in text
