import logging
from backend.services.sosovalue import SoSoValueClient

logger = logging.getLogger(__name__)

BTC_TICKERS = ["IBIT", "FBTC", "ARKB"]
ETH_TICKERS = ["ETHA", "ETHW"]


async def _net_inflow(client: SoSoValueClient, ticker: str) -> float:
    try:
        raw = await client.get_etf_snapshot(ticker)
        data = raw.get("data") or {}
        return float(data.get("net_inflow") or 0)
    except Exception as exc:
        logger.warning("[etf] %s snapshot failed: %s", ticker, exc)
        return 0.0


def _fmt_flow(usd: float) -> str:
    sign = "+" if usd >= 0 else "-"
    abs_val = abs(usd)
    if abs_val >= 1_000_000_000:
        return f"{sign}${abs_val / 1_000_000_000:.1f}B"
    return f"{sign}${abs_val / 1_000_000:.0f}M"


def _arrows(usd: float) -> str:
    if usd > 500_000_000:
        return "↑↑↑"
    if usd > 100_000_000:
        return "↑↑"
    if usd > 0:
        return "↑"
    if usd > -100_000_000:
        return "↓"
    return "↓↓"


async def fetch_etf_data(client: SoSoValueClient) -> tuple[list[dict], float, float, float]:
    """Fetch ETF flows — returns (snapshot_for_display, total_usd, btc_usd, eth_usd)."""
    btc_flow = 0.0
    for ticker in BTC_TICKERS:
        btc_flow += await _net_inflow(client, ticker)

    eth_flow = 0.0
    for ticker in ETH_TICKERS:
        eth_flow += await _net_inflow(client, ticker)

    total = btc_flow + eth_flow

    snapshot = [
        {"name": "BTC ETF", "flow": _fmt_flow(btc_flow), "arrows": _arrows(btc_flow), "positive": btc_flow >= 0},
        {"name": "ETH ETF", "flow": _fmt_flow(eth_flow), "arrows": _arrows(eth_flow), "positive": eth_flow >= 0},
        {"name": "TOTAL",   "flow": _fmt_flow(total),    "arrows": _arrows(total),    "positive": total >= 0, "total": True},
    ]
    return snapshot, total, btc_flow, eth_flow


async def fetch_etf_snapshot(client: SoSoValueClient) -> list[dict]:
    snapshot, _, _, _ = await fetch_etf_data(client)
    return snapshot


async def fetch_etf_total_flow(client: SoSoValueClient) -> float:
    _, total, _, _ = await fetch_etf_data(client)
    return total
