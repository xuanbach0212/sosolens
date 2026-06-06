"""Tests for backend/services/currency.py — CoinGecko global-market override (C3)."""
import pytest
from unittest.mock import AsyncMock, patch

import backend.cache as cache
from backend.services.currency import fetch_market_status, fetch_global_market, fetch_token_prices
from backend.agent.tokens import token_from_cache


@pytest.fixture(autouse=True)
def clear_global_cache():
    """Ensure the global_market cache key doesn't leak across tests."""
    cache.put("global_market", None)
    cache.put("token_prices", None)
    yield
    cache.put("global_market", None)
    cache.put("token_prices", None)


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


# ---------------------------------------------------------------------------
# fetch_token_prices — CoinGecko per-token prices for TOP TOKENS
# ---------------------------------------------------------------------------

def _markets_payload():
    return [
        {"symbol": "sol", "current_price": 142.7, "price_change_percentage_24h": -3.4},
        {"symbol": "bnb", "current_price": 612.0, "price_change_percentage_24h": 1.2},
        # sub-$1 token keeps precision instead of collapsing to "$0"
        {"symbol": "doge", "current_price": 0.1634, "price_change_percentage_24h": -0.7},
        # duplicate symbol — first (higher mcap) wins, this lower one is ignored
        {"symbol": "sol", "current_price": 0.01, "price_change_percentage_24h": 99.0},
        # zero price and empty symbol are skipped
        {"symbol": "dead", "current_price": 0, "price_change_percentage_24h": 5.0},
        {"symbol": "", "current_price": 10.0, "price_change_percentage_24h": 5.0},
    ]


@pytest.mark.asyncio
async def test_fetch_token_prices_parses_and_dedupes():
    client = AsyncMock()
    client.get.return_value = _Resp(_markets_payload())
    with patch("backend.services.currency.httpx.AsyncClient") as mk:
        mk.return_value.__aenter__.return_value = client
        result = await fetch_token_prices()
    assert result["SOL"] == {"price": "$142.70", "change": "-3.4%", "positive": False}
    assert result["BNB"] == {"price": "$612.00", "change": "+1.2%", "positive": True}
    assert result["DOGE"]["price"] == "$0.1634"  # sub-$1 precision preserved
    assert "DEAD" not in result and "" not in result  # zero-price / empty skipped


@pytest.mark.asyncio
async def test_fetch_token_prices_returns_none_on_error():
    with patch("backend.services.currency.httpx.AsyncClient", side_effect=Exception("boom")):
        assert await fetch_token_prices() is None


# ---------------------------------------------------------------------------
# token_from_cache — resolves non-BTC/ETH symbols via the token_prices cache
# ---------------------------------------------------------------------------

def test_token_from_cache_uses_coingecko_for_other_symbols():
    cache.put("token_prices", {"SOL": {"price": "$143", "change": "-3.4%", "positive": False}})
    tok = token_from_cache("SOL", positive=True)
    assert tok == {"symbol": "SOL", "price": "$143", "change": "-3.4%", "positive": False}


def test_token_from_cache_override_wins_over_token_change():
    cache.put("token_prices", {"SOL": {"price": "$143", "change": "-3.4%", "positive": False}})
    tok = token_from_cache("SOL", positive=True, change_override="-21.0%")
    assert tok["price"] == "$143"
    assert tok["change"] == "-21.0%"      # sector roi_7d wins
    assert tok["positive"] is True        # keeps caller's flag when override given


def test_token_from_cache_unknown_symbol_stays_dash():
    cache.put("token_prices", {"SOL": {"price": "$143", "change": "-3.4%", "positive": False}})
    tok = token_from_cache("MSTR", positive=True)  # equity, not on CoinGecko
    assert tok == {"symbol": "MSTR", "price": "—", "change": "—", "positive": True}
