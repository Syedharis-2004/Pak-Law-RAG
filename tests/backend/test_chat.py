import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_chat_unauthorized(client: AsyncClient):
    response = await client.post("/api/v1/chat/query", json={"message": "hello"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_list_conversations(client: AsyncClient, user_token_headers: dict):
    response = await client.get("/api/v1/chat/conversations", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)

@pytest.mark.asyncio
async def test_chat_query_validation(client: AsyncClient, user_token_headers: dict):
    # Missing required message field
    response = await client.post("/api/v1/chat/query", headers=user_token_headers, json={})
    assert response.status_code == 422
