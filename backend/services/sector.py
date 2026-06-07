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

# SoSoValue constituent slug → exchange ticker, for slugs that aren't a clean
# uppercase of the leading word. Covers the current top constituents of every
# sector index; unknown slugs fall back to _slug_to_ticker() below.
_SLUG_TO_TICKER: dict[str, str] = {
    # AI
    "bittensor":          "TAO",
    "worldcoin":          "WLD",
    "render":             "RENDER",
    "fetch-ai":           "FET",
    "virtuals-protocol":  "VIRTUAL",
    "venice-token":       "VVV",
    # DeFi
    "hyperliquid":        "HYPE",
    "chainlink":          "LINK",
    "uniswap":            "UNI",
    "curve-dao-token":    "CRV",
    "maker":              "MKR",
    "aave":               "AAVE",
    "morpho-token":       "MORPHO",
    # RWA
    "ondo-finance":       "ONDO",
    "pendle":             "PENDLE",
    "keeta":              "KTA",
    "creditcoin":         "CTC",
    # Layer 1
    "ethereum":           "ETH",
    "binance-coin":       "BNB",
    "solana":             "SOL",
    "avalanche-2":        "AVAX",
    "avalanche":          "AVAX",
    "bitcoin":            "BTC",
    "tron":               "TRX",
    "cardano":            "ADA",
    "toncoin":            "TON",
    # Layer 2
    "mantle":             "MNT",
    "polygon-ex-matic":   "POL",
    "polygon":            "POL",
    "arbitrum":           "ARB",
    "optimism":           "OP",
    "stacks":             "STX",
    "celestia":           "TIA",
    # Gaming
    "axie-infinity":      "AXS",
    "the-sandbox":        "SAND",
    "decentraland":       "MANA",
    "illuvium":           "ILV",
    "immutablex":         "IMX",
    # NFT
    "pudgy-penguins":     "PENGU",
    "apenft":             "NFT",
    "apecoin":            "APE",
    "superverse":         "SUPER",
    # Meme
    "dogecoin":           "DOGE",
    "memecore":           "M",
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
            # roi_7d matches the "SECTOR FLOWS · 7D" panel label; fall back to
            # 24h change only if 7d ROI is missing.
            roi_7d = data.get("roi_7d")
            change_frac = roi_7d if roi_7d is not None else (data.get("change_pct_24h") or 0)
            change_pct = float(change_frac) * 100

            # Fetch top 6 constituents by weight (fills the 3-col grid as 2 rows)
            try:
                craw = await client.get_index_constituents(ticker)
                constituents = craw.get("data") or []
                constituents.sort(key=lambda c: float(c.get("weight") or 0), reverse=True)
                top_tokens = [_slug_to_ticker(c["symbol"]) for c in constituents[:6] if c.get("symbol")]
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
