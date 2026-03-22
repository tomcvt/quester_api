import uuid

from loguru import logger

from app.exceptions import InvalidCredentialsException, UserAlreadyExistsException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthRequest, AuthResponse


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def authenticate_user(self, request: AuthRequest) -> AuthResponse:
        user = await self.user_repo.get_user_by_installation_id(request.installation_id)
        if user:
            if not request.fcm_token:
                logger.warning("FCM token is missing in the authentication request for existing user: {}", user.username)
            elif request.fcm_token and user.fcm_token != request.fcm_token:
                logger.info("Updating FCM token for user {}: {} -> {}", user.username, user.fcm_token, request.fcm_token)
                await self.user_repo.update_fcm_token(user.id, request.fcm_token)
            else:
                logger.info("FCM token is unchanged for user {}: {}", user.username, user.fcm_token)
            return AuthResponse(
                session_token="mock_session_token",
                username=user.username,
                fcm_token=user.fcm_token if user.fcm_token else ''
            )
        else:
            newUsername = request.username if request.username else f"NEW_USER_{str(request.installation_id)[:8]}"
            fcm_token = request.fcm_token if request.fcm_token else ''
            device_id = request.device_id if request.device_id else f"device_{str(request.installation_id)[:8]}"
            newUser = User(
                device_id=device_id,
                installation_id=request.installation_id,
                username=newUsername,
                fcm_token=fcm_token,
                public_id=uuid.uuid4()  # This will be set by the database with postgres, in sqllite we need to set
            )
            try:
                createdUser = await self.user_repo.create_user(newUser)
            except UserAlreadyExistsException:
                createdUser = await self.user_repo.get_user_by_installation_id(request.installation_id)
                assert createdUser is not None, "User should exist after catching UserAlreadyExistsException"
            except Exception as e:
                raise e
            return AuthResponse(
                session_token="mock_session_token",
                username=createdUser.username,
                fcm_token=createdUser.fcm_token if createdUser.fcm_token else ''
            )
        
    