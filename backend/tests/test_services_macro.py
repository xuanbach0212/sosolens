"""Unit tests for backend/services/macro.py"""
import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock
from backend.services.macro import (
    fetch_macro_events,
    fetch_macro_indicators,
    get_upcoming_events,
    get_macro_status,
    get_risk_environment,
)


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


# --- get_upcoming_events ---

async def test_get_upcoming_events_excludes_beyond_window(client):
    client.get_macro_events.return_value = {
        "data": [
            {"date": _future_date(6),  "events": ["CPI Release"], "time": "08:30"},
            {"date": _future_date(20), "events": ["GDP Report"],  "time": "10:00"},
        ]
    }
    events = await get_upcoming_events(client, days=14)
    names = [" ".join(e["events"]) for e in events]
    assert any("CPI" in n for n in names)
    assert not any("GDP" in n for n in names)


async def test_get_upcoming_events_includes_within_window(client):
    client.get_macro_events.return_value = {
        "data": [{"date": _future_date(6), "events": ["CPI Release"], "time": "08:30"}]
    }
    events = await get_upcoming_events(client, days=14)
    assert len(events) == 1
    assert events[0]["days_until"] == 6


# --- get_macro_status ---

async def test_get_macro_status_identifies_cpi(client):
    status = await get_macro_status(client)
    assert status["cpi"] is not None
    assert status["cpi"]["days_until"] == 6
    assert status["cpi"]["direction"] == "watch"


async def test_get_macro_status_identifies_fed_rate(client):
    status = await get_macro_status(client)
    assert status["fed_rate"] is not None
    assert status["fed_rate"]["days_until"] == 14
    assert status["fed_rate"]["direction"] == "neutral"


async def test_get_macro_status_returns_none_for_missing_indicator(client):
    status = await get_macro_status(client)
    assert status["gdp"] is None
    assert status["nfp"] is None
    assert status["ppi"] is None


# --- get_risk_environment ---

async def test_get_risk_environment_risk_on(client):
    client.get_macro_events.return_value = {
        "data": [{"date": _future_date(3), "events": ["Product Launch"], "time": "09:00"}]
    }
    assert await get_risk_environment(client) == "risk-on"


async def test_get_risk_environment_risk_off(client):
    client.get_macro_events.return_value = {
        "data": [{"date": _future_date(2), "events": ["CPI Release"], "time": "08:30"}]
    }
    assert await get_risk_environment(client) == "risk-off"


async def test_get_risk_environment_neutral(client):
    client.get_macro_events.return_value = {
        "data": [{"date": _future_date(5), "events": ["FOMC Meeting"], "time": "14:00"}]
    }
    assert await get_risk_environment(client) == "neutral"
