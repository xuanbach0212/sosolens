"""Unit tests for backend/services/etf.py"""
import pytest
from unittest.mock import AsyncMock
from backend.services.etf import fetch_etf_snapshot, fetch_etf_total_flow, _fmt_flow, _arrows


def _history(net: float, traded: float = 1_000_000.0):
    """summary-history payload: one daily row for a single date."""
    return {"data": [{"date": "2026-06-05", "total_net_inflow": net, "total_value_traded": traded}]}


@pytest.fixture
def client():
    c = AsyncMock()
    c.get_etf_summary_history.return_value = _history(200_000_000)
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
    client.get_etf_summary_history.return_value = _history(-300_000_000)
    rows = await fetch_etf_snapshot(client)
    total = next(r for r in rows if r.get("total"))
    assert total["positive"] is False


async def test_fetch_etf_total_flow_sums_btc_and_eth(client):
    total = await fetch_etf_total_flow(client)
    # BTC daily + ETH daily, each 200M (same mock) → 400M
    assert total == pytest.approx(400_000_000.0)


async def test_picks_min_traded_row_per_date(client):
    # Two rows same date: daily spot (small traded) vs cumulative (large traded).
    # Helper must keep the smaller-traded row's net inflow.
    client.get_etf_summary_history.return_value = {"data": [
        {"date": "2026-06-05", "total_net_inflow": -325_000_000, "total_value_traded": 5_000_000_000},
        {"date": "2026-06-05", "total_net_inflow": -1_700_000_000, "total_value_traded": 18_000_000_000},
    ]}
    total = await fetch_etf_total_flow(client)
    # BTC -325M + ETH -325M (same mock) = -650M
    assert total == pytest.approx(-650_000_000.0)


async def test_fetch_etf_snapshot_handles_missing_data(client):
    client.get_etf_summary_history.return_value = {}
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
