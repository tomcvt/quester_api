from datetime import datetime, timedelta
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from loguru import logger
from app.models.group_member import MemberRole
from app.schemas.group import CreateGroupRequest, GroupJoinRequest, GroupResponse, SetRoleRequest
from app.schemas.group_member import GroupMembersSyncResponse, GroupMembersSyncResponse
from app.schemas.quest import QuestSyncResponse
from app.services.group_service import GroupService
from app.dependencies import get_group_service, get_current_user
from app.exceptions import GroupNameTakenException, UnauthorizedException

router = APIRouter(prefix="/groups", tags=["groups"])

@router.post("/create", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    body: CreateGroupRequest,
    current_user=Depends(get_current_user),
    service: GroupService = Depends(get_group_service)
):
    logger.info("User {} is creating group with name '{}'", current_user.username, body.name)
    logger.debug("current user: {}", current_user)
    group = await service.create_group(current_user, body)
    return GroupResponse.model_validate(group)
    
@router.get("/{group_public_id}/members", response_model=GroupMembersSyncResponse)
async def get_group_members(
    group_public_id: uuid.UUID,
    since: datetime | None = None,
    service: GroupService = Depends(get_group_service)
):
    #safety net, TODO pagination
    #TODO add user check if member
    if since is None:
        now = datetime.now()
        last_week = now - timedelta(days=7)
        since = last_week
    members = await service.sync_group_members_after_timestamp(group_public_id, since)
    return GroupMembersSyncResponse(members=members)

#TODO - unsafe, dont use
@router.post("/{group_public_id}/join", status_code=status.HTTP_200_OK)
async def join_group_public(
    group_public_id: uuid.UUID,
    #background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    service: GroupService = Depends(get_group_service)
):
    raise HTTPException(status_code=400, detail="Joining groups by public_id is not allowed. Please join by group name and password.")
    logger.info("User {} is joining group with public_id '{}'", current_user.username, group_public_id)
    await service.join_group(current_user, group_public_id)
    return {"message": "Successfully joined the group."}

@router.post("/join", response_model=GroupResponse, status_code=status.HTTP_200_OK)
async def join_group(
    body: GroupJoinRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    service: GroupService = Depends(get_group_service)
):
    logger.info("User {} is joining group with name '{}'", current_user.username, body.name)
    group = await service.join_group_with_password(current_user, body.name, body.password, background_tasks)
    return GroupResponse.model_validate(group)

@router.post("/{group_public_id}/leave", status_code=status.HTTP_200_OK)
async def leave_group(
    group_public_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    service: GroupService = Depends(get_group_service)
):
    logger.info("User {} is leaving group with public_id '{}'", current_user.username, group_public_id)
    await service.leave_group(current_user, group_public_id, background_tasks)
    return {"message": "Successfully left the group."}

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

@router.get("/{group_public_id}/set-role", status_code=status.HTTP_200_OK)
async def set_user_role(
    body: SetRoleRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    service: GroupService = Depends(get_group_service)
):
    if current_user is None:
        raise UnauthorizedException("User must be authenticated to set user roles.")
    try:
        roleEnum = MemberRole(body.role)
    except ValueError:
        raise ValueError(f"Invalid role: {body.role}. Valid roles are: {[role.value for role in MemberRole]}")
    await service.set_user_role(current_user, body.group_public_id, body.user_public_id, roleEnum, background_tasks)
    return {"message": "Successfully set the user role."}