import logging
from backend.services.sosovalue import get_client

logger = logging.getLogger(__name__)

ROTATION_THRESHOLD = 15.0  # leader sector must be above this % to signal
WATCH_THRESHOLD = 8.0      # leader sector must be above this % to emit WATCH
SPREAD_THRESHOLD = 25.0    # leader minus laggard must exceed this for BUY
WATCH_SPREAD = 15.0        # spread threshold for WATCH


class SectorRotationDetector:
    async def run(self) -> list[dict]:
        try:
            client = get_client()
            raw = await client.get_sector_flows()
        except Exception as exc:
            logger.warning("[sector_rotation] API error: %s", exc)
            return []

        rows = raw.get("data") or raw.get("list") or raw
        if not isinstance(rows, list) or len(rows) < 2:
            logger.warning("[sector_rotation] unexpected shape or too few rows")
            return []

        sectors = []
        for item in rows:
            name = item.get("name") or item.get("sectorName") or item.get("sector", "Unknown")
            change = float(
                item.get("change") or item.get("capitalFlow") or item.get("flowChange") or 0
            )
            sectors.append((name, change))

        leader_name, leader_val = max(sectors, key=lambda x: x[1])
        lagger_name, lagger_val = min(sectors, key=lambda x: x[1])
        spread = leader_val - lagger_val

        if leader_val >= ROTATION_THRESHOLD and spread >= SPREAD_THRESHOLD:
            sig_type = "BUY"
        elif leader_val >= WATCH_THRESHOLD and spread >= WATCH_SPREAD:
            sig_type = "WATCH"
        else:
            return []

        flow_signal = "🟢" if sig_type == "BUY" else "🟡"
        leader_label = f"+{leader_val:.1f}%" if leader_val >= 0 else f"{leader_val:.1f}%"
        lagger_label = f"{lagger_val:.1f}%"

        return [{
            "id": "sector-rotation",
            "type": sig_type,
            "sector": f"{leader_name} Sector",
            "timeAgo": "0h",
            "dataSources": [
                {"name": f"{leader_name} Capital Flow", "value": leader_label, "signal": "🟢", "arrow": "↑"},
                {"name": f"{lagger_name} Capital Flow", "value": lagger_label, "signal": "🔴", "arrow": "↓"},
                {"name": "Rotation Spread", "value": f"{spread:.1f}pts", "signal": flow_signal},
                {"name": "Signal Tier", "value": sig_type, "signal": flow_signal},
            ],
            "topTokens": [
                {"symbol": leader_name.split("/")[0][:4].upper(), "change": leader_label},
                {"symbol": lagger_name.split("/")[0][:4].upper(), "change": lagger_label},
            ],
            "pastSignals": [],
            "accuracy": 0,
            "sodexPair": f"BUY {leader_name.split('/')[0].upper()}/USDC" if sig_type == "BUY" else "—",
            "sodexSlippage": "1%",
            "sodexEstOutput": "—",
        }]
