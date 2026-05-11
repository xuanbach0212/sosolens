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
        result.sort(key=lambda e: e["days_until"])
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


_INDICATOR_KEYWORDS: dict[str, set[str]] = {
    "fed_rate": {"fomc", "federal reserve", "rate decision", "interest rate"},
    "cpi":      {"cpi", "inflation"},
    "gdp":      {"gdp"},
    "nfp":      {"nonfarm", "payroll"},
    "ppi":      {"ppi"},
}


async def get_upcoming_events(client: SoSoValueClient, days: int = 14) -> list[dict]:
    """Upcoming macro events within the given day window."""
    events = await fetch_macro_events(client)
    return [e for e in events if e["days_until"] <= days]


async def get_macro_status(client: SoSoValueClient) -> dict:
    """Named macro indicator status derived from event calendar titles.

    Returns None for each indicator not found in the upcoming event stream.
    """
    events = await fetch_macro_events(client)
    result: dict = {k: None for k in _INDICATOR_KEYWORDS}
    for ev in events:
        joined = " ".join(ev["events"]).lower()
        for indicator, keywords in _INDICATOR_KEYWORDS.items():
            if result[indicator] is None and any(k in joined for k in keywords):
                result[indicator] = {
                    "label": ", ".join(ev["events"][:2]),
                    "days_until": ev["days_until"],
                    "direction": "watch" if ev["days_until"] <= 7 else "neutral",
                }
    return result


async def get_risk_environment(client: SoSoValueClient) -> str:
    """Returns 'risk-on', 'risk-off', or 'neutral' based on nearest high-impact event."""
    events = await fetch_macro_events(client)
    nearest_high = next((e for e in events if e["high_impact"]), None)
    if nearest_high is None:
        return "risk-on"
    if nearest_high["days_until"] <= 3:
        return "risk-off"
    return "neutral"
