from contextlib import asynccontextmanager
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
from backend.services.etf import fetch_etf_snapshot
from backend.services.macro import fetch_macro_indicators
from backend.services.sector import fetch_sector_flows
from backend.services.sosovalue import get_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler = start_scheduler()
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


@app.get("/api/signals")
def get_signals() -> dict:
    with get_db() as db:
        db_signals = db.query(Signal).all()
    if db_signals:
        return {"signals": [s.payload for s in db_signals], "stats": SIGNAL_STATS}
    return {"signals": SIGNALS, "stats": SIGNAL_STATS}


@app.get("/api/market")
def get_market() -> dict:
    return {"market": MARKET_STATUS}


@app.get("/api/sector-flows")
async def get_sector_flows() -> dict:
    try:
        data = await fetch_sector_flows(get_client())
        return {"sectorFlows": data}
    except Exception:
        return {"sectorFlows": SECTOR_FLOWS}


@app.get("/api/etf-flows")
async def get_etf_flows() -> dict:
    try:
        data = await fetch_etf_snapshot(get_client())
        return {"etfFlows": data}
    except Exception:
        return {"etfFlows": ETF_FLOWS}


@app.get("/api/macro")
async def get_macro() -> dict:
    try:
        data = await fetch_macro_indicators(get_client())
        return {"macroStatus": data}
    except Exception:
        return {"macroStatus": MACRO_STATUS}


@app.get("/api/btc-treasuries")
def get_btc_treasuries() -> dict:
    return {"btcTreasuries": BTC_TREASURIES}


@app.get("/api/vc-activity")
def get_vc_activity() -> dict:
    return {"vcActivity": VC_ACTIVITY}


@app.get("/api/news")
def get_news() -> dict:
    return {"aiBriefing": AI_BRIEFING, "newsHeadlines": NEWS_HEADLINES}


@app.post("/api/agent/run")
async def trigger_agent_run() -> dict:
    """Debug endpoint — manually trigger the agent loop."""
    await run_agent()
    return {"status": "ok"}
