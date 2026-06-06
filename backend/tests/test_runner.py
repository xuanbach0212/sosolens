"""Unit tests for signal persistence (upsert) in run_agent()."""
import time
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.agent.models import Base, Signal
from backend.agent.runner import run_agent


def _raw_signal(sig_type: str = "BUY") -> dict:
    return {
        "id": "etf-flow-spike",
        "type": sig_type,
        "sector": "Crypto",
        "timeAgo": "1h",
        "dataSources": [],
        "topTokens": [],
        "pastSignals": [],
        "accuracy": 75,
        "sodexPair": "BTC/USDC",
        "sodexSlippage": "0.3%",
        "sodexEstOutput": "0.00105 BTC",
    }


@pytest.fixture
def mem_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    @contextmanager
    def get_db():
        db = Session()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    return get_db, Session


async def test_insert_creates_one_row(mem_db):
    get_db, Session = mem_db
    raw = _raw_signal("BUY")
    mock_detector = AsyncMock()
    mock_detector.run = AsyncMock(return_value=[raw])

    with patch("backend.agent.runner.get_db", get_db), \
         patch("backend.agent.runner.DETECTORS", [mock_detector]), \
         patch("backend.agent.runner.explain_signal", new=AsyncMock(return_value="buy signal")), \
         patch("backend.agent.runner._refresh_panel_cache", new=AsyncMock()):
        await run_agent()

    with Session() as db:
        rows = db.query(Signal).all()
        assert len(rows) == 1
        row = rows[0]
        assert row.signal_id == "etf-flow-spike"
        assert row.type == "BUY"
        assert row.explanation == "buy signal"
        assert row.payload["type"] == "BUY"


async def test_upsert_does_not_duplicate(mem_db):
    get_db, Session = mem_db
    mock_detector = AsyncMock()

    for sig_type in ("BUY", "AVOID"):
        mock_detector.run = AsyncMock(return_value=[_raw_signal(sig_type)])
        with patch("backend.agent.runner.get_db", get_db), \
             patch("backend.agent.runner.DETECTORS", [mock_detector]), \
             patch("backend.agent.runner.explain_signal", new=AsyncMock(return_value="x")), \
             patch("backend.agent.runner._refresh_panel_cache", new=AsyncMock()):
            await run_agent()

    with Session() as db:
        rows = db.query(Signal).all()
    assert len(rows) == 1


async def test_run_agent_broadcasts(mem_db, monkeypatch):
    get_db_func, _ = mem_db
    monkeypatch.setattr("backend.agent.runner.get_db", get_db_func)
    mock_detector = AsyncMock()
    mock_detector.run = AsyncMock(return_value=[_raw_signal()])
    monkeypatch.setattr("backend.agent.runner.DETECTORS", [mock_detector])
    monkeypatch.setattr("backend.agent.runner.explain_signal", AsyncMock(return_value="test"))
    monkeypatch.setattr("backend.agent.runner._refresh_panel_cache", AsyncMock())

    broadcasts = []

    async def fake_broadcast(data):
        broadcasts.append(data)

    monkeypatch.setattr("backend.agent.runner.broadcast", fake_broadcast)

    await run_agent()
    assert len(broadcasts) == 1
    assert "signals" in broadcasts[0]
    assert "market" in broadcasts[0]


async def test_failing_detector_does_not_abort_loop(mem_db):
    """A detector that raises must not prevent subsequent detectors from running."""
    get_db, Session = mem_db
    bad_detector = AsyncMock()
    bad_detector.run = AsyncMock(side_effect=RuntimeError("API down"))
    good_detector = AsyncMock()
    good_detector.run = AsyncMock(return_value=[_raw_signal("BUY")])

    with patch("backend.agent.runner.get_db", get_db), \
         patch("backend.agent.runner.DETECTORS", [bad_detector, good_detector]), \
         patch("backend.agent.runner.explain_signal", new=AsyncMock(return_value="ok")), \
         patch("backend.agent.runner._refresh_panel_cache", new=AsyncMock()):
        await run_agent()

    with Session() as db:
        rows = db.query(Signal).all()
    assert len(rows) == 1, "good detector's signal should be persisted despite bad detector failing"


async def test_upsert_updates_fields(mem_db):
    get_db, Session = mem_db
    mock_detector = AsyncMock()

    mock_detector.run = AsyncMock(return_value=[_raw_signal("BUY")])
    with patch("backend.agent.runner.get_db", get_db), \
         patch("backend.agent.runner.DETECTORS", [mock_detector]), \
         patch("backend.agent.runner.explain_signal", new=AsyncMock(return_value="first")), \
         patch("backend.agent.runner._refresh_panel_cache", new=AsyncMock()):
        await run_agent()

    time.sleep(0.05)

    mock_detector.run = AsyncMock(return_value=[_raw_signal("AVOID")])
    with patch("backend.agent.runner.get_db", get_db), \
         patch("backend.agent.runner.DETECTORS", [mock_detector]), \
         patch("backend.agent.runner.explain_signal", new=AsyncMock(return_value="second")), \
         patch("backend.agent.runner._refresh_panel_cache", new=AsyncMock()):
        await run_agent()

    with Session() as db:
        row = db.query(Signal).first()
        assert row.type == "AVOID"
        assert row.explanation == "second"
        assert row.updated_at > row.created_at
