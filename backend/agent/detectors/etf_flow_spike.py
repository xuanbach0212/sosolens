import logging
from backend.services.sosovalue import get_client

logger = logging.getLogger(__name__)

STRONG_BUY_USD = 400_000_000    # > $400M  → BUY
WATCH_USD = 150_000_000         # > $150M  → WATCH
STRONG_SELL_USD = -200_000_000  # < -$200M → AVOID
BASELINE_USD = 150_000_000      # denominator for ratio display


class ETFFlowSpikeDetector:
    async def run(self) -> list[dict]:
        try:
            client = get_client()
            raw = await client.get_etf_flows()
            rows = raw.get("data") or raw.get("list") or raw
            if not isinstance(rows, list):
                logger.warning("[etf_spike] unexpected API shape, skipping")
                return []

            total = sum(float(r.get("netFlow") or r.get("net_flow") or 0) for r in rows)
        except Exception as exc:
            logger.warning(f"[etf_spike] fetch failed: {exc}")
            return []

        if total > STRONG_BUY_USD:
            sig_type = "BUY"
        elif total > WATCH_USD:
            sig_type = "WATCH"
        elif total < STRONG_SELL_USD:
            sig_type = "AVOID"
        else:
            logger.info(f"[etf_spike] total={_fmt(total)} within normal range — no signal")
            return []

        ratio = total / BASELINE_USD
        flow_signal = "🟢" if total > 0 else "🔴"
        flow_arrow = "↑↑" if total > 0 else "↓↓"

        logger.info(f"[etf_spike] signal={sig_type} total={_fmt(total)} ratio={ratio:.1f}x")

        return [{
            "id": "etf-flow-spike",
            "type": sig_type,
            "sector": "BTC/ETH ETF",
            "timeAgo": "0h",
            "dataSources": [
                {"name": "ETF Net Inflow (24h)", "value": _fmt(total), "signal": flow_signal, "arrow": flow_arrow},
                {"name": "Flow vs Baseline", "value": f"{ratio:.1f}x avg", "signal": "🟢" if ratio > 2 else "🟡"},
                {"name": "Signal Tier", "value": sig_type, "signal": "🟢" if sig_type == "BUY" else "🟡"},
            ],
            "topTokens": [
                {"symbol": "BTC", "price": "—", "change": "—", "positive": True},
                {"symbol": "ETH", "price": "—", "change": "—", "positive": True},
            ],
            "pastSignals": [],
            "accuracy": 0,
            "sodexPair": "BUY BTC/USDC" if sig_type == "BUY" else "—",
            "sodexSlippage": "1%",
            "sodexEstOutput": "—",
        }]


def _fmt(usd: float) -> str:
    sign = "+" if usd >= 0 else "-"
    return f"{sign}${abs(usd) / 1_000_000:.0f}M"
