"""Tests for backend/services/currency.py — CoinGecko global-market override (C3)."""
import pytest
from unittest.mock import AsyncMock, patch

import backend.cache as cache
from backend.services.currency import fetch_market_status, fetch_global_market


@pytest.fixture(autouse=True)
def clear_global_cache():
    """Ensure the global_market cache key doesn't leak across tests."""
    cache.put("global_market", None)
    yield
    cache.put("global_market", None)


# ---------------------------------------------------------------------------
# fetch_global_market
# ---------------------------------------------------------------------------

class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _global_payload(mcap, vol, change):
    return {"data": {
        "total_market_cap": {"usd": mcap},
        "total_volume": {"usd": vol},
        "market_cap_change_percentage_24h_usd": change,
    }}


@pytest.mark.asyncio
async def test_fetch_global_market_formats_figures():
    client = AsyncMock()
    client.get.return_value = _Resp(_global_payload(2_180_000_000_000, 147_000_000_000, -0.31))
    with patch("backend.services.currency.httpx.AsyncClient") as mk:
        mk.return_value.__aenter__.return_value = client
        result = await fetch_global_market()
    assert result == {"mcap": "$2.18T", "vol": "$147B", "mcapChange": "-0.3%"}


@pytest.mark.asyncio
async def test_fetch_global_market_returns_none_on_zero_mcap():
    client = AsyncMock()
    client.get.return_value = _Resp(_global_payload(0, 0, 0))
    with patch("backend.services.currency.httpx.AsyncClient") as mk:
        mk.return_value.__aenter__.return_value = client
        result = await fetch_global_market()
    assert result is None


@pytest.mark.asyncio
async def test_fetch_global_market_returns_none_on_error():
    with patch("backend.services.currency.httpx.AsyncClient", side_effect=Exception("boom")):
        result = await fetch_global_market()
    assert result is None


# ---------------------------------------------------------------------------
# fetch_market_status overrides mcap/vol from the cached global figure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_market_status_overrides_with_cached_global(mock_client):
    cache.put("global_market", {"mcap": "$2.18T", "vol": "$147B", "mcapChange": "-0.3%"})
    result = await fetch_market_status(mock_client)
    assert result["mcap"] == "$2.18T"
    assert result["vol"] == "$147B"
    assert result["mcapChange"] == "-0.3%"


@pytest.mark.asyncio
async def test_market_status_keeps_derived_values_without_cache(mock_client):
    # No global_market cached → mcap/vol come from BTC+ETH snapshot math, not "$2.18T".
    result = await fetch_market_status(mock_client)
    assert result["mcap"] != "$2.18T"
    assert result["mcap"].startswith("$")
