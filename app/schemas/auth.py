import uuid
from pydantic import BaseModel


class TokenResponse(BaseModel):
    session_token: str

#TODO add proper login

class AuthResponse(BaseModel):
    session_token: str
    username: str
    public_id: uuid.UUID
    fcm_token: str

class AuthRequest(BaseModel):
    device_id: str | None = None
    installation_id: str
    api_key: str
    username: str | None = None
    fcm_token: str | None = None

class RegistrationRequest(BaseModel):
    device_id: str | None = None
    installation_id: str
    username: str
    password: str

class RegistrationResponse(BaseModel):
    session_token: str
    api_key: str
    username: str
    public_id: uuid.UUID | None = None

class ChangeUsernameRequest(BaseModel):
    username: str