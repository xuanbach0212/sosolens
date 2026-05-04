# CLAUDE.md — Akindo × SoSoValue WaveHack

## Hackathon Context

| Field | Detail |
|-------|--------|
| **Event** | Build Your One-Person On-Chain Finance Business with SoSoValue |
| **Platform** | Akindo WaveHack (wave-based, not one-shot) |
| **URL** | https://app.akindo.io/wave-hacks/JBEQXgN4Zi2jA3wA |
| **Prize Pool** | ~10,000 USDC |
| **Competitors** | ~470 builders |
| **Tags** | #SoSoValue #SoDEX #ValueChain #Agentic #One-Person #On-Chain Finance #AI x Web3 |
| **API Docs** | https://sosovalue.gitbook.io/soso-value-api-doc/ |
| **SSI Protocol** | https://github.com/SoSoValueLabs/ssi-protocol |
| **Whitepaper** | https://sosovalue-white-paper.gitbook.io/sosovalue-whitepaper |

## WaveHack Format (Critical)

WaveHack is NOT a traditional one-shot hackathon:
- Runs in repeating **waves** (build period + voting period per wave)
- Grants distributed by **community votes** — more votes = more USDC
- Projects can compete across **multiple waves** (continuous improvement rewarded)
- Judging weights: tangible progress, GitHub activity, product updates, ecosystem impact
- A 10% protocol fee is deducted from each wave's distribution

**Winning strategy**: ship fast, iterate every wave, demonstrate real usage and on-chain activity.

---

## Product: AI Signal Platform

One-screen Bloomberg-terminal dashboard that watches SoSoValue's institutional data APIs 24/7 and surfaces actionable trading signals (BUY / WATCH / AVOID) with plain-English AI explanations and a SoDEX trade button.

```
SoSoValue APIs → Python AI Agent (hourly) → SQLite → FastAPI → Next.js Terminal
```

---

## Project Structure

```
backend/                    → Python FastAPI app + AI agent
  main.py                   → FastAPI app, CORS, 8 REST endpoints, lifespan hook
  requirements.txt          → Python dependencies
  .env.example              → env var template (copy to .env)
  .venv/                    → Python virtual environment (activate before running)
  agent/
    models.py               → Signal SQLAlchemy ORM model
    db.py                   → SQLite engine + get_db() context manager
    runner.py               → run_agent() loop + APScheduler hourly job
    scorer.py               → confidence % + risk level (stub — issue #14)
    explainer.py            → Claude Haiku plain-English explanation (stub — issue #15)
    detectors/
      __init__.py           → DETECTORS registry list + register() decorator
      etf_flow_spike.py     → ETFFlowSpikeDetector (issue #11 ✅)
  services/
    sosovalue.py            → SoSoValueClient (async httpx, rate limit, retry) + get_client()
    etf.py                  → fetch_etf_snapshot() normalizer (issue #4 ✅)
  data/
    hardcoded.py            → fallback data for all endpoints (same shape as live data)

frontend/                   → Next.js 16 app (App Router, Tailwind v4)
  app/
    layout.tsx              → root layout, JetBrains Mono font
    page.tsx                → main terminal page, wires all panels
    globals.css             → Tailwind v4 CSS config (@theme inline, dark theme)
  components/
    TopBar.tsx              → market sentiment, BTC/ETH price, fear/greed
    SignalFeed.tsx          → left panel: signal cards + stats
    SignalDetail.tsx        → center panel: detail, data sources, trade button
    MarketIntelligence.tsx  → right panel: sector flows, ETF flows, macro, BTC treasuries, VC
    BottomBar.tsx           → AI briefing + news headlines
  hooks/
    useDashboardData.ts     → polling hook: fetches all 8 endpoints every 30s, fallback to dummy
  types/
    index.ts                → shared TypeScript interfaces (Signal, EtfFlow, MarketStatus, etc.)
  data/
    dummy.ts                → offline fallback data

contracts/                  → Solidity (Foundry) — Wave 2
scripts/                    → deploy scripts
docs/                       → design.md, plan.md, research/
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, FastAPI, uvicorn |
| DB | SQLite via SQLAlchemy 2.x |
| Scheduler | APScheduler (hourly agent loop) |
| HTTP client | httpx (async) |
| AI explanations | Anthropic SDK — Claude Haiku |
| Frontend | Next.js 16, App Router, Tailwind v4 |
| Font | JetBrains Mono |
| Layout | CSS Grid, desktop only, dark theme |
| Smart contracts | Foundry, Solidity (Wave 2) |
| Package manager | npm (frontend), pip via .venv (backend) |

**Note on Tailwind**: Using v4 — config is CSS-based (`@theme inline` in `globals.css`), no `tailwind.config.ts`.

---

## Dev Commands

```bash
# Backend — always activate venv first, run from repo root
source .venv/bin/activate
uvicorn backend.main:app --reload

# Backend — manually trigger the agent loop (debug)
curl -X POST http://localhost:8000/api/agent/run

# Frontend
cd frontend && npm run dev
cd frontend && npm run build

