"""Shared helper: build a topTokens entry with live BTC/ETH prices from cache."""
import backend.cache as cache


def token_from_cache(symbol: str, positive: bool, change_override: str | None = None) -> dict:
    """Return a topTokens entry for the signal payload.

    For BTC/ETH the price and change come from the market_status cache (live data).
    For other symbols, price is "—" and change is the override (e.g. a sector's 24h %)
    or "—" when no override is given.
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
    return {"symbol": symbol, "price": "—", "change": change_override or "—", "positive": positive}
