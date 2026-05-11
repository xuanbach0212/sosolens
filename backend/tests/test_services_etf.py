"""Unit tests for backend/services/etf.py"""
import pytest
from unittest.mock import AsyncMock
from backend.services.etf import fetch_etf_snapshot, fetch_etf_total_flow, _fmt_flow, _arrows


@pytest.fixture
def client():
    c = AsyncMock()
    c.get_etf_snapshot.return_value = {"data": {"net_inflow": 200_000_000}}
    return c


async def test_fetch_etf_snapshot_returns_three_rows(client):
    rows = await fetch_etf_snapshot(client)
    assert len(rows) == 3
    names = [r["name"] for r in rows]
    assert "BTC ETF" in names
    assert "ETH ETF" in names
    assert "TOTAL" in names


async def test_fetch_etf_snapshot_total_row_is_flagged(client):
    rows = await fetch_etf_snapshot(client)
    total = next(r for r in rows if r.get("total"))
    assert total["name"] == "TOTAL"


async def test_fetch_etf_snapshot_positive_flag_for_positive_flow(client):
    rows = await fetch_etf_snapshot(client)
    for r in rows:
        assert r["positive"] is True


async def test_fetch_etf_snapshot_negative_flow_marks_negative(client):
    client.get_etf_snapshot.return_value = {"data": {"net_inflow": -300_000_000}}
    rows = await fetch_etf_snapshot(client)
    total = next(r for r in rows if r.get("total"))
    assert total["positive"] is False


async def test_fetch_etf_total_flow_sums_all_tickers(client):
    total = await fetch_etf_total_flow(client)
    # 3 BTC + 2 ETH tickers, each returning 200M → 5 * 200M = 1000M
    assert total == pytest.approx(1_000_000_000.0)


async def test_fetch_etf_snapshot_handles_missing_data(client):
    client.get_etf_snapshot.return_value = {}
    rows = await fetch_etf_snapshot(client)
    # should still return 3 rows with 0 flows
    assert len(rows) == 3
    total = next(r for r in rows if r.get("total"))
    assert total["flow"] == "+$0M"


def test_fmt_flow_billion():
    assert _fmt_flow(1_500_000_000) == "+$1.5B"


def test_fmt_flow_million():
    assert _fmt_flow(250_000_000) == "+$250M"


def test_fmt_flow_negative():
    assert _fmt_flow(-100_000_000) == "-$100M"


def test_arrows_large_positive():
    assert _arrows(600_000_000) == "↑↑↑"


def test_arrows_small_negative():
    assert _arrows(-50_000_000) == "↓"
