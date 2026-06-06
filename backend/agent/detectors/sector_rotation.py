import logging
import backend.cache as cache
from backend.agent.tokens import token_from_cache
from backend.services.sosovalue import get_client
from backend.services.sector import fetch_sector_flows

logger = logging.getLogger(__name__)

ROTATION_THRESHOLD = 2.0   # leader must be above this % (24h price change)
WATCH_THRESHOLD = 1.0
SPREAD_THRESHOLD = 5.0     # leader minus laggard spread for BUY

# Map sector display names → representative token for SoDEX trade link
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
WATCH_SPREAD = 3.0


class SectorRotationDetector:
    async def run(self) -> list[dict]:
        try:
            client = get_client()
            sectors = await fetch_sector_flows(client)
            cache.put("sector_flows", sectors)
        except Exception as exc:
            logger.warning("[sector_rotation] fetch failed: %s", exc)
            return []

        if len(sectors) < 2:
            logger.warning("[sector_rotation] too few sectors: %d", len(sectors))
            return []

        leader = sectors[0]
        lagger = sectors[-1]
        spread = leader["change"] - lagger["change"]

        if leader["change"] >= ROTATION_THRESHOLD and spread >= SPREAD_THRESHOLD:
            sig_type = "BUY"
        elif leader["change"] >= WATCH_THRESHOLD and spread >= WATCH_SPREAD:
            sig_type = "WATCH"
        else:
            logger.info("[sector_rotation] spread=%.1fpt leader=%.1f%% — no signal", spread, leader["change"])
            return []

        flow_signal = "🟢" if sig_type == "BUY" else "🟡"
        leader_label = f"+{leader['change']:.1f}%" if leader["change"] >= 0 else f"{leader['change']:.1f}%"
        lagger_label = f"{lagger['change']:.1f}%"

        logger.info("[sector_rotation] signal=%s leader=%s lagger=%s spread=%.1fpt",
                    sig_type, leader["name"], lagger["name"], spread)

        return [{
            "id": "sector-rotation",
            "type": sig_type,
            "sector": f"{leader['name']} Sector",
            "timeAgo": "0h",
            "dataSources": [
                {"name": f"{leader['name']} 24h Change", "value": leader_label, "signal": "🟢", "arrow": "↑"},
                {"name": f"{lagger['name']} 24h Change", "value": lagger_label, "signal": "🔴", "arrow": "↓"},
                {"name": "Rotation Spread", "value": f"{spread:.1f}pts", "signal": flow_signal},
                {"name": "Signal Tier", "value": sig_type, "signal": flow_signal},
            ],
            "topTokens": [
                token_from_cache(SECTOR_TOKEN.get(leader["name"], leader["name"].upper()), leader["change"] >= 0, leader_label),
                token_from_cache(SECTOR_TOKEN.get(lagger["name"], lagger["name"].upper()), lagger["change"] >= 0, lagger_label),
            ],
            "pastSignals": [],
            "accuracy": 0,
            "sodexPair": f"BUY {SECTOR_TOKEN.get(leader['name'], leader['name'].upper())}/USDC" if sig_type == "BUY" else "—",
            "sodexSlippage": "1%",
            "sodexEstOutput": "—",
        }]
