"""Unit tests for MacroRiskDetector."""
import pytest
from unittest.mock import patch, AsyncMock
from backend.agent.detectors.macro_risk import MacroRiskDetector


@pytest.fixture
def detector():
    return MacroRiskDetector()


def _events(days_until: int, high_impact: bool = True) -> list[dict]:
    return [{"days_until": days_until, "events": ["CPI Release"], "high_impact": high_impact}]


async def test_buy_signal_no_high_impact_events(detector):
    events = [{"days_until": 10, "events": ["Minor Release"], "high_impact": False}]
    with patch("backend.agent.detectors.macro_risk.get_client") as mock_gc, \
         patch("backend.agent.detectors.macro_risk.fetch_macro_events", new=AsyncMock(return_value=events)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "BUY"


async def test_watch_signal_high_impact_in_7_days(detector):
    with patch("backend.agent.detectors.macro_risk.get_client") as mock_gc, \
         patch("backend.agent.detectors.macro_risk.fetch_macro_events", new=AsyncMock(return_value=_events(6))):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "WATCH"


async def test_avoid_signal_high_impact_within_3_days(detector):
    with patch("backend.agent.detectors.macro_risk.get_client") as mock_gc, \
         patch("backend.agent.detectors.macro_risk.fetch_macro_events", new=AsyncMock(return_value=_events(2))):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "AVOID"


async def test_avoid_on_event_day(detector):
    with patch("backend.agent.detectors.macro_risk.get_client") as mock_gc, \
         patch("backend.agent.detectors.macro_risk.fetch_macro_events", new=AsyncMock(return_value=_events(0))):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert signals[0]["type"] == "AVOID"


async def test_empty_events_returns_no_signal(detector):
    with patch("backend.agent.detectors.macro_risk.get_client") as mock_gc, \
         patch("backend.agent.detectors.macro_risk.fetch_macro_events", new=AsyncMock(return_value=[])):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert signals == []


async def test_signal_has_required_fields(detector):
    with patch("backend.agent.detectors.macro_risk.get_client") as mock_gc, \
         patch("backend.agent.detectors.macro_risk.fetch_macro_events", new=AsyncMock(return_value=_events(6))):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    sig = signals[0]
    for field in ("id", "type", "sector", "dataSources", "topTokens"):
        assert field in sig


async def test_fetch_error_returns_empty(detector):
    with patch("backend.agent.detectors.macro_risk.get_client") as mock_gc, \
         patch("backend.agent.detectors.macro_risk.fetch_macro_events", side_effect=Exception("err")):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert signals == []
