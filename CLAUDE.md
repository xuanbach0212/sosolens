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

## Product: SoSoLens

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

# Smart contracts (Wave 2) — always run from contracts/ subdir
cd contracts && forge build
cd contracts && forge test
cd contracts && forge script script/Deploy.s.sol --rpc-url $RPC_URL --broadcast --private-key $PRIVATE_KEY
```

**Important**: `uvicorn` must be run from the repo root (not from `backend/`), using the `backend.main:app` module path.

---

## Environment Variables

Never commit `.env`. Copy `backend/.env.example` to `backend/.env` and fill in:

```
SOSOVALUE_API_KEY=      # required for live data; without it endpoints fall back to hardcoded
ANTHROPIC_API_KEY=      # required for AI signal explanations (issue #15)
PRIVATE_KEY=            # deployer wallet (Wave 2 smart contracts)
RPC_URL=https://sepolia.base.org  # Base Sepolia RPC
SUBSCRIPTION_CONTRACT_ADDRESS=    # set after deploying contracts/src/SoSoLensSubscription.sol
```

---

## API Endpoints

| Method | Path | Returns |
|--------|------|---------|
| GET | `/api/signals` | `{signals: Signal[], stats: SignalStats}` — free tier: 1h delayed; premium: real-time |
| GET | `/api/market` | `{market: MarketStatus}` |
| GET | `/api/sector-flows` | `{sectorFlows: SectorFlow[]}` — live from SoSoValue, fallback hardcoded |
| GET | `/api/etf-flows` | `{etfFlows: EtfFlow[]}` — live from SoSoValue, fallback hardcoded |
| GET | `/api/macro` | `{macroStatus: MacroItem[], riskEnvironment: string, upcomingEvents: MacroEvent[], macroStatusDetail: dict}` |
| GET | `/api/btc-treasuries` | `{btcTreasuries: BtcTreasury[]}` |
| GET | `/api/vc-activity` | `{vcActivity: VcActivity[]}` |
| GET | `/api/news` | `{aiBriefing: string[], newsHeadlines: NewsHeadline[]}` |
| POST | `/api/agent/run` | `{status: "ok"}` — manually fires the agent loop |
| GET | `/api/price-history?hours=N` | `{priceHistory: [{timestamp, btcPrice, ethPrice}]}` — last N hours of 30s snapshots (default 24h, max 168h) |
| GET | `/api/subscription/status?wallet=0x...` | `{subscribed: bool, expiry: int\|null}` — on-chain check via web3.py |
| GET | `/api/stream?wallet=0x...` | SSE stream — premium only; sends `event: access_denied` if not subscribed |

---

## Agent / Detector Pattern

To add a new signal detector:

1. Create `backend/agent/detectors/<name>.py` with a class that has `async def run(self) -> list[dict]`
2. Each dict in the returned list must include at minimum: `id`, `type` (BUY/WATCH/AVOID), `sector`
3. Also include frontend-required fields: `timeAgo`, `dataSources`, `topTokens`, `pastSignals`, `accuracy`, `sodexPair`, `sodexSlippage`, `sodexEstOutput`
4. Register in `backend/agent/detectors/__init__.py`: add instance to `DETECTORS` list

The runner (`runner.py`) iterates `DETECTORS`, calls `run()`, pipes each raw signal through `score_signal()` and `explain_signal()`, then upserts to DB. Use a fixed `id` per detector if you want hourly upsert (not duplicate); use a timestamped `id` if each run should create a new record.

---

## Wave Progress

### Wave 1 (due 2026-05-18) — 24/24 ✅ COMPLETE
All issues done. Deployed on Raspberry Pi via Docker + Cloudflare Tunnel. 98/98 backend tests passing.

### Wave 2 (due 2026-06-01) — 3/3 ✅ COMPLETE
- ✅ #25 — SoDEX trade button (`buildSodexUrl` in SignalDetail, SECTOR_TOKEN map in sector_rotation.py)
- ✅ #26 — Subscription smart contract (`contracts/src/SoSoLensSubscription.sol`, 5 USDC/30d on Base Sepolia; `backend/services/subscription.py`; `/api/subscription/status`, gated `/api/signals` + `/api/stream`)
- ✅ #27 — Frontend subscription gate (`useWallet` + `useSubscription` + `WalletBar` + `SubscribeModal`; viem on Base Sepolia; SSE reconnects with ?wallet=; ⚠ DELAYED 1H badge for free tier)

### Wave 3 (due 2026-06-15) — 3/4
- ✅ #28 — Historical signal accuracy tracker (`signal_outcomes` table, `check_outcomes()`, `_enrich_with_outcomes()`; real accuracy % + pastSignals in /api/signals; 117/117 tests)
- ✅ #30 — README + API setup guide
- ✅ #31 — Akindo submission description
- ❌ #29 — 90-second demo video

### UI Upgrade Track (ongoing)
- ✅ #46 — Split refresh cadence (BTC/ETH price 30s vs agent hourly)
- ✅ #47 — BTC/ETH price snapshot storage (`price_snapshots` table, 72h retention; `GET /api/price-history`; `btcPriceRaw`/`ethPriceRaw` in market status; 131/131 tests)
- ✅ #48 — News sentiment detector (`backend/agent/detectors/news_sentiment.py`; keyword scoring: 17 bullish / 21 bearish terms; macro-sensitive headlines double-weighted; BUY/WATCH/AVOID; token extraction; 16 tests)
- ✅ #49 — BTC treasury accumulation detector (`backend/agent/detectors/btc_accumulation.py`; net weekly BTC change across top-5 holders; BUY ≥+1,000 BTC / AVOID ≤−500 BTC / WATCH otherwise; 18 tests)
- ✅ #51 — TopBar BTC/ETH 24h sparkline (inline SVG polyline, no new deps; fetches `/api/price-history?hours=24`; green if price up, red if down; downsamples to 60pts)
- ✅ #50 — TopBar MACRO REGIME status badge
- ✅ #52 — TopBar Fear & Greed color coding + trend arrow
- ✅ #53 — MarketIntelligence sector flows color heatmap (`sectorFlowStyle()` in `MarketIntelligence.tsx`; 3-column grid; rgba opacity encodes magnitude 0.15–0.80; green positive / red negative; no new deps)

**Deploy contract (one-time after Wave 2 env vars are set):**
```bash
cd contracts && forge script script/Deploy.s.sol --rpc-url $RPC_URL --broadcast --private-key $PRIVATE_KEY
# Copy printed address → SUBSCRIPTION_CONTRACT_ADDRESS in backend/.env
```

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
2. **Update the roadmap** — mark the issue ✅ in `wiki/outputs/2026-05-04-sosolens-roadmap.md` and update the progress count
3. **Update `wiki/concepts/sosolens.md`** — reflect new build status, issues done/remaining
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
