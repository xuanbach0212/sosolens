import logging
from backend.services.sosovalue import SoSoValueClient

logger = logging.getLogger(__name__)


async def fetch_token_prices(client: SoSoValueClient, symbols: list[str]) -> dict[str, float]:
    try:
        raw = await client.get_prices(symbols)
    except Exception as exc:
        logger.warning("[currency] fetch failed: %s", exc)
        return {}

    items = raw.get("data") or raw.get("prices") or raw.get("list") or []
    if not isinstance(items, list) or not items:
        return {}

    result: dict[str, float] = {}
    for item in items:
        symbol = (item.get("symbol") or item.get("currency") or "").upper()
        price = float(
            item.get("price")
            or item.get("current_price")
            or item.get("close")
            or item.get("last_price")
            or 0
        )
        if symbol and price:
            result[symbol] = price
    return result


async def fetch_market_status(client: SoSoValueClient) -> dict:
    from backend.data.hardcoded import MARKET_STATUS

    prices = await fetch_token_prices(client, ["BTC", "ETH"])
    if not prices:
        return MARKET_STATUS

    base = dict(MARKET_STATUS)
    if "BTC" in prices:
        base["btcPrice"] = f"${prices['BTC']:,.0f}"
    if "ETH" in prices:
        base["ethPrice"] = f"${prices['ETH']:,.0f}"
    return base
