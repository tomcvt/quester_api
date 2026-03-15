from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict
from app.models.group import GroupType, GroupVisibility

class CreateGroupRequest(BaseModel):
    name: str
    password: str | None = None
    type: GroupType = GroupType.WORK
    visibility: GroupVisibility = GroupVisibility.PRIVATE

class GroupResponse(BaseModel):
    public_id: uuid.UUID
    name: str
    type: GroupType
    visibility: GroupVisibility
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)