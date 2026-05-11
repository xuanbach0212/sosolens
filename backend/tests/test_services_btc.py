"""Unit tests for backend/services/btc_treasuries.py"""
import pytest
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
    # Strategy (214246 BTC) should come before MARA Holdings (40435 BTC)
    names = [r["company"] for r in result]
    assert names.index("Strategy") < names.index("MARA Holdings")


async def test_fetch_btc_treasuries_limits_to_5(client):
    tickers = [f"T{i}" for i in range(10)]
    client.get_btc_treasuries.return_value = {
        "data": [{"ticker": t, "name": f"Company {t}", "list_location": "US"} for t in tickers]
    }
    _hist = {t: {"data": [{"btc_holding": str(i * 1000), "btc_acq": "0", "date": "2026-01-01", "ticker": t, "acq_cost": "0", "avg_btc_cost": 0}]}
             for i, t in enumerate(tickers)}
    client.get_btc_treasury_history.side_effect = lambda t: _hist.get(t, {"data": []})
    result = await fetch_btc_treasuries(client)
    assert len(result) <= 5


async def test_fetch_btc_treasuries_positive_weekly_change(client):
    result = await fetch_btc_treasuries(client)
    strategy = next(r for r in result if r["company"] == "Strategy")
    assert strategy["positive"] is True
    assert "+1,282" in strategy["weeklyChange"]


async def test_fetch_btc_treasuries_negative_weekly_change(client):
    result = await fetch_btc_treasuries(client)
    tesla = next(r for r in result if r["company"] == "Tesla")
    assert tesla["positive"] is False


async def test_fetch_btc_treasuries_zero_change_is_none(client):
    result = await fetch_btc_treasuries(client)
    mara = next(r for r in result if r["company"] == "MARA Holdings")
    assert mara["positive"] is None
    assert "±0" in mara["weeklyChange"]


async def test_fetch_btc_treasuries_handles_empty_response(client):
    client.get_btc_treasuries.return_value = {"data": []}
    result = await fetch_btc_treasuries(client)
    assert result == []


async def test_fetch_btc_treasuries_handles_api_error(client):
    client.get_btc_treasuries.side_effect = Exception("API error")
    result = await fetch_btc_treasuries(client)
    assert result == []


async def test_fetch_btc_treasuries_skips_ticker_with_empty_history(client):
    client.get_btc_treasuries.return_value = {
        "data": [{"ticker": "MSTR", "name": "Strategy", "list_location": "US"}]
    }
    client.get_btc_treasury_history.side_effect = None
    client.get_btc_treasury_history.return_value = {"data": []}
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
