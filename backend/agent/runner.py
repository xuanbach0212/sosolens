import asyncio
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, delete
import httpx
from backend.agent.db import get_db
from backend.agent.detectors import DETECTORS
from backend.agent.scorer import score_signal
from backend.agent.explainer import explain_signal
from backend.agent.models import Signal, SignalOutcome, PriceSnapshot, EtfSnapshot
import backend.cache as cache
from backend.events import broadcast
from backend.data.hardcoded import (
    MARKET_STATUS, SECTOR_FLOWS,
    ETF_FLOWS, MACRO_STATUS, BTC_TREASURIES, VC_ACTIVITY,
    AI_BRIEFING, NEWS_HEADLINES,
)

logger = logging.getLogger(__name__)

_CACHE_WORKER_URL = os.environ.get("CACHE_WORKER_URL", "")
_CACHE_PUSH_SECRET = os.environ.get("CACHE_PUSH_SECRET", "")

_background_tasks: set[asyncio.Task] = set()

# Outcome resolution horizon — how long after a signal fires we measure its
# forward return (WIN/LOSS). A short horizon keeps SIMILAR PAST SIGNALS and the
# accuracy stats populated in near-real-time; set OUTCOME_HORIZON_HOURS=24 for a
# canonical daily window.
_OUTCOME_HORIZON_HOURS = int(os.environ.get("OUTCOME_HORIZON_HOURS", "4"))
# Skip logging a new outcome entry for a detector if one was logged within this
# window. Kept below the horizon so history accumulates steadily.
_OUTCOME_DEDUP_HOURS = int(os.environ.get("OUTCOME_DEDUP_HOURS", "3"))


async def _push_to_cache(snapshot: dict) -> None:
    if not _CACHE_WORKER_URL or not _CACHE_PUSH_SECRET:
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{_CACHE_WORKER_URL}/api/push",
                json=snapshot,
                headers={"X-Push-Secret": _CACHE_PUSH_SECRET},
            )
        logger.info("[cache] push ok — %d keys", len(snapshot))
    except Exception as exc:
        logger.warning("[cache] push failed: %s", exc)


async def _refresh_macro_cache() -> None:
    """Refresh macro cache independently — runs every 30 min."""
    from backend.services.sosovalue import get_client
    from backend.services.macro import fetch_macro_events, _INDICATOR_KEYWORDS
    from datetime import date
    client = get_client()
    try:
        events = await fetch_macro_events(client)

        indicators = []
        for ev in events[:7]:
            days = ev["days_until"]
            label = "today" if days == 0 else f"in {days}d"
            warning = ev["high_impact"] and days <= 7
            indicators.append({"name": ", ".join(ev["events"][:2]), "value": label, "arrow": "⚠️" if warning else "", "warning": warning})

        macro_status: dict = {k: None for k in _INDICATOR_KEYWORDS}
        for ev in events:
            joined = " ".join(ev["events"]).lower()
            for indicator, keywords in _INDICATOR_KEYWORDS.items():
                if macro_status[indicator] is None and any(k in joined for k in keywords):
                    macro_status[indicator] = {"label": ", ".join(ev["events"][:2]), "days_until": ev["days_until"], "direction": "watch" if ev["days_until"] <= 7 else "neutral"}

        upcoming = [e for e in events if e["days_until"] <= 14]
        nearest_high = next((e for e in events if e["high_impact"]), None)
        risk = "risk-off" if nearest_high and nearest_high["days_until"] <= 3 else ("neutral" if nearest_high else "risk-on")

        cache.put("macro_status", {"indicators": indicators, "macro_status": macro_status, "upcoming_events": upcoming, "risk_environment": risk})
        logger.info("[agent] cache: macro_status updated (30-min)")
    except Exception as exc:
        logger.warning("[agent] cache: macro_refresh failed: %s", exc)


async def _refresh_market_cache() -> None:
    """Refresh BTC/ETH price and broadcast a partial market update — runs every 30s."""
    from backend.services.sosovalue import get_client
    from backend.services.currency import fetch_market_status
    client = get_client()
    try:
        market = await fetch_market_status(client)
        cache.put("market_status", market)
        logger.info("[agent] cache: market_status updated (30s)")
    except Exception as exc:
        logger.warning("[agent] cache: market_30s failed: %s", exc)
        market = cache.get_or("market_status", MARKET_STATUS)
    else:
        btc_raw = market.get("btcPriceRaw", 0.0)
        eth_raw = market.get("ethPriceRaw", 0.0)
        if btc_raw > 0 and eth_raw > 0:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
            try:
                with get_db() as db:
                    db.add(PriceSnapshot(btc_price=btc_raw, eth_price=eth_raw))
                    db.execute(delete(PriceSnapshot).where(PriceSnapshot.recorded_at < cutoff))
            except Exception as db_exc:
                logger.warning("[agent] price_snapshot write failed: %s", db_exc)
    await broadcast({"market": market})
    cache.save_to_disk()
    _t = asyncio.create_task(_push_to_cache(build_full_snapshot()))
    _background_tasks.add(_t)
    _t.add_done_callback(_background_tasks.discard)


