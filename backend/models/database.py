"""SQLAlchemy async engine and session factory for SQLite."""

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings


# Ensure the data directory exists
_db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
_db_dir = os.path.dirname(_db_path)
if _db_dir:
    os.makedirs(_db_dir, exist_ok=True)


engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},  # Required for SQLite
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency that provides an async database session.

    Usage in FastAPI:
        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables defined in the ORM models.

    Called once at application startup.
    """
    async with engine.begin() as conn:
        from models.orm_models import (  # noqa: F401 — import for side-effects
            User,
            Strategy,
            StrategyVersion,
            BacktestJob,
            BacktestResult,
            DataCacheMetadata,
        )
        await conn.run_sync(Base.metadata.create_all)
