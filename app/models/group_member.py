from dataclasses import dataclass
import enum
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import String, Enum, ForeignKey, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base

class MemberRole(enum.Enum):
    OWNER = "OWNER"
    MEMBER = "MEMBER"

class GroupMember(Base):
    __tablename__ = "group_members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("group_id", "user_id"),
        Index("ix_group_members_group_updated", "group_id", "updated_at"),
        Index("ix_group_members_user_updated", "user_id", "updated_at")
    )

class GroupMemberX(BaseModel):
    id: int
    group_id: int
    user_id: int
    role: MemberRole
    updated_at: datetime
    
    @classmethod
    def from_orm(cls, group_member: GroupMember) -> 'GroupMemberX':
        return cls(
            id=group_member.id,
            group_id=group_member.group_id,
            user_id=group_member.user_id,
            role=group_member.role,
            updated_at=group_member.updated_at
        )