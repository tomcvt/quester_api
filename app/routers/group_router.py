from datetime import datetime, timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.group import CreateGroupRequest, GroupResponse
from app.schemas.group_member import GroupMembersSyncResponse, GroupMembersSyncResponse
from app.schemas.quest import QuestSyncResponse
from app.services.group_service import GroupService
from app.dependencies import get_group_service, get_current_user
from app.exceptions import GroupNameTakenException

router = APIRouter(prefix="/groups", tags=["groups"])

@router.post("/create", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    body: CreateGroupRequest,
    current_user=Depends(get_current_user),
    service: GroupService = Depends(get_group_service)
):
    try:
        group = await service.create_group(current_user, body)
        return GroupResponse.model_validate(group)
    except GroupNameTakenException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    
@router.get("/{group_public_id}/members", response_model=GroupMembersSyncResponse)
async def get_group_members(
    group_public_id: uuid.UUID,
    since: datetime | None = None,
    service: GroupService = Depends(get_group_service)
):
    #safety net, TODO pagination
    if since is None:
        now = datetime.now()
        last_week = now - timedelta(days=7)
        since = last_week
    members = await service.sync_group_members_after_timestamp(group_public_id, since)
    return GroupMembersSyncResponse(members=members)

@router.get("/{group_public_id}/quests", response_model=QuestSyncResponse)
async def get_group_quests(
    group_public_id: uuid.UUID,
    since: datetime | None = None,
    service: GroupService = Depends(get_group_service)
):
    #safety net, TODO pagination
    if since is None:
        now = datetime.now()
        last_week = now - timedelta(days=7)
        since = last_week
    quests = await service.sync_quests_after_timestamp(group_public_id, since)
    return QuestSyncResponse(quests=quests)