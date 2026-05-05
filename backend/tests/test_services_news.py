"""Unit tests for backend/services/news.py"""
import pytest
from unittest.mock import AsyncMock
from backend.services.news import fetch_news_headlines, fetch_fundraising, _is_macro_sensitive, _fmt_usd


@pytest.fixture
def client(mock_client):
    return mock_client


async def test_fetch_news_headlines_returns_tuple(client):
    briefing, headlines = await fetch_news_headlines(client)
    assert isinstance(briefing, list)
    assert isinstance(headlines, list)


async def test_fetch_news_headlines_briefing_len_max_3(client):
    briefing, _ = await fetch_news_headlines(client)
    assert len(briefing) <= 3


async def test_fetch_news_headlines_max_4_items(client):
    # inject 6 news items
    client.get_news.return_value = {
        "data": [{"title": f"Headline {i}", "source_name": "Source"} for i in range(6)]
    }
    _, headlines = await fetch_news_headlines(client)
    assert len(headlines) <= 4


async def test_fetch_news_marks_macro_sensitive(client):
    _, headlines = await fetch_news_headlines(client)
    fed_headline = next(h for h in headlines if "Fed" in h["text"])
    assert fed_headline["macroSensitive"] is True


async def test_fetch_news_non_macro_not_sensitive(client):
    _, headlines = await fetch_news_headlines(client)
    non_macro = next(h for h in headlines if "BlackRock" in h["text"])
    assert non_macro["macroSensitive"] is False


async def test_fetch_news_handles_api_error(client):
    client.get_news.side_effect = Exception("network error")
    briefing, headlines = await fetch_news_headlines(client)
    assert briefing == []
    assert headlines == []


async def test_fetch_fundraising_groups_by_sector(client):
    result = await fetch_fundraising(client)
    # DeFi has 2 rounds, should be aggregated
    defi = next(r for r in result if r["sector"] == "DeFi")
    assert defi["rounds"] == 2


async def test_fetch_fundraising_sorted_by_total_usd(client):
    result = await fetch_fundraising(client)
    # DeFi: $60M, AI: $30M, RWA: $15M
    assert result[0]["sector"] == "DeFi"


async def test_fetch_fundraising_limits_to_5(client):
    client.get_fundraising.return_value = {
        "data": [{"sector": f"Sector{i}", "amount_usd": i * 1_000_000} for i in range(10)]
    }
    result = await fetch_fundraising(client)
    assert len(result) <= 5


async def test_fetch_fundraising_handles_api_error(client):
    client.get_fundraising.side_effect = Exception("API down")
    result = await fetch_fundraising(client)
    assert result == []


def test_is_macro_sensitive_matches_fed():
    assert _is_macro_sensitive("Fed officials signal patience") is True


def test_is_macro_sensitive_matches_cpi():
    assert _is_macro_sensitive("US CPI comes in hotter than expected") is True


def test_is_macro_sensitive_non_macro():
    assert _is_macro_sensitive("DeFi protocol raises $50M") is False


def test_fmt_usd_billions():
    assert _fmt_usd(1_500_000_000) == "$1.5B"


def test_fmt_usd_millions():
    assert _fmt_usd(60_000_000) == "$60M"
