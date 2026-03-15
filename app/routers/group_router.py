from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.group import CreateGroupRequest, GroupResponse
from app.services.group_service import GroupService
from app.dependencies import get_group_service
from app.exceptions import GroupNameTakenException

router = APIRouter(prefix="/api/groups", tags=["groups"])

@router.post("/create", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    body: CreateGroupRequest,
    service: GroupService = Depends(get_group_service)
):
    try:
        group = await service.create_group(body)
        return GroupResponse.model_validate(group)
    except GroupNameTakenException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))