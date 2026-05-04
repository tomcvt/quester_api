from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from loguru import logger
from app.schemas.auth import AuthRequest, AuthResponse, OAuthLoginRequest, RefreshTokenRequest, RegistrationRequest, RegistrationResponse, SessionRequest, SessionResponse, TokenResponse, UpdateFcmTokenRequest, WebLoginRequest, WebRegisterRequest
from app.services.auth_service import AuthService
from app.dependencies import AuthServiceDep, CurrentUser
from app.exceptions import InvalidCredentialsException
from app.web.session import create_session



router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/authenticate", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def authenticate(
    body: AuthRequest,
    service: AuthServiceDep,
):
    response = await service.authenticate_user(body)
    logger.info("User authenticated successfully: {}", response.username)
    return response

@router.post("/oauth-login/google", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def google_oauth_login(
    body: OAuthLoginRequest,
    service: AuthServiceDep,
):
    response = await service.google_oauth_login(body)
    logger.info("User authenticated via Google OAuth successfully: {}", response.username)
    return response

@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegistrationRequest,
    service: AuthServiceDep,
):
    #response = await service.register_user(body)
    newUser = await service.register_user(body)
    response = RegistrationResponse(
        session_token="mock_session_token",
        username=newUser.username,
        api_key=newUser.api_key_hash,
        public_id=newUser.public_id
    )
    logger.info("User registered successfully: {}", response.username)
    return response

'''
MEMBER:
  login (email code / oauth) → issues BOTH access_token + refresh_token
  access_token expires (15min) → use refresh_token → new pair
  refresh_token expires (30d) → must login again (email code / oauth)

GUEST:
  POST /auth/session (installation_id) → issues BOTH access_token + refresh_token
  access_token expires (15min) → use refresh_token → new pair
  refresh_token expires (30d) → POST /auth/session again (no login needed, just UUID)
'''


@router.post("/session", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def create_session_endpoint(
    body: SessionRequest,
    service: AuthServiceDep,
):
    response = await service.create_jwt_session(body.installation_id, body.fcm_token)
    logger.info("Session created successfully for installation_id: {}", body.installation_id)
    return response

@router.post("/refresh", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def refresh_session(
    body: RefreshTokenRequest,
    service: AuthServiceDep,
):
    response = await service.refresh_jwt_session(body.refresh_token)
    logger.info("Session refreshed successfully for user: {}", response.username)
    return response

@router.post("/web/login", status_code=status.HTTP_200_OK)
async def web_login(
    body: WebLoginRequest,
    response: Response,
    service: AuthServiceDep,
):
    try:
        user = await service.web_login(body)
    except InvalidCredentialsException:
        logger.warning("Web login failed for user: {}", body.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    create_session(user.id, redirect)
    logger.info("Web session created for user: {}", user.username)
    return redirect


@router.post("/web/register", status_code=status.HTTP_201_CREATED)
async def web_register(
    body: WebRegisterRequest,
    response: Response,
    service: AuthServiceDep,
):
    user = await service.web_register(body)
    redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    create_session(user.id, redirect)
    logger.info("Web registration and session created for user: {}", user.username)
    return redirect

@router.post("/update-fcm-token", status_code=status.HTTP_200_OK)
async def update_fcm_token(
    body: UpdateFcmTokenRequest,
    current_user: CurrentUser,
    service: AuthServiceDep,
):
    await service.update_fcm_token(current_user, body)
    logger.info("FCM token updated for user: {}", current_user.username)
    return {"message": "FCM token updated successfully"}