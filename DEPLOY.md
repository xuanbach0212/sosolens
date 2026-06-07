# Deploying SoSoLens

Two pieces: a **Next.js frontend** (→ Vercel) and a **FastAPI backend** (→ Raspberry Pi via Docker + Cloudflare Tunnel). They talk over HTTPS via `NEXT_PUBLIC_API_URL`.

---

## Raspberry Pi Deploy (current setup)

The backend runs as Docker Compose on the Pi. A Cloudflare Tunnel container exposes it to the internet — no port forwarding, no static IP needed.

### Step 1 — Create the Cloudflare Tunnel

1. Go to **dash.cloudflare.com → Zero Trust → Networks → Tunnels → Create a tunnel**
2. Choose **Cloudflared** as the connector type, give it a name (e.g. `sosolens`)
3. Copy the **tunnel token** shown in the install step (looks like `eyJ...`)
4. In **Public Hostnames**, add a route:
   - **Subdomain**: `api` (or leave blank for apex)
   - **Domain**: your Cloudflare zone (e.g. `sosolens.xyz`)
   - **Service type**: `HTTP`
   - **URL**: `backend:8000`  ← the Docker service name, not localhost
5. Save — the tunnel URL is now `https://api.sosolens.xyz` (or your chosen subdomain)

### Step 2 — Clone and configure on the Pi

```bash
git clone https://github.com/xuanbach0212/sosolens.git
cd sosolens
cp backend/.env.example backend/.env
```

Edit `backend/.env` — fill in required vars (see table below). Do **not** set `DATABASE_URL` here — docker-compose overrides it automatically to point at the Postgres container.

Create a `.env` file **in the repo root** (for docker-compose):

```bash
# sosolens/.env  (repo root, not backend/)
CLOUDFLARE_TUNNEL_TOKEN=eyJ...   # paste your token here
```

### Step 3 — Build and start

```bash
docker compose up -d --build
```

This starts three containers:
| Container | Role |
|-----------|------|
| `db` | PostgreSQL 16 — stores signals, price history, outcomes |
| `backend` | FastAPI + APScheduler — runs agent hourly, serves API on :8000 |
| `tunnel` | cloudflared — connects Pi to Cloudflare edge, no open ports |

On first boot, `run_agent()` fires within ~2 min and populates signals. OUTCOME TRAIL stays empty until signals age 24h — expected.

### Step 4 — Verify

```bash
# check all three containers are up
docker compose ps

# check backend is healthy
curl http://localhost:8000/api/signals

# check the public tunnel
curl https://api.sosolens.xyz/api/signals
```

### Step 5 — Deploy frontend on Vercel

Set these env vars in Vercel dashboard:

| Var | Value |
|-----|-------|
| `NEXT_PUBLIC_API_URL` | `https://api.sosolens.xyz` (your tunnel URL, no trailing slash) |
| `NEXT_PUBLIC_SUBSCRIPTION_CONTRACT_ADDRESS` | deployed contract addr (or empty = everyone free) |
| `NEXT_PUBLIC_USDC_ADDRESS` | `0x036CbD53842c5426634e7929541eC2318f3dCF7e` (Base Sepolia USDC) |

---

## Why the backend can't be serverless

The backend starts **APScheduler in-process** from the FastAPI `lifespan` — a 30s market tick, an hourly agent run, and a 30min macro refresh. That requires a process that stays alive between requests:

- ❌ **No serverless** (Vercel Functions, Lambda, Cloudflare Workers) — schedulers never fire.
- ⚠️ **No idle-spindown free tiers** — spindown kills the scheduler.
- ✅ **Always-on single worker.** More than one worker = duplicate jobs.

---

## Backend environment variables (`backend/.env`)

| Var | Required | Value / source |
|-----|----------|----------------|
| `DATABASE_URL` | auto-set | docker-compose overrides to `postgresql+psycopg2://sosolens:sosolens@db:5432/sosolens`. Unset → SQLite fallback. |
| `SOSOVALUE_API_KEY` | ✅ | Primary data source. |
| `ANTHROPIC_API_KEY` | ✅ | Default LLM explainer / AI briefing. |
| `AI_PROVIDERS` | ✅ | `anthropic` (comma-sep priority order). |
| `FRED_API_KEY` | recommended | Real macro values; graceful fallback if unset. Free at fredaccount.stlouisfed.org |
| `OPENAI_API_KEY` / `OPENROUTER_API_KEY` / `OPENROUTER_MODEL` / `GEMINI_API_KEY` | optional | LLM fallbacks. |
| `SUBSCRIPTION_CONTRACT_ADDRESS` | for paywall | Deployed contract addr; empty = everyone free tier. |
| `RPC_URL` | for paywall | `https://sepolia.base.org` (read-only `is_subscribed`). |
| `CACHE_WORKER_URL` / `CACHE_PUSH_SECRET` | optional | Cloudflare edge cache; skip for now. |
| `FREE_TIER_DELAY_MINUTES` / `OUTCOME_DEDUP_HOURS` / `OUTCOME_HORIZON_HOURS` | optional | Tuning; defaults are fine. |

> **Do NOT set `PRIVATE_KEY` on the backend.** It is only for the Foundry deploy script.

---

## Maintenance

```bash
# view logs
docker compose logs -f backend

# restart after a code push
git pull && docker compose up -d --build

# stop everything
docker compose down

# wipe the database (destructive — signals lost)
docker compose down -v
```

---

## CORS

Backend is `allow_origins=["*"]` today — fine to launch. After Vercel URL is known, tighten to that domain in `backend/main.py`.
