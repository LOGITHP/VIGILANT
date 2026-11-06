import uuid
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.user import User, Role
from app.models.session import UserSession
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token
)
from app.core.config import settings
from app.services.audit_service import AuditService


class AuthService:
    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username_or_email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, str, str, int]:
        """
        Authenticate user with Argon2id password verification.
        Returns: (User, access_token, refresh_token, expires_in)
        """
        normalized_email = username_or_email.strip().lower()

        # Query user with roles preloaded
        query = select(User).where(User.email == normalized_email).options(selectinload(User.roles))
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            await AuditService.log_event(
                db=db,
                event="LOGIN_FAILED_UNKNOWN_USER",
                user_id=None,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"attempted_email": normalized_email}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            await AuditService.log_event(
                db=db,
                event="LOGIN_FAILED_INACTIVE_USER",
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )

        # Verify password using Argon2id
        is_valid = verify_password(password, user.hashed_password)
        if not is_valid:
            await AuditService.log_event(
                db=db,
                event="LOGIN_FAILED_INVALID_PASSWORD",
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create session record
        session_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        refresh_expires = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        roles_list = [role.name for role in user.roles]

        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "roles": roles_list,
                "superuser": user.is_superuser
            }
        )

        refresh_token = create_refresh_token(
            data={
                "sub": str(user.id),
                "session_id": str(session_id)
            }
        )

        # Save session in database with token hash
        user_session = UserSession(
            id=session_id,
            user_id=user.id,
            refresh_token_hash=hash_token(refresh_token),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=refresh_expires,
            is_revoked=False
        )
        db.add(user_session)

        # Log audit event
        await AuditService.log_event(
            db=db,
            event="LOGIN_SUCCESS",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"roles": roles_list, "session_id": str(session_id)}
        )

        await db.commit()
        await db.refresh(user)

        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return user, access_token, refresh_token, expires_in

    @staticmethod
    async def refresh_tokens(
        db: AsyncSession,
        refresh_token_str: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, str, str, int]:
        """Validate refresh token and issue new token pair."""
        try:
            payload = decode_token(refresh_token_str)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is not a refresh token"
            )

        user_id_str = payload.get("sub")
        session_id_str = payload.get("session_id")
        if not user_id_str or not session_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed refresh token"
            )

        token_hash = hash_token(refresh_token_str)

        # Query session
        session_uuid = uuid.UUID(session_id_str)
        query = select(UserSession).where(
            UserSession.id == session_uuid,
            UserSession.refresh_token_hash == token_hash,
            UserSession.is_revoked == False
        )
        result = await db.execute(query)
        db_session = result.scalar_one_or_none()

        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session revoked or invalid"
            )

        # Check expiration
        now = datetime.now(timezone.utc)
        expires_at = db_session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < now:
            db_session.is_revoked = True
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has expired"
            )

        # Query user
        user_uuid = uuid.UUID(user_id_str)
        user_query = select(User).where(User.id == user_uuid).options(selectinload(User.roles))
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Slide session refresh token
        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id), "session_id": str(db_session.id)}
        )
        db_session.refresh_token_hash = hash_token(new_refresh_token)
        db_session.expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        roles_list = [role.name for role in user.roles]
        new_access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "roles": roles_list,
                "superuser": user.is_superuser
            }
        )

        await AuditService.log_event(
            db=db,
            event="TOKEN_REFRESH",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        await db.commit()
        await db.refresh(user)

        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return user, new_access_token, new_refresh_token, expires_in

    @staticmethod
    async def logout_user(
        db: AsyncSession,
        refresh_token_str: Optional[str] = None,
        user: Optional[User] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Revoke user session."""
        if refresh_token_str:
            token_hash = hash_token(refresh_token_str)
            query = select(UserSession).where(UserSession.refresh_token_hash == token_hash)
            result = await db.execute(query)
            session = result.scalar_one_or_none()
            if session:
                session.is_revoked = True

        if user:
            await AuditService.log_event(
                db=db,
                event="LOGOUT",
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent
            )

        await db.commit()
        return True

    @staticmethod
    async def register_user(
        db: AsyncSession,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> User:
        """Register a new user with Argon2id password hash and assign VIEWER role."""
        normalized_email = email.strip().lower()

        # Check existing user
        existing_query = select(User).where(User.email == normalized_email)
        existing = (await db.execute(existing_query)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists"
            )

        # Fetch or create default VIEWER role
        role_query = select(Role).where(Role.name == "VIEWER")
        role = (await db.execute(role_query)).scalar_one_or_none()
        if not role:
            role = Role(name="VIEWER", description="Standard CCTV viewer")
            db.add(role)
            await db.flush()

        hashed_pwd = hash_password(password)
        new_user = User(
            email=normalized_email,
            hashed_password=hashed_pwd,
            full_name=full_name,
            is_active=True,
            is_superuser=False
        )
        new_user.roles.append(role)
        db.add(new_user)
        await db.flush()

        await AuditService.log_event(
            db=db,
            event="USER_REGISTERED",
            user_id=new_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"email": normalized_email, "role": "VIEWER"}
        )

        await db.commit()
        await db.refresh(new_user)
        return new_user
