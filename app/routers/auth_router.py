from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from loguru import logger
from app.schemas.auth import AuthRequest, AuthResponse, OAuthLoginRequest, RegistrationRequest, RegistrationResponse, TokenResponse, WebLoginRequest, WebRegisterRequest
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service
from app.exceptions import InvalidCredentialsException
from app.web.session import create_session



router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/authenticate", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def authenticate(
    body: AuthRequest,
    service: AuthService = Depends(get_auth_service)
):
    response = await service.authenticate_user(body)
    logger.info("User authenticated successfully: {}", response.username)
    return response

@router.post("/oauth-login/google", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def google_oauth_login(
    body: OAuthLoginRequest,
    service: AuthService = Depends(get_auth_service)
):
    response = await service.google_oauth_login(body)
    logger.info("User authenticated via Google OAuth successfully: {}", response.username)
    return response

@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegistrationRequest,
    service: AuthService = Depends(get_auth_service)
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

@router.post("/web/login", status_code=status.HTTP_200_OK)
async def web_login(
    body: WebLoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service)
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
    service: AuthService = Depends(get_auth_service)
):
    user = await service.web_register(body)
    redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    create_session(user.id, redirect)
    logger.info("Web registration and session created for user: {}", user.username)
    return redirect