async def _refresh_panel_cache() -> None:
    """Fetch panel data and store in cache. Market status is fetched first (highest priority).
    ETF and sector flows are skipped if detectors already cached them this run."""
    from backend.services.sosovalue import get_client
    from backend.services.etf import fetch_etf_data
    from backend.services.sector import fetch_sector_flows
    from backend.services.btc_treasuries import fetch_btc_treasuries
    from backend.services.news import fetch_news_headlines
    from backend.services.currency import fetch_market_status, fetch_global_market
    client = get_client()
    # Total market cap/volume from CoinGecko — refreshed here (hourly) rather
    # than on the 30s tick to respect CoinGecko's free rate limit.
    try:
        glob = await fetch_global_market()
        if glob:
            cache.put("global_market", glob)
            logger.info("[agent] cache: global_market updated")
    except Exception as exc:
        logger.warning("[agent] cache: global_market failed: %s", exc)
    # Market status first — most visible data, fewest calls (2)
    try:
        cache.put("market_status", await fetch_market_status(client))
        logger.info("[agent] cache: market_status updated")
    except Exception as exc:
        logger.warning("[agent] cache: market_status failed: %s", exc)
    # ETF and sector: skip if detectors already populated cache this run
    if not cache.get("etf_flows"):
        try:
            snapshot, total, btc_raw, eth_raw = await fetch_etf_data(client)
            cache.put("etf_flows", snapshot)
            cache.put("etf_raw", {"btc": btc_raw, "eth": eth_raw, "total": total})
            logger.info("[agent] cache: etf_flows updated")
        except Exception as exc:
            logger.warning("[agent] cache: etf_flows failed: %s", exc)
    if not cache.get("sector_flows"):
        try:
            cache.put("sector_flows", await fetch_sector_flows(client))
            logger.info("[agent] cache: sector_flows updated")
        except Exception as exc:
            logger.warning("[agent] cache: sector_flows failed: %s", exc)
    await _refresh_macro_cache()
    if not cache.get("btc_treasuries"):
        try:
            cache.put("btc_treasuries", await fetch_btc_treasuries(client))
            logger.info("[agent] cache: btc_treasuries updated")
        except Exception as exc:
            logger.warning("[agent] cache: btc_treasuries failed: %s", exc)
    if not cache.get("news"):
        try:
            briefing, headlines, vc = await fetch_news_headlines(client)
            cache.put("news", {"briefing": briefing or [], "headlines": headlines or []})
            cache.put("vc_activity", vc if vc is not None else [])
            logger.info("[agent] cache: news+vc_activity updated")
        except Exception as exc:
            logger.warning("[agent] cache: news/vc_activity failed: %s", exc)


async def _refresh_ai_briefing() -> None:
    """Replace the raw-headline briefing with an LLM synthesis of current data.

    Runs after the panel cache is populated. Leaves the existing headline-based
    briefing in place if no AI provider is configured/available."""
    from backend.agent.explainer import generate_briefing
    news_cache = cache.get("news")
    if not isinstance(news_cache, dict):
        return
    headlines = news_cache.get("headlines", [])
    context = {
        "market": cache.get("market_status"),
        "sectorFlows": cache.get("sector_flows"),
        "etfFlows": cache.get("etf_flows"),
        "btcTreasuries": cache.get("btc_treasuries"),
        "headlines": [h.get("text") for h in headlines[:6] if isinstance(h, dict)],
    }
    try:
        bullets = await generate_briefing(context)
    except Exception as exc:
        logger.warning("[agent] AI briefing generation failed: %s", exc)
        return
    if bullets:
        news_cache["briefing"] = bullets
        cache.put("news", news_cache)
        logger.info("[agent] cache: AI briefing generated (%d points)", len(bullets))


_MAX_SIGNAL_AGE_HOURS = 25


def format_time_ago(delta: timedelta) -> str:
    """Mockup-style relative time label: 'just now' / '4m ago' / '2h ago' / '3d ago'."""
    secs = int(delta.total_seconds())
    if secs < 5 * 60:
        return "just now"
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 24 * 3600:
        return f"{secs // 3600}h ago"
    return f"{secs // (24 * 3600)}d ago"


