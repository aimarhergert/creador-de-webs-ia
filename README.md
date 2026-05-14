# AROS — Autonomous Revenue Operating System

**Investor Demo Beta v3.0**

AI-powered autonomous operating system that creates, deploys, monetizes, optimizes, and scales digital businesses automatically using user investment capital.

---

## Architecture

```
creador-web-ia/
├── frontend/          # Next.js 15 · TypeScript · TailwindCSS · Framer Motion · Recharts
├── backend/           # FastAPI · SQLAlchemy · Celery · Pydantic
├── docker-compose.yml # Postgres + Redis + Backend + Worker + Beat + Frontend
└── .claude/           # Claude Code permissions config
```

**Services (Docker):**

| Container | Port | Description |
|-----------|------|-------------|
| `postgres` | 5432 | PostgreSQL: `aros_db` |
| `redis` | 6379 | Redis (Celery broker) |
| `backend` | 8000 | FastAPI REST + WebSocket |
| `celery_worker` | — | Async pipeline + simulation |
| `celery_beat` | — | Periodic task scheduler (60s ticks) |
| `frontend` | 3000 | Next.js dashboard |

---

## Autonomous Loop

```
Capital → Strategy → Asset Generation → Deploy → Traffic/Revenue → ROI → Optimize/Scale/Kill
```

1. User invests capital into wallet
2. Selects investment strategy (6 presets)
3. AI generates digital assets (landing pages, blogs, e-commerce)
4. Assets are deployed with tracking pixels
5. Traffic simulation generates visits, conversions, revenue
6. ROI is calculated in real-time
7. AI decides: **SCALE** (ROI > 3x) · **OPTIMIZE** (1x < ROI < 3x) · **KILL** (ROI < 1x)

---

## Quick Start

```bash
cd /Users/aimarhp/Desktop/creador-web-ia
docker compose up -d
```

**URLs:**
- Dashboard: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

**Demo accounts:**
- `demo@aros.ai` / `demo123`
- `admin@aros.ai` / `admin123`

---

## Current Demo State

### Backend (FastAPI v3.0)
- [x] JWT Authentication (login/register/me)
- [x] Investment Wallet (deposit/transactions/balance)
- [x] 6 Strategy Presets (SEO Growth, Affiliate Arbitrage, Lead Gen, Micro SaaS, Aggressive Scaling, Conservative ROI)
- [x] Asset Factory v2 — 8-file site generation (index, blog, 3 posts, contact, CSS, JS)
- [x] Mock Mode (`SIMULATE_AI=true`) — instant demo sites, no API credits spent
- [x] Local Deployment Engine
- [x] Traffic Simulation Engine (Celery beat every 60s)
- [x] Analytics Engine (portfolio + per-asset metrics)
- [x] Activity Feed + WebSocket (real-time events)
- [x] Optimization Engine (SCALE/OPTIMIZE/KILL logic)
- [x] Billing System (Stripe integration)
- [x] Admin Panel API

### Frontend (Next.js 15)
- [x] Login / Register (JWT auth)
- [x] **Dashboard Bloomberg-Grade** — live activity ticker, KPI cards, revenue bar chart, 12-month capital/revenue projection, real-time WebSocket event feed
- [x] **Pipeline Generator** — keyword → 8-file site with progress animation
- [x] **Assets** — grid view, search, filter, preview iframe, delete
- [x] **Strategies** — glassmorphism cards, risk/speed meters, ROI estimates, simulation params
- [x] **Wallet** — balance, deposit, transaction history
- [x] **Activity Feed** — WebSocket live stream with event type icons
- [x] **Analytics** — portfolio KPIs, per-asset metrics table
- [x] **Billing** — Stripe plan cards, checkout
- [x] **Automations** — API reference, n8n/Make/Zapier integration guides

### Database (15 tables, PostgreSQL)
`users`, `wallets`, `wallet_transactions`, `strategies`, `assets`, `deployments`, `metrics`, `activity_events`, `projects`, `investments`, `optimization_logs`, `traffic_simulations`, `api_keys`, `subscriptions`, `audit_logs`

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, TypeScript, TailwindCSS, Framer Motion, Recharts, Zustand |
| Backend | FastAPI, Python 3.12, SQLAlchemy 2.0 (async), Celery |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis 7 |
| Auth | JWT (HS256), bcrypt |
| AI | Anthropic Claude (abstracted, mock mode available) |
| Payments | Stripe |
| Infra | Docker, Docker Compose |

---

## Environment

Key env vars in `backend/.env`:

| Variable | Purpose |
|----------|---------|
| `SIMULATE_AI` | `true` = instant mock sites (no API cost) |
| `ANTHROPIC_API_KEY` | Claude API key |
| `JWT_SECRET_KEY` | JWT signing key |
| `STRIPE_SECRET_KEY` | Stripe payments |
| `DEBUG` | Debug mode toggle |

---

## Notes

- Set `SIMULATE_AI=true` for investor demos to avoid Anthropic API costs
- Mock mode generates realistic 8-file sites instantly with proper SEO, schema.org JSON-LD, and tracking pixels
- Rebuild after code changes: `docker compose build backend && docker compose up -d --force-recreate backend celery_worker celery_beat`
- All generated sites are served at `http://localhost:8000/static/sites/{name}/`

---

*AROS — "AI is autonomously operating digital businesses."*
