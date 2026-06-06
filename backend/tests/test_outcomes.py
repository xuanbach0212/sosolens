"""Tests for signal outcome tracking (#28)."""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from backend.agent.models import Base, SignalOutcome
from backend.agent.runner import (
    _record_signal_entries,
    _enrich_with_outcomes,
    _fmt_outcome,
    check_outcomes,
)


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
def patch_get_db(mem_session_factory):
    """Redirect all get_db() calls to the in-memory DB."""
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
# _record_signal_entries
# ---------------------------------------------------------------------------

def test_record_entry_inserts_row(mem_session_factory):
    _record_signal_entries({"etf-flow-spike": "BUY"}, 95000.0)
    with mem_session_factory() as db:
        rows = db.scalars(select(SignalOutcome)).all()
    assert len(rows) == 1
    assert rows[0].detector_id == "etf-flow-spike"
    assert rows[0].signal_type == "BUY"
    assert rows[0].entry_price == 95000.0
    assert rows[0].outcome is None


def test_record_entry_skips_within_20h(mem_session_factory):
    _record_signal_entries({"etf-flow-spike": "BUY"}, 95000.0)
    _record_signal_entries({"etf-flow-spike": "BUY"}, 96000.0)  # same detector, <20h later
    with mem_session_factory() as db:
        rows = db.scalars(select(SignalOutcome)).all()
    assert len(rows) == 1  # no duplicate


def test_record_entry_inserts_after_20h(mem_session_factory):
    # Insert a row with recorded_at 21h ago
    old_time = datetime.now(timezone.utc) - timedelta(hours=21)
    with mem_session_factory() as db:
        db.add(SignalOutcome(
            detector_id="etf-flow-spike",
            signal_type="BUY",
            recorded_at=old_time,
            entry_price=90000.0,
        ))
        db.commit()
    _record_signal_entries({"etf-flow-spike": "AVOID"}, 88000.0)
    with mem_session_factory() as db:
        rows = db.scalars(select(SignalOutcome)).all()
    assert len(rows) == 2


def test_watch_signal_recorded_as_skip(mem_session_factory):
    _record_signal_entries({"macro-risk-classifier": "WATCH"}, 95000.0)
    with mem_session_factory() as db:
        rows = db.scalars(select(SignalOutcome)).all()
    assert len(rows) == 1
    assert rows[0].outcome == "SKIP"


def test_multiple_detectors_all_inserted(mem_session_factory):
    _record_signal_entries({
        "etf-flow-spike": "BUY",
        "sector-rotation": "WATCH",
        "macro-risk-classifier": "AVOID",
    }, 95000.0)
    with mem_session_factory() as db:
        rows = db.scalars(select(SignalOutcome)).all()
    assert len(rows) == 3


# ---------------------------------------------------------------------------
# check_outcomes
# ---------------------------------------------------------------------------

def _insert_pending(session_factory, signal_type, entry_price, hours_ago=25):
    recorded = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    with session_factory() as db:
        db.add(SignalOutcome(
            detector_id="etf-flow-spike",
            signal_type=signal_type,
            recorded_at=recorded,
            entry_price=entry_price,
        ))
        db.commit()


@pytest.mark.asyncio
async def test_check_outcomes_resolves_buy_win(mem_session_factory):
    _insert_pending(mem_session_factory, "BUY", 90000.0)
    with patch("backend.services.currency.fetch_btc_price_usd", new=AsyncMock(return_value=95000.0)), \
         patch("backend.services.sosovalue.get_client", return_value=AsyncMock()):
        await check_outcomes()
    with mem_session_factory() as db:
        row = db.scalars(select(SignalOutcome)).first()
    assert row.outcome == "WIN"
    assert row.exit_price == 95000.0


@pytest.mark.asyncio
async def test_check_outcomes_resolves_buy_loss(mem_session_factory):
    _insert_pending(mem_session_factory, "BUY", 90000.0)
    with patch("backend.services.currency.fetch_btc_price_usd", new=AsyncMock(return_value=85000.0)), \
         patch("backend.services.sosovalue.get_client", return_value=AsyncMock()):
        await check_outcomes()
    with mem_session_factory() as db:
        row = db.scalars(select(SignalOutcome)).first()
    assert row.outcome == "LOSS"


