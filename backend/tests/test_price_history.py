"""Tests for BTC/ETH price snapshot storage and /api/price-history endpoint (#47)."""
import pytest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.agent.models import Base, PriceSnapshot
from backend.agent.runner import _refresh_market_cache


# ---------------------------------------------------------------------------
# In-memory DB fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def mem_db_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def mem_session_factory(mem_db_engine):
    return sessionmaker(bind=mem_db_engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def patch_runner_get_db(mem_session_factory):
    @contextmanager
    def _mem_get_db():
        db = mem_session_factory()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    with patch("backend.agent.runner.get_db", _mem_get_db):
        yield


# ---------------------------------------------------------------------------
# Model & schema
# ---------------------------------------------------------------------------

def test_price_snapshot_table_created(mem_db_engine):
    from sqlalchemy import inspect
    inspector = inspect(mem_db_engine)
    assert "price_snapshots" in inspector.get_table_names()


def test_price_snapshot_columns(mem_db_engine):
    from sqlalchemy import inspect
    cols = {c["name"] for c in inspect(mem_db_engine).get_columns("price_snapshots")}
    assert {"id", "recorded_at", "btc_price", "eth_price"} <= cols


# ---------------------------------------------------------------------------
# fetch_market_status returns raw float prices
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_market_status_includes_raw_prices(mock_client):
    from backend.services.currency import fetch_market_status
    result = await fetch_market_status(mock_client)
    assert "btcPriceRaw" in result
    assert "ethPriceRaw" in result
    assert isinstance(result["btcPriceRaw"], float)
    assert isinstance(result["ethPriceRaw"], float)
    assert result["btcPriceRaw"] > 0
    assert result["ethPriceRaw"] > 0


@pytest.mark.asyncio
async def test_fetch_market_status_raw_prices_match_formatted(mock_client):
    from backend.services.currency import fetch_market_status
    result = await fetch_market_status(mock_client)
    # mock_client returns price=95000.0 for both BTC and ETH
    assert result["btcPriceRaw"] == 95000.0
    assert result["ethPriceRaw"] == 95000.0


# ---------------------------------------------------------------------------
# _refresh_market_cache writes PriceSnapshot rows
# ---------------------------------------------------------------------------

_GOOD_MARKET = {
    "btcPrice": "$95,000",
    "ethPrice": "$3,200",
    "btcPriceRaw": 95000.0,
    "ethPriceRaw": 3200.0,
    "sentiment": "RISK-ON",
    "sentimentPositive": True,
    "btcChange": "+2.1%",
    "ethChange": "+1.5%",
    "mcap": "$3.5T",
    "vol": "$120B",
    "fearGreed": 72,
    "fearGreedLabel": "GREED",
}


@pytest.mark.asyncio
async def test_refresh_market_cache_writes_snapshot(mem_session_factory):
    with patch("backend.services.sosovalue.get_client", return_value=AsyncMock()), \
         patch("backend.services.currency.fetch_market_status", new=AsyncMock(return_value=_GOOD_MARKET)), \
         patch("backend.agent.runner.broadcast", new=AsyncMock()):
        await _refresh_market_cache()
    with mem_session_factory() as db:
        rows = db.scalars(select(PriceSnapshot)).all()
    assert len(rows) == 1
    assert rows[0].btc_price == 95000.0
    assert rows[0].eth_price == 3200.0


@pytest.mark.asyncio
async def test_refresh_market_cache_skips_zero_prices(mem_session_factory):
    bad_market = dict(_GOOD_MARKET, btcPriceRaw=0.0, ethPriceRaw=0.0)
    with patch("backend.services.sosovalue.get_client", return_value=AsyncMock()), \
         patch("backend.services.currency.fetch_market_status", new=AsyncMock(return_value=bad_market)), \
         patch("backend.agent.runner.broadcast", new=AsyncMock()):
        await _refresh_market_cache()
    with mem_session_factory() as db:
        rows = db.scalars(select(PriceSnapshot)).all()
    assert len(rows) == 0


@pytest.mark.asyncio
async def test_refresh_market_cache_skips_when_api_fails(mem_session_factory):
    with patch("backend.services.sosovalue.get_client", return_value=AsyncMock()), \
         patch("backend.services.currency.fetch_market_status", new=AsyncMock(side_effect=Exception("API down"))), \
         patch("backend.agent.runner.broadcast", new=AsyncMock()):
        await _refresh_market_cache()  # must not raise
    with mem_session_factory() as db:
        rows = db.scalars(select(PriceSnapshot)).all()
    assert len(rows) == 0


@pytest.mark.asyncio
async def test_refresh_market_cache_multiple_calls_appends_rows(mem_session_factory):
    mock_fetch = AsyncMock(return_value=_GOOD_MARKET)
    with patch("backend.services.sosovalue.get_client", return_value=AsyncMock()), \
         patch("backend.services.currency.fetch_market_status", mock_fetch), \
         patch("backend.agent.runner.broadcast", new=AsyncMock()):
        await _refresh_market_cache()
        await _refresh_market_cache()
    with mem_session_factory() as db:
        rows = db.scalars(select(PriceSnapshot)).all()
    assert len(rows) == 2


# ---------------------------------------------------------------------------
# Pruning: rows older than 72h are deleted
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_prune_removes_old_rows(mem_session_factory):
    old_time = datetime.now(timezone.utc) - timedelta(hours=73)
    with mem_session_factory() as db:
        db.add(PriceSnapshot(recorded_at=old_time, btc_price=80000.0, eth_price=2800.0))
        db.commit()

    with patch("backend.services.sosovalue.get_client", return_value=AsyncMock()), \
         patch("backend.services.currency.fetch_market_status", new=AsyncMock(return_value=_GOOD_MARKET)), \
         patch("backend.agent.runner.broadcast", new=AsyncMock()):
        await _refresh_market_cache()

    with mem_session_factory() as db:
        rows = db.scalars(select(PriceSnapshot)).all()
    # Old row pruned; only the new row remains
    assert len(rows) == 1
    assert rows[0].btc_price == 95000.0


@pytest.mark.asyncio
async def test_prune_keeps_rows_within_72h(mem_session_factory):
    recent_time = datetime.now(timezone.utc) - timedelta(hours=71)
    with mem_session_factory() as db:
        db.add(PriceSnapshot(recorded_at=recent_time, btc_price=80000.0, eth_price=2800.0))
        db.commit()

    with patch("backend.services.sosovalue.get_client", return_value=AsyncMock()), \
         patch("backend.services.currency.fetch_market_status", new=AsyncMock(return_value=_GOOD_MARKET)), \
         patch("backend.agent.runner.broadcast", new=AsyncMock()):
        await _refresh_market_cache()

    with mem_session_factory() as db:
        rows = db.scalars(select(PriceSnapshot)).all()
    assert len(rows) == 2  # old row kept + new row


# ---------------------------------------------------------------------------
# GET /api/price-history endpoint
# ---------------------------------------------------------------------------

@pytest.fixture
def test_client():
    """TestClient with an in-memory DB using StaticPool so threads share one connection."""
    from fastapi.testclient import TestClient
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    @contextmanager
    def _mem_get_db():
        db = Session()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    with patch("backend.main.get_db", _mem_get_db), \
         patch("backend.main.init_db"), \
         patch("backend.agent.runner.start_scheduler"), \
         patch("backend.agent.runner.run_agent", new=AsyncMock()):
        from backend.main import app
        client = TestClient(app, raise_server_exceptions=True)
        yield client, Session


def test_price_history_empty(test_client):
    client, _ = test_client
    resp = client.get("/api/price-history")
    assert resp.status_code == 200
    assert resp.json() == {"priceHistory": []}


def test_price_history_returns_rows(test_client):
    client, Session = test_client
    now = datetime.now(timezone.utc)
    with Session() as db:
        db.add(PriceSnapshot(recorded_at=now - timedelta(hours=2), btc_price=94000.0, eth_price=3100.0))
        db.add(PriceSnapshot(recorded_at=now - timedelta(hours=1), btc_price=95000.0, eth_price=3200.0))
        db.commit()
    resp = client.get("/api/price-history")
    assert resp.status_code == 200
    data = resp.json()["priceHistory"]
    assert len(data) == 2
    assert data[0]["btcPrice"] == 94000.0
    assert data[1]["btcPrice"] == 95000.0
    assert "timestamp" in data[0]


def test_price_history_hours_param_filters(test_client):
    client, Session = test_client
    now = datetime.now(timezone.utc)
    with Session() as db:
        db.add(PriceSnapshot(recorded_at=now - timedelta(hours=50), btc_price=90000.0, eth_price=3000.0))
        db.add(PriceSnapshot(recorded_at=now - timedelta(hours=10), btc_price=95000.0, eth_price=3200.0))
        db.commit()
    resp = client.get("/api/price-history?hours=24")
    data = resp.json()["priceHistory"]
    assert len(data) == 1
    assert data[0]["btcPrice"] == 95000.0


def test_price_history_ordered_asc(test_client):
    client, Session = test_client
    now = datetime.now(timezone.utc)
    with Session() as db:
        db.add(PriceSnapshot(recorded_at=now - timedelta(hours=3), btc_price=91000.0, eth_price=3000.0))
        db.add(PriceSnapshot(recorded_at=now - timedelta(hours=1), btc_price=95000.0, eth_price=3200.0))
        db.add(PriceSnapshot(recorded_at=now - timedelta(hours=2), btc_price=93000.0, eth_price=3100.0))
        db.commit()
    resp = client.get("/api/price-history")
    prices = [r["btcPrice"] for r in resp.json()["priceHistory"]]
    assert prices == [91000.0, 93000.0, 95000.0]  # ascending by timestamp
