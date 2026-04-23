import uuid

from loguru import logger

from app.exceptions import InvalidCredentialsException, UserAlreadyExistsException, UserNotFoundException
from app.models.user import NewUser, User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthRequest, AuthResponse, RegistrationRequest, RegistrationResponse, WebLoginRequest, WebRegisterRequest
from app.utils import gen_utils

reserved_uuids = [
    str(uuid.UUID(int=j)) for j in range(1, 30)
]

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
                phone_number=user.phone_number,
                public_id=user.public_id,
                fcm_token=user.fcm_token if user.fcm_token else '',
                role=user.role
            )
        else:
            logger.warning("No user found with installation ID: {}", request.installation_id)
            #raise UserNotFoundException("Try registering first")
            #for simplicty we will return empty response
            return AuthResponse(
                session_token='',
                username='',
                phone_number=None,    
                public_id=uuid.NIL,
                fcm_token='',
                role=UserRole.USER
            )
    
    async def register_user(self, request: RegistrationRequest) -> User:
        existing_user = await self.user_repo.get_user_by_installation_id(request.installation_id)
        if existing_user:
            #raise UserAlreadyExistsException("User with this installation ID already exists")
            #for simplicty we will return the existing user details now
            return existing_user
        api_key=gen_utils.generate_safe_api_key(request.installation_id) #TODO: implement proper hashing
        api_key_hash = api_key #TODO: hash the api key before storing
        role = UserRole.USER
        if request.installation_id in reserved_uuids:
            role = UserRole.SUPERUSER
        new_user = NewUser(
            device_id=request.device_id if request.device_id else f"device_{str(request.installation_id)}",
            installation_id=request.installation_id,
            api_key_hash=api_key_hash,
            password_hash=gen_utils.hash_password(request.password) if request.password else None,
            username=request.username,
            phone_number=request.phone_number,
            role=role
        )
        created_user = await self.user_repo.create_user(User.new(new_user))
        logger.info(f"Registered new user: {created_user}")
        return created_user

    async def web_login(self, request: WebLoginRequest) -> User:
        """
        Authenticate a web user by username + bcrypt password.
        Since usernames are not unique, all matching users are checked.
        Raises InvalidCredentialsException if none match.
        """
        users = await self.user_repo.get_users_by_username(request.username)
        for user in users:
            logger.debug(f"Checking password for user {user.username} with ID {user.id}")
            logger.debug(f"User password hash: {user.password_hash}")
            logger.debug(f"Provided password: {request.password}")
            logger.debug(f"Password verification result: {gen_utils.verify_password(request.password, user.password_hash) if user.password_hash else 'No password hash'}")
            if user.password_hash and gen_utils.verify_password(request.password, user.password_hash):
                return user
        raise InvalidCredentialsException("Invalid username or password")

    async def web_register(self, request: WebRegisterRequest) -> User:
        """
        Register a new web user with a bcrypt-hashed password.
        installation_id and device_id are generated as UUIDs since this is a web-only account.
        """
        generated_id = str(uuid.uuid4())
        new_user = NewUser(
            device_id=f"web_{generated_id}",
            installation_id=generated_id,
            username=request.username,
            password_hash=gen_utils.hash_password(request.password),
            role=UserRole.USER,
        )
        created_user = await self.user_repo.create_user(User.new(new_user))
        logger.info(f"Registered new web user: {created_user.username}")
        return created_user
    