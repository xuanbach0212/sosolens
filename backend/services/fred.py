"""Real macro indicator values from FRED (Federal Reserve Economic Data).

SoSoValue exposes only a macro *event calendar* (CPI/FOMC dates), not the
actual indicator levels the MACRO STATUS panel is meant to show. FRED is the
canonical free source for these. Requires a free FRED_API_KEY; when it is
unset (or a fetch fails) the callers fall back to the event-calendar-derived
rows, so this is a pure enhancement with no hard dependency.

Refreshed on the 30-min macro cache cycle — well within FRED's rate limits.
"""
import logging
import os
import httpx

logger = logging.getLogger(__name__)

_FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# (panel label, FRED series id, units, value formatter)
#   DFF        — effective federal funds rate (daily, already a %)
#   CPIAUCSL   — CPI; units=pc1 gives "percent change from year ago" → YoY %
#   DGS10      — 10-year Treasury constant-maturity yield (daily, %)
#   DTWEXBGS   — Nominal Broad US Dollar Index (FRED's DXY analogue)
_SERIES: list[tuple[str, str, str, callable]] = [
    ("Fed Rate",  "DFF",      "lin", lambda v: f"{v:.2f}%"),
    ("CPI YoY",   "CPIAUCSL", "pc1", lambda v: f"{v:.1f}%"),
    ("10Y Yield", "DGS10",    "lin", lambda v: f"{v:.2f}%"),
    ("USD Index", "DTWEXBGS", "lin", lambda v: f"{v:.1f}"),
]


async def _latest_value(client: httpx.AsyncClient, series_id: str, units: str, api_key: str) -> float | None:
    """Most recent non-missing observation for a FRED series."""
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "units": units,
        "sort_order": "desc",
        "limit": 5,  # a few rows so a trailing "." missing value doesn't blank us out
    }
    r = await client.get(_FRED_BASE, params=params)
    r.raise_for_status()
    for obs in (r.json().get("observations") or []):
        val = obs.get("value")
        if val not in (None, ".", ""):
            return float(val)
    return None


async def fetch_fred_indicators() -> list[dict] | None:
    """MACRO STATUS rows (Fed rate, CPI YoY, 10Y yield, USD index) from FRED.

    Returns None when FRED_API_KEY is unset or the whole fetch fails, signalling
    callers to fall back to the SoSoValue event-calendar-derived indicators.
    """
    api_key = os.environ.get("FRED_API_KEY", "").strip()
    if not api_key:
        return None

    rows: list[dict] = []
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            for label, series_id, units, fmt in _SERIES:
                try:
                    val = await _latest_value(client, series_id, units, api_key)
                except Exception as exc:
                    logger.warning("[fred] %s fetch failed: %s", series_id, exc)
                    continue
                if val is None:
                    continue
                rows.append({"name": label, "value": fmt(val), "arrow": "", "warning": False})
    except Exception as exc:
        logger.warning("[fred] indicators fetch failed: %s", exc)
        return None

    return rows or None
