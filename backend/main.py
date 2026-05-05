from contextlib import asynccontextmanager
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
        payloads = [s.payload for s in db.query(Signal).all()]
    if payloads:
        return {"signals": payloads, "stats": SIGNAL_STATS}
    return {"signals": SIGNALS, "stats": SIGNAL_STATS}


@app.get("/api/market")
def get_market() -> dict:
    return {"market": MARKET_STATUS}


@app.get("/api/sector-flows")
def get_sector_flows() -> dict:
    return {"sectorFlows": cache.get("sector_flows") or SECTOR_FLOWS}


@app.get("/api/etf-flows")
def get_etf_flows() -> dict:
    return {"etfFlows": cache.get("etf_flows") or ETF_FLOWS}


@app.get("/api/macro")
def get_macro() -> dict:
    return {"macroStatus": cache.get("macro_status") or MACRO_STATUS}


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
    """Manually trigger the agent loop (runs detectors + refreshes panel cache)."""
    await run_agent()
    return {"status": "ok"}
