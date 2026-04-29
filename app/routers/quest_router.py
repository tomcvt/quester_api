import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Query

# from loguru import logger
from app.dependencies import CurrentAdminOrSuperuser, CurrentUser, CurrentUserOptional, QuestServiceDep
from app.exceptions import UnauthorizedException
from app.models.quest import Quest, QuestStatus
from app.models.user import User, UserRole
from app.schemas.quest import CreateQuestRequest, CreateQuestResponse, QuestFullDto, QuestSyncDTO
from app.services.quest_service import QuestService


router = APIRouter(prefix="/quests", tags=["quests"])

@router.post("/create" , response_model=CreateQuestResponse, status_code=201)
async def create_quest(
    body: CreateQuestRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    service: QuestServiceDep,
):
    quest: Quest = await service.create_quest_from_request(current_user, body, background_tasks)
    response: CreateQuestResponse = CreateQuestResponse.from_orm_without_creator(quest)
    response.creator_public_id = current_user.public_id
    
    return response

@router.post("/{quest_public_id}/accept", response_model=QuestSyncDTO, status_code=200)
async def accept_quest(
    quest_public_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    service: QuestServiceDep,
):
    updated_quest = await service.accept_quest(current_user, quest_public_id, background_tasks)
    if not updated_quest:
        raise Exception("Failed to accept quest.")
    return await service.get_quest_dto_by_public_id(quest_public_id)
    
@router.post("/{quest_public_id}/complete", status_code=200)
async def complete_quest(
    quest_public_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    service: QuestServiceDep,
):
    updated_quest = await service.complete_quest(current_user, quest_public_id, background_tasks)
    if not updated_quest:
        raise Exception("Failed to complete quest.")
    return await service.get_quest_dto_by_public_id(quest_public_id)

@router.get("/all", response_model=dict, status_code=200)
async def get_all_quests(
    current_user: CurrentAdminOrSuperuser,
    service: QuestServiceDep,
    page: int = Query(0, ge=0, description="Zero-based page number"),
    size: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
    status: QuestStatus | None = Query(None),
    group_id: int | None = Query(None),
    creator_id: int | None = Query(None),
    name: str | None = Query(None, max_length=200),
):
    quests, total = await service.get_quests_page(page, size, status, group_id, creator_id, name)
    quest_dtos = [QuestFullDto.model_validate(q) for q in quests]
    return {
        "items": [q.model_dump() for q in quest_dtos],
        "total": total,
        "page": page,
        "size": size,
        "total_pages": (total + size - 1) // size,
    }


@router.get("/{quest_public_id}", response_model=QuestSyncDTO, status_code=200)
async def get_quest(
    quest_public_id: str,
    current_user: CurrentUserOptional,
    service: QuestServiceDep,
):
    quest_dto = await service.get_quest_dto_by_public_id(uuid.UUID(quest_public_id))
    if not quest_dto:
        raise Exception("Quest not found.")
    return quest_dto

@router.delete("/{quest_public_id}", status_code=204)
async def delete_quest(
    quest_public_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    service: QuestServiceDep,
):
    await service.delete_quest_by_public_id(current_user, quest_public_id, background_tasks)
    return