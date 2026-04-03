
from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_user_service
from app.exceptions import UnauthorizedException
from app.models.user import User
from app.schemas.auth import ChangeUsernameRequest
from app.schemas.user import UserDto, UsersSyncRequest, UsersSyncResponse
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

@router.post("/fetch-by-public-ids", response_model=UsersSyncResponse, status_code=200)
async def fetch_users_by_public_ids(
    body: UsersSyncRequest,
    current_user: User | None = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    if not current_user:
        raise UnauthorizedException("You must be logged in to fetch user details.")
    users = await service.repo.get_users_by_public_ids(body.public_ids)
    user_dtos = [UserDto.model_validate(user) for user in users]
    return UsersSyncResponse(users=user_dtos)