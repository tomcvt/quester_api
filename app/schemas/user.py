

from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict

from app.models.user import UserRole

class UserFullDto(BaseModel):
    id: int
    username: str | None
    phone_number: str | None
    public_id: uuid.UUID
    role: UserRole
    installation_id: str | None
    
    model_config = ConfigDict(from_attributes=True)

class UserDto(BaseModel):
    username: str | None
    phone_number: str | None
    public_id: uuid.UUID
    role: UserRole
    
    model_config = ConfigDict(from_attributes=True)

class UsersSyncRequest(BaseModel):
    public_ids: list[uuid.UUID]

class UsersSyncResponse(BaseModel):
    users: list[UserDto]
    
    model_config = ConfigDict(from_attributes=True)

class UserUpdateEvent(BaseModel):
    id: int
    public_id: uuid.UUID
    type: str
    data: str | None = None
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)