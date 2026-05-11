import logging
from backend.services.sosovalue import SoSoValueClient

logger = logging.getLogger(__name__)

SECTOR_MAP = [
    ("AI",      "ssiAI"),
    ("DeFi",    "ssiDeFi"),
    ("RWA",     "ssiRWA"),
    ("Layer 1", "ssiLayer1"),
    ("Layer 2", "ssiLayer2"),
    ("Gaming",  "ssiGameFi"),
    ("NFT",     "ssiNFT"),
    ("Meme",    "ssiMeme"),
]


async def fetch_sector_flows(client: SoSoValueClient) -> list[dict]:
    result = []
    for display_name, ticker in SECTOR_MAP:
        try:
            raw = await client.get_index_snapshot(ticker)
            data = raw.get("data") or {}
            change_pct = float(data.get("change_pct_24h") or 0) * 100
            result.append({
                "name": display_name,
                "change": round(change_pct, 1),
                "arrows": _arrows(change_pct),
                "positive": change_pct >= 0,
            })
        except Exception as exc:
            logger.warning("[sector] %s (%s) failed: %s", display_name, ticker, exc)

    result.sort(key=lambda x: x["change"], reverse=True)
    return result


def _arrows(change: float) -> str:
    if change > 5:
        return "↑↑"
    if change > 0:
        return "↑"
    if change < -5:
        return "↓↓"
    return "↓"
