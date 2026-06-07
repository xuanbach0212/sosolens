"""Unit tests for backend/services/sector.py"""
import pytest
from unittest.mock import AsyncMock
from backend.services.sector import fetch_sector_flows


@pytest.fixture
def client():
    c = AsyncMock()
    c.get_index_snapshot.return_value = {"data": {"change_pct_24h": 0.025}}
    return c


async def test_fetch_sector_flows_returns_list(client):
    result = await fetch_sector_flows(client)
    assert isinstance(result, list)
    assert len(result) > 0


async def test_fetch_sector_flows_sorted_descending(client):
    # sector.py reads change_pct_24h (fractional) and multiplies by 100
    values = [0.05, 0.03, 0.01, -0.01, -0.03, -0.05, -0.07, -0.09]
    client.get_index_snapshot.side_effect = [
        {"data": {"change_pct_24h": v}} for v in values
    ]
    result = await fetch_sector_flows(client)
    changes = [r["change"] for r in result]
    assert changes == sorted(changes, reverse=True)


async def test_fetch_sector_flows_contains_expected_fields(client):
    result = await fetch_sector_flows(client)
    for row in result:
        assert "name" in row
        assert "change" in row
        assert "arrows" in row
        assert "positive" in row


async def test_fetch_sector_flows_positive_flag_correct(client):
    pos_vals = [0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02]
    client.get_index_snapshot.side_effect = [
        {"data": {"change_pct_24h": v}} for v in pos_vals
    ]
    result = await fetch_sector_flows(client)
    for row in result:
        assert row["positive"] is True


async def test_fetch_sector_flows_negative_change(client):
    neg_vals = [-0.02, -0.02, -0.02, -0.02, -0.02, -0.02, -0.02, -0.02]
    client.get_index_snapshot.side_effect = [
        {"data": {"change_pct_24h": v}} for v in neg_vals
    ]
    result = await fetch_sector_flows(client)
    for row in result:
        assert row["positive"] is False


async def test_fetch_sector_flows_handles_api_error(client):
    client.get_index_snapshot.side_effect = Exception("network error")
    result = await fetch_sector_flows(client)
    # should return list (with zeros for failed tickers, not crash)
    assert isinstance(result, list)
