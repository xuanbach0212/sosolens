# Deploying SoSoLens

Two pieces: a **Next.js frontend** (→ Vercel) and a **FastAPI backend** (→ a
persistent container host). They talk over HTTPS via `NEXT_PUBLIC_API_URL`.

---

## Why the backend can't be serverless

The backend starts **APScheduler in-process** from the FastAPI `lifespan` — a 30s
market tick, an hourly agent run, and a 30min macro refresh. That requires a process
that stays alive between requests, so:

- ❌ **No serverless** (Vercel Functions, Lambda, Cloudflare Workers) — schedulers never fire.
- ⚠️ **No idle-spindown free tiers** (e.g. Render *free*) — spindown kills the scheduler.
- ✅ **Always-on container/VM, single worker.** More than one worker = duplicate jobs.

### Host recommendation

| Host | Verdict | Notes |
|------|---------|-------|
| **Railway** | ✅ recommended | Persistent service + one-click managed Postgres (auto-injects `DATABASE_URL`), simple env UI, stays warm. |
| **Render** (paid) | ✅ | Use the $7/mo Starter (the free web service idle-spins-down); managed Postgres add-on. |
| **Fly.io** | ✅ | Persistent VMs + Fly Postgres; set `min_machines_running=1`. |

**Start command** (single worker, host-provided `$PORT`):

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

No `--reload`, no `--workers >1`. Python 3.12+; install `backend/requirements.txt`.
On first boot, SQLAlchemy `create_all` builds the tables and `run_agent()` repopulates
signals within ~2 min (OUTCOME TRAIL stays empty until 24h signal aging — expected).

---

## Backend environment variables

| Var | Required | Value / source |
|-----|----------|----------------|
| `DATABASE_URL` | ✅ | Managed Postgres (Railway injects it). `postgresql+psycopg2://USER:PASS@HOST:5432/DB`. Unset → SQLite fallback (do **not** rely on in prod). |
| `SOSOVALUE_API_KEY` | ✅ | Primary data source. |
| `ANTHROPIC_API_KEY` | ✅ | Default LLM explainer / AI briefing. |
| `AI_PROVIDERS` | ✅ | `anthropic` (comma-sep priority order). |
| `FRED_API_KEY` | recommended | Real macro values; graceful fallback to event calendar if unset. |
| `OPENAI_API_KEY` / `OPENROUTER_API_KEY` / `OPENROUTER_MODEL` / `GEMINI_API_KEY` | optional | LLM fallbacks. |
| `SUBSCRIPTION_CONTRACT_ADDRESS` | for paywall | Deployed contract addr; empty = everyone free tier. |
| `RPC_URL` | for paywall | `https://sepolia.base.org` (read-only `is_subscribed`). |
| `CACHE_WORKER_URL` / `CACHE_PUSH_SECRET` | optional | Cloudflare edge cache; skip for first deploy. |
| `FREE_TIER_DELAY_MINUTES` / `OUTCOME_DEDUP_HOURS` / `OUTCOME_HORIZON_HOURS` | optional | Tuning; defaults are fine. |

> **Do NOT set `PRIVATE_KEY` on the backend host.** It is used only by the Foundry
> contract-deploy script, never at runtime.

See `backend/.env.example` for the full annotated template.

---

## Frontend environment variables (Vercel)

| Var | Value |
|-----|-------|
| `NEXT_PUBLIC_API_URL` | `https://<your-backend>.up.railway.app` (no trailing slash) |
| `NEXT_PUBLIC_SUBSCRIPTION_CONTRACT_ADDRESS` | same contract addr as backend (or empty) |
| `NEXT_PUBLIC_USDC_ADDRESS` | `0x036CbD53842c5426634e7929541eC2318f3dCF7e` (Base Sepolia USDC) |

See `frontend/.env.example`.

---

## Deploy order

1. **Provision Postgres** (Railway add-on) → get `DATABASE_URL`.
2. **Deploy backend** with the env above + the start command. Wait ~2 min for first
   `run_agent()` to populate signals; check `GET /api/signals` returns data.
3. **Deploy frontend** on Vercel with `NEXT_PUBLIC_API_URL` = the live backend URL.
4. **Tighten CORS** post-launch: backend is `allow_origins=["*"]` today — fine to
   launch, but restrict to the Vercel domain afterward.
5. **Never commit `.env`** — set everything in the host dashboards.
