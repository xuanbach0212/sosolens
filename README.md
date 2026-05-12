# AI Signal Platform

**Bloomberg-terminal crypto signal dashboard, powered by SoSoValue + AI (Anthropic · OpenAI · OpenRouter · Gemini)**

Monitor SoSoValue's institutional data 24/7. Get BUY / WATCH / AVOID signals with AI-generated explanations. Trade directly via SoDEX.

![Python 3.13](https://img.shields.io/badge/Python-3.13-blue)
![Next.js 16](https://img.shields.io/badge/Next.js-16-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![WaveHack Wave 1](https://img.shields.io/badge/Akindo%20WaveHack-Wave%201-purple)

---

## What It Does

- **Ingests 7 SoSoValue institutional data modules** hourly — ETF flows, sector rotation, macro events, BTC treasuries, VC activity, news, and market prices
- **Runs 3 signal detectors** — ETF flow spike anomaly, sector rotation divergence, macro risk-on/off classifier
- **Scores every signal** — BUY / WATCH / AVOID with confidence % and LOW / MEDIUM / HIGH risk level
- **Explains in plain English** — AI explanation via configurable provider (Anthropic Claude Haiku by default; OpenAI, OpenRouter, Gemini supported)
- **Streams to a Bloomberg-style terminal** — real-time updates via SSE with 60s polling fallback

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, FastAPI, SQLite + SQLAlchemy |
| Scheduler | APScheduler (hourly agent loop) |
| AI | Multi-provider: Anthropic Claude Haiku (default), OpenAI gpt-4o-mini, OpenRouter, Gemini 2.0 Flash — priority chain via `AI_PROVIDERS` env var |
| Frontend | Next.js 16, Tailwind CSS v4, TypeScript, JetBrains Mono |
| Real-time | Server-Sent Events (SSE) |
| Deployment | Docker Compose, Cloudflare Tunnel |

---

## Prerequisites

- Python 3.13+
- Node 22+
- Docker + Docker Compose (for containerized run)
- [SoSoValue API key](https://sosovalue.gitbook.io/soso-value-api-doc/) (free tier — 20 req/min)
- At least one AI provider key — [Anthropic](https://console.anthropic.com/) (default), [OpenAI](https://platform.openai.com/), [OpenRouter](https://openrouter.ai/), or [Google Gemini](https://aistudio.google.com/)

---

## Local Development

```bash
# 1. Clone the repo
git clone https://github.com/xuanbach0212/akindo-sosovalue.git
cd akindo-sosovalue

# 2. Backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

cp backend/.env.example backend/.env
# Edit backend/.env — fill in SOSOVALUE_API_KEY and at least one AI provider key

# Run from repo root (not from backend/)
uvicorn backend.main:app --reload  # → http://localhost:8000

# 3. Frontend (separate terminal)
cd frontend
npm install

# Create frontend/.env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

npm run dev                        # → http://localhost:3000
```

---

## Docker (recommended)

```bash
cp backend/.env.example backend/.env
# Edit backend/.env — fill in SOSOVALUE_API_KEY and at least one AI provider key

docker compose up --build -d
# Frontend: http://localhost:3000
# Backend: internal only (proxied by Next.js rewrites)
```

The `agent_db` named volume persists the SQLite database across container restarts.

---

## Public URL via Cloudflare Tunnel

```bash
cloudflared tunnel --url http://localhost:3000
# Prints a *.trycloudflare.com URL — no account needed
```

Next.js rewrites all `/api/*` calls server-side to the internal backend container — the backend is never exposed publicly.

---

## Environment Variables

| Variable | File | Required | Description |
|----------|------|----------|-------------|
| `SOSOVALUE_API_KEY` | `backend/.env` | Yes | SoSoValue API key |
| `AI_PROVIDERS` | `backend/.env` | No | Comma-sep provider priority (default: `anthropic`) |
| `ANTHROPIC_API_KEY` | `backend/.env` | One required | Anthropic Claude Haiku |
| `OPENAI_API_KEY` | `backend/.env` | One required | OpenAI gpt-4o-mini |
| `OPENROUTER_API_KEY` | `backend/.env` | One required | OpenRouter (100+ models) |
| `OPENROUTER_MODEL` | `backend/.env` | No | OpenRouter model override (default: `llama-3.1-8b-instruct:free`) |
| `GEMINI_API_KEY` | `backend/.env` | One required | Google Gemini 2.0 Flash |
| `NEXT_PUBLIC_API_URL` | `frontend/.env.local` | Local dev only | Backend base URL — omit in Docker |

Never commit `.env` or `.env.local`. Both are in `.gitignore`.

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/signals` | Active signals + stats (filters signals older than 25h) |
| GET | `/api/market` | BTC/ETH price, market cap, volume, fear/greed index |
| GET | `/api/sector-flows` | 9-sector 7D capital rotation (% change) |
| GET | `/api/etf-flows` | 24H ETF net inflows — BTC, ETH, SOL |
| GET | `/api/macro` | Fed rate, CPI, DXY, 10Y yield, M2, upcoming events |
| GET | `/api/btc-treasuries` | Top corporate BTC holdings + weekly change |
| GET | `/api/vc-activity` | 7D VC funding by sector (deal count + USD raised) |
| GET | `/api/news` | AI 3-point briefing + 3 latest news headlines |
| POST | `/api/agent/run` | Manually trigger agent loop (all detectors run immediately) |
| GET | `/api/stream` | SSE stream — full snapshot pushed after each agent run, heartbeat every 30s |

All endpoints fall back to hardcoded data if the SoSoValue API is unavailable.

---

## Running Tests

```bash
# From repo root, with .venv active
pytest backend/tests/        # 87 tests, ~1s
```

---

## Project Structure

```
akindo-sosovalue/
├── backend/
│   ├── main.py              # FastAPI app — all routes + SSE endpoint
│   ├── events.py            # SSE pub/sub broker
│   ├── cache.py             # In-memory panel cache
│   ├── agent/
│   │   ├── runner.py        # run_agent() + APScheduler hourly job + build_full_snapshot()
│   │   ├── scorer.py        # Confidence % + risk level assignment
│   │   ├── explainer.py     # Multi-provider AI explanation (anthropic/openai/openrouter/gemini)
│   │   └── detectors/       # Signal detector plugins (ETF, sector, macro)
│   ├── services/            # SoSoValue API clients (7 modules)
│   └── data/
│       └── hardcoded.py     # Fallback data (same shape as live)
├── frontend/
│   ├── app/                 # Next.js App Router (layout, page, globals.css)
│   ├── components/          # TopBar, SignalFeed, SignalDetail, MarketIntelligence, BottomBar
│   └── hooks/
│       └── useDashboardData.ts  # SSE primary, 60s polling fallback
├── contracts/               # Solidity — Wave 2 subscription contract
├── Dockerfile               # Backend container (uv + Python 3.13)
├── frontend/Dockerfile      # Frontend multi-stage build (Node 22)
└── docker-compose.yml       # Two-service orchestration + agent_db volume
```

---

## Built for Akindo × SoSoValue WaveHack

This project is competing in [Akindo WaveHack](https://app.akindo.io/wave-hacks/JBEQXgN4Zi2jA3wA) — Wave 1 (due 2026-05-18). It uses SoSoValue's institutional-grade API as its primary data backbone and aims to demonstrate a fully autonomous, one-person on-chain finance business.

- Wave 2: SoDEX trade integration + on-chain subscription contract
- Wave 3: Historical signal accuracy tracker + polished demo
