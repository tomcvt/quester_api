from typing import Any, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

def _build_url() -> str:
    if settings.persistence_mode == 'memory':
        return "sqlite+aiosqlite:///:memory:"
    return settings.database_url

engine = create_async_engine(
    _build_url(),
    connect_args={"check_same_thread": False} if "sqlite" in _build_url() else {}
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    async with AsyncSessionLocal() as session:
        yield session