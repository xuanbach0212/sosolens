"""Unit tests for ETFFlowSpikeDetector."""
import pytest
from unittest.mock import patch, AsyncMock
from backend.agent.detectors.etf_flow_spike import ETFFlowSpikeDetector


@pytest.fixture
def detector():
    return ETFFlowSpikeDetector()


async def test_buy_signal_above_400m(detector):
    with patch("backend.agent.detectors.etf_flow_spike.get_client") as mock_gc, \
         patch("backend.agent.detectors.etf_flow_spike.fetch_etf_total_flow", new=AsyncMock(return_value=541_000_000)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "BUY"


async def test_watch_signal_between_150m_and_400m(detector):
    with patch("backend.agent.detectors.etf_flow_spike.get_client") as mock_gc, \
         patch("backend.agent.detectors.etf_flow_spike.fetch_etf_total_flow", new=AsyncMock(return_value=200_000_000)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "WATCH"


async def test_avoid_signal_below_neg200m(detector):
    with patch("backend.agent.detectors.etf_flow_spike.get_client") as mock_gc, \
         patch("backend.agent.detectors.etf_flow_spike.fetch_etf_total_flow", new=AsyncMock(return_value=-250_000_000)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "AVOID"


async def test_no_signal_within_normal_range(detector):
    with patch("backend.agent.detectors.etf_flow_spike.get_client") as mock_gc, \
         patch("backend.agent.detectors.etf_flow_spike.fetch_etf_total_flow", new=AsyncMock(return_value=50_000_000)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert signals == []


async def test_no_signal_small_negative(detector):
    with patch("backend.agent.detectors.etf_flow_spike.get_client") as mock_gc, \
         patch("backend.agent.detectors.etf_flow_spike.fetch_etf_total_flow", new=AsyncMock(return_value=-100_000_000)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert signals == []


async def test_signal_has_required_fields(detector):
    with patch("backend.agent.detectors.etf_flow_spike.get_client") as mock_gc, \
         patch("backend.agent.detectors.etf_flow_spike.fetch_etf_total_flow", new=AsyncMock(return_value=500_000_000)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    sig = signals[0]
    for field in ("id", "type", "sector", "dataSources", "topTokens", "pastSignals"):
        assert field in sig


async def test_fetch_error_returns_empty(detector):
    with patch("backend.agent.detectors.etf_flow_spike.get_client") as mock_gc, \
         patch("backend.agent.detectors.etf_flow_spike.fetch_etf_total_flow", side_effect=Exception("err")):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert signals == []
