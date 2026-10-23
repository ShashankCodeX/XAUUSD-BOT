from datetime import datetime, timedelta, timezone

from bot import news
from bot.journal import Journal

SAMPLE = [
    {"title": "Non-Farm Employment Change", "country": "USD", "impact": "High",
     "date": "2026-11-06T08:30:00-05:00", "forecast": "150K", "previous": "119K"},
    {"title": "Retail Sales", "country": "USD", "impact": "Medium", "date": "2026-11-06T09:00:00-05:00"},
    {"title": "BoE Rate", "country": "GBP", "impact": "High", "date": "2026-11-06T12:00:00+00:00"},
    {"title": "Broken row"},
]


def test_parse_skips_broken_rows_and_converts_to_utc():
    events = news.parse_events(SAMPLE)
    assert len(events) == 3
    nfp = next(e for e in events if e.title.startswith("Non-Farm"))
    assert nfp.time_utc == datetime(2026, 11, 6, 13, 30, tzinfo=timezone.utc)


def test_only_high_impact_usd_counts():
    assert [e.title for e in news.high_impact_usd(news.parse_events(SAMPLE))] == ["Non-Farm Employment Change"]


def test_news_guard_window():
    events = news.parse_events(SAMPLE)
    nfp_time = datetime(2026, 11, 6, 13, 30, tzinfo=timezone.utc)
    assert news.news_guard(events, nfp_time - timedelta(minutes=10)) is not None
    assert news.news_guard(events, nfp_time + timedelta(minutes=10)) is not None
    assert news.news_guard(events, nfp_time - timedelta(minutes=30)) is None


def test_upcoming_window():
    events = news.parse_events(SAMPLE)
    now = datetime(2026, 11, 6, 6, 0, tzinfo=timezone.utc)
    assert len(news.upcoming(events, now)) == 1


def test_parse_handles_garbage():
    assert news.parse_events({"not": "a list"}) == []


def test_journal_roundtrip(tmp_path):
    journal = Journal(tmp_path / "test.db")
    trade_id = journal.add("buy", 2650, 2647, 2656, 2.0, "test")
    assert journal.stats()["closed"] == 0
    assert journal.set_result(trade_id, 2.0)
    assert not journal.set_result(999, 1.0)
    journal.add("sell", 2650, 2653, 2644, 2.0)
    journal.set_result(2, -1.0)
    stats = journal.stats()
    assert stats["closed"] == 2 and stats["total_r"] == 1.0 and stats["wins"] == 1
    assert journal.recent(1)[0]["id"] == 2
