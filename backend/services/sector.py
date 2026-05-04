import logging
from backend.services.sosovalue import SoSoValueClient

logger = logging.getLogger(__name__)


def _arrows(change: float) -> str:
    if change > 20:
        return "↑↑"
    if change > 0:
        return "↑"
    if change < -20:
        return "↓↓"
    return "↓"


async def fetch_sector_flows(client: SoSoValueClient) -> list[dict]:
    raw = await client.get_sector_flows()
    rows = raw.get("data") or raw.get("list") or raw
    if not isinstance(rows, list):
        logger.warning("[sector] unexpected API shape: %s", type(rows))
        return []

    result = []
    for item in rows:
        name = item.get("name") or item.get("sectorName") or item.get("sector", "Unknown")
        change = float(
            item.get("change") or item.get("capitalFlow") or item.get("flowChange") or 0
        )
        result.append({
            "name": name,
            "change": round(change, 1),
            "arrows": _arrows(change),
            "positive": change >= 0,
        })

    return result
