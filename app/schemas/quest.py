

from datetime import datetime
from dataclasses import dataclass
import uuid

from pydantic import BaseModel

from app.models.quest import Quest, QuestStatus, QuestType

from app.models.quest import QuestType


class CreateQuestRequest(BaseModel):
    group_public_id: uuid.UUID
    name: str
    data: str | None = None
    contact_info: str | None = None
    deadline: str | None = None
    address: str | None = None
    contact_number: str | None = None
    type: QuestType
    inclusive: bool
    status: QuestStatus
    creator_public_id: uuid.UUID
    accepted_by_public_id: uuid.UUID | None = None

class CreateQuestResponse(BaseModel):
    public_id: uuid.UUID
    name: str
    data: str | None
    contact_info: str | None
    deadline: str | None
    address: str | None
    contact_number: str | None
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
            data=quest.data,
            contact_info=quest.contact_info,
            deadline=quest.deadline,
            address=quest.address,
            contact_number=quest.contact_number,
            type=quest.type,
            inclusive=quest.inclusive,
            status=quest.status,
            creator_public_id=uuid.NIL,  # This will need to be set separately after fetching the creator's public_id',
            created_at=quest.created_at,
            updated_at=quest.updated_at,
            accepted_by_public_id=uuid.NIL  # This will need to be set separately after fetching the accepter's public_id
        )

class QuestSyncDTO(BaseModel):
    group_public_id: uuid.UUID
    public_id: uuid.UUID
    name: str
    data: str | None
    contact_info: str | None
    deadline: str | None
    address: str | None
    contact_number: str | None
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
    data: str | None
    deadline: str | None
    address: str | None
    contact_number: str | None
    contact_info: str | None
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