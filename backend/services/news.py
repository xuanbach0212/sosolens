import re
import logging
from backend.services.sosovalue import SoSoValueClient

logger = logging.getLogger(__name__)

_MACRO_KEYWORDS = frozenset([
    "fed", "federal reserve", "fomc", "rate", "inflation", "cpi",
    "interest", "recession", "gdp", "unemployment", "nonfarm",
    "payroll", "treasury", "yield", "powell", "dxy", "ppi",
])

_RAISE_PATTERN = re.compile(r'\$\s*([\d,.]+)\s*(million|billion|M\b|B\b)', re.IGNORECASE)
_RAISE_KEYWORDS = frozenset(["raise", "raised", "funding", "round", "invest", "backed", "capital"])

_SECTOR_MAP = {
    "DeFi":    ["defi", "dex", "yield", "liquidity", "lending", "uniswap", "aave", "compound"],
    "AI":      ["ai ", "artificial intelligence", "machine learning", "gpu", "llm"],
    "RWA":     ["rwa", "real-world asset", "tokenized", "real estate", "commodity"],
    "L1":      ["layer 1", "layer one", "l1 ", "solana", "avalanche", "cosmos"],
    "L2":      ["layer 2", "layer two", "l2 ", "rollup", "optimism", "arbitrum", "polygon"],
    "Gaming":  ["gaming", "game", "nft", "metaverse", "play-to-earn"],
    "Infra":   ["infrastructure", "node", "validator", "bridge", "oracle", "protocol"],
}

_SOURCE_RE = re.compile(r'\[([^\]]+)\]\s*$')


def _is_macro_sensitive(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _MACRO_KEYWORDS)


def _fmt_usd(usd: float) -> str:
    if usd >= 1_000_000_000:
        return f"${usd / 1_000_000_000:.1f}B"
    if usd >= 1_000_000:
        return f"${usd / 1_000_000:.0f}M"
    return f"${usd:,.0f}"


def _classify_sector(text: str) -> str:
    lower = text.lower()
    for sector, keywords in _SECTOR_MAP.items():
        if any(kw in lower for kw in keywords):
            return sector
    return "Other"


def _extract_vc_activity(items: list[dict]) -> list[dict]:
    sector_map: dict[str, dict] = {}
    for item in items:
        content = item.get("content", "")
        lower = content.lower()
        if not any(kw in lower for kw in _RAISE_KEYWORDS):
            continue
        match = _RAISE_PATTERN.search(content)
        if not match:
            continue
        amount_str = match.group(1).replace(",", "")
        unit = match.group(2).lower()
        amount = float(amount_str)
        if unit in ("billion", "b"):
            amount *= 1_000_000_000
        else:
            amount *= 1_000_000

        sector = _classify_sector(item.get("title", "") + " " + content)
        if sector not in sector_map:
            sector_map[sector] = {"rounds": 0, "total": 0.0}
        sector_map[sector]["rounds"] += 1
        sector_map[sector]["total"] += amount

    result = sorted(
        [{"sector": s, "rounds": v["rounds"], "totalUsd": _fmt_usd(v["total"]), "_raw": v["total"]}
         for s, v in sector_map.items()],
        key=lambda x: x["_raw"],
        reverse=True,
    )
    for r in result:
        del r["_raw"]
    return result[:5]


async def fetch_news_headlines(client: SoSoValueClient) -> tuple[list[str], list[dict], list[dict]]:
    try:
        raw = await client.get_news()
    except Exception as exc:
        logger.warning("[news] fetch failed: %s", exc)
        return [], [], []

    items = raw.get("data", {}).get("list") or []
    if not isinstance(items, list) or not items:
        return [], [], []

    headlines = []
    for item in items[:6]:
        title = item.get("title", "")
        if not title:
            continue
        content = item.get("content", "")
        src_match = _SOURCE_RE.search(content.strip())
        source = src_match.group(1) if src_match else "SoSoValue"
        headlines.append({
            "text": title,
            "source": source,
            "macroSensitive": _is_macro_sensitive(title),
        })

    briefing = [h["text"] for h in headlines[:3]]
    vc_activity = _extract_vc_activity(items)
    return briefing, headlines, vc_activity
