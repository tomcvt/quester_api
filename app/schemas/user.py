

import uuid

from pydantic import BaseModel, ConfigDict


class UserDto(BaseModel):
    username: str | None
    public_id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)

class UsersSyncRequest(BaseModel):
    public_ids: list[uuid.UUID]

class UsersSyncResponse(BaseModel):
    users: list[UserDto]
    
    model_config = ConfigDict(from_attributes=True)