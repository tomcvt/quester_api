from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import uuid

from loguru import logger

from app.core.config import globalSettings
from app.core.jwt import REFRESH_TOKEN_EXPIRE_DAYS, create_access_token
from app.core.oauth import OAuthClaims, verify_google_token
from app.exceptions import InvalidCredentialsException, UserAlreadyExistsException, UserNotFoundException
from app.models.user import NewUser, User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthRequest, AuthResponse, OAuthLoginRequest, RegistrationRequest, RegistrationResponse, SessionResponse, UpdateFcmTokenRequest, WebLoginRequest, WebRegisterRequest
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
                installation_id=user.installation_id,
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
                installation_id='',
                username='',
                phone_number=None,    
                public_id=uuid.NIL,
                fcm_token='',
                role=UserRole.USER
            )
    '''
    The OAuth login flow is designed to handle several scenarios gracefully:
    For now for simplicity we will delete the previous client side user and return already linked
    user by installation id, but in future we can implement proper account merging and linking flow.
    '''
    
    async def google_oauth_login(self, request: OAuthLoginRequest) -> AuthResponse:
    # Step 1: Verify the token — throws if invalid
        claims: OAuthClaims = verify_google_token(request.id_token, globalSettings.google_client_id)
        
        # Step 2: Look up by oauth_sub first
        existing_oauth_user = await self.user_repo.get_by_oauth_sub(claims.sub)
        
        if existing_oauth_user and existing_oauth_user.installation_id != request.installation_id:
            logger.warning("OAuth sub {} is already linked to a different installation ID {}. Deleting old user and proceeding with new registration.", claims.sub, existing_oauth_user.installation_id)
            await self.user_repo.delete_user_by_installation_id(request.installation_id)
            #TODO we need to gracefully handle deletion
        
        if existing_oauth_user:
            # This OAuth identity is already linked to an account.
            # Could be same device or different device — doesn't matter.
            # Just issue a new session for that user.
            return await self._issue_session(existing_oauth_user, request.fcm_token)
        
        # Step 3: No OAuth link yet. Does this installation already have a user?
        existing_install_user = await self.user_repo.get_user_by_installation_id(
            request.installation_id
        )
        
        if existing_install_user:
            # Account linking: tie this Google identity to the existing user.
            # From now on, any device logging in with this Google account
            # will find this user via Step 2.
            logger.info("Linking OAuth sub {} to existing user with installation ID {}.", claims.sub, request.installation_id)
            await self.user_repo.link_oauth(
                existing_install_user.id,
                claims.provider,
                claims.sub,
                claims.email #request.email is optional, but we can update email if it's not set or different from claims.email
            )
            return await self._issue_session(existing_install_user, request.fcm_token)
        
        #For now if we come here something is wrong
        raise UserNotFoundException("No user found for this OAuth identity, and no existing account to link to. Please register first.")
        # Step 4: Brand new user via OAuth (no prior installation_id user).
        new_user = await self.user_repo.create_user(User.new(NewUser(
            installation_id=request.installation_id,
            device_id=request.installation_id,  # or generate separately #TODO
            oauth_sub=claims.sub,
            oauth_provider=claims.provider,
            email=request.email
        )))
        return await self._issue_session(new_user, request.fcm_token)
    
    async def _issue_session(self, user: User, fcm_token: str | None) -> AuthResponse:
        session_token = gen_utils.generate_session_token()
        await self.user_repo.update_session_token(user.id, session_token)
        if fcm_token and user.fcm_token != fcm_token:
            logger.info("Updating FCM token for user {}: {} -> {}", user.username, user.fcm_token, fcm_token)
            await self.user_repo.update_fcm_token(user.id, fcm_token)
        else:
            logger.info("FCM token is unchanged for user {}: {}", user.username, user.fcm_token)
        return AuthResponse(
            session_token=session_token,
            installation_id=user.installation_id,
            username=user.username,
            phone_number=user.phone_number,
            public_id=user.public_id,
            fcm_token=user.fcm_token if user.fcm_token else '',
            role=user.role,
            oauth_provider=user.oauth_provider
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
    
    async def update_fcm_token(self, user: User, request: UpdateFcmTokenRequest) -> None:
        await self.user_repo.update_fcm_token(user.id, request.fcm_token)
        logger.info(f"Updated FCM token for user {user.username} to {request.fcm_token}")

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
    
    async def create_jwt_session(self, installation_id: str, fcm_token: str | None) -> SessionResponse:
    # upsert user — same logic you have now
        user = await self.user_repo.get_user_by_installation_id(installation_id)
        if not user:
            user = await self.user_repo.create_user(User.new(NewUser(
                installation_id=installation_id,
                device_id=f"device_{installation_id}",
                username=None,
                role=UserRole.USER,
            )))
        
        # update FCM if changed
        if fcm_token and user.fcm_token != fcm_token:
            await self.user_repo.update_fcm_token(user.id, fcm_token)
        
        # issue tokens
        access_token = create_access_token(user)
        refresh_token, family_id = await self._issue_refresh_token(user.id)
        
        return SessionResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            username=user.username,
            phone_number=user.phone_number,
            oauth_provider=user.oauth_provider,
            public_id=user.public_id,
            role=user.role,
            installation_id=user.installation_id,
        )

    async def _issue_refresh_token(self, user_id: int, family_id: uuid.UUID | None = None) -> tuple[str, uuid.UUID]:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        fid = family_id or uuid.uuid4()
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        await self.user_repo.create_refresh_token(user_id, token_hash, fid, expires_at)
        return raw_token, fid  # raw goes to client, hash stays in DB

    async def refresh_session(self, raw_refresh_token: str) -> SessionResponse:
        token_hash = hashlib.sha256(raw_refresh_token.encode()).hexdigest()
        stored = await self.user_repo.get_refresh_token(token_hash)
        
        if not stored or stored.revoked or stored.expires_at < datetime.now(timezone.utc):
            # if revoked — token was already used, possible theft — invalidate family
            if stored and stored.revoked:
                await self.user_repo.revoke_token_family(stored.family_id)
            raise InvalidCredentialsException("Invalid refresh token")
        
        await self.user_repo.revoke_token(stored.id)  # old one dead
        user = await self.user_repo.get_by_id(stored.user_id)
        access_token = create_access_token(user)
        new_refresh, _ = await self._issue_refresh_token(user.id, family_id=stored.family_id)
        
        return SessionResponse(access_token=access_token, refresh_token=new_refresh, ...)
        