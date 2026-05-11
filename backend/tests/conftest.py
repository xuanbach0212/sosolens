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
            {"ticker": "MSTR", "name": "Strategy",      "list_location": "United States"},
            {"ticker": "MARA", "name": "MARA Holdings", "list_location": "United States"},
            {"ticker": "TSLA", "name": "Tesla",         "list_location": "United States"},
        ]
    }
    _history = {
        "MSTR": {"data": [{"date": "2026-04-27", "ticker": "MSTR", "btc_holding": "214246", "btc_acq": "1282",  "acq_cost": "100000000", "avg_btc_cost": 0.09}]},
        "MARA": {"data": [{"date": "2026-04-27", "ticker": "MARA", "btc_holding": "40435",  "btc_acq": "0",     "acq_cost": "0",         "avg_btc_cost": 0.0}]},
        "TSLA": {"data": [{"date": "2026-04-27", "ticker": "TSLA", "btc_holding": "11509",  "btc_acq": "-100",  "acq_cost": "0",         "avg_btc_cost": 0.0}]},
    }
    client.get_btc_treasury_history.side_effect = lambda t: _history.get(t, {"data": []})
    client.get_news.return_value = {
        "data": {
            "page": 1, "page_size": 20, "total": "10",
            "list": [
                {
                    "id": "1",
                    "title": "BlackRock BTC ETF records $380M single-day inflow",
                    "content": "BlackRock ETF saw record inflows today.\n[Bloomberg]",
                    "source_link": "", "release_time": "1000",
                },
                {
                    "id": "2",
                    "title": "Fed officials signal patience on rate cuts",
                    "content": "The Federal Reserve signaled patience.\n[Reuters]",
                    "source_link": "", "release_time": "1001",
                },
                {
                    "id": "3",
                    "title": "DeFi protocol raises $50 million in new funding round",
                    "content": "A DeFi lending protocol raised $50 million in a Series B round backed by a16z.\n[The Block]",
                    "source_link": "", "release_time": "1002",
                },
            ],
        }
    }
    client.get_currency_snapshot.return_value = {
        "data": {
            "price": 95000.0,
            "change_pct_24h": 0.021,
            "marketcap": 1_900_000_000_000.0,
            "turnover_24h": 50_000_000_000.0,
        }
    }

    return client
