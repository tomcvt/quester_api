from typing import Any, AsyncGenerator
from fastapi import FastAPI
from loguru import logger
from fastapi.concurrency import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.base import Base
from app.models import user, group, group_member # type: ignore
# import for Base.metadata.create_all

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

@asynccontextmanager
async def db_lifespan(app: FastAPI):
    if settings.persistence_mode in ('memory', 'sqlite'):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully.")
    yield