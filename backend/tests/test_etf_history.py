"""Tests for ETF snapshot storage and /api/etf-history endpoint (#54)."""
import pytest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.agent.models import Base, EtfSnapshot
from backend.agent.runner import run_agent


# ---------------------------------------------------------------------------
# In-memory DB fixture (for runner tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def mem_session_factory():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


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

def test_etf_snapshot_table_created(mem_session_factory):
    from sqlalchemy import inspect
    engine = mem_session_factory.kw["bind"]
    assert "etf_snapshots" in inspect(engine).get_table_names()


def test_etf_snapshot_columns(mem_session_factory):
    from sqlalchemy import inspect
    engine = mem_session_factory.kw["bind"]
    cols = {c["name"] for c in inspect(engine).get_columns("etf_snapshots")}
    assert {"id", "recorded_at", "btc_flow", "eth_flow", "total_flow"} <= cols


# ---------------------------------------------------------------------------
# run_agent persists EtfSnapshot
# ---------------------------------------------------------------------------

_ETF_RAW = {"btc": 380_000_000.0, "eth": 120_000_000.0, "total": 500_000_000.0}


class _MockDetector:
    """Minimal detector stub — returns no signals, prevents early-return in run_agent()."""
    async def run(self):
        return []


_PATCHES = dict(
    _refresh_panel_cache=AsyncMock(),
    check_outcomes=AsyncMock(),
    broadcast=AsyncMock(),
    build_full_snapshot=lambda: {},
)


@pytest.mark.asyncio
async def test_run_agent_persists_etf_snapshot(mem_session_factory):
    import backend.cache as cache
    cache.put("etf_raw", _ETF_RAW)
    with patch("backend.agent.runner.DETECTORS", [_MockDetector()]), \
         patch("backend.agent.runner._refresh_panel_cache", new=AsyncMock()), \
         patch("backend.agent.runner.check_outcomes", new=AsyncMock()), \
         patch("backend.agent.runner.broadcast", new=AsyncMock()), \
         patch("backend.agent.runner.build_full_snapshot", return_value={}):
        await run_agent()
    with mem_session_factory() as db:
        rows = db.scalars(select(EtfSnapshot)).all()
    assert len(rows) == 1
    assert rows[0].btc_flow == 380_000_000.0
    assert rows[0].eth_flow == 120_000_000.0
    assert rows[0].total_flow == 500_000_000.0


@pytest.mark.asyncio
async def test_run_agent_skips_etf_snapshot_when_no_raw(mem_session_factory):
    import backend.cache as cache
    cache.put("etf_raw", None)
    with patch("backend.agent.runner.DETECTORS", [_MockDetector()]), \
         patch("backend.agent.runner._refresh_panel_cache", new=AsyncMock()), \
         patch("backend.agent.runner.check_outcomes", new=AsyncMock()), \
         patch("backend.agent.runner.broadcast", new=AsyncMock()), \
         patch("backend.agent.runner.build_full_snapshot", return_value={}):
        await run_agent()
    with mem_session_factory() as db:
        rows = db.scalars(select(EtfSnapshot)).all()
    assert len(rows) == 0


@pytest.mark.asyncio
async def test_run_agent_prunes_old_etf_snapshots(mem_session_factory):
    import backend.cache as cache
    old_time = datetime.now(timezone.utc) - timedelta(days=15)
    with mem_session_factory() as db:
        db.add(EtfSnapshot(recorded_at=old_time, btc_flow=100.0, eth_flow=50.0, total_flow=150.0))
        db.commit()
    cache.put("etf_raw", _ETF_RAW)
    with patch("backend.agent.runner.DETECTORS", [_MockDetector()]), \
         patch("backend.agent.runner._refresh_panel_cache", new=AsyncMock()), \
         patch("backend.agent.runner.check_outcomes", new=AsyncMock()), \
         patch("backend.agent.runner.broadcast", new=AsyncMock()), \
         patch("backend.agent.runner.build_full_snapshot", return_value={}):
        await run_agent()
    with mem_session_factory() as db:
        rows = db.scalars(select(EtfSnapshot)).all()
    assert len(rows) == 1  # old row pruned, only the new row remains
    assert rows[0].btc_flow == 380_000_000.0


