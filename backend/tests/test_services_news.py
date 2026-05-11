"""Unit tests for backend/services/news.py"""
import pytest
from backend.services.news import fetch_news_headlines, _extract_vc_activity, _is_macro_sensitive, _fmt_usd


@pytest.fixture
def client(mock_client):
    return mock_client


async def test_fetch_news_headlines_returns_tuple(client):
    briefing, headlines, vc = await fetch_news_headlines(client)
    assert isinstance(briefing, list)
    assert isinstance(headlines, list)
    assert isinstance(vc, list)


async def test_fetch_news_headlines_briefing_len_max_3(client):
    briefing, _, _ = await fetch_news_headlines(client)
    assert len(briefing) <= 3


async def test_fetch_news_max_6_items(client):
    # inject 8 news items — cap is 6
    client.get_news.return_value = {
        "data": {
            "list": [{"id": str(i), "title": f"Headline {i}", "content": f"Content {i}.\n[Source]", "source_link": "", "release_time": str(i)}
                     for i in range(8)]
        }
    }
    _, headlines, _ = await fetch_news_headlines(client)
    assert len(headlines) <= 6


async def test_fetch_news_marks_macro_sensitive(client):
    _, headlines, _ = await fetch_news_headlines(client)
    fed_headline = next(h for h in headlines if "Fed" in h["text"])
    assert fed_headline["macroSensitive"] is True


async def test_fetch_news_non_macro_not_sensitive(client):
    _, headlines, _ = await fetch_news_headlines(client)
    non_macro = next(h for h in headlines if "BlackRock" in h["text"])
    assert non_macro["macroSensitive"] is False


async def test_fetch_news_extracts_source_from_content(client):
    _, headlines, _ = await fetch_news_headlines(client)
    btc_headline = next(h for h in headlines if "BlackRock" in h["text"])
    assert btc_headline["source"] == "Bloomberg"


async def test_fetch_news_handles_api_error(client):
    client.get_news.side_effect = Exception("network error")
    briefing, headlines, vc = await fetch_news_headlines(client)
    assert briefing == []
    assert headlines == []
    assert vc == []


async def test_fetch_news_extracts_vc_from_fundraising_news(client):
    _, _, vc = await fetch_news_headlines(client)
    # "DeFi protocol raises $50 million" should produce a DeFi entry
    assert any(r["sector"] == "DeFi" for r in vc)


def test_extract_vc_activity_groups_by_sector():
    items = [
        {"title": "DeFi protocol raises $50M", "content": "A DeFi dex raised $50 million in funding.\n[Source]"},
        {"title": "AI startup raises $30M",    "content": "An AI company raised $30 million in a round.\n[Source]"},
        {"title": "Another DeFi round",        "content": "DeFi lending raised $10 million backed by investors.\n[Source]"},
    ]
    result = _extract_vc_activity(items)
    defi = next(r for r in result if r["sector"] == "DeFi")
    assert defi["rounds"] == 2


def test_extract_vc_activity_sorted_by_total():
    items = [
        {"title": "DeFi raise", "content": "DeFi raised $10 million in funding.\n[S]"},
        {"title": "AI raise",   "content": "AI raised $50 million in funding.\n[S]"},
    ]
    result = _extract_vc_activity(items)
    assert result[0]["sector"] == "AI"


def test_extract_vc_activity_ignores_non_fundraising():
    items = [
        {"title": "BTC hits new high", "content": "Bitcoin price surged today.\n[Source]"},
    ]
    result = _extract_vc_activity(items)
    assert result == []


def test_extract_vc_activity_limits_to_5():
    items = [
        {"title": f"Sector{i} raise", "content": f"Sector{i} raised ${i * 10} million in funding round.\n[S]"}
        for i in range(1, 8)
    ]
    result = _extract_vc_activity(items)
    assert len(result) <= 5


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
