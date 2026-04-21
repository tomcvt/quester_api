from typing import Literal
import uuid
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    persistence_mode: Literal['db', 'memory'] = 'memory'
    database_url: str
    sqlite_url: str
    secret_key: str
    firebase_credentials_path: str
    reserved_installation_ids: list[str] = [str(uuid.UUID(int=i)) for i in range(20)]

    class Config:
        env_file = ".env"

settings = Settings() # pyright: ignore[reportCallIssue]