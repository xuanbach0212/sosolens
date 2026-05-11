import logging
from backend.services.sosovalue import SoSoValueClient

logger = logging.getLogger(__name__)


def _fmt_holdings(n: int) -> str:
    return f"{n:,} BTC"


def _fmt_change(n: int) -> str:
    if n == 0:
        return "±0"
    sign = "+" if n > 0 else ""
    return f"{sign}{n:,}"


async def fetch_btc_treasuries(client: SoSoValueClient) -> list[dict]:
    try:
        raw = await client.get_btc_treasuries()
    except Exception as exc:
        logger.warning("[btc_treasuries] list fetch failed: %s", exc)
        return []

    companies = raw.get("data") or []
    if not isinstance(companies, list) or not companies:
        return []

    top_tickers = [c["ticker"] for c in companies[:5] if c.get("ticker")]
    names = {c["ticker"]: c.get("name", c["ticker"]) for c in companies[:5]}

    result = []
    for ticker in top_tickers:
        try:
            hist = await client.get_btc_treasury_history(ticker)
        except Exception as exc:
            logger.warning("[btc_treasuries] history fetch failed for %s: %s", ticker, exc)
            continue

        records = hist.get("data") or []
        if not records:
            continue

        latest = records[0]
        holdings = int(float(latest.get("btc_holding") or 0))
        acq = int(float(latest.get("btc_acq") or 0))

        result.append({
            "company": names.get(ticker, ticker),
            "btcHeld": _fmt_holdings(holdings),
            "weeklyChange": _fmt_change(acq),
            "positive": True if acq > 0 else (False if acq < 0 else None),
            "_sort_key": holdings,
        })

    result.sort(key=lambda x: x["_sort_key"], reverse=True)
    for r in result:
        del r["_sort_key"]

    return result
