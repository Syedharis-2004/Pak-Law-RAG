"""
PakLaw AI — Authentication Router Tests

Tests register, login, and access profiling API routes.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient):
    """Test user registration and subsequent token generation login verification."""
    register_payload = {
        "email": "testuser@paklaw.ai",
        "password": "Password123!",
        "full_name": "Test Lawyer",
        "organization": "Supreme Court",
        "designation": "Associate",
        "preferred_language": "en"
    }

    # 1. Register User
    res = await client.post("/api/v1/auth/register", json=register_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == register_payload["email"]
    assert data["full_name"] == register_payload["full_name"]

    # 2. Login User
    login_payload = {
        "email": register_payload["email"],
        "password": register_payload["password"]
    }
    res_login = await client.post("/api/v1/auth/login", json=login_payload)
    assert res_login.status_code == 200
    token_data = res_login.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["user"]["email"] == register_payload["email"]

    # 3. Retrieve User Profile
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    res_me = await client.get("/api/v1/auth/me", headers=headers)
    assert res_me.status_code == 200
    me_data = res_me.json()
    assert me_data["email"] == register_payload["email"]
