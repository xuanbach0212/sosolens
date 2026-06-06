import logging
import backend.cache as cache
from backend.agent.tokens import token_from_cache
from backend.services.sosovalue import get_client
from backend.services.btc_treasuries import fetch_btc_treasuries

logger = logging.getLogger(__name__)


BUY_THRESHOLD = 1_000     # net weekly BTC >= +1,000 → BUY
AVOID_THRESHOLD = -500    # net weekly BTC <= -500   → AVOID


class BtcAccumulationDetector:
    async def run(self) -> list[dict]:
        try:
            client = get_client()
            data = await fetch_btc_treasuries(client)
            cache.put("btc_treasuries", data)
        except Exception as exc:
            logger.warning("[btc_accumulation] fetch failed: %s", exc)
            return []

        data = data[:5]
        if not data or len(data) < 2:
            return []

        changes = [_parse_change(e.get("weeklyChange", "±0")) for e in data]
        net_weekly = sum(changes)

        buying = [(data[i], changes[i]) for i in range(len(data)) if changes[i] > 0]
        selling = [(data[i], changes[i]) for i in range(len(data)) if changes[i] < 0]

        if net_weekly >= BUY_THRESHOLD:
            sig_type = "BUY"
        elif net_weekly <= AVOID_THRESHOLD:
            sig_type = "AVOID"
        else:
            sig_type = "WATCH"

        net_signal = "🟢" if net_weekly > 0 else "🔴"
        if net_weekly >= BUY_THRESHOLD:
            net_arrow = "↑↑"
        elif net_weekly > 0:
            net_arrow = "↑"
        elif net_weekly <= AVOID_THRESHOLD:
            net_arrow = "↓↓"
        else:
            net_arrow = "↓"

        if buying:
            top = max(buying, key=lambda t: t[1])
            top_val = f"{top[0]['company']} {_fmt_change(top[1])}"
            top_signal = "🟢"
        else:
            top_val = "None this week"
            top_signal = "🔴"

        n_buying = len(buying)
        n_selling = len(selling)
        ratio_signal = "🟢" if n_buying > n_selling else ("🔴" if n_selling > n_buying else "🟡")

        logger.info(
            "[btc_accumulation] signal=%s net=%d buying=%d selling=%d",
            sig_type, net_weekly, n_buying, n_selling,
        )

        return [{
            "id": "btc-accumulation",
            "type": sig_type,
            "sector": "BTC Treasury",
            "timeAgo": "0h",
            "dataSources": [
                {"name": "Net Weekly Δ", "value": _fmt_net(net_weekly), "signal": net_signal, "arrow": net_arrow},
                {"name": "Top Buyer", "value": top_val, "signal": top_signal},
                {"name": "Buying / Selling", "value": f"{n_buying} / {n_selling} companies", "signal": ratio_signal},
            ],
            "topTokens": [
                token_from_cache("BTC", net_weekly > 0),
                token_from_cache("MSTR", bool(buying)),
            ],
            "pastSignals": [],
            "accuracy": 0,
            "sodexPair": "BUY BTC/USDC" if sig_type == "BUY" else "—",
            "sodexSlippage": "1%",
            "sodexEstOutput": "—",
        }]


def _parse_change(s: str) -> int:
    """Parse weeklyChange string ('+1,282', '-500', '±0') → int."""
    if not s or s.startswith("±"):
        return 0
    return int(s.replace(",", ""))


def _fmt_change(n: int) -> str:
    if n == 0:
        return "±0"
    sign = "+" if n > 0 else ""
    return f"{sign}{n:,}"


def _fmt_net(n: int) -> str:
    if n == 0:
        return "±0 BTC"
    sign = "+" if n > 0 else ""
    return f"{sign}{n:,} BTC"
