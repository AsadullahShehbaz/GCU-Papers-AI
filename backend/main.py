# ============================================================
# main.py — FastAPI app entry point
# Start with: uvicorn main:app --reload
# ============================================================

import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from database import engine, Base
from routes import papers, auth


# ── Logging setup ─────────────────────────────────────────────
def setup_logging():
    """
    Configure logging to stdout so Vercel captures every line.
    Vercel streams stdout/stderr directly into its log viewer.
    """
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%dT%H:%M:%S"

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        stream=sys.stdout,       # ← Vercel reads stdout
        force=True,              # ← override any existing handlers
    )

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return logging.getLogger("gcul_api")


logger = setup_logging()


# ── Lifespan ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting GCUL Papers API...")
    logger.info("DB  | Creating tables if they don't exist")

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("DB  | Tables ready ✓")
    except Exception:
        logger.exception("DB  | Failed to create tables")
        raise

    logger.info("APP | Startup complete — ready to serve requests")
    yield
    logger.info("APP | Shutting down — goodbye 👋")


# ── App instance ──────────────────────────────────────────────
app = FastAPI(
    title="GCUL Papers API",
    description="Backend for GCUL BSCS Past Papers platform",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Request / Response logging middleware ─────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every incoming request and its response — visible in Vercel logs."""
    request_id = str(uuid.uuid4())[:8]          # short ID to correlate req↔res
    start = time.perf_counter()

    logger.info(
        "REQ  | id=%s  %s %s  client=%s",
        request_id,
        request.method,
        request.url.path,
        request.client.host if request.client else "unknown",
    )

    # Log query params if present
    if request.query_params:
        logger.info("REQ  | id=%s  params=%s", request_id, dict(request.query_params))

    try:
        response: Response = await call_next(request)
    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        logger.exception(
            "ERR  | id=%s  %s %s → UNHANDLED EXCEPTION  (%.1f ms)",
            request_id, request.method, request.url.path, elapsed,
        )
        raise exc

    elapsed = (time.perf_counter() - start) * 1000
    level = logging.WARNING if response.status_code >= 400 else logging.INFO
    logger.log(
        level,
        "RES  | id=%s  %s %s → %d  (%.1f ms)",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )

    return response


# ── CORS ──────────────────────────────────────────────────────
origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
logger.info("CORS | Allowed origins: %s", origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)



# ── Routes ────────────────────────────────────────────────────
app.include_router(papers.router, prefix="/api/papers")
app.include_router(auth.router,   prefix="/api/auth")
logger.info("APP | Routers registered: /api/papers, /api/auth")

# ── Static frontend ───────────────────────────────────────────
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
# ── Health check ──────────────────────────────────────────────
@app.get("/health")
async def health():
    logger.info("HEALTH | ping received")
    return {"status": "ok", "message": "GCUL Papers API is running"}
