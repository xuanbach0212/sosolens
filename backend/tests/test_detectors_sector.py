"""Unit tests for SectorRotationDetector (per-sector signal model)."""
import pytest
from unittest.mock import patch, AsyncMock
from backend.agent.detectors.sector_rotation import SectorRotationDetector


@pytest.fixture
def detector():
    return SectorRotationDetector()


def _sectors(*changes: tuple[str, float]) -> list[dict]:
    """Build sector-flow dicts; tokens kept simple for assertions."""
    return [
        {"name": name, "change": change, "arrows": "↑", "positive": change >= 0,
         "tokens": [name[:3].upper()]}
        for name, change in changes
    ]


async def test_emits_one_signal_per_sector(detector):
    sectors = _sectors(("AI", 5.0), ("DeFi", 1.0), ("Layer2", -3.0))
    with patch("backend.agent.detectors.sector_rotation.get_client") as mock_gc, \
         patch("backend.agent.detectors.sector_rotation.fetch_sector_flows", new=AsyncMock(return_value=sectors)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert len(signals) == 3
    assert {s["sector"] for s in signals} == {"AI", "DeFi", "Layer2"}


async def test_strong_positive_is_buy(detector):
    sectors = _sectors(("AI", 6.5))
    with patch("backend.agent.detectors.sector_rotation.get_client") as mock_gc, \
         patch("backend.agent.detectors.sector_rotation.fetch_sector_flows", new=AsyncMock(return_value=sectors)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert signals[0]["type"] == "BUY"


async def test_mild_change_is_watch(detector):
    sectors = _sectors(("DeFi", 1.5), ("RWA", -2.0))
    with patch("backend.agent.detectors.sector_rotation.get_client") as mock_gc, \
         patch("backend.agent.detectors.sector_rotation.fetch_sector_flows", new=AsyncMock(return_value=sectors)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert all(s["type"] == "WATCH" for s in signals)


async def test_strong_negative_is_avoid(detector):
    sectors = _sectors(("Layer2", -12.0))
    with patch("backend.agent.detectors.sector_rotation.get_client") as mock_gc, \
         patch("backend.agent.detectors.sector_rotation.fetch_sector_flows", new=AsyncMock(return_value=sectors)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert signals[0]["type"] == "AVOID"


async def test_tokens_passed_through(detector):
    sectors = [{"name": "AI", "change": 5.0, "arrows": "↑", "positive": True,
                "tokens": ["TAO", "WLD", "RENDER"]}]
    with patch("backend.agent.detectors.sector_rotation.get_client") as mock_gc, \
         patch("backend.agent.detectors.sector_rotation.fetch_sector_flows", new=AsyncMock(return_value=sectors)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    symbols = [t["symbol"] for t in signals[0]["topTokens"]]
    assert symbols == ["TAO", "WLD", "RENDER"]


async def test_buy_sets_sodex_pair_to_primary_token(detector):
    sectors = [{"name": "AI", "change": 6.0, "arrows": "↑", "positive": True, "tokens": ["TAO", "WLD"]}]
    with patch("backend.agent.detectors.sector_rotation.get_client") as mock_gc, \
         patch("backend.agent.detectors.sector_rotation.fetch_sector_flows", new=AsyncMock(return_value=sectors)):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert signals[0]["sodexPair"] == "BUY TAO/USDC"


async def test_fetch_error_returns_empty(detector):
    with patch("backend.agent.detectors.sector_rotation.get_client") as mock_gc, \
         patch("backend.agent.detectors.sector_rotation.fetch_sector_flows", side_effect=Exception("err")):
        mock_gc.return_value = AsyncMock()
        signals = await detector.run()
    assert signals == []
