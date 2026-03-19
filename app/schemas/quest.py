

from datetime import datetime
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
    #TODO this is a bit of a hack, we should have a separate field for the data that is not a string, but this is easier for now
    #TODO data can be nullable, we should handle that properly
    data: str
    type: QuestType
    inclusive: bool
    status: QuestStatus
    creator_public_id: uuid.UUID
    created_at: datetime
    updated_at: datetime