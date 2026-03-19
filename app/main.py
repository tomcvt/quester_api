from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import logging
import time
from app.core.database import engine
from app.exc_handler import register_exception_handlers
from app.models.base import Base
from app.models import user, group, group_member # type: ignore
# import for Base.metadata.create_all
from app.routers.group_router import router as group_router
from app.routers.user_router import router as user_router
from app.routers.auth_router import router as auth_router
from app.core.config import settings


class InterceptHandler(logging.Handler):
    def emit(self, record):
        level = logger.level(record.levelname).name
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())

logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

app = FastAPI(title="Quester API", version="0.1.0")

global_router = APIRouter(prefix="/api/v1")
global_router.include_router(group_router)
global_router.include_router(user_router)
global_router.include_router(auth_router)

app.include_router(global_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP — lock this down before production
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    body = await request.body()
    logger.debug("incoming body: {}", body.decode())
    response = await call_next(request)
    duration = time.time() - start
    logger.info(
        "method={} path={} status={} duration={:.3f}s",
        request.method,
        request.url.path,
        response.status_code,
        duration
    )
    return response

@app.on_event("startup")
async def startup():
    logger.info("Starting Quester Api with persistence mode: %s", settings.persistence_mode)
    if settings.persistence_mode in ('memory', 'sqlite'):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully.")


#uvicorn app.main:app --reload --port 8100