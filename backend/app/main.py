import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine
from app.models import Base
from app.routes import assets, orchestrator, analytics, billing
from app.routes import auth, wallet, activity
from app.routes import strategies, investments, projects, api_keys, admin
from app.routes import scanner, blog, sectors, agent
from app.dependencies import require_api_key

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

_STATIC_SITES = Path("/app/static/sites")
_STATIC_SITES.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("✓ Base de datos inicializada")
    yield
    await engine.dispose()


app = FastAPI(
    title="AROS — Autonomous Revenue Operating System",
    description="AI-powered digital asset factory: generate, deploy, monetize, optimize.",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Public routes ────────────────────────────────────────────────────────────
app.include_router(auth.router,       prefix="/api/auth",       tags=["Auth"])
app.include_router(analytics.router,  prefix="/api/analytics",  tags=["Analytics"])

# ── JWT-protected routes ─────────────────────────────────────────────────────
app.include_router(wallet.router,     prefix="/api/wallet",     tags=["Wallet"])
app.include_router(activity.router,   prefix="/api/activity",   tags=["Activity"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])
app.include_router(investments.router,prefix="/api/investments",tags=["Investments"])
app.include_router(projects.router,   prefix="/api/projects",   tags=["Projects"])
app.include_router(api_keys.router,   prefix="/api/keys",       tags=["API Keys"])
app.include_router(admin.router,      prefix="/api/admin",      tags=["Admin"])
app.include_router(scanner.router,    prefix="/api/scanner",    tags=["Scanner"])
app.include_router(blog.router,       prefix="/api/blog",       tags=["Blog"])
app.include_router(sectors.router,    prefix="/api/sectors",    tags=["Sectors"])
app.include_router(agent.router,      prefix="/api/agent",      tags=["Agent"])

# ── API-key protected routes ─────────────────────────────────────────────────
_auth = [Depends(require_api_key)]
app.include_router(assets.router,       prefix="/api/assets",      tags=["Assets"],       dependencies=_auth)
app.include_router(orchestrator.router, prefix="/api/orchestrate",  tags=["Orchestrator"], dependencies=_auth)
app.include_router(billing.router,      prefix="/api/billing",      tags=["Billing"],      dependencies=_auth)

app.mount("/static", StaticFiles(directory=str(_STATIC_SITES.parent), html=True), name="static")


@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "ok",
        "service": "AROS — Autonomous Revenue Operating System",
        "version": "3.0.0",
        "api_key_enabled": bool(settings.AROS_API_KEY),
        "docs": "/docs",
    }
