# SoSoLens

**Bloomberg-terminal crypto signal dashboard, powered by SoSoValue + AI (Anthropic · OpenAI · OpenRouter · Gemini)**

Monitor SoSoValue's institutional data 24/7. Get BUY / WATCH / AVOID signals with AI-generated explanations. Trade directly on SoDEX. Subscribe on-chain.

![Python 3.13](https://img.shields.io/badge/Python-3.13-blue)
![Next.js 16](https://img.shields.io/badge/Next.js-16-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![Base Sepolia](https://img.shields.io/badge/Base%20Sepolia-On--chain-0052ff)
![WaveHack Wave 2](https://img.shields.io/badge/Akindo%20WaveHack-Wave%202-purple)
![Tests](https://img.shields.io/badge/Tests-204%20passing-brightgreen)

---

## What It Does

- **Ingests 7 SoSoValue institutional data modules** hourly — ETF flows, sector rotation, BTC treasuries, macro events, VC activity, news, market prices
- **Runs 5 signal detectors** — ETF flow spike, sector rotation divergence, macro risk classifier, BTC treasury accumulation, news sentiment
- **Prices 45+ tokens live** — CoinGecko `/coins/markets` top-500 powers per-token prices in every sector signal; FRED powers real Fed rate / CPI / DXY / 10Y
- **Scores every signal** — BUY / WATCH / AVOID with confidence % and LOW / MEDIUM / HIGH risk level
- **Explains in plain English** — AI explanation via configurable multi-provider chain (Anthropic default; OpenAI, OpenRouter, Gemini fallback)
- **Tracks signal accuracy** — historical WIN / LOSS outcomes resolved at 4h horizon, visible in "SIMILAR PAST SIGNALS"
- **Streams live to a Bloomberg-style terminal** — 30s market tick, hourly agent loop, SSE push for premium subscribers
- **On-chain subscription** — 5 USDC / 30 days on Base Sepolia; free tier gets 1h-delayed signals
- **Trade directly on SoDEX** — every signal has a one-click trade button pre-filled with the sector's primary token

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, FastAPI, uvicorn |
| Database | PostgreSQL 16 (Docker); SQLite fallback if `DATABASE_URL` unset |
| Scheduler | APScheduler — 30s market tick, hourly agent, 30min macro |
| AI | Multi-provider: Anthropic Claude (default), OpenAI, OpenRouter, Gemini — priority chain via `AI_PROVIDERS` |
| External data | SoSoValue API (primary) · CoinGecko `/global` + `/coins/markets` · FRED · alternative.me (fear/greed) |
| Smart contracts | Solidity + Foundry — `SoSoLensSubscription.sol` on Base Sepolia |
| Frontend | Next.js 16, App Router, Tailwind CSS v4, TypeScript, JetBrains Mono |
| Real-time | SSE stream (premium) + 30s polling (free) |
| Hosting | Vercel (FE) + Railway (BE) — see `DEPLOY.md` |

---

## Local Development

```bash
# 1. Clone
git clone https://github.com/xuanbach0212/sosolens.git
cd sosolens

# 2. Start PostgreSQL (Docker)
docker run -d --name sosolens-postgres \
  -e POSTGRES_USER=sosolens \
  -e POSTGRES_PASSWORD=sosolens \
  -e POSTGRES_DB=sosolens \
  -p 5432:5432 postgres:16-alpine

# 3. Backend — always activate venv first, run from repo root
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

cp backend/.env.example backend/.env
# Fill in: DATABASE_URL, SOSOVALUE_API_KEY, ANTHROPIC_API_KEY (minimum)

uvicorn backend.main:app --reload   # → http://localhost:8000

# 4. Frontend (separate terminal)
cd frontend
npm install
cp .env.example .env.local          # already has NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                         # → http://localhost:3000
```

On first boot, SQLAlchemy creates all tables and `run_agent()` populates signals within ~2 min.

---

## Deploy

See **[DEPLOY.md](DEPLOY.md)** for the full step-by-step.

**TL;DR:** Vercel for the frontend, Railway for the backend (APScheduler runs in-process — needs an always-on container, not serverless).

```bash
# Backend start command (Railway / Render / Fly)
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

---

## Environment Variables

### Backend

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | `postgresql+psycopg2://USER:PASS@HOST:5432/DB` — Railway injects this from the Postgres add-on |
| `SOSOVALUE_API_KEY` | ✅ | Primary data source |
| `ANTHROPIC_API_KEY` | ✅ | Default AI provider |
| `AI_PROVIDERS` | ✅ | Comma-sep priority order (e.g. `anthropic,openrouter`) |
| `FRED_API_KEY` | recommended | Real macro values (Fed rate / CPI / DXY / 10Y); falls back to event calendar |
| `SUBSCRIPTION_CONTRACT_ADDRESS` | for paywall | Deployed contract — leave empty for open access |
| `RPC_URL` | for paywall | Base Sepolia RPC (default: `https://sepolia.base.org`) |
| `OPENAI_API_KEY` / `OPENROUTER_API_KEY` / `GEMINI_API_KEY` | optional | AI fallbacks |

> **Do not set `PRIVATE_KEY` on the server.** It is only needed for the one-time contract deploy script.

### Frontend (Vercel)

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://<your-backend>.up.railway.app` |
| `NEXT_PUBLIC_SUBSCRIPTION_CONTRACT_ADDRESS` | deployed contract address (or empty) |
| `NEXT_PUBLIC_USDC_ADDRESS` | `0x036CbD53842c5426634e7929541eC2318f3dCF7e` |

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/signals` | Active signals + stats (free: 1h delayed; premium: real-time) |
| GET | `/api/market` | BTC/ETH price, total market cap, volume, fear/greed index |
| GET | `/api/sector-flows` | 8-sector 7D capital rotation (% change, live from SoSoValue) |
| GET | `/api/etf-flows` | Whole-universe BTC/ETH ETF net flows via `/etfs/summary-history` |
| GET | `/api/macro` | Real Fed rate / CPI / DXY / 10Y (FRED) + upcoming event calendar |
| GET | `/api/btc-treasuries` | Top corporate BTC holdings + weekly change |
| GET | `/api/vc-activity` | Funding mentions extracted from news headlines |
| GET | `/api/news` | AI 3-point briefing + latest news headlines |
| GET | `/api/price-history?hours=N` | BTC/ETH 30s price snapshots (default 24h, max 168h) |
| GET | `/api/etf-history?hours=N` | Hourly ETF flow snapshots (default 168h / 7d) |
| GET | `/api/signal-outcomes?hours=N` | WIN/LOSS outcome trail (default 48h) |
| GET | `/api/subscription/status?wallet=0x…` | On-chain subscription check (Base Sepolia) |
| GET | `/api/stream?wallet=0x…` | SSE push stream — premium only |
| POST | `/api/agent/run` | Manually trigger full agent loop |

---

## Smart Contract

`contracts/src/SoSoLensSubscription.sol` — ERC-20 payment (USDC), 30-day subscription, on Base Sepolia.

```bash
# One-time deploy (after setting PRIVATE_KEY and RPC_URL)
cd contracts
forge script script/Deploy.s.sol --rpc-url $RPC_URL --broadcast --private-key $PRIVATE_KEY
# Copy the printed address → SUBSCRIPTION_CONTRACT_ADDRESS in backend/.env
```

---

## Running Tests

```bash
source .venv/bin/activate
pytest backend/tests/    # 204 tests, ~3 min
```

---

## Project Structure

```
sosolens/
├── backend/
│   ├── main.py                  # FastAPI app — 13 routes + SSE + lifespan
│   ├── cache.py                 # In-memory cache + disk snapshot (instant restarts)
│   ├── agent/
│   │   ├── runner.py            # run_agent() + APScheduler (30s/hourly/30min)
│   │   ├── scorer.py            # Confidence % + risk level
│   │   ├── explainer.py         # Multi-provider AI explanation
│   │   ├── tokens.py            # Shared token_from_cache() helper
│   │   └── detectors/           # 5 signal detectors
│   ├── services/
│   │   ├── sosovalue.py         # SoSoValue API client (rate-limited, async)
│   │   ├── currency.py          # CoinGecko global + top-500 token prices
│   │   ├── fred.py              # FRED macro values (Fed rate / CPI / DXY / 10Y)
│   │   ├── sector.py            # Sector flows + top-6 live constituents
│   │   ├── etf.py               # ETF flows (whole-universe)
│   │   ├── subscription.py      # On-chain is_subscribed() via web3.py
│   │   └── ...
│   └── tests/                   # 204 tests
├── frontend/
│   ├── app/                     # Next.js App Router
│   ├── components/              # TopBar, SignalFeed, SignalDetail, MarketIntelligence, BottomBar
│   └── hooks/                   # useDashboardData (30s poll) + useSubscription
├── contracts/                   # Solidity + Foundry
├── DEPLOY.md                    # Hosting guide (Vercel + Railway)
└── backend/.env.example         # Annotated env template
```

---

## Built for Akindo × SoSoValue WaveHack

Competing in [Akindo WaveHack](https://app.akindo.io/wave-hacks/JBEQXgN4Zi2jA3wA) — demonstrating a fully autonomous, one-person on-chain finance business powered by SoSoValue's institutional data APIs.

| Wave | Status | Key Deliverables |
|------|--------|-----------------|
| Wave 1 | ✅ Complete | Terminal dashboard, 3 detectors, live SoSoValue data, SSE stream |
| Wave 2 | ✅ Complete | SoDEX trade button, on-chain subscription (Base Sepolia), real data everywhere (FRED/CoinGecko), 5 detectors, signal accuracy tracker, 204 tests |
| Wave 3 | 🔄 3/4 | README ✅ · Submission ✅ · Accuracy tracker ✅ · Demo video ⏳ |
