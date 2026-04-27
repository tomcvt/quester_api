"""
Legacy quest model retained during product-model refactor.

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
            deadline_start=quest.deadline_start,
            deadline_end=quest.deadline_end,
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
    description: Mapped[str] = mapped_column(String, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    deadline_start: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    deadline_end: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    address: Mapped[str] = mapped_column(String, nullable=True)
    contact_number: Mapped[str] = mapped_column(String, nullable=True)
    contact_info: Mapped[str] = mapped_column(String, nullable=True)
    data: Mapped[str] = mapped_column(String, nullable=True)
    type: Mapped[QuestType] = mapped_column(Enum(QuestType), nullable=False)
    inclusive: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[QuestStatus] = mapped_column(Enum(QuestStatus), nullable=False)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    accepted_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    __table_args__ = (
        Index("ix_quests_public_id", "public_id"),
        Index("ix_quests_group_id_updated_at", "group_id", "updated_at")
    )
    
    def __repr__(self):
        return f"<Quest(id={self.id}, public_id={self.public_id}, name='{self.name}', group_id={self.group_id}, creator_id={self.creator_id})>"

class QuestX(BaseModel):
    id: int
    group_id: int
    public_id: uuid.UUID
    name: str
    description: str | None
    date: datetime | None
    deadline_start: datetime | None
    deadline_end: datetime | None
    address: str | None
    contact_number: str | None
    contact_info: str | None
    data: str | None
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
            description=quest.description,
            date=quest.date,
            deadline_start=quest.deadline_start,
            deadline_end=quest.deadline_end,
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
    description: str | None
    date: datetime | None
    deadline_start: datetime | None 
    deadline_end: datetime | None
    address: str | None
    contact_number: str | None
    contact_info: str | None
    data: str | None
    type: QuestType
    inclusive: bool
    status: QuestStatus
    creator_id: int
    accepted_by_id: int | None = None

class UpdateQuest(BaseModel):
    name: str | None = None
    description: str | None = None
    date: datetime | None = None
    deadline_start: datetime | None = None
    deadline_end: datetime | None = None
    address: str | None = None
    contact_number: str | None = None
    contact_info: str | None = None
    data: str | None = None
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
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
import enum
import uuid

from pydantic import BaseModel
from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base

JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None


class RewardType(enum.Enum):
    NONE = "NONE"
    CURRENCY = "CURRENCY"
    PRIZE = "PRIZE"


class QuestStatus(enum.Enum):
    CREATED = "CREATED"
    OPEN = "OPEN"
    ACCEPTED = "ACCEPTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class Quest(Base):
    __tablename__ = "quests"
    # TODO [WARNING]: the database table still needs a real schema migration from the legacy quest columns
    # to deadline/start_time/data/reward_type/reward_value and the new status set. Commenting old Python code does not
    # migrate persisted data.

    @staticmethod
    def new(quest: "NewQuest") -> "Quest":
        return Quest(
            group_id=quest.group_id,
            public_id=uuid.uuid4(),
            name=quest.name,
            description=quest.description,
            start_time=quest.start_time,
            deadline=quest.deadline,
            address=quest.address,
            data=quest.data,
            reward_type=quest.reward_type,
            reward_value=quest.reward_value,
            inclusive=quest.inclusive,
            status=quest.status,
            creator_id=quest.creator_id,
            accepted_by_id=quest.accepted_by_id,
        )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    public_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True, native_uuid=False), default=uuid.uuid4, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    data: Mapped[JsonValue] = mapped_column(JSON, nullable=True)
    reward_type: Mapped[RewardType] = mapped_column(Enum(RewardType), nullable=False, default=RewardType.NONE)
    reward_value: Mapped[str | None] = mapped_column(String, nullable=True)
    inclusive: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[QuestStatus] = mapped_column(Enum(QuestStatus), nullable=False)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    accepted_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_quests_public_id", "public_id"),
        Index("ix_quests_group_id_updated_at", "group_id", "updated_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Quest(id={self.id}, public_id={self.public_id}, name='{self.name}', "
            f"group_id={self.group_id}, creator_id={self.creator_id}, status={self.status.value})>"
        )


class QuestX(BaseModel):
    id: int
    group_id: int
    public_id: uuid.UUID
    name: str
    description: str | None
    start_time: datetime | None
    deadline: datetime | None
    address: str | None
    data: JsonValue
    reward_type: RewardType
    reward_value: str | None
    inclusive: bool
    status: QuestStatus
    creator_id: int
    created_at: datetime
    updated_at: datetime
    accepted_by_id: int | None = None

    @classmethod
    def from_orm(cls, quest: Quest) -> "QuestX":
        return cls(
            id=quest.id,
            group_id=quest.group_id,
            public_id=quest.public_id,
            name=quest.name,
            description=quest.description,
            start_time=quest.start_time,
            deadline=quest.deadline,
            address=quest.address,
            data=quest.data,
            reward_type=quest.reward_type,
            reward_value=quest.reward_value,
            inclusive=quest.inclusive,
            status=quest.status,
            creator_id=quest.creator_id,
            created_at=quest.created_at,
            updated_at=quest.updated_at,
            accepted_by_id=quest.accepted_by_id,
        )


@dataclass
class NewQuest:
    group_id: int
    name: str
    description: str | None
    start_time: datetime | None
    deadline: datetime | None
    address: str | None
    data: JsonValue
    reward_type: RewardType
    reward_value: str | None
    inclusive: bool
    status: QuestStatus
    creator_id: int
    accepted_by_id: int | None = None


class UpdateQuest(BaseModel):
    name: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    deadline: datetime | None = None
    address: str | None = None
    data: JsonValue = None
    reward_type: RewardType | None = None
    reward_value: str | None = None
    inclusive: bool | None = None
    status: QuestStatus | None = None
    accepted_by_id: int | None = None


# TODO [PENDING]: delayed-start quests now persist as CREATED when start_time is present.
# A separate queue/worker still needs to promote them to OPEN and trigger the right notifications at start_time.