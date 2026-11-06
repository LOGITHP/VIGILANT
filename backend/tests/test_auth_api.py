import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert "VIGILANT" in data["system"]


@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient):
    # 1. Register a test user
    reg_payload = {
        "email": "operator1@vigilant.ai",
        "password": "Password123!",
        "full_name": "Test CCTV Operator"
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["email"] == "operator1@vigilant.ai"
    assert "VIEWER" in reg_data["roles"]

    # 2. Login with correct credentials
    login_payload = {
        "username": "operator1@vigilant.ai",
        "password": "Password123!"
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    tokens = login_res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["user"]["email"] == "operator1@vigilant.ai"

    # 3. Access protected /me endpoint
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "operator1@vigilant.ai"
    assert me_data["full_name"] == "Test CCTV Operator"

    # 4. Refresh token
    refresh_payload = {"refresh_token": tokens["refresh_token"]}
    refresh_res = await client.post("/api/v1/auth/refresh", json=refresh_payload)
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    # 5. Logout
    logout_payload = {"refresh_token": new_tokens["refresh_token"]}
    logout_res = await client.post(
        "/api/v1/auth/logout",
        json=logout_payload,
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"}
    )
    assert logout_res.status_code == 200
    assert "Successfully logged out" in logout_res.json()["message"]


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    # Register user first
    await client.post("/api/v1/auth/register", json={
        "email": "guard@vigilant.ai",
        "password": "CorrectPassword123"
    })

    # Attempt login with wrong password
    bad_res = await client.post("/api/v1/auth/login", json={
        "username": "guard@vigilant.ai",
        "password": "WrongPassword!"
    })
    assert bad_res.status_code == 401
    assert "Invalid username or password" in bad_res.json()["detail"]


@pytest.mark.asyncio
async def test_unauthorized_access_without_token(client: AsyncClient):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401
