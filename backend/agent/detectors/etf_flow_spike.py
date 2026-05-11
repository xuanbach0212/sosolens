import logging
import backend.cache as cache
from backend.services.sosovalue import get_client
from backend.services.etf import fetch_etf_data
from backend.services.currency import fetch_btc_eth_prices

logger = logging.getLogger(__name__)

STRONG_BUY_USD = 400_000_000    # > $400M  → BUY
WATCH_USD      =  50_000_000    # > $50M   → WATCH
WATCH_NEG_USD  = -50_000_000    # < -$50M  → WATCH (caution)
STRONG_SELL_USD = -200_000_000  # < -$200M → AVOID
BASELINE_USD = 150_000_000


class ETFFlowSpikeDetector:
    async def run(self) -> list[dict]:
        try:
            client = get_client()
            snapshot, total = await fetch_etf_data(client)
            cache.set("etf_flows", snapshot)
        except Exception as exc:
            logger.warning("[etf_spike] fetch failed: %s", exc)
            return []

        btc_token, eth_token = await fetch_btc_eth_prices(client)

        if total > STRONG_BUY_USD:
            sig_type = "BUY"
        elif total > WATCH_USD:
            sig_type = "WATCH"
        elif total < STRONG_SELL_USD:
            sig_type = "AVOID"
        elif total < WATCH_NEG_USD:
            sig_type = "WATCH"
        else:
            logger.info("[etf_spike] total=%s within normal range — no signal", _fmt(total))
            return []

        ratio = total / BASELINE_USD
        flow_signal = "🟢" if total > 0 else "🔴"
        flow_arrow = "↑↑" if total > 0 else "↓↓"

        logger.info("[etf_spike] signal=%s total=%s ratio=%.1fx", sig_type, _fmt(total), ratio)

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
            "topTokens": [btc_token, eth_token],
            "pastSignals": [],
            "accuracy": 0,
            "sodexPair": "BUY BTC/USDC" if sig_type == "BUY" else "—",
            "sodexSlippage": "1%",
            "sodexEstOutput": "—",
        }]


def _fmt(usd: float) -> str:
    sign = "+" if usd >= 0 else "-"
    return f"{sign}${abs(usd) / 1_000_000:.0f}M"
