
import uuid
from datetime import datetime
from sqlalchemy import Index, String, DateTime, Boolean, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    family_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True, native_uuid=False), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    __table_args__ = (
        Index("ix_refresh_tokens_token_hash", "token_hash"),
        Index("ix_refresh_tokens_family_id", "family_id")
    )
    
    def __repr__(self):
        return f"RefreshToken(id={self.id}, user_id={self.user_id}, " \
               f"token_hash='{self.token_hash}', family_id='{self.family_id}', " \
               f"expires_at='{self.expires_at}', revoked={self.revoked}, " \
               f"created_at='{self.created_at}')"
    def __str__(self):
        return self.__repr__()
    
    def is_expired(self) -> bool:
        return datetime.utcnow() >= self.expires_at
    
    def revoke(self):
        self.revoked = True