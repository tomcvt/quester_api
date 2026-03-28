from dataclasses import dataclass
from datetime import datetime
import enum, uuid
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import Boolean, ForeignKey, Index, String, Enum, Uuid, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base

'''
Data model
class QuestX(BaseModel):
    id: int
    group_id: int
    public_id: uuid.UUID
    name: str
    data: str | None
    deadline: str | None
    address: str | None
    contact_number: str | None
    contact_info: str | None
    type: QuestType
    inclusive: bool
    status: QuestStatus
    creator_id: int
    created_at: datetime
    updated_at: datetime
'''


class QuestType(enum.Enum):
    JOB = "JOB"

class QuestStatus(enum.Enum):
    STARTED = "STARTED"
    ACCEPTED = "ACCEPTED"
    COMPLETED = "COMPLETED"
    DELETED = "DELETED"
    TIMED_OUT = "TIMED_OUT"

class Quest(Base):
    __tablename__ = "quests"
    
    @staticmethod
    def new(quest: NewQuest) -> 'Quest':
        return Quest(
            group_id=quest.group_id,
            name=quest.name,
            public_id=uuid.uuid4(),
            data=quest.data,
            contact_info=quest.contact_info,
            deadline=quest.deadline,
            address=quest.address,
            contact_number=quest.contact_number,
            type=quest.type,
            inclusive=quest.inclusive,
            status=quest.status,
            creator_id=quest.creator_id,
            accepted_by_id=None
        )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    public_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True, native_uuid=False), default=uuid.uuid4, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    data: Mapped[str] = mapped_column(String, nullable=True)  # JSON string or any other relevant data
    deadline: Mapped[str] = mapped_column(String, nullable=True)
    address: Mapped[str] = mapped_column(String, nullable=True)
    contact_number: Mapped[str] = mapped_column(String, nullable=True)
    contact_info: Mapped[str] = mapped_column(String, nullable=True)  # Optional field for contact info
    type: Mapped[QuestType] = mapped_column(Enum(QuestType), nullable=False)
    inclusive: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[QuestStatus] = mapped_column(Enum(QuestStatus), nullable=False)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    accepted_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    __table_args__ = (
        # Unique constraint to prevent duplicate quests with the same name in the same group
        # This is just an example, you can adjust it based on your requirements
        # For instance, you might want to allow duplicate names but enforce uniqueness on public_id
        Index("ix_quests_public_id", "public_id"),
        Index("ix_quests_group_id_updated_at", "group_id", "updated_at")
    )
    
    def __repr__(self):
        return f"<Quest(id={self.id}, group_id={self.group_id}, public_id={self.public_id}, name='{self.name}', type={self.type}, status={self.status})>"

class QuestX(BaseModel):
    id: int
    group_id: int
    public_id: uuid.UUID
    name: str
    data: str | None
    deadline: str | None
    address: str | None
    contact_number: str | None
    contact_info: str | None
    type: QuestType
    inclusive: bool
    status: QuestStatus
    creator_id: int
    created_at: datetime
    updated_at: datetime
    accepted_by_id: int | None = None
    
    @classmethod
    def from_orm(cls, quest: Quest) -> 'QuestX':
        return cls(
            id=quest.id,
            group_id=quest.group_id,
            public_id=quest.public_id,
            name=quest.name,
            deadline=quest.deadline,
            address=quest.address,
            contact_number=quest.contact_number,
            data=quest.data,
            contact_info=quest.contact_info,
            type=quest.type,
            inclusive=quest.inclusive,
            status=quest.status,
            creator_id=quest.creator_id,
            created_at=quest.created_at,
            updated_at=quest.updated_at,
            accepted_by_id=quest.accepted_by_id
        )

@dataclass
class NewQuest:
    group_id: int
    name: str
    data: str | None
    deadline: str | None
    address: str | None
    contact_number: str | None
    contact_info: str | None
    type: QuestType
    inclusive: bool
    status: QuestStatus
    creator_id: int
    accepted_by_id: int | None = None

class UpdateQuest(BaseModel):
    name: str | None = None
    data: str | None = None
    deadline: str | None = None
    address: str | None = None
    contact_number: str | None = None
    contact_info: str | None = None
    type: QuestType | None = None
    inclusive: bool | None = None
    status: QuestStatus | None = None
    accepted_by_id: int | None = None
###
#and quest which is id, publicId, type enum [JOB] (for now), 
# inclusive boolean (if creator is participating), 
# status [STARTED, ACCEPTED, COMPLETED, DELETED, TIMED OUT], 
# created_at, updated_at, creator (userId). 
# as we go we just focus on ONE route for now and i will 
# try to by learning create others and will ask for help in 
# integrating them in services