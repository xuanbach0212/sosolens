import logging
from backend.agent.tokens import token_from_cache
from backend.services.sosovalue import get_client
from backend.services.macro import fetch_macro_events

logger = logging.getLogger(__name__)

AVOID_DAYS = 3   # high-impact event within this many days → AVOID
WATCH_DAYS = 7   # high-impact event within this many days → at least WATCH


class MacroRiskDetector:
    async def run(self) -> list[dict]:
        try:
            client = get_client()
            events = await fetch_macro_events(client)
        except Exception as exc:
            logger.warning("[macro_risk] fetch failed: %s", exc)
            return []

        if not events:
            return []

        high_events = [ev for ev in events if ev["high_impact"]]
        nearest_high = min(high_events, key=lambda ev: ev["days_until"]) if high_events else None

        if nearest_high is None:
            sig_type = "BUY"
            label = "No high-impact events in the near term"
        elif nearest_high["days_until"] <= AVOID_DAYS:
            sig_type = "AVOID"
            label = f"High-impact event imminent: {', '.join(nearest_high['events'][:2])}"
        elif nearest_high["days_until"] <= WATCH_DAYS:
            sig_type = "WATCH"
            label = (
                f"High-impact event in {nearest_high['days_until']}d: "
                f"{', '.join(nearest_high['events'][:2])}"
            )
        else:
            sig_type = "BUY"
            label = f"Next high-impact event in {nearest_high['days_until']}d"

        data_sources = []
        for ev in events[:5]:
            days = ev["days_until"]
            time_label = "today" if days == 0 else f"in {days}d"
            emoji = "🔴" if (ev["high_impact"] and days <= AVOID_DAYS) else \
                    "⚠️" if (ev["high_impact"] and days <= WATCH_DAYS) else "🟡"
            data_sources.append({
                "name": ", ".join(ev["events"][:2]),
                "value": time_label,
                "signal": emoji,
                "arrow": "→",
            })

        logger.info("[macro_risk] signal=%s nearest_high=%s", sig_type,
                    nearest_high["events"] if nearest_high else None)

        return [{
            "id": "macro-risk-classifier",
            "type": sig_type,
            "sector": "Macro",
            "timeAgo": "0h",
            "dataSources": data_sources,
            "topTokens": [
                token_from_cache("BTC", sig_type != "AVOID"),
                token_from_cache("ETH", sig_type != "AVOID"),
            ],
            "pastSignals": [],
            "accuracy": 0,
            "sodexPair": "BUY BTC/USDC" if sig_type == "BUY" else ("SELL BTC/USDC" if sig_type == "AVOID" else "WATCH BTC/USDC"),
            "sodexSlippage": "1%",
            "sodexEstOutput": "—",
        }]
