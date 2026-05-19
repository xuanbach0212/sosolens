"""Unit tests for BtcAccumulationDetector."""
import pytest
from unittest.mock import patch, AsyncMock
from backend.agent.detectors.btc_accumulation import BtcAccumulationDetector

_ENTRY = lambda company, change, positive: {
    "company": company, "btcHeld": "10,000 BTC", "weeklyChange": change, "positive": positive
}

# net = +1,282 + 200 = +1,482 >= 1,000 → BUY
_STRONG_BUY = [
    _ENTRY("MicroStrategy", "+1,282", True),
    _ENTRY("Marathon", "+200", True),
    _ENTRY("Tesla", "±0", None),
]

# net = -600 <= -500 → AVOID
_AVOID = [
    _ENTRY("MicroStrategy", "-600", False),
    _ENTRY("Marathon", "±0", None),
    _ENTRY("Tesla", "±0", None),
]

# net = +500, 0 < 500 < 1,000 → WATCH
_WATCH_POS = [
    _ENTRY("MicroStrategy", "+500", True),
    _ENTRY("Marathon", "±0", None),
    _ENTRY("Tesla", "±0", None),
]

# net = -200, -500 < -200 < 0 → WATCH
_WATCH_NEG = [
    _ENTRY("MicroStrategy", "-200", False),
    _ENTRY("Marathon", "±0", None),
    _ENTRY("Tesla", "±0", None),
]

# net = 0 → no signal
_ALL_ZERO = [
    _ENTRY("MicroStrategy", "±0", None),
    _ENTRY("Marathon", "±0", None),
]


@pytest.fixture
def detector():
    return BtcAccumulationDetector()


def _patch(data, raise_error=False):
    return (
        patch("backend.agent.detectors.btc_accumulation.get_client"),
        patch(
            "backend.agent.detectors.btc_accumulation.fetch_btc_treasuries",
            new=AsyncMock(
                side_effect=Exception("err") if raise_error else None,
                return_value=data,
            ),
        ),
    )


# --- Signal type classification ---

async def test_buy_signal_strong_accumulation(detector):
    gc, fetch = _patch(_STRONG_BUY)
    with gc, fetch:
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "BUY"


async def test_avoid_signal_net_negative(detector):
    gc, fetch = _patch(_AVOID)
    with gc, fetch:
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "AVOID"


async def test_watch_signal_mild_positive(detector):
    gc, fetch = _patch(_WATCH_POS)
    with gc, fetch:
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "WATCH"


async def test_watch_signal_mild_negative(detector):
    gc, fetch = _patch(_WATCH_NEG)
    with gc, fetch:
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "WATCH"


# --- No-signal guards ---

async def test_no_signal_all_zero(detector):
    gc, fetch = _patch(_ALL_ZERO)
    with gc, fetch:
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "WATCH"


async def test_no_signal_fewer_than_two_entries(detector):
    gc, fetch = _patch([_ENTRY("MicroStrategy", "+1,500", True)])
    with gc, fetch:
        signals = await detector.run()
    assert signals == []


async def test_no_signal_empty_data(detector):
    gc, fetch = _patch([])
    with gc, fetch:
        signals = await detector.run()
    assert signals == []


async def test_fetch_error_returns_empty(detector):
    gc, fetch = _patch([], raise_error=True)
    with gc, fetch:
        signals = await detector.run()
    assert signals == []


# --- Signal shape ---

async def test_signal_has_required_fields(detector):
    gc, fetch = _patch(_STRONG_BUY)
    with gc, fetch:
        signals = await detector.run()
    sig = signals[0]
    for field in (
        "id", "type", "sector",
        "timeAgo", "dataSources", "topTokens", "pastSignals",
        "accuracy", "sodexPair", "sodexSlippage", "sodexEstOutput",
    ):
        assert field in sig, f"missing field: {field}"


async def test_signal_id_is_fixed(detector):
    gc, fetch = _patch(_STRONG_BUY)
    with gc, fetch:
        signals = await detector.run()
    assert signals[0]["id"] == "btc-accumulation"


async def test_datasources_has_three_rows(detector):
    gc, fetch = _patch(_STRONG_BUY)
    with gc, fetch:
        signals = await detector.run()
    assert len(signals[0]["dataSources"]) == 3


async def test_datasources_rows_have_required_keys(detector):
    gc, fetch = _patch(_STRONG_BUY)
    with gc, fetch:
        signals = await detector.run()
    for row in signals[0]["dataSources"]:
        assert "name" in row
        assert "value" in row
        assert "signal" in row


# --- SoDEX pair ---

async def test_buy_sets_sodex_pair(detector):
    gc, fetch = _patch(_STRONG_BUY)
    with gc, fetch:
        signals = await detector.run()
    assert signals[0]["type"] == "BUY"
    assert signals[0]["sodexPair"] == "BUY BTC/USDC"


async def test_avoid_clears_sodex_pair(detector):
    gc, fetch = _patch(_AVOID)
    with gc, fetch:
        signals = await detector.run()
    assert signals[0]["type"] == "AVOID"
    assert signals[0]["sodexPair"] == "—"


async def test_watch_clears_sodex_pair(detector):
    gc, fetch = _patch(_WATCH_POS)
    with gc, fetch:
        signals = await detector.run()
    assert signals[0]["type"] == "WATCH"
    assert signals[0]["sodexPair"] == "—"


# --- dataSources signals ---

async def test_buy_net_delta_signal_is_green(detector):
    gc, fetch = _patch(_STRONG_BUY)
    with gc, fetch:
        signals = await detector.run()
    net_row = next(d for d in signals[0]["dataSources"] if d["name"] == "Net Weekly Δ")
    assert net_row["signal"] == "🟢"


async def test_avoid_net_delta_signal_is_red(detector):
    gc, fetch = _patch(_AVOID)
    with gc, fetch:
        signals = await detector.run()
    net_row = next(d for d in signals[0]["dataSources"] if d["name"] == "Net Weekly Δ")
    assert net_row["signal"] == "🔴"


# --- topTokens ---

async def test_toptokens_always_includes_btc(detector):
    gc, fetch = _patch(_STRONG_BUY)
    with gc, fetch:
        signals = await detector.run()
    symbols = {t["symbol"] for t in signals[0]["topTokens"]}
    assert "BTC" in symbols
