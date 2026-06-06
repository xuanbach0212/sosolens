import logging
import httpx
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

# Stable numeric currency IDs from GET /currencies list
BTC_ID = "1673723677362319866"
ETH_ID = "1673723677362319867"


def _fmt_price(usd: float) -> str:
    return f"${usd:,.0f}"


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
    """Return (btc_token, eth_token) dicts ready for topTokens, or placeholder dicts on failure."""
    placeholder = lambda sym: {"symbol": sym, "price": "—", "change": "—", "positive": True}
    try:
        btc_raw = (await client.get_currency_snapshot(BTC_ID)).get("data") or {}
        eth_raw = (await client.get_currency_snapshot(ETH_ID)).get("data") or {}
    except Exception as exc:
        logger.warning("[currency] price fetch failed: %s", exc)
        return placeholder("BTC"), placeholder("ETH")

    def _token(sym: str, raw: dict) -> dict:
        price = float(raw.get("price") or 0)
        change = float(raw.get("change_pct_24h") or 0)
        if not price:
            return {"symbol": sym, "price": "—", "change": "—", "positive": True}
        return {
            "symbol": sym,
            "price": _fmt_price(price),
            "change": _fmt_change(change),
            "positive": change >= 0,
        }

    return _token("BTC", btc_raw), _token("ETH", eth_raw)


async def fetch_btc_price_usd(client: SoSoValueClient) -> float:
    """Return current BTC price as a raw float, or raise on failure."""
    raw = (await client.get_currency_snapshot(BTC_ID)).get("data") or {}
    price = float(raw.get("price") or 0)
    if price <= 0:
        raise ValueError("BTC price returned zero from API")
    return price


async def fetch_market_status(client: SoSoValueClient) -> dict:
    from backend.data.hardcoded import MARKET_STATUS

    def _fallback_status() -> dict:
        base = dict(MARKET_STATUS)
        base.setdefault("btcPriceRaw", 0.0)
        base.setdefault("ethPriceRaw", 0.0)
        return base

    try:
        btc_raw = (await client.get_currency_snapshot(BTC_ID)).get("data") or {}
        eth_raw = (await client.get_currency_snapshot(ETH_ID)).get("data") or {}
    except Exception as exc:
        logger.warning("[currency] snapshot failed: %s", exc)
        return _fallback_status()

    btc_price = float(btc_raw.get("price") or 0)
    eth_price = float(eth_raw.get("price") or 0)
    if not btc_price or not eth_price:
        return _fallback_status()

    btc_change = float(btc_raw.get("change_pct_24h") or 0)
    eth_change = float(eth_raw.get("change_pct_24h") or 0)
    btc_mcap = float(btc_raw.get("marketcap") or 0)
    eth_mcap = float(eth_raw.get("marketcap") or 0)
    btc_vol = float(btc_raw.get("turnover_24h") or 0)
    eth_vol = float(eth_raw.get("turnover_24h") or 0)

    total_mcap = btc_mcap + eth_mcap
    total_vol = btc_vol + eth_vol
    sentiment, positive = _sentiment(btc_change)

    # Derive aggregate 24h mcap change from individual 24h changes (supply ~constant over 24h).
    mcap_change_str = "—"
    if btc_mcap and eth_mcap:
        btc_mcap_y = btc_mcap / (1 + btc_change) if (1 + btc_change) != 0 else 0
        eth_mcap_y = eth_mcap / (1 + eth_change) if (1 + eth_change) != 0 else 0
        total_y = btc_mcap_y + eth_mcap_y
        if total_y > 0:
            mcap_change_str = _fmt_change((total_mcap - total_y) / total_y)

    fg = await fetch_fear_greed()

    base = dict(MARKET_STATUS)
    base.update({
        "btcPrice": _fmt_price(btc_price),
        "btcChange": _fmt_change(btc_change),
        "ethPrice": _fmt_price(eth_price),
        "ethChange": _fmt_change(eth_change),
        "mcap": _fmt_large(total_mcap) if total_mcap else base["mcap"],
        "mcapChange": mcap_change_str,
        "vol": _fmt_large(total_vol) if total_vol else base["vol"],
        "volChange": "—",  # no 24h volume history available from the API
        "sentiment": sentiment,
        "sentimentPositive": positive,
        "btcPriceRaw": btc_price,
        "ethPriceRaw": eth_price,
    })
    if fg:
        base["fearGreed"] = fg[0]
        base["fearGreedLabel"] = fg[1]
    return base
