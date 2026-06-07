"""Tests for backend/services/fred.py — real macro indicators (C2)."""
import pytest
from unittest.mock import AsyncMock, patch

from backend.services.fred import fetch_fred_indicators


class _Resp:
    def __init__(self, observations):
        self._obs = observations

    def raise_for_status(self):
        pass

    def json(self):
        return {"observations": self._obs}


def _value_for(series_id: str) -> str:
    return {
        "DFF": "4.33",
        "CPIAUCSL": "3.2",
        "DGS10": "4.21",
        "DTWEXBGS": "121.34",
    }[series_id]


def _mock_client_returns_values():
    """AsyncMock httpx client whose .get reflects the requested series_id."""
    client = AsyncMock()

    async def _get(url, params=None):
        sid = (params or {}).get("series_id")
        return _Resp([{"date": "2026-06-05", "value": _value_for(sid)}])

    client.get.side_effect = _get
    return client


@pytest.mark.asyncio
async def test_returns_none_without_api_key(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    assert await fetch_fred_indicators() is None


@pytest.mark.asyncio
async def test_returns_none_with_blank_api_key(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "   ")
    assert await fetch_fred_indicators() is None


@pytest.mark.asyncio
async def test_formats_all_four_indicators(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "testkey")
    client = _mock_client_returns_values()
    with patch("backend.services.fred.httpx.AsyncClient") as mk:
        mk.return_value.__aenter__.return_value = client
        rows = await fetch_fred_indicators()
    by_name = {r["name"]: r["value"] for r in rows}
    assert by_name == {
        "Fed Rate": "4.33%",
        "CPI YoY": "3.2%",
        "10Y Yield": "4.21%",
        "USD Index": "121.3",
    }
    assert all(r["arrow"] == "" and r["warning"] is False for r in rows)


@pytest.mark.asyncio
async def test_skips_missing_values_uses_next_observation(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "testkey")
    client = AsyncMock()

    async def _get(url, params=None):
        # First obs is a FRED "." missing marker; helper should fall through.
        return _Resp([
            {"date": "2026-06-06", "value": "."},
            {"date": "2026-06-05", "value": "4.50"},
        ])

    client.get.side_effect = _get
    with patch("backend.services.fred.httpx.AsyncClient") as mk:
        mk.return_value.__aenter__.return_value = client
        rows = await fetch_fred_indicators()
    assert rows[0]["value"] == "4.50%"  # Fed Rate from the second obs


@pytest.mark.asyncio
async def test_returns_none_when_all_series_fail(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "testkey")
    client = AsyncMock()
    client.get.side_effect = Exception("FRED down")
    with patch("backend.services.fred.httpx.AsyncClient") as mk:
        mk.return_value.__aenter__.return_value = client
        rows = await fetch_fred_indicators()
    assert rows is None  # no rows collected → None so caller falls back
