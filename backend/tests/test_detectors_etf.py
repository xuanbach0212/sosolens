"""Unit tests for ETFFlowSpikeDetector."""
import pytest
from unittest.mock import patch, AsyncMock
from backend.agent.detectors.etf_flow_spike import ETFFlowSpikeDetector

_PLACEHOLDER_TOKEN = {"symbol": "BTC", "price": "—", "change": "—", "positive": True}
_SNAPSHOT = []


@pytest.fixture
def detector():
    return ETFFlowSpikeDetector()


def _patch(total: float, raise_error: bool = False):
    """Context managers patching get_client and fetch_etf_data.

    The detector builds topTokens via token_from_cache (reads the cache),
    so no price-fetch patch is needed."""
    etf_mock = AsyncMock(side_effect=Exception("err") if raise_error else None,
                         return_value=(_SNAPSHOT, total, total * 0.75, total * 0.25))
    return (
        patch("backend.agent.detectors.etf_flow_spike.get_client"),
        patch("backend.agent.detectors.etf_flow_spike.fetch_etf_data", new=etf_mock),
    )


async def test_buy_signal_above_400m(detector):
    gc, etf = _patch(541_000_000)
    with gc, etf:
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "BUY"


async def test_watch_signal_between_50m_and_400m(detector):
    gc, etf = _patch(200_000_000)
    with gc, etf:
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "WATCH"


async def test_avoid_signal_below_neg200m(detector):
    gc, etf = _patch(-250_000_000)
    with gc, etf:
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "AVOID"


async def test_watch_signal_moderate_negative(detector):
    gc, etf = _patch(-100_000_000)
    with gc, etf:
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "WATCH"


async def test_no_signal_within_normal_range(detector):
    gc, etf = _patch(30_000_000)
    with gc, etf:
        signals = await detector.run()
    assert signals == []


async def test_signal_has_required_fields(detector):
    gc, etf = _patch(500_000_000)
    with gc, etf:
        signals = await detector.run()
    sig = signals[0]
    for field in (
        "id", "type", "sector",
        "timeAgo", "dataSources", "topTokens", "pastSignals",
        "accuracy", "sodexPair", "sodexSlippage", "sodexEstOutput",
    ):
        assert field in sig


async def test_avoid_signal_has_bearish_metadata(detector):
    gc, etf = _patch(-250_000_000)
    with gc, etf:
        signals = await detector.run()
    sig = signals[0]
    tier_entry = next(d for d in sig["dataSources"] if d["name"] == "Signal Tier")
    assert tier_entry["signal"] == "🔴"


async def test_fetch_error_returns_empty(detector):
    gc, etf = _patch(0, raise_error=True)
    with gc, etf:
        signals = await detector.run()
    assert signals == []
