# app/core/jwt.py
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
import uuid
from jose import JWTError, jwt
from app.core.config import globalSettings
from app.exceptions import InvalidCredentialsException
from app.models.user import User, UserRole

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30
ALGORITHM = "HS256"

@dataclass
class AuthUser:
    public_id: uuid.UUID
    username: str
    role: UserRole
    installation_id: str

def create_access_token(user: User) -> str:
    claims = {
        "sub": str(user.public_id),
        "username": user.username,
        "role": user.role.value,
        "installation_id": user.installation_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(claims, globalSettings.jwt_secret, algorithm=ALGORITHM)

def decode_access_token(token: str) -> AuthUser:
    try:
        payload = jwt.decode(token, globalSettings.jwt_secret, algorithms=[ALGORITHM])
        return AuthUser(
            public_id=uuid.UUID(payload["sub"]),
            username=payload["username"],
            role=UserRole(payload["role"]),
            installation_id=payload["installation_id"],
        )
    except JWTError:
        raise InvalidCredentialsException("Invalid or expired token")