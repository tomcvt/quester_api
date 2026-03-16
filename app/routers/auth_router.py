from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from app.schemas.auth import AuthRequest, AuthResponse, TokenResponse
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service
from app.exceptions import InvalidCredentialsException



router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/authenticate", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def authenticate(
    body: AuthRequest,
    service: AuthService = Depends(get_auth_service)
):
    try:
        response = await service.authenticate_user(body)
        logger.info("User authenticated successfully: {}", response.username)
        return response
    except InvalidCredentialsException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