@pytest.mark.asyncio
async def test_check_outcomes_resolves_avoid_win(mem_session_factory):
    _insert_pending(mem_session_factory, "AVOID", 90000.0)
    with patch("backend.services.currency.fetch_btc_price_usd", new=AsyncMock(return_value=85000.0)), \
         patch("backend.services.sosovalue.get_client", return_value=AsyncMock()):
        await check_outcomes()
    with mem_session_factory() as db:
        row = db.scalars(select(SignalOutcome)).first()
    assert row.outcome == "WIN"


@pytest.mark.asyncio
async def test_check_outcomes_resolves_avoid_loss(mem_session_factory):
    _insert_pending(mem_session_factory, "AVOID", 90000.0)
    with patch("backend.services.currency.fetch_btc_price_usd", new=AsyncMock(return_value=95000.0)), \
         patch("backend.services.sosovalue.get_client", return_value=AsyncMock()):
        await check_outcomes()
    with mem_session_factory() as db:
        row = db.scalars(select(SignalOutcome)).first()
    assert row.outcome == "LOSS"


@pytest.mark.asyncio
async def test_check_outcomes_skips_young_rows(mem_session_factory):
    _insert_pending(mem_session_factory, "BUY", 90000.0, hours_ago=2)  # younger than the 4h horizon
    with patch("backend.services.currency.fetch_btc_price_usd", new=AsyncMock(return_value=95000.0)), \
         patch("backend.services.sosovalue.get_client", return_value=AsyncMock()):
        await check_outcomes()
    with mem_session_factory() as db:
        row = db.scalars(select(SignalOutcome)).first()
    assert row.outcome is None  # untouched


@pytest.mark.asyncio
async def test_check_outcomes_handles_price_failure(mem_session_factory):
    _insert_pending(mem_session_factory, "BUY", 90000.0)
    with patch("backend.services.currency.fetch_btc_price_usd", new=AsyncMock(side_effect=Exception("API down"))), \
         patch("backend.services.sosovalue.get_client", return_value=AsyncMock()):
        await check_outcomes()  # must not raise
    with mem_session_factory() as db:
        row = db.scalars(select(SignalOutcome)).first()
    assert row.outcome is None  # still pending


@pytest.mark.asyncio
async def test_check_outcomes_does_not_touch_skip_rows(mem_session_factory):
    recorded = datetime.now(timezone.utc) - timedelta(hours=25)
    with mem_session_factory() as db:
        db.add(SignalOutcome(
            detector_id="macro-risk-classifier",
            signal_type="WATCH",
            recorded_at=recorded,
            entry_price=90000.0,
            outcome="SKIP",
        ))
        db.commit()
    with patch("backend.services.currency.fetch_btc_price_usd", new=AsyncMock(return_value=95000.0)), \
         patch("backend.services.sosovalue.get_client", return_value=AsyncMock()):
        await check_outcomes()
    with mem_session_factory() as db:
        row = db.scalars(select(SignalOutcome)).first()
    assert row.outcome == "SKIP"  # unchanged
    assert row.exit_price is None


# ---------------------------------------------------------------------------
# _enrich_with_outcomes
# ---------------------------------------------------------------------------

def test_enrich_with_outcomes_no_history(mem_session_factory):
    payloads = [{"id": "etf-flow-spike", "accuracy": 0, "pastSignals": []}]
    with mem_session_factory() as db:
        result, global_acc = _enrich_with_outcomes(db, payloads)
    assert global_acc == 0
    assert result[0]["accuracy"] == 0
    assert result[0]["pastSignals"] == []


def test_enrich_with_outcomes_accuracy(mem_session_factory):
    now = datetime.now(timezone.utc)
    with mem_session_factory() as db:
        db.add(SignalOutcome(detector_id="etf-flow-spike", signal_type="BUY",
                             recorded_at=now - timedelta(days=3), entry_price=90000,
                             exit_price=95000, resolved_at=now, outcome="WIN"))
        db.add(SignalOutcome(detector_id="etf-flow-spike", signal_type="BUY",
                             recorded_at=now - timedelta(days=2), entry_price=92000,
                             exit_price=94000, resolved_at=now, outcome="WIN"))
        db.add(SignalOutcome(detector_id="etf-flow-spike", signal_type="AVOID",
                             recorded_at=now - timedelta(days=1), entry_price=94000,
                             exit_price=95000, resolved_at=now, outcome="LOSS"))
        db.commit()
        payloads = [{"id": "etf-flow-spike", "accuracy": 0, "pastSignals": []}]
        result, global_acc = _enrich_with_outcomes(db, payloads)
    assert result[0]["accuracy"] == 67  # 2 WIN / 3 total
    assert global_acc == 67
    assert len(result[0]["pastSignals"]) == 3


