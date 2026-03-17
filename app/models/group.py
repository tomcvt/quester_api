# app/models/group.py
from dataclasses import dataclass
import enum, uuid
from datetime import datetime
from sqlalchemy import DateTime, Index, String, Enum, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class GroupType(enum.Enum):
    WORK = "WORK"

class GroupVisibility(enum.Enum):
    PRIVATE = "PRIVATE"
    PUBLIC = "PUBLIC"

class Group(Base):
    """Represents a group that users can join to share quests and progress."""
    __tablename__ = "groups"
    
    @staticmethod
    def new(group: NewGroup) -> 'Group':
        return Group(
            name=group.name,
            public_id=uuid.uuid4(),
            password=group.password,
            type=group.type,
            visibility=group.visibility
        )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    public_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True, native_uuid=False), default=uuid.uuid4, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[GroupType] = mapped_column(Enum(GroupType), nullable=False)
    visibility: Mapped[GroupVisibility] = mapped_column(Enum(GroupVisibility), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index("ix_groups_public_id", "public_id"),
        Index("ix_groups_name", "name")
    )

@dataclass
class NewGroup:
    name: str
    password: str | None
    type: GroupType
    visibility: GroupVisibility
    
#TODO change native uuid when we switch to postgres, also add index on public_id and name