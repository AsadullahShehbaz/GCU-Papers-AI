# ============================================================
# main.py — FastAPI app entry point
# Start with: uvicorn main:app --reload
# ============================================================

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import engine, Base
from routes import papers, auth
from fastapi.staticfiles import StaticFiles


# ── Create DB tables on startup ───────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


# ── App instance ──────────────────────────────────────────────
app = FastAPI(
    title="GCUL Papers API",
    description="Backend for GCUL BSCS Past Papers platform",
    version="1.0.0",
    lifespan=lifespan,
)


# ── CORS — allow frontend to call this API ────────────────────
origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# After all routes are registered, add at the bottom:
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# ── Register routes ───────────────────────────────────────────
app.include_router(papers.router, prefix="/api")
app.include_router(auth.router, prefix="/api")


# ── Health check ─────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "ok", "message": "GCUL Papers API is running"}