
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
import firebase_admin
from firebase_admin import credentials
from loguru import logger
from app.core.config import settings


@asynccontextmanager
async def firebase_lifespan(app: FastAPI):
    # startup
    cred = credentials.Certificate(settings.firebase_credentials_path)
    firebase_app = firebase_admin.initialize_app(cred)
    logger.info("Firebase initialized successfully with app name: {}", firebase_app.name)
    yield
    # shutdown (nothing needed for firebase)