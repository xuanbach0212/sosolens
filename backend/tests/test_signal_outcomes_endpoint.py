"""Tests for GET /api/signal-outcomes endpoint (#55)."""
import pytest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from backend.agent.models import Base, SignalOutcome
from backend.main import app


# ---------------------------------------------------------------------------
# In-memory DB fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def mem_db_engine():
    # StaticPool keeps one connection so the in-memory DB is shared across threads
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def mem_session_factory(mem_db_engine):
    return sessionmaker(bind=mem_db_engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def patch_main_get_db(mem_session_factory):
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

    with patch("backend.main.get_db", _mem_get_db):
        yield


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _add_outcome(session_factory, detector_id, signal_type, outcome, hours_ago=1.0):
    recorded = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    with session_factory() as db:
        db.add(SignalOutcome(
            detector_id=detector_id,
            signal_type=signal_type,
            recorded_at=recorded,
            entry_price=90000.0,
            outcome=outcome,
        ))
        db.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_empty_returns_empty_list(client):
    resp = client.get("/api/signal-outcomes")
    assert resp.status_code == 200
    assert resp.json() == {"signalOutcomes": []}


def test_returns_outcome_within_window(client, mem_session_factory):
    _add_outcome(mem_session_factory, "etf-flow-spike", "BUY", "WIN", hours_ago=2)
    resp = client.get("/api/signal-outcomes?hours=48")
    data = resp.json()["signalOutcomes"]
    assert len(data) == 1
    assert data[0]["detectorId"] == "etf-flow-spike"
    assert data[0]["signalType"] == "BUY"
    assert data[0]["outcome"] == "WIN"


def test_excludes_outcome_older_than_window(client, mem_session_factory):
    _add_outcome(mem_session_factory, "etf-flow-spike", "BUY", "WIN", hours_ago=50)
    resp = client.get("/api/signal-outcomes?hours=48")
    assert resp.json()["signalOutcomes"] == []


def test_pending_outcome_serialized_as_pending(client, mem_session_factory):
    _add_outcome(mem_session_factory, "macro-risk", "AVOID", None, hours_ago=1)
    data = client.get("/api/signal-outcomes").json()["signalOutcomes"]
    assert len(data) == 1
    assert data[0]["outcome"] == "PENDING"


def test_hours_param_respected(client, mem_session_factory):
    _add_outcome(mem_session_factory, "etf-flow-spike", "BUY", "WIN",  hours_ago=5)
    _add_outcome(mem_session_factory, "macro-risk",     "AVOID", "LOSS", hours_ago=25)
    resp = client.get("/api/signal-outcomes?hours=10")
    data = resp.json()["signalOutcomes"]
    assert len(data) == 1
    assert data[0]["detectorId"] == "etf-flow-spike"


def test_results_ordered_oldest_first(client, mem_session_factory):
    _add_outcome(mem_session_factory, "b-detector", "BUY",   "WIN",  hours_ago=10)
    _add_outcome(mem_session_factory, "a-detector", "AVOID", "LOSS", hours_ago=5)
    data = client.get("/api/signal-outcomes").json()["signalOutcomes"]
    assert len(data) == 2
    assert data[0]["detectorId"] == "b-detector"
    assert data[1]["detectorId"] == "a-detector"


def test_skip_outcome_included(client, mem_session_factory):
    _add_outcome(mem_session_factory, "sector-rotation", "WATCH", "SKIP", hours_ago=3)
    data = client.get("/api/signal-outcomes").json()["signalOutcomes"]
    assert len(data) == 1
    assert data[0]["outcome"] == "SKIP"