def _record_signal_entries(active_signals: dict[str, str], btc_price: float) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=_OUTCOME_DEDUP_HOURS)
    with get_db() as db:
        for detector_id, signal_type in active_signals.items():
            recent = db.scalars(
                select(SignalOutcome)
                .where(SignalOutcome.detector_id == detector_id)
                .where(SignalOutcome.recorded_at >= cutoff)
            ).first()
            if recent:
                continue
            db.add(SignalOutcome(
                detector_id=detector_id,
                signal_type=signal_type,
                recorded_at=datetime.now(timezone.utc),
                entry_price=btc_price,
                outcome="SKIP" if signal_type == "WATCH" else None,
            ))


async def check_outcomes() -> None:
    from backend.services.sosovalue import get_client
    from backend.services.currency import fetch_btc_price_usd

    cutoff = datetime.now(timezone.utc) - timedelta(hours=_OUTCOME_HORIZON_HOURS)
    with get_db() as db:
        pending = db.scalars(
            select(SignalOutcome)
            .where(SignalOutcome.outcome.is_(None))
            .where(SignalOutcome.recorded_at <= cutoff)
        ).all()
        if not pending:
            return

    try:
        btc_price = await fetch_btc_price_usd(get_client())
    except Exception as exc:
        logger.warning("[outcomes] price fetch failed, will retry: %s", exc)
        return

    now = datetime.now(timezone.utc)
    with get_db() as db:
        for row in db.scalars(
            select(SignalOutcome)
            .where(SignalOutcome.outcome.is_(None))
            .where(SignalOutcome.recorded_at <= cutoff)
        ).all():
            row.exit_price = btc_price
            row.resolved_at = now
            row.outcome = (
                "WIN" if (row.signal_type == "BUY" and btc_price > row.entry_price)
                      or (row.signal_type == "AVOID" and btc_price < row.entry_price)
                else "LOSS"
            )


def _fmt_outcome(o: SignalOutcome) -> dict:
    recorded = o.recorded_at
    if recorded.tzinfo is None:
        recorded = recorded.replace(tzinfo=timezone.utc)
    date_str = recorded.strftime("%b %-d")
    if o.outcome == "SKIP" or o.exit_price is None or not o.entry_price:
        return {"date": date_str, "label": o.signal_type, "result": "—", "success": False}
    pct = (o.exit_price - o.entry_price) / o.entry_price * 100
    result = f"+{pct:.1f}%" if pct >= 0 else f"{pct:.1f}%"
    return {"date": date_str, "label": o.signal_type, "result": result, "success": o.outcome == "WIN"}


def _enrich_with_outcomes(db, payloads: list[dict]) -> tuple[list[dict], int]:
    """Inject accuracy + pastSignals into each payload. Returns (payloads, global_accuracy)."""
    rows = db.scalars(
        select(SignalOutcome)
        .where(SignalOutcome.outcome.is_not(None))
        .order_by(SignalOutcome.recorded_at.desc())
    ).all()

    by_detector: dict[str, list] = defaultdict(list)
    for row in rows:
        by_detector[row.detector_id].append(row)

    for p in payloads:
        det_rows = by_detector.get(p["id"], [])
        scored = [o for o in det_rows if o.outcome in ("WIN", "LOSS")]
        wins   = [o for o in scored if o.outcome == "WIN"]
        p["accuracy"]    = round(len(wins) / len(scored) * 100) if scored else 0
        # SIMILAR PAST SIGNALS shows only resolved WIN/LOSS outcomes — SKIP
        # rows (WATCH non-events) are not real past signals and were rendering
        # as misleading "— ✗" entries.
        p["pastSignals"] = [_fmt_outcome(o) for o in scored[:3]]

    all_scored = [o for o in rows if o.outcome in ("WIN", "LOSS")]
    all_wins   = [o for o in all_scored if o.outcome == "WIN"]
    global_acc = round(len(all_wins) / len(all_scored) * 100) if all_scored else 0
    return payloads, global_acc