def test_enrich_skips_skip_in_accuracy(mem_session_factory):
    now = datetime.now(timezone.utc)
    with mem_session_factory() as db:
        db.add(SignalOutcome(detector_id="macro-risk-classifier", signal_type="WATCH",
                             recorded_at=now - timedelta(days=1), entry_price=90000,
                             outcome="SKIP"))
        db.add(SignalOutcome(detector_id="macro-risk-classifier", signal_type="BUY",
                             recorded_at=now - timedelta(days=2), entry_price=88000,
                             exit_price=92000, resolved_at=now, outcome="WIN"))
        db.commit()
        payloads = [{"id": "macro-risk-classifier", "accuracy": 0, "pastSignals": []}]
        result, global_acc = _enrich_with_outcomes(db, payloads)
    assert result[0]["accuracy"] == 100  # SKIP not counted; 1 WIN / 1 scored
    # SIMILAR PAST SIGNALS shows only resolved WIN/LOSS rows — the SKIP (a WATCH
    # non-event) is excluded so it can't render as a misleading "— ✗" entry.
    assert len(result[0]["pastSignals"]) == 1
    assert result[0]["pastSignals"][0]["label"] == "BUY"


def test_enrich_isolates_per_detector(mem_session_factory):
    now = datetime.now(timezone.utc)
    with mem_session_factory() as db:
        db.add(SignalOutcome(detector_id="etf-flow-spike", signal_type="BUY",
                             recorded_at=now - timedelta(days=1), entry_price=90000,
                             exit_price=95000, resolved_at=now, outcome="WIN"))
        db.add(SignalOutcome(detector_id="sector-rotation", signal_type="AVOID",
                             recorded_at=now - timedelta(days=1), entry_price=90000,
                             exit_price=95000, resolved_at=now, outcome="LOSS"))
        db.commit()
        payloads = [
            {"id": "etf-flow-spike",  "accuracy": 0, "pastSignals": []},
            {"id": "sector-rotation", "accuracy": 0, "pastSignals": []},
        ]
        result, global_acc = _enrich_with_outcomes(db, payloads)
    etf = next(p for p in result if p["id"] == "etf-flow-spike")
    sec = next(p for p in result if p["id"] == "sector-rotation")
    assert etf["accuracy"] == 100
    assert sec["accuracy"] == 0
    assert global_acc == 50  # 1 WIN + 1 LOSS globally


# ---------------------------------------------------------------------------
# _fmt_outcome
# ---------------------------------------------------------------------------

def test_fmt_outcome_win():
    now = datetime.now(timezone.utc)
    o = SignalOutcome(
        detector_id="etf-flow-spike", signal_type="BUY",
        recorded_at=now, entry_price=90000.0,
        exit_price=95000.0, outcome="WIN",
    )
    result = _fmt_outcome(o)
    assert result["success"] is True
    assert result["label"] == "BUY"
    assert result["result"] == "+5.6%"


def test_fmt_outcome_loss():
    now = datetime.now(timezone.utc)
    o = SignalOutcome(
        detector_id="etf-flow-spike", signal_type="BUY",
        recorded_at=now, entry_price=90000.0,
        exit_price=85000.0, outcome="LOSS",
    )
    result = _fmt_outcome(o)
    assert result["success"] is False
    assert result["result"] == "-5.6%"


def test_fmt_outcome_skip():
    now = datetime.now(timezone.utc)
    o = SignalOutcome(
        detector_id="macro-risk-classifier", signal_type="WATCH",
        recorded_at=now, entry_price=90000.0,
        outcome="SKIP",
    )
    result = _fmt_outcome(o)
    assert result["result"] == "—"
    assert result["success"] is False
