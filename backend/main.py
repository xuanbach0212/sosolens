import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv("backend/.env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.data.hardcoded import (
    SIGNALS,
    SIGNAL_STATS,
    MARKET_STATUS,
    SECTOR_FLOWS,
    ETF_FLOWS,
    MACRO_STATUS,
    BTC_TREASURIES,
    VC_ACTIVITY,
    AI_BRIEFING,
    NEWS_HEADLINES,
)
from backend.agent.db import init_db, get_db
from backend.agent.models import Signal
from backend.agent.runner import run_agent, start_scheduler
import backend.cache as cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler = start_scheduler()
    asyncio.create_task(run_agent())  # populate cache + DB immediately; scheduler handles hourly after
    yield
    scheduler.shutdown()


app = FastAPI(title="SoSoAlpha API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _compute_stats(payloads: list[dict]) -> dict:
    total = len(payloads)
    # accuracy is historical win-rate; not tracked yet — keep hardcoded baseline
    return {"today": total, "thisWeek": total, "accuracy": SIGNAL_STATS["accuracy"]}


@app.get("/api/signals")
def get_signals() -> dict:
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
    if payloads:
        return {"signals": payloads, "stats": _compute_stats(payloads)}
    return {"signals": SIGNALS, "stats": SIGNAL_STATS}


@app.get("/api/market")
def get_market() -> dict:
    return {"market": cache.get("market_status") or MARKET_STATUS}


@app.get("/api/sector-flows")
def get_sector_flows() -> dict:
    return {"sectorFlows": cache.get("sector_flows") or SECTOR_FLOWS}


@app.get("/api/etf-flows")
def get_etf_flows() -> dict:
    return {"etfFlows": cache.get("etf_flows") or ETF_FLOWS}


@app.get("/api/macro")
def get_macro() -> dict:
    cached = cache.get("macro_status")
    if isinstance(cached, dict) and "indicators" in cached:
        return {
            "macroStatus": cached.get("indicators") or MACRO_STATUS,
            "riskEnvironment": cached.get("risk_environment", "neutral"),
            "upcomingEvents": cached.get("upcoming_events", []),
            "macroStatusDetail": cached.get("macro_status", {}),
        }
    return {"macroStatus": cached or MACRO_STATUS}


@app.get("/api/btc-treasuries")
def get_btc_treasuries() -> dict:
    return {"btcTreasuries": cache.get("btc_treasuries") or BTC_TREASURIES}


@app.get("/api/vc-activity")
def get_vc_activity() -> dict:
    return {"vcActivity": cache.get("vc_activity") or VC_ACTIVITY}


@app.get("/api/news")
def get_news() -> dict:
    cached = cache.get("news")
    if cached:
        return {"aiBriefing": cached.get("briefing", []), "newsHeadlines": cached.get("headlines", [])}
    return {"aiBriefing": AI_BRIEFING, "newsHeadlines": NEWS_HEADLINES}


@app.post("/api/agent/run")
async def trigger_agent_run() -> dict:
    """Manually trigger the agent loop (runs detectors + refreshes panel cache)."""
    await run_agent()
    return {"status": "ok"}
