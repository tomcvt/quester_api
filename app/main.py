from fastapi import APIRouter, FastAPI, Request
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import logging
import time
from app.core.database import db_lifespan
from app.exc_handler import register_exception_handlers
from app.models.base import Base
from app.models import user, group, group_member # type: ignore
# import for Base.metadata.create_all
from app.routers.quest_router import router as quest_router
from app.routers.group_router import router as group_router
from app.routers.user_router import router as user_router
from app.routers.auth_router import router as auth_router
from app.core.config import settings
from app.core.firebase import firebase_lifespan
from app.dev.dev_data_seeder import dev_data_seeder_lifespan


class InterceptHandler(logging.Handler):
    def emit(self, record):
        level = logger.level(record.levelname).name
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())

logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
logging.getLogger("aiosqlite").setLevel(logging.INFO) 

@asynccontextmanager
async def lifespan(app: FastAPI):
    #startup
    async with db_lifespan(app):
        async with firebase_lifespan(app):
            async with dev_data_seeder_lifespan(app):
                yield

app = FastAPI(title="Quester API", version="0.1.0", lifespan=lifespan)

global_router = APIRouter(prefix="/api/v1")
global_router.include_router(group_router)
global_router.include_router(user_router)
global_router.include_router(auth_router)
global_router.include_router(quest_router)

app.include_router(global_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP — lock this down before production
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
'''
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
'''

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    if response.status_code in (400, 422):
        body_bytes = b""
        async for chunk in response.body_iterator:
            body_bytes += chunk
        logger.warning(
            "method={} path={} status={} duration={:.3f}s body={}",
            request.method,
            request.url.path,
            response.status_code,
            duration,
            body_bytes.decode()
        )
        from starlette.responses import Response
        return Response(
            content=body_bytes,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )

    logger.info(
        "method={} path={} status={} duration={:.3f}s",
        request.method,
        request.url.path,
        response.status_code,
        duration
    )
    return response

#uvicorn app.main:app --reload --port 8100