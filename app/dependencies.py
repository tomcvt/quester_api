
import uuid
from typing import Annotated, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.exceptions import ForbiddenException, UnauthorizedException
from app.models.user import NewUser, User, UserRole
from sqlalchemy import select
from fastapi import Cookie, Depends
from fastapi.security import APIKeyHeader
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

_installation_id_header = APIKeyHeader(name="X-Installation-ID", auto_error=False)
_session_token_header = APIKeyHeader(name="X-Session-Token", auto_error=False)

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
    user_repo: UserRepository = Depends(get_user_repository),
    notification_service: NotificationService = Depends(get_notification_service)
    ) -> QuestService:
    return QuestService(repo, group_repo, group_member_repo, user_repo, notification_service)

def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)

'''
TODO refactor to authuser and jwt
async def get_current_user(
    authorization: str | None = Header(None),
    repo: UserRepository = Depends(get_user_repository),
) -> AuthUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing token")
    token = authorization.removeprefix("Bearer ")
    return decode_access_token(token)  # no DB hit

async def get_full_user(
    auth: AuthUser = Depends(get_current_user),
    repo: UserRepository = Depends(get_user_repository),
) -> User:
    return await repo.get_by_public_id(auth.public_id)

'''

async def get_current_user(
    x_installation_id: str | None = Depends(_installation_id_header),
    x_session_token: str | None = Depends(_session_token_header),
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
                    device_id=f"device_{x_installation_id}",
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

async def require_current_user(
    current_user: User | None = Depends(get_current_user)
) -> User:
    if not current_user:
        raise UnauthorizedException("User must be authenticated to access this resource.")
    return current_user

async def require_admin_role(
    current_user: User = Depends(require_current_user)
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException("User must be an admin to access this resource.")
    return current_user

async def require_admin_or_superuser(
    current_user: User = Depends(require_current_user)
) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPERUSER):
        raise ForbiddenException("User must be an admin or superuser to access this resource.")
    return current_user


# --- Annotated dependency aliases — use these in routers instead of Depends(...) ---

CurrentUserOptional = Annotated[User | None, Depends(get_current_user)]
CurrentUser = Annotated[User, Depends(require_current_user)]
CurrentAdmin = Annotated[User, Depends(require_admin_role)]
CurrentAdminOrSuperuser = Annotated[User, Depends(require_admin_or_superuser)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
GroupServiceDep = Annotated[GroupService, Depends(get_group_service)]
QuestServiceDep = Annotated[QuestService, Depends(get_quest_service)]