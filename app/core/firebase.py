
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
import firebase_admin
from firebase_admin import credentials
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    cred = credentials.Certificate(settings.firebase_credentials_path)
    firebase_app = firebase_admin.initialize_app(cred)
    yield
    # shutdown (nothing needed for firebase)