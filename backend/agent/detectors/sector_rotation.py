import logging
import backend.cache as cache
from backend.agent.tokens import token_from_cache
from backend.services.sosovalue import get_client
from backend.services.sector import fetch_sector_flows

logger = logging.getLogger(__name__)

SECTOR_TOKEN = {
    "AI":      "FET",
    "DeFi":    "UNI",
    "RWA":     "ONDO",
    "Layer 1": "ETH",
    "Layer 2": "OP",
    "Gaming":  "GALA",
    "NFT":     "BLUR",
    "Meme":    "DOGE",
}


def _sector_signal_type(change: float) -> tuple[str, int, str]:
    """Return (signal_type, confidence, risk) based on 7d sector flow change %."""
    abs_c = abs(change)
    if change >= 5.0:
        return "BUY", min(90, 65 + int(abs_c * 2)), "LOW"
    elif change >= 0.0:
        return "WATCH", 55 + min(10, int(abs_c * 2)), "MEDIUM"
    elif change >= -5.0:
        return "WATCH", 50 + min(10, int(abs_c)), "MEDIUM"
    else:
        return "AVOID", min(90, 60 + int(abs_c)), "HIGH"


class SectorRotationDetector:
    async def run(self) -> list[dict]:
        try:
            client = get_client()
            sectors = await fetch_sector_flows(client)
            cache.put("sector_flows", sectors)
        except Exception as exc:
            logger.warning("[sector_rotation] fetch failed: %s", exc)
            return []

        if not sectors:
            return []

        signals = []
        for sector in sectors:
            name = sector["name"]
            change = sector.get("change", 0.0)
            sig_type, confidence, risk = _sector_signal_type(change)
            change_str = f"+{change:.1f}%" if change >= 0 else f"{change:.1f}%"
            token = SECTOR_TOKEN.get(name, name.upper()[:4])

            signals.append({
                "id": f"sector-{name.lower().replace(' ', '-')}",
                "type": sig_type,
                "sector": name,
                "dataSources": [
                    {
                        "name": "7D Price Change",
                        "value": change_str,
                        "signal": "🟢" if change >= 0 else "🔴",
                        "arrow": "↑" if change >= 0 else "↓",
                    },
                    {"name": "Sector", "value": name, "signal": "🟡"},
                ],
                "topTokens": [
                    token_from_cache(token, change >= 0, change_str),
                ],
                "pastSignals": [],
                "accuracy": 0,
                "sodexPair": f"BUY {token}/USDC" if sig_type == "BUY" else "—",
                "sodexSlippage": "1%",
                "sodexEstOutput": "—",
                "confidence": confidence,
                "risk": risk,
            })

        logger.info("[sector_rotation] emitted %d sector signals", len(signals))
        return signals
