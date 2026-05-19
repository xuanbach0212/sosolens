import logging
from backend.services.sosovalue import get_client
from backend.services.news import fetch_news_headlines

logger = logging.getLogger(__name__)

_BULLISH = frozenset([
    "rally", "surge", "gain", "rise", "record", "high", "bull",
    "institutional", "adoption", "approve", "launch", "inflow",
    "breakout", "accumulate", "positive", "milestone", "all-time",
])
_BEARISH = frozenset([
    "crash", "drop", "fall", "decline", "fear", "ban", "hack",
    "exploit", "breach", "regulation", "fine", "suspend", "halt",
    "warning", "bear", "outflow", "liquidat", "probe", "investigat",
    "sanction", "panic",
])

_TOKEN_MAP = {
    "BTC": ["btc", "bitcoin"],
    "ETH": ["eth", "ethereum"],
    "SOL": ["sol", "solana"],
    "BNB": ["bnb", "binance"],
    "XRP": ["xrp", "ripple"],
}

_BUY_THRESHOLD   =  3
_AVOID_THRESHOLD = -3


def _score_headline(text: str) -> int:
    lower = text.lower()
    return (
        sum(1 for kw in _BULLISH if kw in lower)
        - sum(1 for kw in _BEARISH if kw in lower)
    )


def _headline_signal(score: int) -> str:
    if score > 0:
        return "🟢"
    if score < 0:
        return "🔴"
    return "🟡"


def _extract_tokens(headlines: list[dict]) -> list[dict]:
    counts: dict[str, int] = {}
    for h in headlines:
        lower = h["text"].lower()
        for symbol, kws in _TOKEN_MAP.items():
            if any(kw in lower for kw in kws):
                counts[symbol] = counts.get(symbol, 0) + 1

    top = sorted(counts, key=lambda s: counts[s], reverse=True)
    for fallback in ("BTC", "ETH"):
        if len(top) >= 2:
            break
        if fallback not in top:
            top.append(fallback)

    return [
        {"symbol": sym, "price": "—", "change": "—", "positive": True}
        for sym in top[:2]
    ]


class NewsSentimentDetector:
    async def run(self) -> list[dict]:
        try:
            client = get_client()
            _, headlines, _ = await fetch_news_headlines(client)
        except Exception as exc:
            logger.warning("[news_sentiment] fetch failed: %s", exc)
            return []

        if len(headlines) < 2:
            logger.info("[news_sentiment] too few headlines (%d) — no signal", len(headlines))
            return []

        bullish_total = 0
        bearish_total = 0
        scored: list[tuple] = []
        for h in headlines:
            score = _score_headline(h["text"])
            weight = 2 if h.get("macroSensitive") else 1
            if score > 0:
                bullish_total += score * weight
            elif score < 0:
                bearish_total += abs(score) * weight
            scored.append((h, score))

        if bullish_total == 0 and bearish_total == 0:
            logger.info("[news_sentiment] no keywords matched — no signal")
            return []

        net = bullish_total - bearish_total

        if net >= _BUY_THRESHOLD:
            sig_type = "BUY"
        elif net <= _AVOID_THRESHOLD:
            sig_type = "AVOID"
        else:
            sig_type = "WATCH"

        data_sources = []
        for h, score in scored[:3]:
            text_short = h["text"][:40] + ("…" if len(h["text"]) > 40 else "")
            data_sources.append({
                "name": text_short,
                "value": h.get("source", "SoSoValue"),
                "signal": _headline_signal(score),
            })
        data_sources.append({
            "name": "Sentiment Balance",
            "value": f"Bullish {bullish_total} | Bearish {bearish_total}",
            "signal": "🟢" if net > 0 else ("🔴" if net < 0 else "🟡"),
            "arrow": "↑" if net > 0 else ("↓" if net < 0 else "→"),
        })

        top_tokens = _extract_tokens(headlines)

        logger.info("[news_sentiment] signal=%s net=%d bullish=%d bearish=%d",
                    sig_type, net, bullish_total, bearish_total)

        return [{
            "id": "news-sentiment",
            "type": sig_type,
            "sector": "Crypto News Sentiment",
            "timeAgo": "0h",
            "dataSources": data_sources,
            "topTokens": top_tokens,
            "pastSignals": [],
            "accuracy": 0,
            "sodexPair": "BUY BTC/USDC" if sig_type == "BUY" else "—",
            "sodexSlippage": "1%",
            "sodexEstOutput": "—",
        }]
