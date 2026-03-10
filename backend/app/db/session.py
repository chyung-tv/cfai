from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

if not settings.database_url:
    raise RuntimeError("DATABASE_URL is required. Set a Neon pooled connection string.")

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
