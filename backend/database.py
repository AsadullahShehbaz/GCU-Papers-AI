# ============================================================
# database.py — Neon PostgreSQL connection
# Uses SQLAlchemy async engine for non-blocking DB calls
# ============================================================

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import settings

# asyncpg driver needed: pip install asyncpg
# Convert postgres:// → postgresql+asyncpg://
DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
)

# Engine — one instance for the whole app
engine = create_async_engine(
    DATABASE_URL,
    echo=False,   # set True to log all SQL (useful for debugging)
)

# Session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class all models inherit from
class Base(DeclarativeBase):
    pass

# ── Dependency for FastAPI routes ─────────────────────────────
# Usage in any route: db: AsyncSession = Depends(get_db)
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise