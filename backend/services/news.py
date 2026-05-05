import logging
from backend.services.sosovalue import SoSoValueClient

logger = logging.getLogger(__name__)

_MACRO_KEYWORDS = frozenset([
    "fed", "federal reserve", "fomc", "rate", "inflation", "cpi",
    "interest", "recession", "gdp", "unemployment", "nonfarm",
    "payroll", "treasury", "yield", "powell", "dxy", "ppi",
])


def _is_macro_sensitive(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _MACRO_KEYWORDS)


def _fmt_usd(usd: float) -> str:
    if usd >= 1_000_000_000:
        return f"${usd / 1_000_000_000:.1f}B"
    if usd >= 1_000_000:
        return f"${usd / 1_000_000:.0f}M"
    return f"${usd:,.0f}"


async def fetch_news_headlines(client: SoSoValueClient) -> tuple[list[str], list[dict]]:
    try:
        raw = await client.get_news()
    except Exception as exc:
        logger.warning("[news] fetch failed: %s", exc)
        return [], []

    items = raw.get("data") or raw.get("news") or raw.get("list") or []
    if not isinstance(items, list) or not items:
        return [], []

    headlines = []
    for item in items[:4]:
        title = (
            item.get("title")
            or item.get("headline")
            or item.get("content", "")[:120]
        )
        source = (
            item.get("source_name")
            or item.get("source")
            or item.get("media")
            or "Unknown"
        )
        if not title:
            continue
        headlines.append({
            "text": title,
            "source": source,
            "macroSensitive": _is_macro_sensitive(title),
        })

    briefing = [h["text"] for h in headlines[:3]]
    return briefing, headlines


async def fetch_fundraising(client: SoSoValueClient) -> list[dict]:
    try:
        raw = await client.get_fundraising()
    except Exception as exc:
        logger.warning("[fundraising] fetch failed: %s", exc)
        return []

    items = raw.get("data") or raw.get("rounds") or raw.get("list") or []
    if not isinstance(items, list) or not items:
        return []

    sector_map: dict[str, dict] = {}
    for item in items:
        sector = (
            item.get("category")
            or item.get("sector")
            or item.get("track")
            or item.get("type")
            or "Other"
        )
        amount = float(
            item.get("amount_usd")
            or item.get("amount")
            or item.get("funding_amount")
            or item.get("raised")
            or 0
        )
        if sector not in sector_map:
            sector_map[sector] = {"rounds": 0, "total": 0.0}
        sector_map[sector]["rounds"] += 1
        sector_map[sector]["total"] += amount

    result = sorted(
        [
            {"sector": s, "rounds": v["rounds"], "totalUsd": _fmt_usd(v["total"]), "_raw": v["total"]}
            for s, v in sector_map.items()
        ],
        key=lambda x: x["_raw"],
        reverse=True,
    )
    for r in result:
        del r["_raw"]

    return result[:5]
