import logging
import httpx
import backend.cache as cache
from backend.services.sosovalue import SoSoValueClient

logger = logging.getLogger(__name__)


async def fetch_fear_greed() -> tuple[int, str] | None:
    """Fetch crypto fear/greed index from alternative.me — free, no auth, separate from SoSoValue rate limit."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get("https://api.alternative.me/fng/")
            r.raise_for_status()
            entry = (r.json().get("data") or [{}])[0]
            return int(entry.get("value", 0)), entry.get("value_classification", "").upper()
    except Exception as exc:
        logger.warning("[currency] fear/greed fetch failed: %s", exc)
        return None


async def fetch_global_market() -> dict | None:
    """Total crypto market cap + 24h volume + 24h mcap change from CoinGecko /global.

    Free, no API key. SoSoValue exposes no total-market endpoint, so this is the
    only source for a true market-wide figure. Called ~hourly (not per 30s tick)
    to stay well within CoinGecko's free rate limit."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get("https://api.coingecko.com/api/v3/global")
            r.raise_for_status()
            d = r.json().get("data") or {}
        mcap = float((d.get("total_market_cap") or {}).get("usd") or 0)
        vol = float((d.get("total_volume") or {}).get("usd") or 0)
        if mcap <= 0:
            return None
        return {
            "mcap": _fmt_large(mcap),
            "vol": _fmt_large(vol),
            "mcapChange": _fmt_change(float(d.get("market_cap_change_percentage_24h_usd") or 0) / 100),
        }
    except Exception as exc:
        logger.warning("[currency] global market fetch failed: %s", exc)
        return None

async def fetch_token_prices() -> dict[str, dict] | None:
    """Live price + 24h change for the top-500 tokens by market cap, keyed by
    upper-case symbol, from CoinGecko /coins/markets.

    SoSoValue has no bulk price endpoint (each currency needs a numeric ID), so
    this is the only practical source for per-token TOP TOKENS prices beyond
    BTC/ETH. Free, no API key. Called ~hourly (not per 30s tick) to respect
    CoinGecko's free rate limit — two pages of 250 per cycle catches mid-cap
    sector constituents (IMX, etc.) that drop below rank 250 in a down market.
    First occurrence of a symbol wins (highest market cap), resolving collisions
    like 'M'/'NFT' to the largest coin."""
    rows: list[dict] = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for page in (1, 2):
                r = await client.get(
                    "https://api.coingecko.com/api/v3/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "order": "market_cap_desc",
                        "per_page": 250,
                        "page": page,
                        "price_change_percentage": "24h",
                    },
                )
                r.raise_for_status()
                page_rows = r.json() or []
                rows.extend(page_rows)
                if len(page_rows) < 250:
                    break  # last page reached
    except Exception as exc:
        logger.warning("[currency] token prices fetch failed: %s", exc)
        return rows and _rows_to_prices(rows) or None

    return _rows_to_prices(rows)


def _rows_to_prices(rows: list[dict]) -> dict[str, dict] | None:
    out: dict[str, dict] = {}
    for row in rows:
        sym = str(row.get("symbol") or "").upper()
        price = float(row.get("current_price") or 0)
        if not sym or not price or sym in out:
            continue
        change = float(row.get("price_change_percentage_24h") or 0) / 100
        out[sym] = {
            "price": _fmt_token_price(price),
            "change": _fmt_change(change),
            "positive": change >= 0,
        }
    return out or None


# Stable numeric currency IDs from GET /currencies list
BTC_ID = "1673723677362319866"
ETH_ID = "1673723677362319867"


def _fmt_price(usd: float) -> str:
    return f"${usd:,.0f}"


def _fmt_token_price(usd: float) -> str:
    """Price formatter for alt-tokens — keeps precision for sub-$1 coins so
    DOGE/ONDO/SHIB don't collapse to '$0' the way whole-dollar _fmt_price does."""
    if usd >= 1000:
        return f"${usd:,.0f}"
    if usd >= 1:
        return f"${usd:,.2f}"
    if usd >= 0.01:
        return f"${usd:.4f}"
    if usd >= 0.0001:
        return f"${usd:.6f}"
    if usd > 0:
        return f"${usd:.8f}"  # ultra-low caps (APENFT etc.) — avoid "$0.000000"
    return "$0"


