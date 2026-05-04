import logging
from backend.services.sosovalue import SoSoValueClient

logger = logging.getLogger(__name__)


async def fetch_macro_indicators(client: SoSoValueClient) -> list[dict]:
    try:
        raw = await client.get_macro()
        rows = raw.get("data") or raw.get("list") or raw
        if not isinstance(rows, list):
            logger.warning("[macro] unexpected API shape")
            return []
        return [
            {
                "name": row.get("name", ""),
                "value": str(row.get("value", "—")),
                "arrow": row.get("arrow", "→"),
                "warning": bool(row.get("warning", False)),
            }
            for row in rows
        ]
    except Exception as exc:
        logger.warning(f"[macro] fetch failed: {exc}")
        return []
