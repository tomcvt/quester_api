




import uuid

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_quest_service
from app.models.user import User
from app.schemas.quest import CreateQuestRequest, CreateQuestResponse
from app.services.quest_service import QuestService


router = APIRouter(prefix="/quests", tags=["quests"])

@router.post("/create" , response_model=CreateQuestResponse, status_code=201)
async def create_quest(
    body: CreateQuestRequest,
    current_user=Depends(get_current_user),
    service: QuestService = Depends(get_quest_service)
):
    quest = await service.create_quest(current_user, body)
    return quest

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