# Smart contracts (Wave 2)
cd contracts && forge build
cd contracts && forge test
cd contracts && forge script scripts/Deploy.s.sol --rpc-url $RPC_URL
```

**Important**: `uvicorn` must be run from the repo root (not from `backend/`), using the `backend.main:app` module path.

---

## Environment Variables

Never commit `.env`. Copy `backend/.env.example` to `backend/.env` and fill in:

```
SOSOVALUE_API_KEY=      # required for live data; without it endpoints fall back to hardcoded
ANTHROPIC_API_KEY=      # required for AI signal explanations (issue #15)
PRIVATE_KEY=            # deployer wallet (Wave 2 smart contracts)
RPC_URL=                # target chain RPC (Wave 2)
NEXT_PUBLIC_CHAIN_ID=   # (Wave 2)
```

---

## API Endpoints

| Method | Path | Returns |
|--------|------|---------|
| GET | `/api/signals` | `{signals: Signal[], stats: SignalStats}` — from DB if populated, else hardcoded |
| GET | `/api/market` | `{market: MarketStatus}` |
| GET | `/api/sector-flows` | `{sectorFlows: SectorFlow[]}` |
| GET | `/api/etf-flows` | `{etfFlows: EtfFlow[]}` — live from SoSoValue, fallback hardcoded |
| GET | `/api/macro` | `{macroStatus: MacroItem[]}` |
| GET | `/api/btc-treasuries` | `{btcTreasuries: BtcTreasury[]}` |
| GET | `/api/vc-activity` | `{vcActivity: VcActivity[]}` |
| GET | `/api/news` | `{aiBriefing: string[], newsHeadlines: NewsHeadline[]}` |
| POST | `/api/agent/run` | `{status: "ok"}` — manually fires the agent loop |

---

## Agent / Detector Pattern

To add a new signal detector:

1. Create `backend/agent/detectors/<name>.py` with a class that has `async def run(self) -> list[dict]`
2. Each dict in the returned list must include at minimum: `id`, `type` (BUY/WATCH/AVOID), `sector`
3. Also include frontend-required fields: `timeAgo`, `dataSources`, `topTokens`, `pastSignals`, `accuracy`, `sodexPair`, `sodexSlippage`, `sodexEstOutput`
4. Register in `backend/agent/detectors/__init__.py`: add instance to `DETECTORS` list

The runner (`runner.py`) iterates `DETECTORS`, calls `run()`, pipes each raw signal through `score_signal()` and `explain_signal()`, then upserts to DB. Use a fixed `id` per detector if you want hourly upsert (not duplicate); use a timestamped `id` if each run should create a new record.

---

## Wave 1 Progress (due 2026-05-18)

**Done (14/24):**
- #1 Frontend scaffold + terminal layout
- #2 Python agent scaffold (models, DB, runner, scheduler, detector registry)
- #3 SoSoValue API client (auth, rate limit, retry)
- #4 ETF API normalization + `/api/etf-flows` live data ✅
- #11 ETF flow spike detector (BUY/WATCH/AVOID thresholds) ✅
- #17 REST API (all 8 endpoints)
- #18–#24 All frontend panels + live polling hook

**Remaining (10/24):**
- #5–#10 API modules (Sector, BTC Treasuries, Macro, News, Fundraising, Currency)
- #12 Signal detector: sector rotation divergence
- #13 Signal detector: macro risk-on / risk-off
- #14 Real scorer (confidence % + risk)
- #15 AI explanation generator (Claude Haiku prompt)
- #16 Signal persistence review

---

## Judging Criteria (How to Win)

1. **Deep SoSoValue integration** — use their APIs and/or SSI Protocol, not just superficially
2. **Real on-chain activity** — deployed contracts, actual transactions, live demo
3. **"One-person business" narrative** — clear how a solo operator earns revenue on-chain
4. **Agentic/AI angle** — #Agentic tag is prominent; automation is rewarded
5. **GitHub activity** — judges look at commit history, progress, and updates each wave
6. **Community votes** — write good updates, engage in the Akindo community

## Rules (Always Follow)

### Backend — always activate venv first
Before running ANY Python command, importing backend modules, or starting the server:
```bash
source .venv/bin/activate
```
Never use the system `python3` or `pip` — they don't have the project dependencies.

### After finishing any task — update everything
When a task, issue, or feature is complete, always do ALL of the following before moving on:
1. **Close the GitHub issue** — `gh issue close <N> --comment "..."` with a brief summary
2. **Update the roadmap** — mark the issue ✅ in `wiki/outputs/2026-05-04-akindo-sosovalue-roadmap.md` and update the progress count
3. **Update `wiki/concepts/ai-signal-platform.md`** — reflect new build status, issues done/remaining
4. **Append to `wiki/log.md`** (in `/home/tyler/2ndbrain/`) — new entry at the top with pages updated, files created/modified, key claim
5. **Update this CLAUDE.md** — if project structure, tech stack, dev commands, or Wave 1 progress changed
6. **Commit and push** — don't leave finished work uncommitted on dev

---

## Principles for This Project

- Ship a working MVP first; polish later
- Every wave: write a progress update on Akindo with screenshots/demo links
- Prioritize on-chain verifiability over off-chain logic
- Keep the "one person" angle clear in all copy and demos
- Use SoSoValue API for data — don't pull from CoinGecko or similar
