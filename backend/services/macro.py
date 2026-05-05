import logging
from datetime import date, datetime
from backend.services.sosovalue import SoSoValueClient

logger = logging.getLogger(__name__)

HIGH_IMPACT_KEYWORDS = {
    "cpi", "fomc", "federal reserve", "nonfarm", "payroll", "ppi",
    "gdp", "interest rate", "rate decision", "inflation",
}


def _days_until(date_str: str) -> int:
    try:
        event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (event_date - date.today()).days
    except Exception:
        return 999


def _is_high_impact(events: list[str]) -> bool:
    joined = " ".join(events).lower()
    return any(k in joined for k in HIGH_IMPACT_KEYWORDS)


async def fetch_macro_events(client: SoSoValueClient) -> list[dict]:
    """Returns upcoming macro events with days_until and impact flag."""
    try:
        raw = await client.get_macro_events()
        rows = raw.get("data") or []
        result = []
        for row in rows:
            days = _days_until(row.get("date", ""))
            if days < 0:
                continue
            events = row.get("events") or []
            result.append({
                "date": row.get("date", ""),
                "days_until": days,
                "events": events,
                "high_impact": _is_high_impact(events),
            })
        return result
    except Exception as exc:
        logger.warning("[macro] fetch failed: %s", exc)
        return []


async def fetch_macro_indicators(client: SoSoValueClient) -> list[dict]:
    """Frontend-friendly format for /api/macro — lists upcoming events as indicator rows."""
    events = await fetch_macro_events(client)
    result = []
    for ev in events[:7]:
        days = ev["days_until"]
        label = "today" if days == 0 else f"in {days}d"
        warning = ev["high_impact"] and days <= 7
        result.append({
            "name": ", ".join(ev["events"][:2]),
            "value": label,
            "arrow": "⚠️" if warning else "",
            "warning": warning,
        })
    return result
