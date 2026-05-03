

"""
Legacy quest schemas retained during product-model refactor.

from datetime import datetime
from dataclasses import dataclass
import uuid

from pydantic import BaseModel, ConfigDict

from app.models.quest import Quest, QuestStatus, QuestType

class QuestFullDto(BaseModel):
    id: int
    public_id: uuid.UUID
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
    created_at: datetime
    updated_at: datetime
    accepted_by_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class CreateQuestRequest(BaseModel):
    group_public_id: uuid.UUID
    name: str
    description: str | None = None
    date: datetime | None = None
    deadline_start: datetime | None = None
    deadline_end: datetime | None = None
    address: str | None = None
    contact_number: str | None = None
    contact_info: str | None = None
    data: str | None = None
    type: QuestType
    inclusive: bool
    status: QuestStatus
    creator_public_id: uuid.UUID
    accepted_by_public_id: uuid.UUID | None = None

class CreateQuestResponse(BaseModel):
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
    creator_public_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    accepted_by_public_id: uuid.UUID | None = None

    @classmethod
    def from_orm_without_creator(cls, quest: Quest) -> 'CreateQuestResponse':
        return cls(
            public_id=quest.public_id,
            name=quest.name,
            description=quest.description,
            date=quest.date,
            deadline_start=quest.deadline_start,
            deadline_end=quest.deadline_end,
            address=quest.address,
            contact_number=quest.contact_number,
            contact_info=quest.contact_info,
            data=quest.data,
            type=quest.type,
            inclusive=quest.inclusive,
            status=quest.status,
            creator_public_id=uuid.UUID(int=0),
            created_at=quest.created_at,
            updated_at=quest.updated_at,
            accepted_by_public_id=None,
        )

class QuestSyncDTO(BaseModel):
    group_public_id: uuid.UUID
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
    creator_public_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    accepted_by_public_id: uuid.UUID | None = None

class QuestSyncResponse(BaseModel):
    quests: list[QuestSyncDTO]

@dataclass
class QuestWithUserPId:
    id: int
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
    creator_public_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    accepted_by_public_id: uuid.UUID | None = None

@dataclass
class QuestUpdateEvent:
    id: int
    public_id: uuid.UUID
    group_id: int
    group_public_id: uuid.UUID
    status: QuestStatus
    updated_at: datetime
    accepted_by_public_id: uuid.UUID | None = None
    source_user_public_id: uuid.UUID | None = None
"""

from dataclasses import dataclass
from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict

from app.models.quest import JsonValue, Quest, QuestStatus, RewardType


class QuestFullDto(BaseModel):
    id: int
    public_id: uuid.UUID
    group_id: int
    name: str
    description: str | None
    start_time: datetime
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

    model_config = ConfigDict(from_attributes=True)


class CreateQuestRequest(BaseModel):
    group_public_id: uuid.UUID
    name: str
    description: str | None = None
    start_time: datetime | None = None
    deadline: datetime | None = None
    address: str | None = None
    data: JsonValue = None
    reward_type: RewardType = RewardType.NONE
    reward_value: str | None = None
    inclusive: bool
    automatic_reward: bool = True
    status: QuestStatus = QuestStatus.OPEN


class CreateQuestResponse(BaseModel):
    public_id: uuid.UUID
    name: str
    description: str | None
    start_time: datetime
    deadline: datetime | None
    address: str | None
    data: JsonValue
    reward_type: RewardType
    reward_value: str | None
    inclusive: bool
    automatic_reward: bool
    status: QuestStatus
    creator_public_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    accepted_by_public_id: uuid.UUID | None = None

    @classmethod
    def from_orm_without_creator(cls, quest: Quest) -> "CreateQuestResponse":
        return cls(
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
            automatic_reward=quest.automatic_reward,
            status=quest.status,
            creator_public_id=uuid.UUID(int=0),
            created_at=quest.created_at,
            updated_at=quest.updated_at,
            accepted_by_public_id=None,
        )


class QuestSyncDTO(BaseModel):
    group_public_id: uuid.UUID
    public_id: uuid.UUID
    name: str
    description: str | None
    start_time: datetime
    deadline: datetime | None
    address: str | None
    data: JsonValue
    reward_type: RewardType
    reward_value: str | None
    inclusive: bool
    automatic_reward: bool = True
    status: QuestStatus
    creator_public_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    accepted_by_public_id: uuid.UUID | None = None


class QuestSyncResponse(BaseModel):
    quests: list[QuestSyncDTO]


@dataclass
class QuestWithUserPId:
    id: int
    public_id: uuid.UUID
    name: str
    description: str | None
    start_time: datetime
    deadline: datetime | None
    address: str | None
    data: JsonValue
    reward_type: RewardType
    reward_value: str | None
    inclusive: bool
    status: QuestStatus
    creator_public_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    accepted_by_public_id: uuid.UUID | None = None
    automatic_reward: bool = True


@dataclass
class QuestUpdateEvent:
    id: int
    public_id: uuid.UUID
    group_id: int
    group_public_id: uuid.UUID
    status: QuestStatus
    updated_at: datetime
    accepted_by_public_id: uuid.UUID | None = None
    source_user_public_id: uuid.UUID | None = None