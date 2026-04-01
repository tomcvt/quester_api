import uuid

from loguru import logger

from app.exceptions import InvalidCredentialsException, UserAlreadyExistsException, UserNotFoundException
from app.models.user import NewUser, User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthRequest, AuthResponse, RegistrationRequest, RegistrationResponse
from app.utils import gen_utils


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def authenticate_user(self, request: AuthRequest) -> AuthResponse:
        user = await self.user_repo.get_user_by_installation_id(request.installation_id)
        if user:
            api_hash = request.api_key #TODO: hash the api key and compare with stored hash
            # check key
            if not user.api_key_hash:
                logger.warning("User {} does not have an API key hash set. This may indicate a data integrity issue.", user.username)
            elif user.api_key_hash != api_hash:
                logger.warning("Invalid API key provided for user {}. Expected hash: {}, Provided hash: {}", user.username, user.api_key_hash, api_hash)
                raise InvalidCredentialsException("Invalid API key")
            # handle FCM token update
            if not request.fcm_token:
                logger.warning("FCM token is missing in the authentication request for existing user: {}", user.username)
            elif request.fcm_token and user.fcm_token != request.fcm_token:
                logger.info("Updating FCM token for user {}: {} -> {}", user.username, user.fcm_token, request.fcm_token)
                await self.user_repo.update_fcm_token(user.id, request.fcm_token)
            else:
                logger.info("FCM token is unchanged for user {}: {}", user.username, user.fcm_token)
            # generate new session token
            newSessionToken = gen_utils.generate_session_token()
            await self.user_repo.update_session_token(user.id, newSessionToken)
            return AuthResponse(
                session_token=newSessionToken,
                username=user.username,
                public_id=user.public_id,
                fcm_token=user.fcm_token if user.fcm_token else ''
            )
        else:
            logger.warning("No user found with installation ID: {}", request.installation_id)
            #raise UserNotFoundException("Try registering first")
            #for simplicty we will return empty response
            return AuthResponse(
                session_token='',
                username='',
                public_id=uuid.NIL,
                fcm_token=''
            )
    
    async def register_user(self, request: RegistrationRequest) -> RegistrationResponse:
        existing_user = await self.user_repo.get_user_by_installation_id(request.installation_id)
        if existing_user:
            #raise UserAlreadyExistsException("User with this installation ID already exists")
            #for simplicty we will return the existing user details now
            return RegistrationResponse(
                session_token="mock_session_token",
                api_key=existing_user.api_key_hash, #TODO handle this
                username=existing_user.username,
                public_id=existing_user.public_id
            )
        api_key=gen_utils.generate_safe_api_key(request.password) #TODO: implement proper hashing
        api_key_hash = api_key #TODO: hash the api key before storing
        new_user = NewUser(
            device_id=request.device_id if request.device_id else f"device_{str(request.installation_id)[:8]}",
            installation_id=request.installation_id,
            api_key_hash=api_key_hash,
            username=request.username,
        )
        created_user = await self.user_repo.create_user(User.new(new_user))
        return RegistrationResponse(
            session_token="mock_session_token",
            api_key=api_key,
            username=created_user.username,
            public_id=created_user.public_id
        )
        
    