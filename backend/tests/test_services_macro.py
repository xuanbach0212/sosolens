"""Unit tests for backend/services/macro.py"""
import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock
from backend.services.macro import fetch_macro_events, fetch_macro_indicators


def _future_date(days: int) -> str:
    return (date.today() + timedelta(days=days)).strftime("%Y-%m-%d")


def _past_date(days: int) -> str:
    return (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")


@pytest.fixture
def client():
    c = AsyncMock()
    c.get_macro_events.return_value = {
        "data": [
            {"date": _future_date(6),  "events": ["CPI Release"], "time": "08:30"},
            {"date": _future_date(14), "events": ["FOMC Meeting"], "time": "14:00"},
            {"date": _past_date(2),    "events": ["Old Event"],    "time": "10:00"},
        ]
    }
    return c


async def test_fetch_macro_events_filters_past_events(client):
    events = await fetch_macro_events(client)
    for ev in events:
        assert ev["days_until"] >= 0


async def test_fetch_macro_events_days_until_calculated(client):
    events = await fetch_macro_events(client)
    # e["events"] is a list of strings — use any() for substring search
    cpi = next((e for e in events if any("CPI" in s for s in e["events"])), None)
    assert cpi is not None
    assert cpi["days_until"] == 6


async def test_fetch_macro_events_high_impact_keywords(client):
    events = await fetch_macro_events(client)
    cpi = next((e for e in events if any("CPI" in s for s in e["events"])), None)
    fomc = next((e for e in events if any("FOMC" in s for s in e["events"])), None)
    assert cpi is not None and cpi["high_impact"] is True
    assert fomc is not None and fomc["high_impact"] is True


async def test_fetch_macro_events_non_keyword_not_high_impact(client):
    client.get_macro_events.return_value = {
        "data": [{"date": _future_date(3), "events": ["Product Launch"], "time": "09:00"}]
    }
    events = await fetch_macro_events(client)
    assert events[0]["high_impact"] is False


async def test_fetch_macro_events_returns_sorted_by_date(client):
    events = await fetch_macro_events(client)
    days = [e["days_until"] for e in events]
    assert days == sorted(days)


async def test_fetch_macro_indicators_formats_for_frontend(client):
    indicators = await fetch_macro_indicators(client)
    assert isinstance(indicators, list)
    for item in indicators:
        assert "name" in item
        assert "value" in item
        assert "arrow" in item


async def test_fetch_macro_indicators_warning_for_imminent_high_impact(client):
    client.get_macro_events.return_value = {
        "data": [{"date": _future_date(5), "events": ["CPI Release"], "time": "08:30"}]
    }
    indicators = await fetch_macro_indicators(client)
    cpi_row = next((i for i in indicators if "CPI" in i["name"]), None)
    assert cpi_row is not None
    assert cpi_row.get("warning") is True