def build_full_snapshot() -> dict:
    with get_db() as db:
        rows = db.scalars(select(Signal).order_by(Signal.updated_at.desc())).all()
        now = datetime.now(timezone.utc)
        payloads = []
        for s in rows:
            updated = s.updated_at
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            delta = now - updated
            if delta.total_seconds() > _MAX_SIGNAL_AGE_HOURS * 3600:
                continue  # skip stale signals
            p = dict(s.payload)
            p["timeAgo"] = format_time_ago(delta)
            payloads.append(p)
        payloads, global_acc = _enrich_with_outcomes(db, payloads)

    signals = payloads
    stats = {"today": len(signals), "thisWeek": len(signals), "accuracy": global_acc}

    cached_macro = cache.get("macro_status")
    if isinstance(cached_macro, dict) and "indicators" in cached_macro:
        macro = {
            "macroStatus": cached_macro.get("indicators") or MACRO_STATUS,
            "riskEnvironment": cached_macro.get("risk_environment", "neutral"),
            "upcomingEvents": cached_macro.get("upcoming_events", []),
            "macroStatusDetail": cached_macro.get("macro_status", {}),
        }
    else:
        macro = {
            "macroStatus": cached_macro or MACRO_STATUS,
            "riskEnvironment": "neutral",
            "upcomingEvents": [],
            "macroStatusDetail": {},
        }

    cached_news = cache.get("news")
    news = (
        {"aiBriefing": cached_news.get("briefing", []), "newsHeadlines": cached_news.get("headlines", [])}
        if isinstance(cached_news, dict)
        else {"aiBriefing": AI_BRIEFING, "newsHeadlines": NEWS_HEADLINES}
    )

    return {
        "signals": signals,
        "stats": stats,
        "market": cache.get_or("market_status", MARKET_STATUS),
        "is_fallback": not cache.has("market_status"),
        "sectorFlows": cache.get_or("sector_flows", SECTOR_FLOWS),
        "etfFlows": cache.get_or("etf_flows", ETF_FLOWS),
        **macro,
        "btcTreasuries": cache.get_or("btc_treasuries", BTC_TREASURIES),
        "vcActivity": cache.get_or("vc_activity", VC_ACTIVITY),
        **news,
    }


async def run_agent() -> None:
    logger.info(f"[agent] run_agent: {len(DETECTORS)} detectors loaded")
    if not DETECTORS:
        await _refresh_panel_cache()
        logger.info("[agent] No detectors registered — nothing to do")
        return

    generated = 0
    active_signals: dict[str, str] = {}
    for detector in DETECTORS:
        try:
            raw_signals = await detector.run()
        except Exception as exc:
            logger.warning("[agent] detector %s failed: %s", type(detector).__name__, exc)
            continue
        for raw in raw_signals:
            scores = score_signal(raw)
            explanation = await explain_signal(raw)
            # Detector-supplied confidence/risk (e.g. per-sector rotation) take
            # precedence; scorer only fills gaps for detectors that omit them.
            payload = {**scores, **raw, "explanation": explanation}

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
            active_signals[raw["id"]] = payload["type"]
            generated += 1

    await _refresh_panel_cache()
    await _refresh_ai_briefing()
    if active_signals:
        try:
            from backend.services.sosovalue import get_client
            from backend.services.currency import fetch_btc_price_usd
            btc_price = await fetch_btc_price_usd(get_client())
            _record_signal_entries(active_signals, btc_price)
        except Exception as exc:
            logger.warning("[agent] outcome entry recording skipped: %s", exc)
    await check_outcomes()
    etf_raw = cache.get("etf_raw")
    if isinstance(etf_raw, dict) and (etf_raw.get("btc") or etf_raw.get("eth")):
        cutoff = datetime.now(timezone.utc) - timedelta(days=14)
        try:
            with get_db() as db:
                db.add(EtfSnapshot(
                    btc_flow=etf_raw["btc"],
                    eth_flow=etf_raw["eth"],
                    total_flow=etf_raw["total"],
                ))
                db.execute(delete(EtfSnapshot).where(EtfSnapshot.recorded_at < cutoff))
        except Exception as db_exc:
            logger.warning("[agent] etf_snapshot write failed: %s", db_exc)
    snapshot = build_full_snapshot()
    await broadcast(snapshot)
    cache.save_to_disk()
    _t = asyncio.create_task(_push_to_cache(snapshot))
    _background_tasks.add(_t)
    _t.add_done_callback(_background_tasks.discard)
    logger.info("[agent] run_agent done — %d signals upserted, SSE broadcast sent", generated)


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_agent, "interval", hours=1, id="agent_hourly", max_instances=1, coalesce=True)
    scheduler.add_job(_refresh_macro_cache, "interval", minutes=30, id="macro_30min")
    scheduler.add_job(_refresh_market_cache, "interval", seconds=30, id="market_30s",
                      max_instances=1, coalesce=True, misfire_grace_time=15)
    scheduler.start()
    logger.info("[agent] Scheduler started — run_agent hourly, macro 30min, market price 30s")
    return scheduler
