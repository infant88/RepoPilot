import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Configure engine based on URL
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

is_sqlite = db_url.startswith("sqlite")

engine_kwargs = {"echo": False}
if not is_sqlite:
    engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_pre_ping": True,
    })

engine = create_async_engine(db_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

def get_session_context():
    return AsyncSessionLocal()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initializes tables and pgvector extension if using PostgreSQL, falling back to SQLite if offline."""
    global engine, AsyncSessionLocal, is_sqlite
    try:
        async with engine.begin() as conn:
            if not is_sqlite:
                try:
                    from sqlalchemy import text
                    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    logger.info("pgvector extension initialized or already enabled")
                except Exception as e:
                    logger.warning(f"Could not enable pgvector extension: {e}")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to connect to primary database ({settings.DATABASE_URL}): {e}")
        logger.info("Switching to local fallback SQLite database (sqlite+aiosqlite:///./repopilot_local.db)...")
        is_sqlite = True
        engine = create_async_engine("sqlite+aiosqlite:///./repopilot_local.db", echo=False)
        AsyncSessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Local fallback database initialized successfully.")

