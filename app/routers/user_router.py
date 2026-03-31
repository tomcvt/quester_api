
from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_user_service
from app.models.user import User
from app.schemas.auth import ChangeUsernameRequest
from app.services.user_service import UserService


router = APIRouter(prefix="/users", tags=["users"])

@router.post("/change-username", status_code=200)
async def change_username(
    body: ChangeUsernameRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    new_username = body.username
    updated_user = await service.change_username(current_user, new_username)
    return {"message": "Username changed successfully", "new_username": updated_user.username}