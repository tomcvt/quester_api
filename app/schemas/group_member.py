from dataclasses import dataclass
from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict
from app.models.group_member import GroupMember, GroupMemberX, MemberRole
from app.models.user import User, UserX

class GroupMemberSyncDTO(BaseModel):
    #public_id: str
    group_public_id: uuid.UUID
    user_public_id: uuid.UUID
    role: MemberRole
    username: str
    currency: int = 0
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

@dataclass
class GroupMemberWithUserSlim:
    #group_member: GroupMember /we cant use because its the sqlalchemy and pydantic doesnt know how to handle it
    id: int
    group_id: int
    user_id: int
    role: MemberRole
    updated_at: datetime
    username: str
    user_public_id: uuid.UUID
    currency: int = 0

@dataclass
class GroupMemberWithUser:
    group_member: GroupMemberX
    user: UserX

class GroupMembersSyncResponse(BaseModel):
    members: list[GroupMemberSyncDTO]