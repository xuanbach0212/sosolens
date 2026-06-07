import logging
import backend.cache as cache
from backend.agent.tokens import token_from_cache
from backend.services.sosovalue import get_client
from backend.services.etf import fetch_etf_data

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
            snapshot, total, btc_raw, eth_raw = await fetch_etf_data(client)
        except Exception as exc:
            logger.warning("[etf_spike] fetch failed: %s", exc)
            return []
        cache.put("etf_flows", snapshot)
        cache.put("etf_raw", {"btc": btc_raw, "eth": eth_raw, "total": total})

        # market_status is populated by the prioritized _refresh_market_cache bootstrap
        btc_token = token_from_cache("BTC", btc_raw >= 0)
        eth_token = token_from_cache("ETH", eth_raw >= 0)

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
            "sector": "ETF Flows",
            "timeAgo": "0h",
            "dataSources": [
                {"name": "ETF Net Inflow (24h)", "value": _fmt(total), "signal": flow_signal, "arrow": flow_arrow},
                {"name": "Flow vs Baseline", "value": f"{ratio:.1f}x avg", "signal": "🔴" if total < 0 else ("🟢" if ratio > 2 else "🟡")},
                {"name": "Signal Tier", "value": sig_type, "signal": "🟢" if sig_type == "BUY" else ("🔴" if sig_type == "AVOID" else "🟡")},
            ],
            "topTokens": [btc_token, eth_token],
            "pastSignals": [],
            "accuracy": 0,
            "sodexPair": "BUY BTC/USDC" if sig_type == "BUY" else ("SELL BTC/USDC" if sig_type == "AVOID" else "WATCH BTC/USDC"),
            "sodexSlippage": "1%",
            "sodexEstOutput": "—",
        }]


def _fmt(usd: float) -> str:
    sign = "+" if usd >= 0 else "-"
    return f"{sign}${abs(usd) / 1_000_000:.0f}M"
