"""Unit tests for backend/services/btc_treasuries.py"""
import pytest
from unittest.mock import AsyncMock
from backend.services.btc_treasuries import fetch_btc_treasuries, _fmt_holdings, _fmt_change


@pytest.fixture
def client(mock_client):
    return mock_client


async def test_fetch_btc_treasuries_returns_list(client):
    result = await fetch_btc_treasuries(client)
    assert isinstance(result, list)
    assert len(result) > 0


async def test_fetch_btc_treasuries_sorted_by_holdings_descending(client):
    result = await fetch_btc_treasuries(client)
    # MicroStrategy (214246) should come before Marathon (40435)
    names = [r["company"] for r in result]
    assert names.index("MicroStrategy") < names.index("Marathon")


async def test_fetch_btc_treasuries_limits_to_5(client):
    client.get_btc_treasuries.return_value = {
        "data": [
            {"short_name": f"Company{i}", "total_holdings": i * 1000, "btc_change_7d": 0}
            for i in range(10, 0, -1)
        ]
    }
    result = await fetch_btc_treasuries(client)
    assert len(result) <= 5


async def test_fetch_btc_treasuries_positive_weekly_change(client):
    result = await fetch_btc_treasuries(client)
    microstrategy = next(r for r in result if r["company"] == "MicroStrategy")
    assert microstrategy["positive"] is True
    assert "+1,282" in microstrategy["weeklyChange"]


async def test_fetch_btc_treasuries_negative_weekly_change(client):
    result = await fetch_btc_treasuries(client)
    tesla = next(r for r in result if r["company"] == "Tesla")
    assert tesla["positive"] is False


async def test_fetch_btc_treasuries_zero_change_is_none(client):
    result = await fetch_btc_treasuries(client)
    marathon = next(r for r in result if r["company"] == "Marathon")
    assert marathon["positive"] is None
    assert "±0" in marathon["weeklyChange"]


async def test_fetch_btc_treasuries_handles_empty_response(client):
    client.get_btc_treasuries.return_value = {"data": []}
    result = await fetch_btc_treasuries(client)
    assert result == []


async def test_fetch_btc_treasuries_handles_api_error(client):
    client.get_btc_treasuries.side_effect = Exception("API error")
    result = await fetch_btc_treasuries(client)
    assert result == []


def test_fmt_holdings_formats_with_commas():
    assert _fmt_holdings(214246) == "214,246 BTC"


def test_fmt_change_positive():
    assert _fmt_change(1282) == "+1,282"


def test_fmt_change_negative():
    assert _fmt_change(-100) == "-100"


def test_fmt_change_zero():
    assert _fmt_change(0) == "±0"
