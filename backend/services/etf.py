import logging
from backend.services.sosovalue import SoSoValueClient

logger = logging.getLogger(__name__)


def _daily_net_by_date(rows: list[dict]) -> dict[str, float]:
    """Collapse summary-history rows to one net-inflow value per date.

    The endpoint returns several rows per date for different aggregation
    windows; the single-day spot figure is the one with the smallest traded
    volume (multi-day/cumulative rows carry much larger volume), so we keep
    min(total_value_traded) per date.
    """
    by_date: dict[str, tuple[float, float]] = {}
    for r in rows:
        date = r.get("date")
        if not date:
            continue
        traded = float(r.get("total_value_traded") or 0)
        net = float(r.get("total_net_inflow") or 0)
        if date not in by_date or traded < by_date[date][0]:
            by_date[date] = (traded, net)
    return {d: v[1] for d, v in by_date.items()}


async def _latest_daily_net(client: SoSoValueClient, symbol: str) -> float:
    """Whole-universe most-recent daily net inflow (USD) for a symbol."""
    try:
        raw = await client.get_etf_summary_history(symbol)
        rows = raw.get("data") or []
    except Exception as exc:
        logger.warning("[etf] %s summary-history failed: %s", symbol, exc)
        return 0.0
    daily = _daily_net_by_date(rows)
    if not daily:
        return 0.0
    return daily[max(daily)]  # ISO dates sort chronologically


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
    """Fetch ETF flows — returns (snapshot_for_display, total_usd, btc_usd, eth_usd).

    Uses /etfs/summary-history, which aggregates net inflow across the whole
    US spot-ETF universe (not a hand-picked ticker list)."""
    btc_flow = await _latest_daily_net(client, "BTC")
    eth_flow = await _latest_daily_net(client, "ETH")

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
