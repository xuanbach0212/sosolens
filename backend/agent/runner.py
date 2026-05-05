import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.agent.db import get_db
from backend.agent.detectors import DETECTORS
from backend.agent.scorer import score_signal
from backend.agent.explainer import explain_signal
from backend.agent.models import Signal
import backend.cache as cache

logger = logging.getLogger(__name__)


async def _refresh_panel_cache() -> None:
    """Fetch slow panel data in background and store in cache for REST endpoints."""
    from backend.services.sosovalue import get_client
    from backend.services.etf import fetch_etf_snapshot
    from backend.services.sector import fetch_sector_flows
    from backend.services.macro import fetch_macro_indicators
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
    try:
        cache.set("macro_status", await fetch_macro_indicators(client))
        logger.info("[agent] cache: macro_status updated")
    except Exception as exc:
        logger.warning("[agent] cache: macro_status failed: %s", exc)
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

    logger.info(f"[agent] run_agent done — {generated} signals upserted")
    await _refresh_panel_cache()


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_agent, "interval", hours=1, id="agent_hourly")
    scheduler.start()
    logger.info("[agent] Scheduler started — run_agent fires every hour")
    return scheduler
