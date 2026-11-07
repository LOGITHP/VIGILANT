import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from scripts.seed_first_user import seed_database
from app.models.user import User
from app.core.security import verify_password
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_seeding_creates_admin_and_is_idempotent(db_session: AsyncSession, monkeypatch):
    # Override AsyncSessionLocal to use the test db_session
    class DummyContext:
        async def __aenter__(self):
            return db_session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    def dummy_session_maker():
        return DummyContext()

    monkeypatch.setattr("scripts.seed_first_user.AsyncSessionLocal", dummy_session_maker)

    # 1. First run: should create cctv@gmail.com
    await seed_database()

    # Query user
    q = select(User).where(User.email == "cctv@gmail.com").options(selectinload(User.roles))
    res = await db_session.execute(q)
    user = res.scalar_one_or_none()
    assert user is not None
    assert user.email == "cctv@gmail.com"
    assert user.is_superuser is True
    assert any(r.name == "SUPERADMIN" for r in user.roles)
    assert verify_password("123456789", user.hashed_password) is True

    # Test AuthService authenticating with seeded credentials
    auth_user, access_token, refresh_token, _ = await AuthService.authenticate_user(
        db=db_session,
        username_or_email="cctv@gmail.com",
        password="123456789"
    )
    assert auth_user.id == user.id
    assert access_token is not None

    # 2. Second run: should be idempotent and not fail or duplicate
    await seed_database()

    # Verify count is still exactly 1
    count_q = select(User).where(User.email == "cctv@gmail.com")
    all_users = (await db_session.execute(count_q)).scalars().all()
    assert len(all_users) == 1
