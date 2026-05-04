import uuid
from pydantic import BaseModel

from app.models.user import UserRole

class OAuthLoginRequest(BaseModel):
    id_token: str
    installation_id: str
    email: str | None = None
    fcm_token: str | None = None

class TokenResponse(BaseModel):
    session_token: str

class UpdateFcmTokenRequest(BaseModel):
    installation_id: str
    fcm_token: str

class SessionRequest(BaseModel):
    installation_id: str
    fcm_token: str | None = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str
    

#TODO add proper login
'''return SessionResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            username=user.username,
            phone_number=user.phone_number,
            oauth_provider=user.oauth_provider,
            public_id=user.public_id,
            role=user.role,
            installation_id=user.installation_id,
        )
'''
class SessionResponse(BaseModel):
    access_token: str
    refresh_token: str
    username: str | None
    phone_number: str | None
    oauth_provider: str | None
    public_id: uuid.UUID
    role: UserRole
    installation_id: str

class AuthResponse(BaseModel):
    session_token: str
    installation_id: str
    username: str | None
    phone_number: str | None
    role: UserRole
    public_id: uuid.UUID
    email: str | None = None
    fcm_token: str | None = None
    oauth_provider: str | None = None

class AuthRequest(BaseModel):
    device_id: str | None = None
    installation_id: str
    api_key: str
    username: str | None = None
    password: str | None = None
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

class WebLoginRequest(BaseModel):
    username: str
    password: str

class WebRegisterRequest(BaseModel):
    username: str
    password: str