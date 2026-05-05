import logging
from backend.services.sosovalue import SoSoValueClient

logger = logging.getLogger(__name__)


def _fmt_holdings(n: float) -> str:
    return f"{int(n):,} BTC"


def _fmt_change(n: float) -> str:
    n = int(n)
    if n == 0:
        return "±0"
    sign = "+" if n > 0 else ""
    return f"{sign}{n:,}"


async def fetch_btc_treasuries(client: SoSoValueClient) -> list[dict]:
    try:
        raw = await client.get_btc_treasuries()
    except Exception as exc:
        logger.warning("[btc_treasuries] fetch failed: %s", exc)
        return []

    items = raw.get("data") or raw.get("holdings") or []
    if not isinstance(items, list) or not items:
        return []

    result = []
    for item in items:
        company = (
            item.get("short_name")
            or item.get("company_name")
            or item.get("name")
            or "Unknown"
        )
        holdings = float(
            item.get("total_holdings")
            or item.get("btc_holdings")
            or item.get("holdings")
            or 0
        )
        change_7d = float(
            item.get("btc_change_7d")
            or item.get("change_7d")
            or item.get("weekly_change")
            or item.get("change")
            or 0
        )
        result.append({
            "company": company,
            "btcHeld": _fmt_holdings(holdings),
            "weeklyChange": _fmt_change(change_7d),
            "positive": True if change_7d > 0 else (False if change_7d < 0 else None),
            "_sort_key": holdings,
        })

    result.sort(key=lambda x: x["_sort_key"], reverse=True)
    for r in result:
        del r["_sort_key"]

    return result[:5]
