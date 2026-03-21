from typing import Literal
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    persistence_mode: Literal['db', 'memory'] = 'memory'
    database_url: str
    sqlite_url: str
    secret_key: str
    firebase_credentials_path: str

    class Config:
        env_file = ".env"

settings = Settings() # pyright: ignore[reportCallIssue]