import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from loguru import logger
from app.dependencies import get_current_user, get_quest_service, get_user_service
from app.models.quest import Quest
from app.models.user import User
from app.schemas.quest import CreateQuestRequest, CreateQuestResponse, QuestSyncDTO
from app.services.quest_service import QuestService


router = APIRouter(prefix="/quests", tags=["quests"])

@router.post("/create" , response_model=CreateQuestResponse, status_code=201)
async def create_quest(
    body: CreateQuestRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: QuestService = Depends(get_quest_service),
    user_service = Depends(get_user_service)
):
    quest: Quest = await service.create_quest(current_user, body, background_tasks)
    creator_user: User | None = await user_service.get_user_by_id(quest.creator_id) if quest.creator_id else None
    if not creator_user:
        logger.error(f"Creator with id {quest.creator_id} not found when creating quest response.")
        creatorPublicId = None
    else:
        creatorPublicId = creator_user.public_id
    if not creatorPublicId:
        logger.error(f"Creator public_id not found for user with id {quest.creator_id} when creating quest response.")
        raise ValueError(f"Creator public_id not found for user with id {quest.creator_id} when creating quest response.")
        
    response: CreateQuestResponse = CreateQuestResponse.from_orm_without_creator(quest)
    response.creator_public_id = creatorPublicId
    
    return response

@router.post("/{quest_public_id}/accept", status_code=200)
async def accept_quest(
    quest_public_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: QuestService = Depends(get_quest_service)
):
    updated_quest = await service.accept_quest(current_user, quest_public_id, background_tasks)
    if not updated_quest:
        raise Exception("Failed to accept quest.")
    

@router.get("/{quest_public_id}", response_model=CreateQuestResponse)
async def get_quest(
    quest_public_id: str,
    current_user: User | None = Depends(get_current_user),
    service: QuestService = Depends(get_quest_service)
):
    try:
        '''
        quest = await service.get_quest_by_public_id(quest_public_id)
        if not quest:
            return {"error": "Quest not found"}
        return quest
        '''
    except Exception as e:
        return {"error": str(e)}

@router.delete("/{quest_public_id}", status_code=204)
async def delete_quest(
    quest_public_id: uuid.UUID,
    current_user: User | None = Depends(get_current_user),
    service: QuestService = Depends(get_quest_service)
):
    await service.delete_quest_by_public_id(current_user, quest_public_id)
    return