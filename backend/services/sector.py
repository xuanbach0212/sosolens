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

# CoinGecko slug → exchange ticker for slugs that aren't guessable
_SLUG_TO_TICKER: dict[str, str] = {
    "fetch-ai":           "FET",
    "worldcoin":          "WLD",
    "bittensor":          "TAO",
    "virtuals-protocol":  "VIRTUAL",
    "venice-token":       "VVV",
    "uniswap":            "UNI",
    "curve-dao-token":    "CRV",
    "maker":              "MKR",
    "aave":               "AAVE",
    "optimism":           "OP",
    "polygon":            "MATIC",
    "arbitrum":           "ARB",
    "avalanche-2":        "AVAX",
    "solana":             "SOL",
    "ethereum":           "ETH",
    "bitcoin":            "BTC",
    "axie-infinity":      "AXS",
    "illuvium":           "ILV",
    "the-sandbox":        "SAND",
    "apecoin":            "APE",
    "dogecoin":           "DOGE",
    "shiba-inu":          "SHIB",
}


def _slug_to_ticker(slug: str) -> str:
    if slug in _SLUG_TO_TICKER:
        return _SLUG_TO_TICKER[slug]
    # Already looks like a ticker (short, uppercase, no hyphens)
    if slug.isupper() and len(slug) <= 8:
        return slug
    # Slug like "render" → "RENDER", "fartcoin" → "FARTCOIN"
    base = slug.split("-")[0].upper()
    return base[:8]


async def fetch_sector_flows(client: SoSoValueClient) -> list[dict]:
    result = []
    for display_name, ticker in SECTOR_MAP:
        try:
            raw = await client.get_index_snapshot(ticker)
            data = raw.get("data") or {}
            change_pct = float(data.get("change_pct_24h") or 0) * 100

            # Fetch top 3 constituents by weight
            try:
                craw = await client.get_index_constituents(ticker)
                constituents = craw.get("data") or []
                constituents.sort(key=lambda c: float(c.get("weight") or 0), reverse=True)
                top_tokens = [_slug_to_ticker(c["symbol"]) for c in constituents[:3] if c.get("symbol")]
            except Exception as exc:
                logger.warning("[sector] %s constituents failed: %s", display_name, exc)
                top_tokens = []

            result.append({
                "name": display_name,
                "change": round(change_pct, 1),
                "arrows": _arrows(change_pct),
                "positive": change_pct >= 0,
                "tokens": top_tokens,
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
