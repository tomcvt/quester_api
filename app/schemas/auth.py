import uuid
from pydantic import BaseModel

from app.models.user import UserRole


class TokenResponse(BaseModel):
    session_token: str

#TODO add proper login

class AuthResponse(BaseModel):
    session_token: str
    username: str | None
    #phone_number: str | None
    #role: UserRole
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
    username: str | None = None
    phone_number: str | None = None
    password: str

class RegistrationResponse(BaseModel):
    session_token: str
    api_key: str
    username: str | None = None
    public_id: uuid.UUID | None = None
    
    def __str__(self):
        return f"RegistrationResponse(session_token={self.session_token},\n api_key={self.api_key},\n username={self.username},\n public_id={self.public_id})"

class ChangeUsernameRequest(BaseModel):
    username: str

class ChangePhoneNumberRequest(BaseModel):
    phone_number: str

class ChangeUsernamePhoneRequest(BaseModel):
    username: str | None = None
    phone_number: str | None = None