# ---------------------------------------------------------------------------
# GET /api/etf-history endpoint
# ---------------------------------------------------------------------------

@pytest.fixture
def test_client():
    """TestClient with StaticPool in-memory DB."""
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
        from fastapi.testclient import TestClient
        client = TestClient(app, raise_server_exceptions=True)
        yield client, Session


def test_etf_history_empty(test_client):
    client, _ = test_client
    resp = client.get("/api/etf-history")
    assert resp.status_code == 200
    assert resp.json() == {"etfHistory": []}


def test_etf_history_returns_rows(test_client):
    client, Session = test_client
    now = datetime.now(timezone.utc)
    with Session() as db:
        db.add(EtfSnapshot(recorded_at=now - timedelta(hours=2), btc_flow=300e6, eth_flow=100e6, total_flow=400e6))
        db.add(EtfSnapshot(recorded_at=now - timedelta(hours=1), btc_flow=380e6, eth_flow=120e6, total_flow=500e6))
        db.commit()
    resp = client.get("/api/etf-history")
    assert resp.status_code == 200
    data = resp.json()["etfHistory"]
    assert len(data) == 2
    assert data[0]["btcFlow"] == 300e6
    assert data[1]["btcFlow"] == 380e6
    assert "timestamp" in data[0]


def test_etf_history_hours_param_filters(test_client):
    client, Session = test_client
    now = datetime.now(timezone.utc)
    with Session() as db:
        db.add(EtfSnapshot(recorded_at=now - timedelta(hours=200), btc_flow=100e6, eth_flow=50e6, total_flow=150e6))
        db.add(EtfSnapshot(recorded_at=now - timedelta(hours=10), btc_flow=380e6, eth_flow=120e6, total_flow=500e6))
        db.commit()
    resp = client.get("/api/etf-history?hours=168")
    data = resp.json()["etfHistory"]
    assert len(data) == 1
    assert data[0]["btcFlow"] == 380e6


def test_etf_history_ordered_ascending(test_client):
    client, Session = test_client
    now = datetime.now(timezone.utc)
    with Session() as db:
        db.add(EtfSnapshot(recorded_at=now - timedelta(hours=3), btc_flow=100e6, eth_flow=50e6, total_flow=150e6))
        db.add(EtfSnapshot(recorded_at=now - timedelta(hours=1), btc_flow=380e6, eth_flow=120e6, total_flow=500e6))
        db.add(EtfSnapshot(recorded_at=now - timedelta(hours=2), btc_flow=200e6, eth_flow=80e6, total_flow=280e6))
        db.commit()
    resp = client.get("/api/etf-history")
    btc_flows = [r["btcFlow"] for r in resp.json()["etfHistory"]]
    assert btc_flows == [100e6, 200e6, 380e6]


def test_etf_history_default_168h_window(test_client):
    client, Session = test_client
    now = datetime.now(timezone.utc)
    with Session() as db:
        db.add(EtfSnapshot(recorded_at=now - timedelta(hours=169), btc_flow=50e6, eth_flow=20e6, total_flow=70e6))
        db.add(EtfSnapshot(recorded_at=now - timedelta(hours=100), btc_flow=380e6, eth_flow=120e6, total_flow=500e6))
        db.commit()
    resp = client.get("/api/etf-history")
    data = resp.json()["etfHistory"]
    assert len(data) == 1
    assert data[0]["btcFlow"] == 380e6


def test_etf_history_max_hours_clamp(test_client):
    client, _ = test_client
    resp = client.get("/api/etf-history?hours=9999")
    assert resp.status_code == 422  # FastAPI validation error — exceeds le=336
