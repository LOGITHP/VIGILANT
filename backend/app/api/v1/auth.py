from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_client_ip, get_user_agent, get_current_user
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    TokenResponse,
    MessageResponse
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _format_user_response(user: User) -> UserResponse:
    roles_list = [r.name for r in user.roles] if user.roles else []
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        roles=roles_list,
        created_at=user.created_at
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT token pair"
)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    user, access_token, refresh_token, expires_in = await AuthService.authenticate_user(
        db=db,
        username_or_email=body.username,
        password=body.password,
        ip_address=ip,
        user_agent=ua
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
        user=_format_user_response(user)
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token and issue new access token"
)
async def refresh_token(
    request: Request,
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    user, new_access, new_refresh, expires_in = await AuthService.refresh_tokens(
        db=db,
        refresh_token_str=body.refresh_token,
        ip_address=ip,
        user_agent=ua
    )

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=expires_in,
        user=_format_user_response(user)
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke session and logout"
)
async def logout(
    request: Request,
    body: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    await AuthService.logout_user(
        db=db,
        refresh_token_str=body.refresh_token,
        user=current_user,
        ip_address=ip,
        user_agent=ua
    )
    return MessageResponse(message="Successfully logged out of VIGILANT session")


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile"
)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    return _format_user_response(current_user)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account"
)
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    new_user = await AuthService.register_user(
        db=db,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        ip_address=ip,
        user_agent=ua
    )
    return _format_user_response(new_user)

