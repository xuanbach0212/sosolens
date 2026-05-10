import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.agent.db import get_db
from backend.agent.detectors import DETECTORS
from backend.agent.scorer import score_signal
from backend.agent.explainer import explain_signal
from backend.agent.models import Signal
import backend.cache as cache
from backend.events import broadcast
from backend.data.hardcoded import (
    SIGNALS, SIGNAL_STATS, MARKET_STATUS, SECTOR_FLOWS,
    ETF_FLOWS, MACRO_STATUS, BTC_TREASURIES, VC_ACTIVITY,
    AI_BRIEFING, NEWS_HEADLINES,
)

logger = logging.getLogger(__name__)


async def _refresh_macro_cache() -> None:
    """Refresh macro cache independently — runs every 30 min."""
    from backend.services.sosovalue import get_client
    from backend.services.macro import (
        fetch_macro_indicators,
        get_macro_status,
        get_upcoming_events,
        get_risk_environment,
    )
    client = get_client()
    try:
        cache.set("macro_status", {
            "indicators": await fetch_macro_indicators(client),
            "macro_status": await get_macro_status(client),
            "upcoming_events": await get_upcoming_events(client, days=14),
            "risk_environment": await get_risk_environment(client),
        })
        logger.info("[agent] cache: macro_status updated (30-min)")
    except Exception as exc:
        logger.warning("[agent] cache: macro_refresh failed: %s", exc)


async def _refresh_panel_cache() -> None:
    """Fetch slow panel data in background and store in cache for REST endpoints."""
    from backend.services.sosovalue import get_client
    from backend.services.etf import fetch_etf_snapshot
    from backend.services.sector import fetch_sector_flows
    from backend.services.btc_treasuries import fetch_btc_treasuries
    from backend.services.news import fetch_news_headlines, fetch_fundraising
    from backend.services.currency import fetch_market_status
    client = get_client()
    try:
        cache.set("etf_flows", await fetch_etf_snapshot(client))
        logger.info("[agent] cache: etf_flows updated")
    except Exception as exc:
        logger.warning("[agent] cache: etf_flows failed: %s", exc)
    try:
        cache.set("sector_flows", await fetch_sector_flows(client))
        logger.info("[agent] cache: sector_flows updated")
    except Exception as exc:
        logger.warning("[agent] cache: sector_flows failed: %s", exc)
    await _refresh_macro_cache()
    try:
        cache.set("btc_treasuries", await fetch_btc_treasuries(client))
        logger.info("[agent] cache: btc_treasuries updated")
    except Exception as exc:
        logger.warning("[agent] cache: btc_treasuries failed: %s", exc)
    try:
        briefing, headlines = await fetch_news_headlines(client)
        if briefing or headlines:
            cache.set("news", {"briefing": briefing, "headlines": headlines})
            logger.info("[agent] cache: news updated")
        vc = await fetch_fundraising(client)
        if vc:
            cache.set("vc_activity", vc)
            logger.info("[agent] cache: vc_activity updated")
    except Exception as exc:
        logger.warning("[agent] cache: news/vc_activity failed: %s", exc)
    try:
        cache.set("market_status", await fetch_market_status(client))
        logger.info("[agent] cache: market_status updated")
    except Exception as exc:
        logger.warning("[agent] cache: market_status failed: %s", exc)


def build_full_snapshot() -> dict:
    with get_db() as db:
        rows = db.query(Signal).all()
        now = datetime.now(timezone.utc)
        payloads = []
        for s in rows:
            p = dict(s.payload)
            updated = s.updated_at
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            delta = now - updated
            hours = int(delta.total_seconds() // 3600)
            p["timeAgo"] = f"{hours}h" if hours < 24 else f"{delta.days}d"
            payloads.append(p)

    signals = payloads if payloads else SIGNALS
    stats = (
        {"today": len(signals), "thisWeek": len(signals), "accuracy": SIGNAL_STATS["accuracy"]}
        if payloads else SIGNAL_STATS
    )

    cached_macro = cache.get("macro_status")
    if isinstance(cached_macro, dict) and "indicators" in cached_macro:
        macro = {
            "macroStatus": cached_macro.get("indicators") or MACRO_STATUS,
            "riskEnvironment": cached_macro.get("risk_environment", "neutral"),
            "upcomingEvents": cached_macro.get("upcoming_events", []),
            "macroStatusDetail": cached_macro.get("macro_status", {}),
        }
    else:
        macro = {"macroStatus": cached_macro or MACRO_STATUS}

    cached_news = cache.get("news")
    news = (
        {"aiBriefing": cached_news.get("briefing", []), "newsHeadlines": cached_news.get("headlines", [])}
        if cached_news
        else {"aiBriefing": AI_BRIEFING, "newsHeadlines": NEWS_HEADLINES}
    )

    return {
        "signals": signals,
        "stats": stats,
        "market": cache.get("market_status") or MARKET_STATUS,
        "sectorFlows": cache.get("sector_flows") or SECTOR_FLOWS,
        "etfFlows": cache.get("etf_flows") or ETF_FLOWS,
        **macro,
        "btcTreasuries": cache.get("btc_treasuries") or BTC_TREASURIES,
        "vcActivity": cache.get("vc_activity") or VC_ACTIVITY,
        **news,
    }


async def run_agent() -> None:
    logger.info(f"[agent] run_agent: {len(DETECTORS)} detectors loaded")
    if not DETECTORS:
        logger.info("[agent] No detectors registered — nothing to do")
        return

    generated = 0
    for detector in DETECTORS:
        raw_signals = await detector.run()
        for raw in raw_signals:
            scores = score_signal(raw)
            explanation = await explain_signal(raw)
            payload = {**raw, **scores, "explanation": explanation}

            with get_db() as db:
                existing = db.query(Signal).filter_by(signal_id=raw["id"]).first()
                if existing:
                    existing.type = payload["type"]
                    existing.sector = payload["sector"]
                    existing.confidence = payload["confidence"]
                    existing.risk = payload["risk"]
                    existing.explanation = explanation
                    existing.payload = payload
                    existing.updated_at = datetime.now(timezone.utc)
                else:
                    db.add(Signal(
                        signal_id=raw["id"],
                        type=payload["type"],
                        sector=payload["sector"],
                        confidence=payload["confidence"],
                        risk=payload["risk"],
                        explanation=explanation,
                        payload=payload,
                    ))
            generated += 1

    await _refresh_panel_cache()
    await broadcast(build_full_snapshot())
    logger.info("[agent] run_agent done — %d signals upserted, SSE broadcast sent", generated)


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_agent, "interval", hours=1, id="agent_hourly")
    scheduler.add_job(_refresh_macro_cache, "interval", minutes=30, id="macro_30min")
    scheduler.start()
    logger.info("[agent] Scheduler started — run_agent hourly, macro refresh every 30 min")
    return scheduler