def _fmt_large(usd: float) -> str:
    if usd >= 1_000_000_000_000:
        return f"${usd / 1_000_000_000_000:.2f}T"
    if usd >= 1_000_000_000:
        return f"${usd / 1_000_000_000:.0f}B"
    return f"${usd / 1_000_000:.0f}M"


def _fmt_change(pct: float) -> str:
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct * 100:.1f}%"


def _sentiment(btc_change: float) -> tuple[str, bool]:
    if btc_change > 0.01:
        return "RISK-ON", True
    if btc_change < -0.01:
        return "RISK-OFF", False
    return "NEUTRAL", True


async def fetch_btc_eth_prices(client: SoSoValueClient) -> tuple[dict, dict]:
    """Return (btc_token, eth_token) dicts ready for topTokens from CoinGecko, or placeholders."""
    placeholder = lambda sym: {"symbol": sym, "price": "—", "change": "—", "positive": True}
    prices = await _fetch_btc_eth_from_coingecko()
    if prices is None:
        return placeholder("BTC"), placeholder("ETH")
    btc_price, btc_change, eth_price, eth_change = prices
    return (
        {"symbol": "BTC", "price": _fmt_price(btc_price), "change": _fmt_change(btc_change), "positive": btc_change >= 0},
        {"symbol": "ETH", "price": _fmt_price(eth_price), "change": _fmt_change(eth_change), "positive": eth_change >= 0},
    )


async def fetch_btc_price_usd(client: SoSoValueClient) -> float:
    """Return current BTC price as a raw float from CoinGecko, or raise on failure."""
    prices = await _fetch_btc_eth_from_coingecko()
    if prices is None or prices[0] <= 0:
        raise ValueError("BTC price unavailable from CoinGecko")
    return prices[0]


async def _fetch_btc_eth_from_coingecko() -> tuple[float, float, float, float] | None:
    """Return (btc_price, btc_change, eth_price, eth_change) from CoinGecko /simple/price.
    Fast, free, no auth. Returns None on failure."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": "bitcoin,ethereum",
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                },
            )
            r.raise_for_status()
            d = r.json()
        btc = d.get("bitcoin") or {}
        eth = d.get("ethereum") or {}
        btc_price = float(btc.get("usd") or 0)
        eth_price = float(eth.get("usd") or 0)
        if not btc_price or not eth_price:
            return None
        btc_change = float(btc.get("usd_24h_change") or 0) / 100
        eth_change = float(eth.get("usd_24h_change") or 0) / 100
        return btc_price, btc_change, eth_price, eth_change
    except Exception as exc:
        logger.warning("[currency] coingecko simple/price failed: %s", exc)
        return None


async def fetch_market_status(client: SoSoValueClient) -> dict:
    from backend.data.hardcoded import MARKET_STATUS

    def _fallback_status() -> dict:
        base = dict(MARKET_STATUS)
        base.setdefault("btcPriceRaw", 0.0)
        base.setdefault("ethPriceRaw", 0.0)
        return base

    prices = await _fetch_btc_eth_from_coingecko()
    if prices is None:
        logger.warning("[currency] market status: coingecko failed, returning fallback")
        return _fallback_status()

    btc_price, btc_change, eth_price, eth_change = prices
    sentiment, positive = _sentiment(btc_change)

    fg = await fetch_fear_greed()

    base = dict(MARKET_STATUS)
    base.update({
        "btcPrice": _fmt_price(btc_price),
        "btcChange": _fmt_change(btc_change),
        "ethPrice": _fmt_price(eth_price),
        "ethChange": _fmt_change(eth_change),
        "mcap": base["mcap"],
        "mcapChange": "—",
        "vol": base["vol"],
        "volChange": "—",
        "sentiment": sentiment,
        "sentimentPositive": positive,
        "btcPriceRaw": btc_price,
        "ethPriceRaw": eth_price,
    })
    if fg:
        base["fearGreed"] = fg[0]
        base["fearGreedLabel"] = fg[1]

    # Override mcap/vol with true market-wide totals from CoinGecko (cached
    # hourly under "global_market"); fall back to hardcoded placeholder.
    glob = cache.get("global_market")
    if isinstance(glob, dict):
        base["mcap"] = glob.get("mcap", base["mcap"])
        base["vol"] = glob.get("vol", base["vol"])
        base["mcapChange"] = glob.get("mcapChange", base["mcapChange"])

    return base
