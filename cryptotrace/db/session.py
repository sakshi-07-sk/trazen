"""Database session management with SQLAlchemy 2.0 AsyncEngine."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from cryptotrace.config import get_settings
from cryptotrace.core.logging import logger
from cryptotrace.db.base import Base

settings = get_settings()

# Engine creation: handle sqlite vs postgresql connection options
engine_kwargs = {"echo": settings.DB_ECHO}
if "sqlite" in settings.DATABASE_URL:
    # SQLite does not support pool_size / max_overflow
    pass
else:
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_pre_ping": True,
    })

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session with automatic commit/rollback."""
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
    """Create all schema tables if they do not exist."""
    async with engine.begin() as conn:
        # Import all models to ensure metadata registration
        import cryptotrace.db.models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")
