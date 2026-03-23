import uuid
from pydantic import BaseModel


class TokenResponse(BaseModel):
    session_token: str

class AuthResponse(BaseModel):
    session_token: str
    username: str
    fcm_token: str
    

#TODO : add proper login
class AuthRequest(BaseModel):
    device_id: str | None = None
    installation_id: str
    username: str | None = None
    fcm_token: str | None = None

class RegistrationRequest(BaseModel):
    device_id: str | None = None
    installation_id: str
    username: str
    password: str

class RegistrationResponse(BaseModel):
    session_token: str
    username: str