# app/models/group.py
import enum, uuid
from datetime import datetime
from sqlalchemy import DateTime, String, Enum, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class GroupType(enum.Enum):
    WORK = "WORK"

class GroupVisibility(enum.Enum):
    PRIVATE = "PRIVATE"
    PUBLIC = "PUBLIC"

class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    public_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=uuid.uuid4, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[GroupType] = mapped_column(Enum(GroupType), nullable=False)
    visibility: Mapped[GroupVisibility] = mapped_column(Enum(GroupVisibility), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())