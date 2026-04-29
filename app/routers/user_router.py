
from fastapi import APIRouter, Query

from app.dependencies import CurrentAdminOrSuperuser, CurrentUser, CurrentUserOptional, UserServiceDep
from app.exceptions import UnauthorizedException
from app.models.user import UserRole
from app.schemas.auth import ChangePhoneNumberRequest, ChangeUsernamePhoneRequest, ChangeUsernameRequest
from app.schemas.user import UserDto, UserFullDto, UsersSyncRequest, UsersSyncResponse


router = APIRouter(prefix="/users", tags=["users"])

@router.post("/change-username", status_code=200)
async def change_username(
    body: ChangeUsernameRequest,
    current_user: CurrentUser,
    service: UserServiceDep,
):
    new_username = body.username
    updated_user = await service.change_username(current_user, new_username)
    return {"message": "Username changed successfully", "new_username": updated_user.username}

@router.post("/change-phone-number", status_code=200)
async def change_phone_number(
    body: ChangePhoneNumberRequest,
    current_user: CurrentUser,
    service: UserServiceDep,
):
    new_phone_number = body.phone_number
    updated_user = await service.change_phone_number(current_user, new_phone_number)
    return {"message": "Phone number changed successfully", "new_phone_number": updated_user.phone_number}

@router.post("/change-username-phone-number", status_code=200)
async def change_username_and_phone_number(
    body: ChangeUsernamePhoneRequest,
    current_user: CurrentUser,
    service: UserServiceDep,
):
    new_username = body.username
    new_phone_number = body.phone_number
    updated_user = current_user
    if new_username:
        updated_user = await service.change_username(current_user, new_username)
    if new_phone_number:
        updated_user = await service.change_phone_number(current_user, new_phone_number)
    
    return {
        "message": "User details changed successfully",
        "new_username": updated_user.username,
        "new_phone_number": updated_user.phone_number
    }

@router.post("/fetch-by-public-ids", response_model=UsersSyncResponse, status_code=200)
async def fetch_users_by_public_ids(
    body: UsersSyncRequest,
    current_user: CurrentUser,
    service: UserServiceDep,
):
    users = await service.repo.get_users_by_public_ids(body.public_ids)
    user_dtos = [UserDto.model_validate(user) for user in users]
    return UsersSyncResponse(users=user_dtos)


@router.get("/all", response_model=dict, status_code=200)
async def get_all_users(
    current_user: CurrentAdminOrSuperuser,
    service: UserServiceDep,
    page: int = Query(0, ge=0, description="Zero-based page number"),
    size: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
):
    users, total = await service.get_users_page(page, size)
    user_dtos = [UserFullDto.model_validate(u) for u in users]
    return {
        "items": [u.model_dump() for u in user_dtos],
        "total": total,
        "page": page,
        "size": size,
        "total_pages": (total + size - 1) // size,
    }