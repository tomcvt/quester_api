

from datetime import datetime
import datetime
from dataclasses import dataclass
import uuid

from pydantic import BaseModel

from app.models.quest import QuestStatus, QuestType

from app.models.quest import QuestType


class CreateQuestRequest(BaseModel):
    group_public_id: uuid.UUID
    name: str
    data: str
    type: QuestType
    inclusive: bool
    status: QuestStatus
    creator_public_id: uuid.UUID

class CreateQuestResponse(BaseModel):
    public_id: uuid.UUID
    name: str
    data: str
    type: QuestType
    inclusive: bool
    status: QuestStatus
    creator_public_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

class QuestSyncDTO(BaseModel):
    group_public_id: uuid.UUID
    public_id: uuid.UUID
    name: str
    data: str
    type: QuestType
    inclusive: bool
    status: QuestStatus
    creator_public_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

class QuestSyncResponse(BaseModel):
    quests: list[QuestSyncDTO]

@dataclass
class QuestWithUser:
    id: int
    public_id: uuid.UUID
    name: str
    data: str
    type: QuestType
    inclusive: bool
    status: QuestStatus
    creator_public_id: uuid.UUID
    created_at: datetime
    updated_at: datetime