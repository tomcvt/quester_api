
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import NewUser, User
from sqlalchemy import select
from fastapi import Cookie, Depends, Header
from loguru import logger
from app.core.database import get_db
from app.web.session import get_user_id_from_session, COOKIE_NAME
from app.repositories.group_repository import GroupRepository
from app.repositories.quest_repository import QuestRepository
from app.repositories.user_repository import UserRepository
from app.repositories.group_member_repository import GroupMemberRepository
from app.services.auth_service import AuthService
from app.services.group_service import GroupService
from app.services.notification_service import NotificationService
from app.services.quest_service import QuestService
from app.services.user_service import UserService

def get_group_repository(db: AsyncSession = Depends(get_db)) -> GroupRepository:
    return GroupRepository(db)

def get_group_member_repository(db: AsyncSession = Depends(get_db)) -> GroupMemberRepository:
    return GroupMemberRepository(db)

def get_quest_repository(db: AsyncSession = Depends(get_db)) -> QuestRepository:
    return QuestRepository(db)

def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)




def get_notification_service(
    gm_repo = Depends(get_group_member_repository),
    user_repo = Depends(get_user_repository),
    quest_repo = Depends(get_quest_repository)
) -> NotificationService:
    return NotificationService(gm_repo, user_repo, quest_repo)

def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
    notif_service: NotificationService = Depends(get_notification_service)
) -> UserService:
    return UserService(repo, notif_service)

def get_group_service(
    repo: GroupRepository = Depends(get_group_repository), 
    member_repo: GroupMemberRepository = Depends(get_group_member_repository),
    quest_repo: QuestRepository = Depends(get_quest_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    notif_service: NotificationService = Depends(get_notification_service)
) -> GroupService:
    return GroupService(repo, member_repo, quest_repo, user_repo, notif_service)

def get_quest_service(
    repo: QuestRepository = Depends(get_quest_repository), 
    group_repo: GroupRepository = Depends(get_group_repository), 
    group_member_repo: GroupMemberRepository = Depends(get_group_member_repository),
    notification_service: NotificationService = Depends(get_notification_service)
    ) -> QuestService:
    return QuestService(repo, group_repo, group_member_repo, notification_service)

def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)

async def get_current_user(
    x_installation_id: Optional[str] = Header(None, alias="X-Installation-ID"),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    jsessionid: Optional[str] = Cookie(None, alias=COOKIE_NAME),
    repo: UserRepository = Depends(get_user_repository),
    ) -> User | None:

    # --- Auth flow 1: header-based (mobile / API clients) ---
    if x_installation_id:
        result = await repo.db.execute(select(User).where(User.installation_id == x_installation_id))
        user = result.scalars().first()
        if user and (not x_session_token or user.session_token != x_session_token):
            logger.warning(f"Invalid session token for installation_id {x_installation_id}.")
            return None
        if not user:
            logger.warning(f"No user found with installation_id {x_installation_id}.")
            #TODO: This is a temporary solution to create a user if it doesn't exist. We should have a proper registration flow in the future.
            user = User.new(
                NewUser(
                    device_id=f"device_{x_installation_id[:8]}",
                    installation_id=x_installation_id,
                    username=f"NEW_USER_{x_installation_id[:8]}",
                    fcm_token=''
                )
            )
        return user

    # --- Auth flow 2: session cookie (web clients) ---
    user_id = get_user_id_from_session(jsessionid)
    if user_id is None:
        return None
    result = await repo.db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()