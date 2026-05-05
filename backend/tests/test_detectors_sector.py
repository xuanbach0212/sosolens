"""Unit tests for SectorRotationDetector."""
import pytest
from unittest.mock import patch, AsyncMock
from backend.agent.detectors.sector_rotation import SectorRotationDetector


@pytest.fixture
def detector():
    return SectorRotationDetector()


def _sector_data(leader_change: float, lagger_change: float) -> list[dict]:
    sectors = [
        {"name": "AI",    "change": leader_change, "arrows": "↑", "positive": leader_change >= 0},
        {"name": "DeFi",  "change": 1.0,           "arrows": "↑", "positive": True},
        {"name": "Layer2","change": lagger_change,  "arrows": "↓", "positive": lagger_change >= 0},
    ]
    return sorted(sectors, key=lambda x: x["change"], reverse=True)


async def test_buy_signal_large_spread(detector):
    sectors = _sector_data(leader_change=5.0, lagger_change=-3.0)
    with patch("backend.agent.detectors.sector_rotation.get_client") as mock_gc, \
         patch("backend.agent.detectors.sector_rotation.fetch_sector_flows", new=AsyncMock(return_value=sectors)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "BUY"


async def test_watch_signal_small_spread(detector):
    sectors = _sector_data(leader_change=1.5, lagger_change=-2.0)
    with patch("backend.agent.detectors.sector_rotation.get_client") as mock_gc, \
         patch("backend.agent.detectors.sector_rotation.fetch_sector_flows", new=AsyncMock(return_value=sectors)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "WATCH"


async def test_no_signal_flat_market(detector):
    sectors = _sector_data(leader_change=0.5, lagger_change=0.0)
    with patch("backend.agent.detectors.sector_rotation.get_client") as mock_gc, \
         patch("backend.agent.detectors.sector_rotation.fetch_sector_flows", new=AsyncMock(return_value=sectors)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert signals == []


async def test_no_signal_low_spread(detector):
    # leader above threshold but spread too small
    sectors = _sector_data(leader_change=3.0, lagger_change=2.0)
    with patch("backend.agent.detectors.sector_rotation.get_client") as mock_gc, \
         patch("backend.agent.detectors.sector_rotation.fetch_sector_flows", new=AsyncMock(return_value=sectors)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert signals == []


async def test_signal_sector_name_reflects_leader(detector):
    sectors = _sector_data(leader_change=5.0, lagger_change=-3.0)
    with patch("backend.agent.detectors.sector_rotation.get_client") as mock_gc, \
         patch("backend.agent.detectors.sector_rotation.fetch_sector_flows", new=AsyncMock(return_value=sectors)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert "AI" in signals[0]["sector"]


async def test_fetch_error_returns_empty(detector):
    with patch("backend.agent.detectors.sector_rotation.get_client") as mock_gc, \
         patch("backend.agent.detectors.sector_rotation.fetch_sector_flows", side_effect=Exception("err")):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert signals == []
