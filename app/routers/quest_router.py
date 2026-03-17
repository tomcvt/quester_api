




from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_quest_service
from app.schemas.quest import CreateQuestRequest, CreateQuestResponse
from app.services.quest_service import QuestService


router = APIRouter(prefix="/quests", tags=["quests"])

@router.post("/create" , response_model=CreateQuestResponse, status_code=201)
async def create_quest(
    body: CreateQuestRequest,
    current_user=Depends(get_current_user),
    service: QuestService = Depends(get_quest_service)
):
    try:
        quest = await service.create_quest(current_user, body)
        return quest
    except Exception as e:
        return {"error": str(e)}

@router.get("/{quest_public_id}", response_model=CreateQuestResponse)
async def get_quest(
    quest_public_id: str,
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
