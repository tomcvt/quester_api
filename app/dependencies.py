
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from sqlalchemy import select
from fastapi import Depends, Header
from app.core.database import get_db
from app.repositories.group_repository import GroupRepository
from app.repositories.user_repository import UserRepository
from app.repositories.group_member_repository import GroupMemberRepository
from app.services.auth_service import AuthService
from app.services.group_service import GroupService

def get_group_repository(db: AsyncSession = Depends(get_db)) -> GroupRepository:
    return GroupRepository(db)

def get_group_member_repository(db: AsyncSession = Depends(get_db)) -> GroupMemberRepository:
    return GroupMemberRepository(db)

def get_group_service(repo: GroupRepository = Depends(get_group_repository), member_repo: GroupMemberRepository = Depends(get_group_member_repository)) -> GroupService:
    return GroupService(repo, member_repo)

def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)

async def get_current_user(x_installation_id: str = Header("X-Installation-ID"), repo: UserRepository = Depends(get_user_repository)) -> User | None:
    result = await repo.db.execute(select(User).where(User.installation_id == x_installation_id))
    user = result.scalars().first()
    if not user:
        #TODO: This is a temporary solution to create a user if it doesn't exist. We should have a proper registration flow in the future.
        user = await repo.create_user(
            User(
                device_id=f"device_{x_installation_id[:8]}",
                installation_id=x_installation_id,
                username=f"NEW_USER_{x_installation_id[:8]}",
                public_id=uuid.uuid4(),  # This will be set in db with postgres but with sqlite we set
                fcm_token=''
            )
        )
    return user