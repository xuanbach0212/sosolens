import logging
import re
from backend.services.sosovalue import get_client
from backend.services.macro import fetch_macro_indicators

logger = logging.getLogger(__name__)

# Indicators where rising (↑) is risk-off for crypto
_RISK_OFF_IF_RISING = {"fed rate", "us cpi", "cpi", "dxy", "10y yield"}
# Indicators where rising (↑) is risk-on for crypto
_RISK_ON_IF_RISING = {"m2 supply", "m2"}


def _arrow(ind: dict) -> str:
    """Extract direction from arrow field, falling back to value text (e.g. M2 Supply)."""
    a = ind.get("arrow", "")
    if a in ("↑", "↓", "→"):
        return a
    v = ind.get("value", "")
    if "↑" in v:
        return "↑"
    if "↓" in v:
        return "↓"
    return "→"


def _is_event(ind: dict) -> bool:
    """True if this indicator represents an upcoming macro event within 7 days."""
    if ind.get("warning"):
        return True
    m = re.search(r"in\s+(\d+)d", ind.get("value", ""))
    return bool(m and int(m.group(1)) <= 7)


class MacroRiskDetector:
    async def run(self) -> list[dict]:
        try:
            client = get_client()
            indicators = await fetch_macro_indicators(client)
        except Exception as exc:
            logger.warning(f"[macro_risk] fetch failed: {exc}")
            return []

        if not indicators:
            return []

        risk_on = 0
        risk_off = 0
        event_risk = False
        data_sources = []

        for ind in indicators:
            name = ind["name"].strip()
            key = name.lower()
            value = ind["value"]

            if _is_event(ind):
                event_risk = True
                data_sources.append({"name": name, "value": value, "signal": "⚠️", "arrow": "→"})
                continue

            direction = _arrow(ind)

            if key in _RISK_OFF_IF_RISING:
                if direction == "↑":
                    risk_off += 1
                    emoji = "🔴"
                elif direction == "↓":
                    risk_on += 1
                    emoji = "🟢"
                else:
                    emoji = "🟡"
            elif key in _RISK_ON_IF_RISING:
                if direction == "↑":
                    risk_on += 1
                    emoji = "🟢"
                elif direction == "↓":
                    risk_off += 1
                    emoji = "🔴"
                else:
                    emoji = "🟡"
            else:
                emoji = "🟡"

            data_sources.append({"name": name, "value": value, "signal": emoji, "arrow": direction})

        if risk_off > risk_on:
            sig_type = "AVOID"
        elif risk_on > risk_off:
            sig_type = "WATCH" if event_risk else "BUY"
        else:
            sig_type = "WATCH"

        logger.info(
            f"[macro_risk] signal={sig_type} risk_on={risk_on} "
            f"risk_off={risk_off} event_risk={event_risk}"
        )

        return [{
            "id": "macro-risk-classifier",
            "type": sig_type,
            "sector": "Macro — Risk-On / Risk-Off",
            "timeAgo": "0h",
            "dataSources": data_sources,
            "topTokens": [
                {"symbol": "BTC", "price": "—", "change": "—", "positive": sig_type != "AVOID"},
                {"symbol": "ETH", "price": "—", "change": "—", "positive": sig_type != "AVOID"},
            ],
            "pastSignals": [],
            "accuracy": 0,
            "sodexPair": "BUY BTC/USDC" if sig_type == "BUY" else "—",
            "sodexSlippage": "1%",
            "sodexEstOutput": "—",
        }]
