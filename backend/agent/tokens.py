"""Shared helper: build a topTokens entry with live BTC/ETH prices from cache."""
import backend.cache as cache


def token_from_cache(symbol: str, positive: bool, change_override: str | None = None) -> dict:
    """Return a topTokens entry for the signal payload.

    BTC/ETH price and change come from the market_status cache (live SoSoValue data).
    Other symbols fall back to the token_prices cache (CoinGecko top-250, hourly),
    so TOP TOKENS shows real prices for sector/signal tokens too. A caller-supplied
    change_override (e.g. a sector's roi_7d) always wins over the token's own 24h
    change. Symbols absent from both caches (e.g. equities like MSTR) stay "—".
    """
    market = cache.get("market_status") or {}
    if symbol == "BTC":
        return {
            "symbol": "BTC",
            "price": market.get("btcPrice", "—"),
            "change": change_override or market.get("btcChange", "—"),
            "positive": positive,
        }
    if symbol == "ETH":
        return {
            "symbol": "ETH",
            "price": market.get("ethPrice", "—"),
            "change": change_override or market.get("ethChange", "—"),
            "positive": positive,
        }
    token_prices = cache.get("token_prices") or {}
    entry = token_prices.get(symbol.upper())
    if entry:
        return {
            "symbol": symbol,
            "price": entry["price"],
            "change": change_override or entry["change"],
            "positive": positive if change_override else entry["positive"],
        }
    return {"symbol": symbol, "price": "—", "change": change_override or "—", "positive": positive}
