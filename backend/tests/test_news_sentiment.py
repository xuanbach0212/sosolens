"""Unit tests for NewsSentimentDetector."""
import pytest
from unittest.mock import patch, AsyncMock
from backend.agent.detectors.news_sentiment import NewsSentimentDetector


@pytest.fixture
def detector():
    return NewsSentimentDetector()


def _headlines(*items):
    """Build headline list from (text, macroSensitive) tuples."""
    return [{"text": t, "source": "Test", "macroSensitive": m} for t, m in items]


def _patch(headlines):
    return (
        patch("backend.agent.detectors.news_sentiment.get_client"),
        patch(
            "backend.agent.detectors.news_sentiment.fetch_news_headlines",
            new=AsyncMock(return_value=([], headlines, [])),
        ),
    )


# --- Signal type classification ---

async def test_bullish_headlines_return_buy(detector):
    h = _headlines(
        ("Bitcoin surges to record high after institutional adoption", False),
        ("ETH rally breakout and inflow continue rising", False),
        ("Markets rise with positive momentum and gains", False),
    )
    gc, news = _patch(h)
    with gc, news:
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "BUY"


async def test_bearish_headlines_return_avoid(detector):
    h = _headlines(
        ("Bitcoin crash and hack exploit causes market fear", False),
        ("Regulation ban leads to price drop and decline", False),
        ("Bear market outflow as assets fall sharply", False),
    )
    gc, news = _patch(h)
    with gc, news:
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "AVOID"


async def test_mixed_headlines_return_watch(detector):
    h = _headlines(
        ("Bitcoin surges to new record high today", False),
        ("Crypto regulation warning issued by authorities", False),
        ("Market observers await further developments this week", False),
    )
    gc, news = _patch(h)
    with gc, news:
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "WATCH"


# --- Macro weight ---

async def test_macro_sensitive_headline_doubles_weight(detector):
    # H1: "surge" + "record" = bullish_score=2, weight=1 → bullish_total=2
    # H2: "crash" + "decline" + "fear" = bearish_score=3, weight=2 (macro) → bearish_total=6
    # net = 2-6 = -4 <= -3 → AVOID
    h = _headlines(
        ("Bitcoin surges record performance today", False),
        ("Federal Reserve crash decline fear spreads", True),
    )
    gc, news = _patch(h)
    with gc, news:
        signals = await detector.run()
    assert len(signals) == 1
    assert signals[0]["type"] == "AVOID"


# --- Edge cases: empty / insufficient data ---

async def test_fewer_than_two_headlines_returns_empty(detector):
    h = _headlines(("Bitcoin surges to record high rally", False))
    gc, news = _patch(h)
    with gc, news:
        signals = await detector.run()
    assert signals == []


async def test_empty_headlines_returns_empty(detector):
    gc, news = _patch([])
    with gc, news:
        signals = await detector.run()
    assert signals == []


async def test_no_keywords_matched_returns_empty(detector):
    h = _headlines(
        ("Developers discuss protocol governance at weekly meeting", False),
        ("Analysts review conditions for upcoming quarter results", False),
        ("Tech teams present roadmap updates at developer conference", False),
    )
    gc, news = _patch(h)
    with gc, news:
        signals = await detector.run()
    assert signals == []


async def test_fetch_failure_returns_empty(detector):
    gc = patch("backend.agent.detectors.news_sentiment.get_client")
    news = patch(
        "backend.agent.detectors.news_sentiment.fetch_news_headlines",
        new=AsyncMock(side_effect=Exception("network error")),
    )
    with gc, news:
        signals = await detector.run()
    assert signals == []


# --- Signal shape ---

async def test_signal_has_required_fields(detector):
    h = _headlines(
        ("Bitcoin surges to record high after institutional adoption rally", False),
        ("ETH gains breakout inflow positive momentum", False),
    )
    gc, news = _patch(h)
    with gc, news:
        signals = await detector.run()
    sig = signals[0]
    for field in (
        "id", "type", "sector",
        "timeAgo", "dataSources", "topTokens", "pastSignals",
        "accuracy", "sodexPair", "sodexSlippage", "sodexEstOutput",
    ):
        assert field in sig, f"missing field: {field}"


async def test_signal_id_is_fixed(detector):
    h = _headlines(
        ("Bitcoin surges record high rally", False),
        ("ETH inflow institutional adoption gains", False),
    )
    gc, news = _patch(h)
    with gc, news:
        signals = await detector.run()
    assert signals[0]["id"] == "news-sentiment"


async def test_data_sources_contains_sentiment_balance_row(detector):
    h = _headlines(
        ("Bitcoin surges record high rally", False),
        ("ETH inflow institutional adoption", False),
    )
    gc, news = _patch(h)
    with gc, news:
        signals = await detector.run()
    names = [d["name"] for d in signals[0]["dataSources"]]
    assert "Sentiment Balance" in names


async def test_data_sources_rows_have_required_keys(detector):
    h = _headlines(
        ("Bitcoin surges record high rally", False),
        ("ETH inflow institutional adoption", False),
    )
    gc, news = _patch(h)
    with gc, news:
        signals = await detector.run()
    for row in signals[0]["dataSources"]:
        assert "name" in row
        assert "value" in row
        assert "signal" in row


# --- Token extraction ---

async def test_top_tokens_extracted_from_bitcoin_eth_mentions(detector):
    h = _headlines(
        ("Bitcoin BTC surges to record high breakout rally", False),
        ("Ethereum ETH gains momentum institutional inflow", False),
    )
    gc, news = _patch(h)
    with gc, news:
        signals = await detector.run()
    symbols = {t["symbol"] for t in signals[0]["topTokens"]}
    assert "BTC" in symbols
    assert "ETH" in symbols


async def test_top_tokens_always_returns_two(detector):
    h = _headlines(
        ("DeFi protocol gains traction with new adoption launch", False),
        ("Blockchain ecosystem sees record rally and inflow surge", False),
    )
    gc, news = _patch(h)
    with gc, news:
        signals = await detector.run()
    assert len(signals[0]["topTokens"]) == 2


# --- SoDEX pair ---

async def test_buy_signal_sets_sodex_pair(detector):
    h = _headlines(
        ("Bitcoin surges record high institutional adoption rally inflow", False),
        ("ETH gains breakout positive milestone accumulate", False),
    )
    gc, news = _patch(h)
    with gc, news:
        signals = await detector.run()
    assert signals[0]["type"] == "BUY"
    assert signals[0]["sodexPair"] == "BUY BTC/USDC"


async def test_avoid_signal_clears_sodex_pair(detector):
    h = _headlines(
        ("Bitcoin crash hack exploit causes fear and decline", False),
        ("Regulation ban and outflow as markets fall and drop", False),
    )
    gc, news = _patch(h)
    with gc, news:
        signals = await detector.run()
    assert signals[0]["type"] == "AVOID"
    assert signals[0]["sodexPair"] == "—"
