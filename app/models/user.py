from dataclasses import dataclass
from datetime import datetime
from typing import Self
import uuid
import enum
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Enum, Index, String, DateTime, Uuid
from sqlalchemy.sql import func

from app.models.base import Base


class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"
    SUPERUSER = "superuser"

class User(Base):
    __tablename__ = "users"
    
    @staticmethod
    def new(user: NewUser) -> 'User':
        return User(
            device_id=user.device_id,
            installation_id=user.installation_id,
            username=user.username,
            phone_number=user.phone_number,
            public_id=uuid.uuid4(),
            fcm_token=user.fcm_token,
            api_key_hash=user.api_key_hash,
            password_hash=user.password_hash,
            role=user.role
        )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    installation_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=True)
    public_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True, native_uuid=False), unique=True, nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String, nullable=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=True)
    session_token: Mapped[str] = mapped_column(String, nullable=True)
    fcm_token: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index("ix_users_public_id", "public_id"),
        Index("ix_users_installation_id", "installation_id"),
    )
    
    def __repr__(self):
        return f"User(id={self.id}, device_id='{self.device_id}', installation_id='{self.installation_id}', username='{self.username}', phone_number='{self.phone_number}', public_id='{self.public_id}', created_at='{self.created_at}', updated_at='{self.updated_at}')"
    
    '''Intentionally shortened representation for __str__'''
    def __str__(self):
        return f"User(id={self.id},\n device_id='{self.device_id}',\n installation_id='{self.installation_id}',\n username='{self.username}',\n phone_number='{self.phone_number}',\n public_id='{self.public_id}',\n role='{self.role}')"

class UserX(BaseModel):
    id: int
    device_id: str
    installation_id: str
    username: str | None
    role: UserRole
    phone_number: str | None
    public_id: uuid.UUID
    api_key_hash: str | None
    session_token: str | None
    fcm_token: str | None
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_orm(cls, user: User) -> Self:
        return cls(
            id=user.id,
            device_id=user.device_id,
            installation_id=user.installation_id,
            username=user.username,
            role=user.role,
            phone_number=user.phone_number,
            public_id=user.public_id,
            api_key_hash=user.api_key_hash,
            session_token=user.session_token,
            fcm_token=user.fcm_token,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

@dataclass
class NewUser:
    device_id: str
    installation_id: str
    username: str | None = None
    role: UserRole = UserRole.USER
    phone_number: str | None = None
    fcm_token: str | None = None
    api_key_hash: str | None = None
    password_hash: str | None = None
    session_token: str | None = None