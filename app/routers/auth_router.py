from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from app.schemas.auth import AuthRequest, AuthResponse, RegistrationRequest, RegistrationResponse, TokenResponse
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service
from app.exceptions import InvalidCredentialsException



router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/authenticate", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def authenticate(
    body: AuthRequest,
    service: AuthService = Depends(get_auth_service)
):
    response = await service.authenticate_user(body)
    logger.info("User authenticated successfully: {}", response.username)
    return response

@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegistrationRequest,
    service: AuthService = Depends(get_auth_service)
):
    response = await service.register_user(body)
    logger.info("User registered successfully: {}", response.username)
    return response