"""Shared fixtures for backend unit tests."""
import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def mock_client():
    """AsyncMock of SoSoValueClient with sensible default responses."""
    client = AsyncMock()

    client.get_etf_snapshot.return_value = {"data": {"net_inflow": 200_000_000}}
    client.get_index_snapshot.return_value = {"data": {"change_24h": 2.5}}
    client.get_macro_events.return_value = {
        "data": [
            {"date": "2099-01-10", "events": ["CPI Release"], "time": "08:30"},
            {"date": "2099-01-15", "events": ["FOMC Meeting"], "time": "14:00"},
        ]
    }
    client.get_btc_treasuries.return_value = {
        "data": [
            {"short_name": "MicroStrategy", "total_holdings": 214246, "btc_change_7d": 1282},
            {"short_name": "Marathon",      "total_holdings": 40435,  "btc_change_7d": 0},
            {"short_name": "Tesla",         "total_holdings": 11509,  "btc_change_7d": -100},
        ]
    }
    client.get_news.return_value = {
        "data": [
            {"title": "BlackRock BTC ETF records $380M single-day inflow", "source_name": "Bloomberg"},
            {"title": "Fed officials signal patience on rate cuts",         "source_name": "Reuters"},
            {"title": "DeFi protocol raises $50M in new funding round",    "source_name": "The Block"},
        ]
    }
    client.get_fundraising.return_value = {
        "data": [
            {"sector": "DeFi",    "amount_usd": 50_000_000},
            {"sector": "DeFi",    "amount_usd": 10_000_000},
            {"sector": "AI",      "amount_usd": 30_000_000},
            {"sector": "RWA",     "amount_usd": 15_000_000},
        ]
    }
    client.get_prices.return_value = {
        "data": [
            {"symbol": "BTC", "price": 95000.0},
            {"symbol": "ETH", "price": 1800.0},
        ]
    }

    return client
